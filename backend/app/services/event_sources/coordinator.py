"""Event source registry and orchestrated sync."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion
from app.services.event_service import EventValidationError
from app.services.event_sources.base import EventSource, EventSyncResult
from app.services.event_sources.kudago_source import KudaGoEventSource
from app.services.event_sources.timepad_source import TimePadEventSource
from app.services.event_sources.vk_source import VkEventSource

_SOURCES: dict[str, EventSource] = {
    "vk": VkEventSource(),
    "timepad": TimePadEventSource(),
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
    return await source.sync_events(db, region=region, actor_id=actor_id)


async def sync_all_event_sources(
    db: AsyncSession,
    *,
    actor_id: int | None = None,
) -> list[EventSyncResult]:
    results: list[EventSyncResult] = []
    for name in ("vk", "timepad", "kudago"):
        try:
            results.extend(await sync_event_source(db, name, actor_id=actor_id))
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
    return results
