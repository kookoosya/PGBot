"""Tests for event date parsing from Russian text."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.event_sources.text_utils import parse_event_date_range, parse_event_datetime

MOSCOW = ZoneInfo("Europe/Moscow")
FALLBACK = datetime(2026, 6, 1, 10, 0, tzinfo=MOSCOW)


def test_parse_named_month_date():
    result = parse_event_datetime("Фестиваль 19 июня в 18:00", fallback=FALLBACK)
    assert result is not None
    assert result.day == 19
    assert result.month == 6
    assert result.year == 2026
    assert result.hour == 18


def test_parse_date_range_named():
    start, end = parse_event_date_range(
        "Бугровский гарнец — 19 и 20 июня 2026 в Бугрово",
        fallback=FALLBACK,
    )
    assert start is not None
    assert end is not None
    assert start.day == 19
    assert end.day == 20
    assert start.month == 6
    assert end.month == 6


def test_parse_date_range_numeric():
    start, end = parse_event_date_range("Анонс 19-20.06.2026", fallback=FALLBACK)
    assert start is not None
    assert end is not None
    assert start.day == 19
    assert end.day == 20


def test_find_upcoming_skips_past_keeps_future():
    from app.services.event_sources.text_utils import find_upcoming_event_range

    now = datetime(2026, 6, 16, 12, 0, tzinfo=MOSCOW)
    text = "Репортаж 10 июня прошёл. Приглашаем 21 июня на концерт."
    start, end = find_upcoming_event_range(text, fallback=now, now=now)
    assert start is not None
    assert start.day == 21


def test_find_upcoming_date_range():
    from app.services.event_sources.text_utils import find_upcoming_event_range

    now = datetime(2026, 6, 10, 12, 0, tzinfo=MOSCOW)
    start, end = find_upcoming_event_range(
        "«Бугровский гарнец» 19 и 20 июня 2026",
        fallback=now,
        now=now,
    )
    assert start is not None
    assert start.day == 19
    assert end is not None
    assert end.day == 20


def test_parse_numeric_date_with_time():
    result = parse_event_datetime("Старт 19.06.2026 15:30", fallback=FALLBACK)
    assert result is not None
    assert result.day == 19
    assert result.hour == 15
    assert result.minute == 30
