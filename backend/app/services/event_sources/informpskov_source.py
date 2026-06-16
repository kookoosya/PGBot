"""Informpskov.ru RSS import."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.informpskov_service import InformpskovEvent, fetch_informpskov_events

logger = logging.getLogger(__name__)


def _to_fetched(item: InformpskovEvent) -> FetchedEvent:
    return FetchedEvent(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        location=item.location,
        region=item.region,
        category=item.category,
        source="informpskov",
        source_url=item.source_url,
        poster_url=item.poster_url,
    )


class InformpskovEventSource(EventSource):
    name = "informpskov"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        items = await fetch_informpskov_events()
        if region is not None:
            items = [item for item in items if item.region == region]
        return [_to_fetched(item) for item in items]

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        errors: list[str] = []
        created = updated = skipped = 0
        items = await fetch_informpskov_events()
        if region is not None:
            items = [item for item in items if item.region == region]

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
                logger.exception("Informpskov import failed for %s", item.title)
                errors.append(str(exc))

        region_label = region.value if region else "all"
        return [EventSyncResult(
            source="informpskov",
            region=region_label,
            fetched=len(items),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]
