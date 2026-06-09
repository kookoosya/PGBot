"""TimePad event import adapter."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import EventRegion
from app.services.event_service import EventValidationError
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.timepad_service import (
    _parse_timepad_datetime,
    _event_location,
    fetch_timepad_events,
    infer_timepad_region,
    map_timepad_category,
    timepad_event_url,
)

logger = logging.getLogger(__name__)
settings = get_settings()
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def _item_to_fetched(item: dict) -> FetchedEvent | None:
    starts_at = _parse_timepad_datetime(item.get("starts_at"))
    if not starts_at:
        return None
    if starts_at < datetime.now(MOSCOW_TZ) - timedelta(days=1):
        return None

    title = (item.get("name") or "").strip()
    if len(title) < 3:
        return None

    description = (item.get("description_short") or item.get("description_html") or "")[:2000]
    ends_at = _parse_timepad_datetime(item.get("ends_at"))

    return FetchedEvent(
        title=title[:300],
        description=description or None,
        starts_at=starts_at,
        ends_at=ends_at,
        location=_event_location(item),
        region=infer_timepad_region(item),
        category=map_timepad_category(item),
        source="timepad",
        source_url=timepad_event_url(item),
    )


async def fetch_timepad_fetched_events(region: EventRegion | None = None) -> list[FetchedEvent]:
    raw = await fetch_timepad_events(limit=60)
    events: list[FetchedEvent] = []
    for item in raw:
        fetched = _item_to_fetched(item)
        if fetched and (region is None or fetched.region == region):
            events.append(fetched)
    return events


async def sync_events_from_timepad(
    db: AsyncSession,
    region: EventRegion | None = None,
    *,
    actor_id: int | None = None,
) -> EventSyncResult:
    token = (settings.TIMEPAD_API_TOKEN or "").strip()
    if not token:
        raise EventValidationError(
            "TimePad API недоступен. Укажите TIMEPAD_API_TOKEN в .env (dev.timepad.ru)."
        )

    errors: list[str] = []
    created = updated = skipped = 0
    items = await fetch_timepad_fetched_events(region)

    for item in items:
        try:
            action = await upsert_fetched_event(db, item, actor_id=actor_id)
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
            else:
                skipped += 1
        except Exception as exc:
            logger.exception("TimePad import failed for %s", item.source_url)
            errors.append(str(exc))

    return EventSyncResult(
        source="timepad",
        region=region.value if region else "all",
        fetched=len(items),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )


class TimePadEventSource(EventSource):
    name = "timepad"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        return await fetch_timepad_fetched_events(region)

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        return [await sync_events_from_timepad(db, region, actor_id=actor_id)]
