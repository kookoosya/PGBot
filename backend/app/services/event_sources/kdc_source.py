"""KDC Pushgory culture center import."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.kdc_pushgory_service import KdcEvent, fetch_kdc_events

logger = logging.getLogger(__name__)


def _to_fetched(item: KdcEvent) -> FetchedEvent:
    return FetchedEvent(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        location=item.location,
        region=EventRegion.PUSHKIN_GORY,
        category=item.category,
        source="kdc",
        source_url=item.source_url,
        poster_url=item.poster_url,
    )


class KdcEventSource(EventSource):
    name = "kdc"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        if region is not None and region != EventRegion.PUSHKIN_GORY:
            return []
        raw = await fetch_kdc_events()
        return [_to_fetched(item) for item in raw]

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if region is not None and region != EventRegion.PUSHKIN_GORY:
            return [EventSyncResult(
                source="kdc",
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[f"KDC только для {EventRegion.PUSHKIN_GORY.value}"],
            )]

        errors: list[str] = []
        created = updated = skipped = 0
        items = await fetch_kdc_events()

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
                logger.exception("KDC import failed for %s", item.title)
                errors.append(str(exc))

        return [EventSyncResult(
            source="kdc",
            region=EventRegion.PUSHKIN_GORY.value,
            fetched=len(items),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]
