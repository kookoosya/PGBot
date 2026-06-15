"""Mirage Cinema Pskov — schedule from mirage.ru/psk/schedule/."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.constants.pskov_cinemas import PSKOV_CINEMAS
from app.models.enums import EventCategory

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
SCHEDULE_URL = "https://www.mirage.ru/psk/schedule/"
MIRAGE_LOCATION = next(c for c in PSKOV_CINEMAS if "мираж" in c.aliases[0]).name + ", " + next(
    c for c in PSKOV_CINEMAS if "мираж" in c.aliases[0]
).address

_SESSION_RE = re.compile(
    r'<div class="session">\s*<a href="(?P<ticket>[^"]+)"[^>]*>'
    r"(?P<body>.*?)</a>\s*</div>",
    re.DOTALL,
)


@dataclass(frozen=True, slots=True)
class MirageCinemaEvent:
    title: str
    description: str | None
    starts_at: datetime
    location: str
    category: EventCategory
    source_url: str
    poster_url: str | None
    genre: str | None = None


def _upscale_poster(url: str | None) -> str | None:
    if not url:
        return None
    return url.replace("/small/", "/big/")


def _parse_schedule_page(page: str, *, day: datetime) -> list[MirageCinemaEvent]:
    events: list[MirageCinemaEvent] = []
    seen: set[tuple[str, str]] = set()

    for match in _SESSION_RE.finditer(page):
        body = match.group("body")
        title_m = re.search(r'<div class="title">([^<]+)</div>', body)
        genre_m = re.search(r'<div class="genre">\s*([^<]+?)\s*</div>', body)
        time_m = re.search(r'<div class="time">(\d{1,2}:\d{2})</div>', body)
        hall_m = re.search(r'<span class="blue">([^<]+)</span>', body)
        poster_m = re.search(r'<img src="([^"]+)"', body)
        if not (title_m and time_m):
            continue

        title = html.unescape(title_m.group(1)).strip()
        hour, minute = (int(x) for x in time_m.group(1).split(":"))
        starts_at = day.replace(hour=hour, minute=minute, second=0, microsecond=0, tzinfo=MOSCOW_TZ)
        key = (title, starts_at.isoformat())
        if key in seen:
            continue
        seen.add(key)

        genre = html.unescape(genre_m.group(1)).strip() if genre_m else None
        hall = html.unescape(hall_m.group(1)).strip() if hall_m else None
        ticket_path = match.group("ticket")
        source_url = ticket_path if ticket_path.startswith("http") else f"https://www.mirage.ru{ticket_path}"

        desc_parts = []
        if genre:
            desc_parts.append(f"Жанр: {genre}.")
        if hall:
            desc_parts.append(hall + ".")
        desc_parts.append("Билеты на mirage.ru.")

        events.append(
            MirageCinemaEvent(
                title=title[:300],
                description=" ".join(desc_parts)[:2000] or None,
                starts_at=starts_at,
                location=MIRAGE_LOCATION,
                category=EventCategory.CINEMA,
                source_url=source_url,
                poster_url=_upscale_poster(poster_m.group(1) if poster_m else None),
                genre=genre[:120] if genre else None,
            )
        )
    return events


async def fetch_mirage_cinema_events(*, days_ahead: int = 6) -> list[MirageCinemaEvent]:
    """Scrape Mirage Pskov schedule for today and upcoming days."""
    now = datetime.now(MOSCOW_TZ)
    events: list[MirageCinemaEvent] = []
    seen: set[tuple[str, str]] = set()

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for offset in range(days_ahead + 1):
                day = (now + timedelta(days=offset)).replace(hour=0, minute=0, second=0, microsecond=0)
                if offset == 0:
                    url = SCHEDULE_URL
                else:
                    url = f"{SCHEDULE_URL}{day.strftime('%d.%m.%Y')}/"
                response = await client.get(url, headers={"User-Agent": "PGBot/1.0 (+events; mirage)"})
                if response.status_code >= 400:
                    logger.warning("Mirage schedule %s returned %s", url, response.status_code)
                    continue
                for item in _parse_schedule_page(response.text, day=day):
                    if item.starts_at < now - timedelta(hours=1):
                        continue
                    key = (item.title, item.starts_at.isoformat())
                    if key in seen:
                        continue
                    seen.add(key)
                    events.append(item)
    except Exception as exc:
        logger.warning("Mirage fetch failed: %s", exc)
        return []

    logger.info("Mirage: parsed %s cinema sessions", len(events))
    return events
