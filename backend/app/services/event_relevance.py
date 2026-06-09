"""Score events for VK wall and digest promotion."""

from __future__ import annotations

from datetime import datetime, timezone

from app.models.enums import EventCategory, EventRegion
from app.models.event import Event

_SOURCE_BONUS = {
    "orbilet": 12,
    "vk": 10,
    "timepad": 10,
    "proculture": 8,
    "manual": 2,
}


def score_event_for_promotion(event: Event, *, now: datetime | None = None) -> int:
    """Higher = more worthy of a VK wall post."""
    ref = now or datetime.now(timezone.utc)
    score = 0

    try:
        category = EventCategory(event.category)
    except ValueError:
        category = EventCategory.OTHER

    if category == EventCategory.CINEMA:
        score += 35
    elif category in (EventCategory.CULTURE, EventCategory.HOLIDAY):
        score += 28
    elif category == EventCategory.TOURISM:
        score += 22
    else:
        score += 12

    try:
        region = EventRegion(event.region)
    except ValueError:
        region = None

    if region == EventRegion.PSKOV:
        score += 10
    if region == EventRegion.PUSHKIN_GORY:
        score += 15

    if (event.poster_url or "").strip():
        score += 18
    if (event.genre or "").strip():
        score += 8
    if event.description and len(event.description.strip()) >= 60:
        score += 10

    score += _SOURCE_BONUS.get((event.source or "").strip(), 0)

    starts = event.starts_at
    if starts.tzinfo is None:
        starts = starts.replace(tzinfo=timezone.utc)
    hours = (starts - ref).total_seconds() / 3600
    if 0 <= hours <= 48:
        score += 30
    elif 0 <= hours <= 168:
        score += 18
    elif hours < 0:
        score -= 50

    title = (event.title or "").lower()
    if any(skip in title for skip in ("тест", "демо", "премьера недели")):
        score -= 40

    return score


def is_wall_worthy(event: Event, *, min_score: int = 40) -> bool:
    return score_event_for_promotion(event) >= min_score
