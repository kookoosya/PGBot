"""Drampush.ru theater afisha import."""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_sources.fetchers.drampush import DrampushEvent, fetch_drampush_events
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event

logger = logging.getLogger(__name__)


def _to_fetched(item: DrampushEvent) -> FetchedEvent:
    return FetchedEvent(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.starts_at + timedelta(hours=2, minutes=30),
        location=item.location,
        region=EventRegion.PSKOV,
        category=item.category,
        source="drampush",
        source_url=item.source_url,
    )


class DrampushEventSource(EventSource):
    name = "drampush"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        if region is not None and region != EventRegion.PSKOV:
            return []
        return [_to_fetched(item) for item in await fetch_drampush_events()]

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if region is not None and region != EventRegion.PSKOV:
            return [EventSyncResult(
                source="drampush",
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[f"Drampush только для {EventRegion.PSKOV.value}"],
            )]

        errors: list[str] = []
        created = updated = skipped = 0
        items = await fetch_drampush_events()

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
                logger.exception("Drampush import failed for %s", item.title)
                errors.append(str(exc))

        return [EventSyncResult(
            source="drampush",
            region=EventRegion.PSKOV.value,
            fetched=len(items),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]
