"""TimePad REST API client — events for Pskov region.

Docs: https://dev.timepad.ru/api/get-v1-events
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings
from app.constants.event_config import TIMEPAD_CATEGORY_MAP, TIMEPAD_CITY_FILTERS, TIMEPAD_KEYWORD_FILTERS
from app.models.enums import EventCategory, EventRegion
from app.services.event_sources.text_utils import infer_category_from_text

logger = logging.getLogger(__name__)
settings = get_settings()
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
TIMEPAD_API_BASE = "https://api.timepad.ru/v1"


def _auth_headers() -> dict[str, str]:
    token = (settings.TIMEPAD_API_TOKEN or "").strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def map_timepad_category(item: dict[str, Any]) -> EventCategory:
    """Map TimePad categories to internal event category."""
    for cat in item.get("categories", []):
        name = (cat.get("name") or "").lower()
        for fragment, slug in TIMEPAD_CATEGORY_MAP.items():
            if fragment in name:
                try:
                    return EventCategory(slug)
                except ValueError:
                    continue
    text = f"{item.get('name', '')} {item.get('description_short', '')}"
    return infer_category_from_text(text)


def _parse_timepad_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=MOSCOW_TZ)
        return dt.astimezone(MOSCOW_TZ)
    except ValueError:
        return None


def _event_location(item: dict[str, Any]) -> str | None:
    location = item.get("location") or {}
    parts = [location.get("city"), location.get("address")]
    joined = ", ".join(part.strip() for part in parts if part and str(part).strip())
    return joined[:500] or None


def infer_timepad_region(item: dict[str, Any]) -> EventRegion:
    """Assign Pushkin Gory vs Pskov from city/address text."""
    location = item.get("location") or {}
    blob = " ".join(
        str(location.get(key, "")) for key in ("city", "address", "country")
    ).lower()
    if any(marker in blob for marker in ("пушкин", "михайловск", "святогор", "пушкиногор")):
        return EventRegion.PUSHKIN_GORY
    return EventRegion.PSKOV


async def fetch_timepad_events(
    *,
    limit: int = 50,
    cities: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Fetch upcoming public events from TimePad API."""
    token = (settings.TIMEPAD_API_TOKEN or "").strip()
    if not token:
        logger.warning("TIMEPAD_API_TOKEN not set — TimePad sync unavailable")
        return []

    now = datetime.now(MOSCOW_TZ)
    params: list[tuple[str, str]] = [
        ("limit", str(min(max(limit, 1), 100))),
        ("access_statuses", "public"),
        ("moderation_statuses", "featured"),
        ("moderation_statuses", "shown"),
        ("moderation_statuses", "not_moderated"),
        ("starts_at_min", now.isoformat()),
        ("starts_at_max", (now + timedelta(days=60)).isoformat()),
        ("sort", "+starts_at"),
    ]
    for city in cities or TIMEPAD_CITY_FILTERS:
        params.append(("cities", city))
    for keyword in TIMEPAD_KEYWORD_FILTERS:
        params.append(("keywords", keyword))

    async with httpx.AsyncClient(timeout=25.0) as client:
        response = await client.get(
            f"{TIMEPAD_API_BASE}/events",
            params=params,
            headers={**_auth_headers(), "Accept": "application/json"},
        )
        if response.status_code == 403:
            logger.warning("TimePad API 403 — check TIMEPAD_API_TOKEN")
            return []
        response.raise_for_status()
        payload = response.json()

    values = payload.get("values") or payload.get("result", {}).get("values") or []
    return list(values)


def timepad_event_url(item: dict[str, Any]) -> str:
    url = (item.get("url") or "").strip()
    if url:
        return url
    event_id = item.get("id")
    return f"https://timepad.ru/event/{event_id}/"
