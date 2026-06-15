"""Kinopskov60 cinema import — Победа, Смена."""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.kinopskov_service import KinopskovEvent, fetch_kinopskov_events

logger = logging.getLogger(__name__)


def _to_fetched(item: KinopskovEvent) -> FetchedEvent:
    return FetchedEvent(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.starts_at + timedelta(hours=2, minutes=30),
        location=item.location,
        region=EventRegion.PSKOV,
        category=item.category,
        source="kinopskov",
        source_url=item.source_url,
        genre=item.genre,
        poster_url=item.poster_url,
    )


class KinopskovEventSource(EventSource):
    name = "kinopskov"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        if region is not None and region != EventRegion.PSKOV:
            return []
        raw = await fetch_kinopskov_events()
        return [_to_fetched(item) for item in raw]

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if region is not None and region != EventRegion.PSKOV:
            return [EventSyncResult(
                source="kinopskov",
                region=region.value,
                fetched=0, created=0, updated=0, skipped=0,
                errors=[f"Kinopskov только для {EventRegion.PSKOV.value}"],
            )]

        errors: list[str] = []
        created = updated = skipped = 0
        items = await fetch_kinopskov_events()

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
                logger.exception("Kinopskov import failed for %s", item.title)
                errors.append(str(exc))

        return [EventSyncResult(
            source="kinopskov",
            region=EventRegion.PSKOV.value,
            fetched=len(items),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]
