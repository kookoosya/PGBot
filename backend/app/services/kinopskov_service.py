"""Kinopskov60.com — сеть Победа / Смена (p24.app), не все кинотеатры Пскова."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.constants.pskov_cinemas import format_cinema_location
from app.models.enums import EventCategory

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
KINOPSKOV_URL = "https://kinopskov60.com/"

_MOVIE_BLOCK_RE = re.compile(r'itemType="http://schema\.org/Movie">')
_FACILITY_RE = re.compile(r"facility-address\">([^<]+)")


@dataclass(frozen=True, slots=True)
class KinopskovEvent:
    title: str
    description: str | None
    starts_at: datetime
    location: str
    category: EventCategory
    source_url: str
    poster_url: str | None
    genre: str | None = None


def _resolve_facility(page: str, position: int) -> str:
    ctx = page[max(0, position - 4000) : position]
    matches = _FACILITY_RE.findall(ctx)
    if not matches:
        return "Псков"
    raw = html.unescape(matches[-1].replace("<!-- -->", "")).strip()
    return raw.split(",")[0].strip()


def _parse_page(page: str) -> list[KinopskovEvent]:
    now = datetime.now(MOSCOW_TZ)
    events: list[KinopskovEvent] = []
    seen: set[tuple[str, str, str]] = set()

    for match in _MOVIE_BLOCK_RE.finditer(page):
        block = page[match.start() : match.start() + 14000]
        title_m = re.search(r'itemProp="name" content="([^"]+)"', block)
        if not title_m:
            continue
        title = html.unescape(title_m.group(1)).strip()
        poster_m = re.search(r'itemProp="image" content="([^"]+)"', block)
        poster = poster_m.group(1) if poster_m else None
        genre_m = re.search(r'itemProp="genre" content="([^"]+)"', block)
        genre = html.unescape(genre_m.group(1)) if genre_m else None
        desc_m = re.search(r'itemProp="description" content="([^"]+)"', block)
        description = html.unescape(desc_m.group(1))[:2000] if desc_m else None
        link_m = re.search(r'href="(/events/[^"?]+)', block)
        event_path = link_m.group(1) if link_m else ""
        source_url = f"https://kinopskov60.com{event_path}" if event_path else KINOPSKOV_URL

        facility = _resolve_facility(page, match.start())
        location = format_cinema_location(facility) or f"Кинотеатр «{facility}», Псков"

        date_m = re.search(r"date=(\d{4}/\d{2}/\d{2})", block)
        date_s = date_m.group(1) if date_m else now.strftime("%Y/%m/%d")
        year, month, day = (int(x) for x in date_s.split("/"))

        times = list(dict.fromkeys(re.findall(r'show-time[^>]*>(\d{1,2}:\d{2})', block)))
        for time_label in times:
            hour, minute = (int(x) for x in time_label.split(":"))
            starts_at = datetime(year, month, day, hour, minute, tzinfo=MOSCOW_TZ)
            if starts_at < now - timedelta(hours=1):
                continue
            key = (title, location, starts_at.isoformat())
            if key in seen:
                continue
            seen.add(key)
            events.append(
                KinopskovEvent(
                    title=title[:300],
                    description=description,
                    starts_at=starts_at,
                    location=location[:500],
                    category=EventCategory.CINEMA,
                    source_url=source_url,
                    poster_url=poster,
                    genre=genre,
                )
            )
    return events


async def fetch_kinopskov_events() -> list[KinopskovEvent]:
    """Scrape cinema schedule from kinopskov60.com (Победа / Смена)."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                KINOPSKOV_URL,
                headers={"User-Agent": "PGBot/1.0 (+events; kinopskov60)"},
            )
            response.raise_for_status()
            page = response.text
    except Exception as exc:
        logger.warning("Kinopskov fetch failed: %s", exc)
        return []

    events = _parse_page(page)
    logger.info("Kinopskov: parsed %s cinema sessions", len(events))
    return events
