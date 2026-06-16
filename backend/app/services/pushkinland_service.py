"""Pushkinland.ru — official Mikhailovskoe museum calendar."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.models.enums import EventCategory, EventRegion

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
PUSHKINLAND_BASE_URL = "https://pushkinland.ru"
DEFAULT_LOCATION = "Пушкинские Горы, Михайловское"

_ROW_BLOCK_RE = re.compile(
    r'<div class="three wide column">\s*<p class="ab"><b>\s*(?P<date>[^<]+?)\s*</b></p>\s*</div>\s*'
    r'<div class="thirteen wide column">\s*<p class="ab">(?P<body>.*?)</p>',
    re.DOTALL | re.IGNORECASE,
)
_LINK_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
_SKIP_DATE_RE = re.compile(r"по\s+заявк", re.IGNORECASE)
_MONTH_NAME_RE = re.compile(
    r"январ|феврал|март|апрел|мая|май|июн|июл|август|сентябр|октябр|ноябр|декабр",
    re.IGNORECASE,
)
_MAX_SPAN_DAYS = 45
_KEEP_MULTI_MONTH_RE = re.compile(
    r"фестиваль|концерт|праздник|спектакл|гарнец|лекци|ярмарк",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class PushkinlandEvent:
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    location: str
    category: EventCategory
    source_url: str


def calendar_url_for_year(year: int) -> str:
    suffix = f"{year % 100:02d}"
    return f"{PUSHKINLAND_BASE_URL}/2018/calend/calend{suffix}/calend{suffix}.php"


def _normalize_text(value: str) -> str:
    cleaned = value.replace("\xa0", " ").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def _strip_tags(value: str) -> str:
    return _normalize_text(html.unescape(re.sub(r"<[^>]+>", " ", value)))


def _clean_title(title: str) -> str:
    cleaned = _normalize_text(title)
    cleaned = re.sub(r"([»\"])\s*\.\s*", r"\1. ", cleaned)
    cleaned = re.sub(r"\s+\.\s+", " — ", cleaned)
    cleaned = re.sub(r"^\.\s+", "", cleaned)
    return cleaned.strip(" .")


def _extract_title_and_url(body: str) -> tuple[str, str | None]:
    link_match = _LINK_RE.search(body)
    source_url = None
    if link_match:
        href = link_match.group(1)
        source_url = href if href.startswith("http") else f"{PUSHKINLAND_BASE_URL}{href}"
    title = _clean_title(_strip_tags(body))
    return title[:300], source_url


def _infer_location(title: str) -> str:
    lower = title.lower()
    for place, label in (
        ("бугров", "Бугрово, Пушкинские Горы"),
        ("тригорск", "Тригорское, Пушкинские Горы"),
        ("петровск", "Петровское, Пушкинские Горы"),
        ("михайловск", "Михайловское, Пушкинские Горы"),
        ("воткинск", "Воткинск"),
    ):
        if place in lower:
            return label
    return DEFAULT_LOCATION


def _should_skip_span(starts_at: datetime, ends_at: datetime | None, *, title: str) -> bool:
    if ends_at is None:
        return False
    span_days = (ends_at.date() - starts_at.date()).days
    if span_days <= _MAX_SPAN_DAYS:
        return False
    lower = title.lower()
    if any(word in lower for word in ("фестиваль", "концерт", "праздник", "спектакл", "гарнец")):
        return False
    return True


def _is_long_running_date(date_raw: str, *, title: str) -> bool:
    months = {match.group(0).lower()[:5] for match in _MONTH_NAME_RE.finditer(date_raw)}
    if len(months) < 2:
        return False
    return _KEEP_MULTI_MONTH_RE.search(title) is None


def parse_pushkinland_calendar(page: str, *, year: int | None = None) -> list[PushkinlandEvent]:
    """Parse museum calendar HTML into upcoming events."""
    from app.services.event_sources.text_utils import infer_category_from_text, parse_event_date_range

    now = datetime.now(MOSCOW_TZ)
    year = year or now.year
    default_url = calendar_url_for_year(year)
    events: list[PushkinlandEvent] = []
    seen: set[tuple[str, str]] = set()

    for match in _ROW_BLOCK_RE.finditer(page):
        date_raw = _normalize_text(match.group("date"))
        body = match.group("body")
        if not date_raw or not re.search(r"\d", date_raw):
            continue
        if _SKIP_DATE_RE.search(date_raw):
            continue

        title, source_url = _extract_title_and_url(body)
        if len(title) < 6:
            continue
        if _is_long_running_date(date_raw, title=title):
            continue

        combined = f"{date_raw}. {title}"
        try:
            starts_at, ends_at = parse_event_date_range(combined, fallback=now)
        except ValueError:
            continue
        if not starts_at:
            continue
        if starts_at < now - timedelta(days=2):
            continue
        if starts_at > now + timedelta(days=150):
            continue
        if _should_skip_span(starts_at, ends_at, title=title):
            continue

        key = (title.lower(), starts_at.date().isoformat())
        if key in seen:
            continue
        seen.add(key)

        events.append(
            PushkinlandEvent(
                title=title,
                description=None,
                starts_at=starts_at,
                ends_at=ends_at,
                location=_infer_location(title),
                category=infer_category_from_text(combined),
                source_url=source_url or default_url,
            )
        )

    events.sort(key=lambda item: item.starts_at)
    return events


async def fetch_pushkinland_events(*, year: int | None = None) -> list[PushkinlandEvent]:
    """Fetch and parse the museum events calendar for ``year`` (default: current)."""
    now = datetime.now(MOSCOW_TZ)
    year = year or now.year
    url = calendar_url_for_year(year)
    headers = {"User-Agent": "PGBot-Events/1.0 (+https://192-210-213-135.sslip.io/events)"}

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            page = response.content.decode("cp1251", errors="replace")
            return parse_pushkinland_calendar(page, year=year)
    except Exception:
        logger.exception("Pushkinland calendar fetch failed")
        return []
