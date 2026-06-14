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
) -> Event | None:
    """Find duplicate by ``source_url`` or similar title on the same calendar day."""
    if source_url:
        by_url = await db.execute(select(Event).where(Event.source_url == source_url))
        existing = by_url.scalar_one_or_none()
        if existing:
            return existing

    starts_moscow = starts_at.astimezone(MOSCOW_TZ)
    day_start = starts_moscow.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    normalized = normalize_event_title(title)
    if len(normalized) < 8:
        return None

    result = await db.execute(
        select(Event).where(
            Event.starts_at >= day_start,
            Event.starts_at < day_end,
        )
    )
    for candidate in result.scalars().all():
        if normalize_event_title(candidate.title) == normalized:
            return candidate
        if _titles_similar(normalized, normalize_event_title(candidate.title)):
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
