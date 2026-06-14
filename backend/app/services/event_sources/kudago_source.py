"""KudaGo event source adapter (wraps existing service)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_sources.base import EventSource, EventSyncResult
from app.services.kudago_service import sync_all_kudago_sources, sync_events_from_kudago


class KudaGoEventSource(EventSource):
    name = "kudago"

    async def fetch_events(self, region: EventRegion | None = None) -> list:
        # KudaGo adapter works via direct upsert; fetch is internal to kudago_service.
        return []

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if region:
            result = await sync_events_from_kudago(db, region, actor_id=actor_id)
            return [_kudago_to_result(result)]
        return [_kudago_to_result(r) for r in await sync_all_kudago_sources(db, actor_id=actor_id)]


def _kudago_to_result(result) -> EventSyncResult:
    return EventSyncResult(
        source="kudago",
        region=result.region,
        fetched=result.fetched,
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        errors=result.errors,
    )
