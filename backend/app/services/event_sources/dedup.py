"""Deduplication helpers for event imports."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
_TITLE_NORMALIZE_RE = re.compile(r"[^\w\s]+", re.UNICODE)


def normalize_event_title(title: str) -> str:
    """Lowercase alphanumeric title for fuzzy duplicate checks."""
    cleaned = _TITLE_NORMALIZE_RE.sub(" ", title.lower())
    return " ".join(cleaned.split())


async def find_existing_event(
    db: AsyncSession,
    *,
    source_url: str | None,
    title: str,
    starts_at: datetime,
    region: str | None = None,
    location: str | None = None,
) -> Event | None:
    """Find duplicate by ``source_url`` or same show (title + minute + region + venue)."""
    if source_url:
        by_url = await db.execute(
            select(Event)
            .where(Event.source_url == source_url)
            .order_by(Event.id.asc())
            .limit(1)
        )
        existing = by_url.scalars().first()
        if existing:
            return existing

    normalized = normalize_event_title(title)
    if len(normalized) < 4:
        return None

    starts_moscow = starts_at.astimezone(MOSCOW_TZ).replace(second=0, microsecond=0)
    window_start = starts_moscow - timedelta(minutes=5)
    window_end = starts_moscow + timedelta(minutes=5)
    loc_key = " ".join((location or "").lower().split())

    result = await db.execute(
        select(Event).where(
            Event.starts_at >= window_start,
            Event.starts_at <= window_end,
        )
    )
    for candidate in result.scalars().all():
        if region and candidate.region != region:
            continue
        cand_title = normalize_event_title(candidate.title)
        if cand_title != normalized and not _titles_similar(normalized, cand_title):
            continue
        cand_loc = " ".join((candidate.location or "").lower().split())
        if loc_key and cand_loc and loc_key != cand_loc:
            continue
        return candidate

    # Fallback: same title on the same calendar day (merge orbilet session URL updates)
    day_start = starts_moscow.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    result = await db.execute(
        select(Event).where(
            Event.starts_at >= day_start,
            Event.starts_at < day_end,
        )
    )
    for candidate in result.scalars().all():
        if region and candidate.region != region:
            continue
        cand_title = normalize_event_title(candidate.title)
        if cand_title == normalized or _titles_similar(normalized, cand_title):
            cand_loc = " ".join((candidate.location or "").lower().split())
            if loc_key and cand_loc and loc_key != cand_loc:
                continue
            return candidate
    return None


def _titles_similar(a: str, b: str) -> bool:
    """True when titles share a long common prefix (≥ 70% of shorter)."""
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if shorter in longer:
        return len(shorter) >= max(12, int(len(longer) * 0.6))
    prefix = 0
    for left, right in zip(a, b, strict=False):
        if left != right:
            break
        prefix += 1
    return prefix >= max(15, int(min(len(a), len(b)) * 0.7))
