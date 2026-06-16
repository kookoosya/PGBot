"""Upsert date normalization."""

from datetime import datetime, timezone

from app.services.event_sources.upsert import _normalize_ends_at


def test_normalize_ends_at_drops_invalid():
    start = datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 19, 20, 0, tzinfo=timezone.utc)
    assert _normalize_ends_at(start, end) is None


def test_normalize_ends_at_keeps_valid():
    start = datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 20, 20, 0, tzinfo=timezone.utc)
    assert _normalize_ends_at(start, end) == end
