"""Shared text parsing for event posts (VK, etc.)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.constants.event_config import EVENT_CATEGORY_KEYWORDS
from app.models.enums import EventCategory

MOSCOW_TZ = ZoneInfo("Europe/Moscow")

_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})[.\-/](?P<month>\d{1,2})(?:[.\-/](?P<year>\d{2,4}))?"
    r"(?:\s+(?P<hour>\d{1,2})[:.](?P<minute>\d{2}))?",
    re.IGNORECASE,
)

_DATE_RANGE_NUMERIC_RE = re.compile(
    r"(?P<day1>\d{1,2})\s*(?:и|[-–—])\s*(?P<day2>\d{1,2})[.\-/](?P<month>\d{1,2})"
    r"(?:[.\-/](?P<year>\d{2,4}))?",
    re.IGNORECASE,
)

_DATE_NAMED_RE = re.compile(
    r"(?:(?P<day1>\d{1,2})\s*(?:и|[-–—])\s*)?(?P<day>\d{1,2})\s+"
    r"(?P<month>январ|феврал|март|апрел|мая|май|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*"
    r"(?:\s+(?P<year>\d{4}))?"
    r"(?:\s+(?:в|с)\s+(?P<hour>\d{1,2})[:.](?P<minute>\d{2}))?",
    re.IGNORECASE,
)

_DATE_RANGE_NAMED_RE = re.compile(
    r"(?P<day1>\d{1,2})\s*(?:и|[-–—])\s*(?P<day2>\d{1,2})\s+"
    r"(?P<month>январ|феврал|март|апрел|мая|май|июн|июл|август|сентябр|октябр|ноябр|декабр)\w*"
    r"(?:\s+(?P<year>\d{4}))?",
    re.IGNORECASE,
)

_MONTH_NUMBERS: dict[str, int] = {
    "январ": 1,
    "феврал": 2,
    "март": 3,
    "апрел": 4,
    "мая": 5,
    "май": 5,
    "июн": 6,
    "июл": 7,
    "август": 8,
    "сентябр": 9,
    "октябр": 10,
    "ноябр": 11,
    "декабр": 12,
}

VK_AD_KEYWORDS = (
    "реклам", "подписывайт", "розыгрыш", "скидк", "промокод",
    "спонсор", "партнёр", "партнер", "купить", "заказать",
    "доставк", "ваканси", "требуется", "набор сотрудник",
    "опрос", "голосован", "репост", "конкурс репост",
    "выиграй", "приз", "кэшбэк", "кешбэк", "cashback",
)

_KEYWORD_RE_CACHE: dict[str, re.Pattern[str]] = {}


def _keyword_in_text(text: str, keyword: str) -> bool:
    """Match keyword without false positives like «кино» inside «пушкиногорья»."""
    lower = text.lower()
    if keyword not in lower:
        return False
    if len(keyword) >= 5:
        return True
    cached = _KEYWORD_RE_CACHE.get(keyword)
    if cached is None:
        cached = re.compile(
            rf"(?<![а-яёa-z]){re.escape(keyword)}(?![а-яёa-z])",
            re.IGNORECASE,
        )
        _KEYWORD_RE_CACHE[keyword] = cached
    return cached.search(lower) is not None


def infer_category_from_text(text: str) -> EventCategory:
    """Guess event category from post text keywords."""
    lower = text.lower()
    for category, keywords in EVENT_CATEGORY_KEYWORDS.items():
        if any(_keyword_in_text(lower, keyword) for keyword in keywords):
            try:
                return EventCategory(category)
            except ValueError:
                continue
    if any(word in lower for word in ("музей", "пушкин", "михайловск", "бугров")):
        return EventCategory.CULTURE
    return EventCategory.OTHER


def _month_from_name(fragment: str) -> int:
    lower = fragment.lower()
    for prefix, num in _MONTH_NUMBERS.items():
        if lower.startswith(prefix):
            return num
    return 0


def _resolve_year(month: int, day: int, *, fallback: datetime, year_raw: str | None) -> int:
    if year_raw:
        year = int(year_raw)
        if year < 100:
            year += 2000
        return year
    year = fallback.year
    candidate = datetime(year, month, day, tzinfo=MOSCOW_TZ)
    if candidate < fallback.astimezone(MOSCOW_TZ) - timedelta(days=30):
        year += 1
    return year


def _build_datetime(
    *,
    day: int,
    month: int,
    year: int,
    hour: int | None = None,
    minute: int | None = None,
) -> datetime | None:
    try:
        return datetime(
            year,
            month,
            day,
            hour if hour is not None else 12,
            minute if minute is not None else 0,
            tzinfo=MOSCOW_TZ,
        )
    except ValueError:
        return None


def parse_event_date_range(
    text: str,
    *,
    fallback: datetime,
) -> tuple[datetime | None, datetime | None]:
    """Extract start/end datetimes for multi-day event announcements."""
    range_named = _DATE_RANGE_NAMED_RE.search(text)
    if range_named:
        month = _month_from_name(range_named.group("month"))
        if month:
            year = _resolve_year(month, int(range_named.group("day1")), fallback=fallback, year_raw=range_named.group("year"))
            day1 = int(range_named.group("day1"))
            day2 = int(range_named.group("day2"))
            starts = _build_datetime(day=day1, month=month, year=year)
            ends = _build_datetime(day=day2, month=month, year=year, hour=20)
            return starts, ends

    range_numeric = _DATE_RANGE_NUMERIC_RE.search(text)
    if range_numeric:
        month = int(range_numeric.group("month"))
        year = _resolve_year(month, int(range_numeric.group("day1")), fallback=fallback, year_raw=range_numeric.group("year"))
        starts = _build_datetime(day=int(range_numeric.group("day1")), month=month, year=year)
        ends = _build_datetime(day=int(range_numeric.group("day2")), month=month, year=year, hour=20)
        return starts, ends

    return _parse_single_event_datetime(text, fallback=fallback), None


def _parse_single_event_datetime(text: str, *, fallback: datetime) -> datetime | None:
    match = _DATE_RE.search(text)
    if match:
        day = int(match.group("day"))
        month = int(match.group("month"))
        year = _resolve_year(month, day, fallback=fallback, year_raw=match.group("year"))
        hour = int(match.group("hour") or 12)
        minute = int(match.group("minute") or 0)
        return _build_datetime(day=day, month=month, year=year, hour=hour, minute=minute)

    named = _DATE_NAMED_RE.search(text)
    if named:
        month = _month_from_name(named.group("month"))
        if month:
            day = int(named.group("day"))
            year = _resolve_year(month, day, fallback=fallback, year_raw=named.group("year"))
            hour = int(named.group("hour")) if named.group("hour") else None
            minute = int(named.group("minute")) if named.group("minute") else None
            return _build_datetime(day=day, month=month, year=year, hour=hour, minute=minute)

    return None


def parse_event_datetime(text: str, *, fallback: datetime) -> datetime | None:
    """Extract the first date/time from post text."""
    starts_at, _ = parse_event_date_range(text, fallback=fallback)
    return starts_at


def post_title(text: str) -> str:
    line = next((part.strip() for part in text.split("\n") if part.strip()), "Событие")
    return line[:300]


def is_relevant_event_post(text: str, *, parsed_date: datetime | None) -> bool:
    """Filter VK posts: require event signals, drop ads and noise."""
    from app.services.event_sources.vk_parsing import is_relevant_vk_event_post

    return is_relevant_vk_event_post(text, parsed_date=parsed_date)
