"""Orbilet regional afisha import adapter."""

from __future__ import annotations

import logging
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventCategory, EventRegion
from app.services.event_enrichment_service import resolve_cinema_location_from_text
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.orbilet_service import OrbiletEvent, fetch_orbilet_events
from app.services.region_inference import infer_event_region_from_text

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def _to_fetched(item: OrbiletEvent) -> FetchedEvent:
    region = infer_event_region_from_text(f"{item.title} {item.location or ''}")
    location = item.location
    if item.category == EventCategory.CINEMA and location:
        location = resolve_cinema_location_from_text(location, region=region) or location
    return FetchedEvent(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.starts_at + timedelta(hours=2),
        location=location,
        region=region,
        category=item.category,
        source="orbilet",
        source_url=item.source_url,
        genre=item.genre,
    )


class OrbiletEventSource(EventSource):
    name = "orbilet"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        raw = await fetch_orbilet_events()
        items = [_to_fetched(item) for item in raw]
        if region is not None:
            items = [item for item in items if item.region == region]
        return items

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        errors: list[str] = []
        created = updated = skipped = 0
        raw = await fetch_orbilet_events()
        items = [_to_fetched(item) for item in raw]
        if region is not None:
            items = [item for item in items if item.region == region]

        for fetched in items:
            try:
                action = await upsert_fetched_event(db, fetched, actor_id=actor_id)
                if action == "created":
                    created += 1
                elif action == "updated":
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:
                logger.exception("Orbilet import failed for %s", fetched.source_url)
                errors.append(str(exc))

        return [EventSyncResult(
            source="orbilet",
            region=region.value if region else "all",
            fetched=len(items),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]
