"""Event source registry and orchestrated sync."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_service import EventValidationError
from app.services.event_sources.base import EventSource, EventSyncResult
from app.services.event_sources.kudago_source import KudaGoEventSource
from app.services.event_sources.orbilet_source import OrbiletEventSource
from app.services.event_sources.proculture_source import ProCultureEventSource
from app.services.event_sources.timepad_source import TimePadEventSource
from app.services.event_dedupe_service import cleanup_duplicate_events, unpublish_stale_demo_cinema
from app.services.vk_wall_publisher import publish_relevant_events_to_wall
from app.services.event_enrichment_batch import (
    enrich_missing_posters,
    enrich_stale_events,
    recategorize_other_events,
)
from app.services.event_sources.vk_source import VkEventSource

logger = logging.getLogger(__name__)

_SOURCES: dict[str, EventSource] = {
    "vk": VkEventSource(),
    "timepad": TimePadEventSource(),
    "orbilet": OrbiletEventSource(),
    "proculture": ProCultureEventSource(),
    "kudago": KudaGoEventSource(),
}


def get_event_source(name: str) -> EventSource | None:
    return _SOURCES.get(name)


def list_event_sources() -> list[str]:
    return list(_SOURCES.keys())


async def sync_event_source(
    db: AsyncSession,
    source_name: str,
    *,
    region: EventRegion | None = None,
    actor_id: int | None = None,
) -> list[EventSyncResult]:
    source = get_event_source(source_name)
    if not source:
        return [EventSyncResult(
            source=source_name,
            region=region.value if region else "all",
            fetched=0,
            created=0,
            updated=0,
            skipped=0,
            errors=[f"Неизвестный источник: {source_name}"],
        )]
    results = await source.sync_events(db, region=region, actor_id=actor_id)
    recategorized = await recategorize_other_events(db)
    enriched = await enrich_stale_events(db)
    posters = await enrich_missing_posters(db)
    removed = await cleanup_duplicate_events(db)
    demos = await unpublish_stale_demo_cinema(db)
    if enriched:
        logger.info("Post-sync event enrichment (%s): %s events updated", source_name, enriched)
    if posters:
        logger.info("Post-sync poster enrichment (%s): %s events updated", source_name, posters)
    if removed or demos:
        logger.info("Post-sync dedupe (%s): -%s dupes, -%s demo cinema", source_name, removed, demos)
    wall = await publish_relevant_events_to_wall(db)
    if wall:
        logger.info("Post-sync VK wall (%s): %s posts", source_name, wall)
    return results


async def sync_all_event_sources(
    db: AsyncSession,
    *,
    actor_id: int | None = None,
) -> list[EventSyncResult]:
    results: list[EventSyncResult] = []
    for name in ("vk", "timepad", "orbilet", "proculture", "kudago"):
        source = get_event_source(name)
        if not source:
            continue
        try:
            results.extend(await source.sync_events(db, actor_id=actor_id))
        except EventValidationError as exc:
            results.append(EventSyncResult(
                source=name,
                region="all",
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[exc.detail],
            ))
        except Exception as exc:
            results.append(EventSyncResult(
                source=name,
                region="all",
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[str(exc)],
            ))
    recategorized = await recategorize_other_events(db)
    enriched = await enrich_stale_events(db)
    posters = await enrich_missing_posters(db)
    removed = await cleanup_duplicate_events(db)
    demos = await unpublish_stale_demo_cinema(db)
    if enriched:
        logger.info("Post-sync event enrichment: %s events updated", enriched)
    if posters:
        logger.info("Post-sync poster enrichment: %s events updated", posters)
    if removed or demos:
        logger.info("Post-sync dedupe: -%s dupes, -%s demo cinema", removed, demos)
    wall = await publish_relevant_events_to_wall(db)
    if wall:
        logger.info("Post-sync VK wall: %s posts", wall)
    return results
