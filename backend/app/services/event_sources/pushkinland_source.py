"""Pushkinland.ru museum calendar import."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.models.event import Event
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.event_sources.fetchers.pushkinland import PushkinlandEvent, fetch_pushkinland_events

logger = logging.getLogger(__name__)


async def _unpublish_superseded_festival_parents(
    db: AsyncSession,
    items: list[PushkinlandEvent],
) -> int:
    """Hide multi-day festival umbrella rows replaced by per-show program entries."""
    by_url: dict[str, list[PushkinlandEvent]] = {}
    for item in items:
        if "/news/" in item.source_url:
            by_url.setdefault(item.source_url, []).append(item)

    unpublished = 0
    for url, group in by_url.items():
        if len(group) < 2:
            continue
        result = await db.execute(
            select(Event).where(
                Event.source == "pushkinland",
                Event.source_url == url,
                Event.is_published.is_(True),
                Event.title.ilike("%фестиваль%"),
                Event.title.ilike("%гарнец%"),
            )
        )
        for parent in result.scalars().all():
            if not parent.ends_at or not parent.starts_at:
                continue
            if (parent.ends_at.date() - parent.starts_at.date()).days < 1:
                continue
            parent.is_published = False
            unpublished += 1
    if unpublished:
        await db.flush()
    return unpublished


def _to_fetched(item: PushkinlandEvent) -> FetchedEvent:
    return FetchedEvent(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        location=item.location,
        region=EventRegion.PUSHKIN_GORY,
        category=item.category,
        source="pushkinland",
        source_url=item.source_url,
    )


class PushkinlandEventSource(EventSource):
    name = "pushkinland"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        if region is not None and region != EventRegion.PUSHKIN_GORY:
            return []
        return [_to_fetched(item) for item in await fetch_pushkinland_events()]

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if region is not None and region != EventRegion.PUSHKIN_GORY:
            return [EventSyncResult(
                source="pushkinland",
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[f"Pushkinland только для {EventRegion.PUSHKIN_GORY.value}"],
            )]

        errors: list[str] = []
        created = updated = skipped = 0
        items = await fetch_pushkinland_events()

        for item in items:
            try:
                action = await upsert_fetched_event(db, _to_fetched(item), actor_id=actor_id)
                if action == "created":
                    created += 1
                elif action == "updated":
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:
                logger.exception("Pushkinland import failed for %s", item.title)
                errors.append(str(exc))

        await _unpublish_superseded_festival_parents(db, items)

        return [EventSyncResult(
            source="pushkinland",
            region=EventRegion.PUSHKIN_GORY.value,
            fetched=len(items),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]
