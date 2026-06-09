"""Orbilet Pskov afisha scraper — concerts, excursions, planetarium, theater."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.models.enums import EventCategory
from app.services.event_sources.text_utils import infer_category_from_text

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
ORBILET_URL = "https://www.orbilet.ru/"

_SESSION_BLOCK_RE = re.compile(
    r'data-timestamp="(?P<ts>\d+)(?:\.\d+)?"[^>]*>.*?'
    r'class="eventName">\s*<a href="/event/(?P<event_id>\d+)">(?P<title>.*?)</a>.*?'
    r'class="eventDate"><a href="/session/(?P<session_id>\d+)">(?P<date_label>.*?)</a>.*?'
    r'class="eventVenue">.*?<a[^>]*>(?P<venue>.*?)</a>',
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class OrbiletEvent:
    title: str
    description: str | None
    starts_at: datetime
    location: str | None
    category: EventCategory
    source_url: str
    genre: str | None = None


def _map_category(title: str, venue: str | None = None) -> EventCategory:
    return infer_category_from_text(f"{title} {venue or ''}")


def _build_description(title: str, venue: str | None, date_label: str) -> str:
    parts = [title.rstrip(".") + "."]
    if venue:
        parts.append(f"Место: {venue}.")
    parts.append(f"Сеанс: {date_label.strip()}.")
    parts.append("Билеты на orbilet.ru.")
    return " ".join(parts)


async def fetch_orbilet_events() -> list[OrbiletEvent]:
    """Scrape upcoming sessions from orbilet.ru (Pskov region)."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(ORBILET_URL, headers={"User-Agent": "PGBot/1.0 (+events)"})
            response.raise_for_status()
            page = response.text
    except Exception as exc:
        logger.warning("Orbilet fetch failed: %s", exc)
        return []

    now = datetime.now(MOSCOW_TZ)
    events: list[OrbiletEvent] = []
    seen_sessions: set[str] = set()

    for match in _SESSION_BLOCK_RE.finditer(page):
        session_id = match.group("session_id")
        if session_id in seen_sessions:
            continue
        seen_sessions.add(session_id)

        try:
            starts_at = datetime.fromtimestamp(int(match.group("ts")), tz=MOSCOW_TZ)
        except (ValueError, OSError):
            continue
        if starts_at < now:
            continue

        title = html.unescape(re.sub(r"\s+", " ", match.group("title")).strip())
        venue = html.unescape(re.sub(r"\s+", " ", match.group("venue")).strip())
        date_label = html.unescape(re.sub(r"\s+", " ", match.group("date_label")).strip())
        if len(title) < 3:
            continue

        category = _map_category(title, venue)
        events.append(
            OrbiletEvent(
                title=title[:300],
                description=_build_description(title, venue, date_label),
                starts_at=starts_at,
                location=venue[:500] or "Псков",
                category=category,
                source_url=f"https://www.orbilet.ru/session/{session_id}",
            )
        )

    logger.info("Orbilet: parsed %s upcoming sessions", len(events))
    return events
