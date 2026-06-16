"""Pskov drama theater afisha — drampush.ru (Listim widget HTML)."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.models.enums import EventCategory

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
DRAMPUSH_AFISHA_URL = "https://drampush.ru/afisha/"
DEFAULT_LOCATION = "Псков, театр драмы им. А.С. Пушкина"

_AFISHA_START_RE = re.compile(r'<div class="afishalist"[^>]*data-date="(\d{8})"[^>]*>', re.IGNORECASE)
_TIME_RE = re.compile(r'<div class="news_date">.*?<div>\s*(\d{1,2}:\d{2})\s*</div>', re.DOTALL)
_TITLE_RE = re.compile(r"<h2>\s*<a[^>]*>([^<]+)</a>", re.IGNORECASE)
_EVENT_ID_RE = re.compile(r"event_id:\s*(\d+)")
_PLACE_RE = re.compile(r"data-place=\"([^\"]+)\"")
_VENUE_RE = re.compile(r"Большая сцена|Маленький театр|Новый зал|Буфет|Варлаамовская башня", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class DrampushEvent:
    title: str
    description: str | None
    starts_at: datetime
    location: str
    category: EventCategory
    source_url: str


def _venue_label(raw_place: str | None, body: str) -> str:
    venue = _VENUE_RE.search(body)
    if venue:
        return f"Псков, {venue.group(0)}"
    if raw_place:
        mapping = {
            "большаясцена": "Большая сцена",
            "маленькийтеатр": "Маленький театр",
            "новыйзал": "Новый зал",
        }
        label = mapping.get(raw_place.lower(), raw_place)
        return f"Псков, {label}"
    return DEFAULT_LOCATION


def _parse_page(page: str) -> list[DrampushEvent]:
    now = datetime.now(MOSCOW_TZ)
    events: list[DrampushEvent] = []
    seen: set[tuple[str, str]] = set()

    starts = list(_AFISHA_START_RE.finditer(page))
    for index, match in enumerate(starts):
        date_raw = match.group(1)
        end = starts[index + 1].start() if index + 1 < len(starts) else len(page)
        block = page[match.start() : end]
        year, month, day = int(date_raw[:4]), int(date_raw[4:6]), int(date_raw[6:8])
        time_match = _TIME_RE.search(block)
        hour, minute = (12, 0)
        if time_match:
            hour, minute = (int(x) for x in time_match.group(1).split(":"))
        starts_at = datetime(year, month, day, hour, minute, tzinfo=MOSCOW_TZ)
        if starts_at < now - timedelta(hours=2):
            continue
        if starts_at > now + timedelta(days=120):
            continue

        title_match = _TITLE_RE.search(block)
        if not title_match:
            continue
        title = html.unescape(title_match.group(1)).strip()
        title = re.sub(r"^ПРЕМЬЕРА\.\s*", "", title, flags=re.IGNORECASE).strip()
        if len(title) < 3:
            continue

        place_match = _PLACE_RE.search(block)
        location = _venue_label(place_match.group(1) if place_match else None, block)
        event_id = _EVENT_ID_RE.search(block)
        source_url = (
            f"https://drampush.ru/afisha/#{event_id.group(1)}"
            if event_id
            else DRAMPUSH_AFISHA_URL
        )

        key = (title, starts_at.isoformat())
        if key in seen:
            continue
        seen.add(key)

        desc_bits = []
        strong = re.search(r"<strong>([^<]+)</strong>", block)
        if strong:
            desc_bits.append(html.unescape(strong.group(1)).strip())
        events.append(
            DrampushEvent(
                title=title[:300],
                description=" · ".join(desc_bits)[:2000] or None,
                starts_at=starts_at,
                location=location[:500],
                category=EventCategory.CULTURE,
                source_url=source_url,
            )
        )
    return events


async def fetch_drampush_events() -> list[DrampushEvent]:
    headers = {"User-Agent": "PGBot-Events/1.0 (+https://192-210-213-135.sslip.io/events)"}
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(DRAMPUSH_AFISHA_URL)
            response.raise_for_status()
            return _parse_page(response.text)
    except Exception:
        logger.exception("Drampush afisha fetch failed")
        return []
