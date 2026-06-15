"""Unit tests for event deduplication in the public feed."""

from datetime import datetime, timezone

from app.models.event import Event
from app.services.event_dedupe_service import (
    dedupe_display_events,
    event_dedupe_key,
    group_events_by_show,
)


def _event(
    id: int,
    title: str,
    *,
    starts_at: datetime | None = None,
    source: str = "vk",
    location: str = "Кинотеатр Мираж",
    region: str = "pskov",
    category: str = "cinema",
    poster_url: str | None = None,
    description: str = "",
) -> Event:
    return Event(
        id=id,
        title=title,
        starts_at=starts_at or datetime(2026, 6, 10, 18, 0, tzinfo=timezone.utc),
        location=location,
        region=region,
        category=category,
        source=source,
        poster_url=poster_url,
        description=description,
        is_published=True,
    )


def test_event_dedupe_key_normalizes_title():
    a = _event(1, "«Майкл»")
    b = _event(2, "майкл")
    assert event_dedupe_key(a) == event_dedupe_key(b)


def test_dedupe_display_events_keeps_richest_source():
    vk = _event(1, "Майкл", source="vk", description="short")
    orbilet = _event(2, "Майкл", source="orbilet", poster_url="https://x/p.jpg", description="longer text")
    result = dedupe_display_events([vk, orbilet])
    assert len(result) == 1
    assert result[0].id == 2


def test_dedupe_display_events_preserves_chronological_order():
    early = _event(1, "Концерт А", starts_at=datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc), category="culture")
    late = _event(2, "Концерт Б", starts_at=datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc), category="culture")
    dup = _event(3, "Концерт А", starts_at=early.starts_at, source="orbilet", category="culture")
    result = dedupe_display_events([early, late, dup])
    assert [e.id for e in result] == [3, 2]


def test_group_events_by_show_keeps_nearest_session():
    late = _event(1, "Дюна", starts_at=datetime(2026, 6, 12, 21, 0, tzinfo=timezone.utc))
    early = _event(2, "Дюна", starts_at=datetime(2026, 6, 10, 18, 0, tzinfo=timezone.utc))
    result = group_events_by_show([late, early])
    assert len(result) == 1
    assert result[0].id == 2


def test_different_venues_are_not_merged():
    a = _event(1, "Майкл", location="Мираж")
    b = _event(2, "Майкл", location="Сильвер Сити")
    assert event_dedupe_key(a) != event_dedupe_key(b)
    assert len(dedupe_display_events([a, b])) == 2
