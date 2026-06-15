"""Unit tests for event title normalization."""

from app.services.event_dedupe_service import event_dedupe_key
from app.services.event_title_utils import normalize_event_title


def test_normalize_event_title_strips_punctuation():
    assert normalize_event_title("«Майкл»") == normalize_event_title("Майкл")


def test_normalize_event_title_collapses_spaces():
    assert normalize_event_title("  Дюна   2  ") == "дюна 2"


def test_dedupe_key_uses_normalized_title():
    from datetime import datetime, timezone

    from app.models.event import Event

    a = Event(
        id=1,
        title="«Концерт»",
        starts_at=datetime(2026, 6, 10, 18, 0, tzinfo=timezone.utc),
        location="НКЦ",
        region="pushkin_gory",
        category="culture",
        is_published=True,
    )
    b = Event(
        id=2,
        title="концерт",
        starts_at=a.starts_at,
        location="НКЦ",
        region="pushkin_gory",
        category="culture",
        is_published=True,
    )
    assert event_dedupe_key(a) == event_dedupe_key(b)
