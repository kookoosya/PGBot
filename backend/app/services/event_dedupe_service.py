"""Remove and hide duplicate events in the public feed."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.services.event_sources.dedup import normalize_event_title

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

_SOURCE_PRIORITY = {
    "orbilet": 5,
    "vk": 4,
    "timepad": 4,
    "proculture": 4,
    "kudago": 3,
    "manual": 1,
}


def _starts_key(starts_at: datetime) -> str:
    local = starts_at.astimezone(MOSCOW_TZ).replace(second=0, microsecond=0)
    return local.isoformat()


def _location_key(location: str | None) -> str:
    return " ".join((location or "").lower().split())[:120]


def event_dedupe_key(event: Event) -> tuple[str, str, str, str, str]:
    """Identity for duplicate detection: title + time + region + category + venue."""
    return (
        normalize_event_title(event.title),
        _starts_key(event.starts_at),
        event.region or "",
        event.category or "",
        _location_key(event.location),
    )


def _rank_event(event: Event) -> tuple[int, int, int, int]:
    source = _SOURCE_PRIORITY.get((event.source or "").strip(), 0)
    poster = 1 if (event.poster_url or "").strip() else 0
    desc = len((event.description or "").strip())
    return (source, poster, desc, -event.id)


def dedupe_display_events(events: list[Event]) -> list[Event]:
    """Keep the richest single card per show (same title, time, venue)."""
    best: dict[tuple[str, str, str, str, str], Event] = {}
    for event in events:
        key = event_dedupe_key(event)
        current = best.get(key)
        if current is None or _rank_event(event) > _rank_event(current):
            best[key] = event
    # Preserve chronological order from input
    seen: set[int] = set()
    result: list[Event] = []
    for event in events:
        key = event_dedupe_key(event)
        winner = best[key]
        if winner.id in seen:
            continue
        seen.add(winner.id)
        result.append(winner)
    return result


async def cleanup_duplicate_events(db: AsyncSession) -> int:
    """Unpublish duplicate rows, keeping the best source per show."""
    result = await db.execute(
        select(Event).where(Event.is_published.is_(True)).order_by(Event.starts_at.asc())
    )
    events = list(result.scalars().all())
    groups: dict[tuple[str, str, str, str, str], list[Event]] = {}
    for event in events:
        groups.setdefault(event_dedupe_key(event), []).append(event)

    removed = 0
    for group in groups.values():
        if len(group) < 2:
            continue
        group.sort(key=_rank_event, reverse=True)
        for duplicate in group[1:]:
            duplicate.is_published = False
            removed += 1

    if removed:
        await db.flush()
        logger.info("Unpublished %s duplicate events", removed)
    return removed


async def unpublish_stale_demo_cinema(db: AsyncSession) -> int:
    """Hide hand-seeded cinema cards when real afisha sources exist."""
    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == "cinema",
            Event.source == "manual",
        )
    )
    demos = list(result.scalars().all())
    if not demos:
        return 0

    real = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == "cinema",
            Event.source.in_(("orbilet", "vk", "timepad", "proculture")),
        ).limit(1)
    )
    if not real.scalar_one_or_none():
        return 0

    count = 0
    for event in demos:
        loc = (event.location or "").lower()
        if "русь" in loc or event.source_url in (None, "", "https://kudago.com/pskov/"):
            event.is_published = False
            count += 1
    if count:
        await db.flush()
        logger.info("Unpublished %s stale demo cinema events", count)
    return count
