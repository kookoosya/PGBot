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

_MONTH_NAMES = (
    "январ", "феврал", "март", "апрел", "мая", "июн",
    "июл", "август", "сентябр", "октябр", "ноябр", "декабр",
)

VK_AD_KEYWORDS = (
    "реклам", "подписывайт", "розыгрыш", "скидк", "промокод",
    "спонсор", "партнёр", "партнер", "купить", "заказать",
    "доставк", "ваканси", "требуется", "набор сотрудник",
    "опрос", "голосован", "репост", "конкурс репост",
    "выиграй", "приз", "кэшбэк", "кешбэк", "cashback",
)


def infer_category_from_text(text: str) -> EventCategory:
    """Guess event category from post text keywords."""
    lower = text.lower()
    for category, keywords in EVENT_CATEGORY_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            try:
                return EventCategory(category)
            except ValueError:
                continue
    if any(word in lower for word in (
        "музей", "пушкин", "михайловск", "планетар", "полнокупольн",
        "спектакл", "салон", "филармон", "библиотек", "сказк",
    )):
        return EventCategory.CULTURE
    if "экскурс" in lower:
        return EventCategory.TOURISM
    return EventCategory.OTHER


def parse_event_datetime(text: str, *, fallback: datetime) -> datetime | None:
    """Extract the first date/time from post text."""
    match = _DATE_RE.search(text)
    if not match:
        return None

    day = int(match.group("day"))
    month = int(match.group("month"))
    year_raw = match.group("year")
    if year_raw:
        year = int(year_raw)
        if year < 100:
            year += 2000
    else:
        year = fallback.year
        candidate = datetime(year, month, day, tzinfo=MOSCOW_TZ)
        if candidate < fallback.astimezone(MOSCOW_TZ) - timedelta(days=30):
            year += 1

    hour = int(match.group("hour") or 12)
    minute = int(match.group("minute") or 0)
    try:
        return datetime(year, month, day, hour, minute, tzinfo=MOSCOW_TZ)
    except ValueError:
        return None


def post_title(text: str) -> str:
    line = next((part.strip() for part in text.split("\n") if part.strip()), "Событие")
    return line[:300]


def is_relevant_event_post(text: str, *, parsed_date: datetime | None) -> bool:
    """Filter VK posts: require event signals, drop ads and noise."""
    from app.services.event_sources.vk_parsing import is_relevant_vk_event_post

    return is_relevant_vk_event_post(text, parsed_date=parsed_date)
