"""KDC Pushgory (kdc-pushgory.ru) — municipal culture center events."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.models.enums import EventCategory, EventRegion
from app.services.event_sources.text_utils import infer_category_from_text, parse_event_date_range

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
KDC_BASE_URL = "https://kdc-pushgory.ru"
DEFAULT_LOCATION = "Пушкинские Горы"

_ITEM_LINK_RE = re.compile(r'href="/item/(\d+)"')
_EVENTS_MENU_RE = re.compile(
    r'id="menu_118278"[^>]*>.*?<ul class="dropdown-menu[^"]*">(.*?)</ul>',
    re.DOTALL | re.IGNORECASE,
)
_NEWS_TILE_RE = re.compile(
    r'<a class="content_block" href="/item/(\d+)">.*?'
    r'<span class="bottom_block">([^<]*)</span>.*?'
    r'<h4 class="text-center"><a href="/item/\d+">([^<]+)</a>',
    re.DOTALL,
)
_TITLE_RE = re.compile(r"<h3[^>]*>([^<]+)</h3>", re.IGNORECASE)
_ISO_TS_RE = re.compile(r'iso-timestamp="([^"]+)"')
_BODY_RE = re.compile(r"<p>([^<]+)</p>", re.IGNORECASE)
_PAST_EVENT_RE = re.compile(
    r"\b(прошёл|прошла|прошло|состоялся|состоялась|состоялось|отметили|отметил)\b",
    re.IGNORECASE,
)
_SKIP_MENU_IDS = frozenset({
    "118278", "118283", "849991", "118284", "141676", "702027", "255985", "255980",
})


@dataclass(frozen=True, slots=True)
class KdcEvent:
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    location: str
    category: EventCategory
    source_url: str
    poster_url: str | None = None


def _strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value)).strip()


def _extract_item_ids(page: str) -> dict[str, str]:
    """Map item id -> short title from homepage news and events menu."""
    items: dict[str, str] = {}

    for match in _NEWS_TILE_RE.finditer(page):
        item_id, teaser, title = match.groups()
        items[item_id] = _strip_tags(title) or _strip_tags(teaser)

    menu_match = _EVENTS_MENU_RE.search(page)
    if menu_match:
        menu_html = menu_match.group(1)
        for item_id, title in re.findall(r'href="/item/(\d+)"[^>]*>([^<]{4,200})</a>', menu_html):
            if item_id in _SKIP_MENU_IDS:
                continue
            items.setdefault(item_id, _strip_tags(title))

    return items


def _parse_item_page(item_id: str, page: str, *, fallback_title: str) -> KdcEvent | None:
    title_match = _TITLE_RE.search(page)
    title = _strip_tags(title_match.group(1)) if title_match else fallback_title
    if not title or len(title) < 4:
        return None

    body_parts = [_strip_tags(part) for part in _BODY_RE.findall(page)]
    body = " ".join(part for part in body_parts if part).strip()
    combined = f"{title}. {body}"

    iso_match = _ISO_TS_RE.search(page)
    fallback_dt = datetime.now(MOSCOW_TZ)
    if iso_match:
        try:
            fallback_dt = datetime.fromisoformat(iso_match.group(1).replace("Z", "+00:00")).astimezone(MOSCOW_TZ)
        except ValueError:
            pass

    starts_at, ends_at = parse_event_date_range(combined, fallback=fallback_dt)
    if not starts_at:
        starts_at = fallback_dt.replace(hour=12, minute=0, second=0, microsecond=0)

    now = datetime.now(MOSCOW_TZ)
    if starts_at < now - timedelta(days=2):
        if _PAST_EVENT_RE.search(combined):
            return None
        if starts_at < now - timedelta(days=14):
            return None

    if starts_at > now + timedelta(days=120):
        return None

    category = infer_category_from_text(combined)
    location = DEFAULT_LOCATION
    lower = combined.lower()
    for place, label in (
        ("бугров", "Бугрово, Пушкинские Горы"),
        ("михайловск", "Михайловское, Пушкинские Горы"),
        ("васильев", "с. Васильевское"),
        ("велье", "с. Велье"),
        ("исск", "с. Исск"),
    ):
        if place in lower:
            location = label
            break

    poster_match = re.search(r'<img src="([^"]+)" alt=', page)
    poster_url = poster_match.group(1) if poster_match else None
    if poster_url and poster_url.startswith("/"):
        poster_url = f"{KDC_BASE_URL}{poster_url}"

    description = body[:2000] if body else None
    return KdcEvent(
        title=title[:300],
        description=description,
        starts_at=starts_at,
        ends_at=ends_at,
        location=location[:500],
        category=category,
        source_url=f"{KDC_BASE_URL}/item/{item_id}",
        poster_url=poster_url,
    )


def _parse_homepage(page: str) -> list[KdcEvent]:
    """Parse homepage tiles only (used in tests without HTTP)."""
    events: list[KdcEvent] = []
    now = datetime.now(MOSCOW_TZ)
    for match in _NEWS_TILE_RE.finditer(page):
        item_id, teaser, title = match.groups()
        clean_title = _strip_tags(title)
        combined = f"{clean_title}. {_strip_tags(teaser)}"
        starts_at, ends_at = parse_event_date_range(combined, fallback=now)
        if not starts_at:
            continue
        if starts_at < now - timedelta(days=2):
            continue
        events.append(
            KdcEvent(
                title=clean_title[:300],
                description=_strip_tags(teaser)[:2000] or None,
                starts_at=starts_at,
                ends_at=ends_at,
                location=DEFAULT_LOCATION,
                category=infer_category_from_text(combined),
                source_url=f"{KDC_BASE_URL}/item/{item_id}",
            )
        )
    return events


async def fetch_kdc_events(*, item_limit: int = 30) -> list[KdcEvent]:
    """Scrape recent events from kdc-pushgory.ru."""
    headers = {"User-Agent": "PGBot-Events/1.0 (+https://192-210-213-135.sslip.io/events)"}
    events: list[KdcEvent] = []
    seen: set[str] = set()

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers=headers) as client:
            home_resp = await client.get(f"{KDC_BASE_URL}/")
            home_resp.raise_for_status()
            item_map = _extract_item_ids(home_resp.text)

            for item_id, fallback_title in list(item_map.items())[:item_limit]:
                if item_id in seen:
                    continue
                seen.add(item_id)
                try:
                    detail_resp = await client.get(f"{KDC_BASE_URL}/item/{item_id}")
                    detail_resp.raise_for_status()
                    parsed = _parse_item_page(item_id, detail_resp.text, fallback_title=fallback_title)
                    if parsed:
                        events.append(parsed)
                except Exception:
                    logger.warning("KDC item %s fetch failed", item_id, exc_info=True)
    except Exception:
        logger.exception("KDC homepage fetch failed")

    return events
