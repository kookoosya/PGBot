"""Silver Cinema Pskov — Kinoplan widget API (kinokassa.kinoplan24.ru)."""

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
KINOKASSA = "https://kinokassa.kinoplan24.ru"
SILVER_HOME = "https://www.silvercinema.ru/pskov/"
CINEMA_ID = 7613
CITY_ID = 148
_silver = next(c for c in PSKOV_CINEMAS if "silver" in c.aliases[0])
SILVER_LOCATION = f"{_silver.name}, {_silver.address}"

_FILM_CELL_RE = re.compile(
    r'<a href="([^"]+)" title="([^"]+)" class="[^"]*movie-cell[^"]*"',
    re.IGNORECASE,
)
_KINOPLAN_RE = re.compile(r"kinowidget\.kinoplan\.ru/release/(\d+)/(\d+)")


@dataclass(frozen=True, slots=True)
class SilverCinemaEvent:
    title: str
    description: str | None
    starts_at: datetime
    location: str
    category: EventCategory
    source_url: str
    poster_url: str | None
    genre: str | None = None


def _kinoplan_headers(token: str) -> dict[str, str]:
    return {
        "User-Agent": "PGBot/1.0 (+events; silver)",
        "Accept": "application/json",
        "X-Platform": "widget",
        "X-Application-Token": token,
    }


async def _get_kinoplan_token(client: httpx.AsyncClient) -> str | None:
    response = await client.get(
        f"{KINOKASSA}/api/v2/app",
        params={"cinema_id": CINEMA_ID},
        headers={"User-Agent": "PGBot/1.0", "X-Platform": "widget"},
    )
    response.raise_for_status()
    return response.json().get("token")


async def _list_silver_releases(client: httpx.AsyncClient) -> list[tuple[str, str, int]]:
    """Return (slug, title, kinoplan_release_id) for films on the afisha page."""
    response = await client.get(SILVER_HOME, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    page = response.text
    releases: list[tuple[str, str, int]] = []
    seen_ids: set[int] = set()

    for slug, title in _FILM_CELL_RE.findall(page):
        if slug.startswith("http"):
            continue
        film_url = f"{SILVER_HOME.rstrip('/')}/{slug.strip('/')}"
        film_resp = await client.get(film_url, headers={"User-Agent": "Mozilla/5.0"})
        if film_resp.status_code >= 400:
            continue
        match = _KINOPLAN_RE.search(film_resp.text)
        if not match or int(match.group(1)) != CINEMA_ID:
            continue
        release_id = int(match.group(2))
        if release_id in seen_ids:
            continue
        seen_ids.add(release_id)
        releases.append((slug, html.unescape(title).strip(), release_id))
    return releases


async def fetch_silver_cinema_events(*, days_ahead: int = 6) -> list[SilverCinemaEvent]:
    """Fetch Silver Cinema Pskov showtimes via Kinoplan API."""
    now = datetime.now(MOSCOW_TZ)
    events: list[SilverCinemaEvent] = []
    seen: set[tuple[str, str]] = set()

    try:
        async with httpx.AsyncClient(timeout=45.0, follow_redirects=True) as client:
            token = await _get_kinoplan_token(client)
            if not token:
                logger.warning("Silver: Kinoplan token missing")
                return []

            headers = _kinoplan_headers(token)
            releases = await _list_silver_releases(client)
            if not releases:
                logger.warning("Silver: no releases on afisha page")
                return []

            for slug, list_title, release_id in releases:
                rel_resp = await client.get(
                    f"{KINOKASSA}/api/v2/release/{release_id}",
                    headers=headers,
                )
                if rel_resp.status_code >= 400:
                    continue
                rel = rel_resp.json().get("release") or {}
                title = (rel.get("title") or list_title).strip()
                genres = ", ".join(g.get("title", "") for g in rel.get("genres") or [] if g.get("title"))
                description = (rel.get("description") or "").strip() or None
                poster = rel.get("poster") or rel.get("thumbnail")
                source_url = f"{SILVER_HOME.rstrip('/')}/{slug.strip('/')}"

                for offset in range(days_ahead + 1):
                    day = (now + timedelta(days=offset)).date()
                    seances_resp = await client.get(
                        f"{KINOKASSA}/api/v2/release/{release_id}/seances",
                        params={"city_id": CITY_ID, "date": day.isoformat()},
                        headers=headers,
                    )
                    if seances_resp.status_code >= 400:
                        continue
                    for seance in seances_resp.json():
                        if seance.get("cinema_id") != CINEMA_ID:
                            continue
                        raw_time = seance.get("start_date_time")
                        if not raw_time:
                            continue
                        starts_at = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
                        if starts_at.tzinfo is None:
                            starts_at = starts_at.replace(tzinfo=MOSCOW_TZ)
                        else:
                            starts_at = starts_at.astimezone(MOSCOW_TZ)
                        if starts_at < now - timedelta(hours=1):
                            continue

                        hall = seance.get("hall") or {}
                        hall_title = hall.get("title")
                        formats = ", ".join(f.get("title", "") for f in seance.get("formats") or [])
                        desc = description
                        if hall_title:
                            extra = f"Зал №{hall_title}"
                            if formats:
                                extra += f", {formats}"
                            desc = f"{extra}. {description}" if description else extra

                        key = (title, starts_at.isoformat())
                        if key in seen:
                            continue
                        seen.add(key)
                        events.append(
                            SilverCinemaEvent(
                                title=title[:300],
                                description=(desc or "Билеты на silvercinema.ru.")[:2000],
                                starts_at=starts_at,
                                location=SILVER_LOCATION,
                                category=EventCategory.CINEMA,
                                source_url=source_url,
                                poster_url=poster,
                                genre=genres[:120] or None,
                            )
                        )
    except Exception as exc:
        logger.warning("Silver fetch failed: %s", exc)
        return []

    logger.info("Silver: parsed %s cinema sessions", len(events))
    return events
