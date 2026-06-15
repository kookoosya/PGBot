"""PRO.Культура.РФ events API (optional — requires partner apiKey)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings
from app.models.enums import EventCategory, EventRegion

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
API_BASE = "https://pro.culture.ru/api/2.5"

_PROCATEGORY_MAP = {
    "kino": EventCategory.CINEMA,
    "koncerty": EventCategory.CULTURE,
    "spektakli": EventCategory.CULTURE,
    "vystavki": EventCategory.CULTURE,
    "ekskursii": EventCategory.TOURISM,
    "prazdniki": EventCategory.HOLIDAY,
    "obuchenie": EventCategory.EDUCATION,
    "vstrechi": EventCategory.COMMUNITY,
    "prochie": EventCategory.OTHER,
}


def _api_key() -> str | None:
    key = (get_settings().PROCULTURE_API_KEY or "").strip()
    return key or None


async def _get_json(path: str, *, params: dict[str, Any]) -> dict[str, Any] | None:
    key = _api_key()
    if not key:
        return None
    params = {**params, "apiKey": key}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{API_BASE}/{path}", params=params)
            if response.status_code == 403:
                logger.warning("PRO.Культура: invalid apiKey")
                return None
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning("PRO.Культура request failed: %s", exc)
        return None


async def resolve_pskov_locale_id() -> int | None:
    """Find locale id for Pskov city/oblast."""
    cached = get_settings().PROCULTURE_PSKOV_LOCALE_ID
    if cached:
        return int(cached)
    data = await _get_json("locales", params={"nameQuery": "Псков", "limit": 20})
    if not data:
        return None
    for locale in data.get("locales", []):
        name = (locale.get("name") or "").lower()
        if "псков" in name:
            return int(locale["_id"])
    return None


def _map_category(item: dict[str, Any]) -> EventCategory:
    sys_name = ((item.get("category") or {}).get("sysName") or "").lower()
    return _PROCATEGORY_MAP.get(sys_name, EventCategory.OTHER)


def _first_seance_ms(item: dict[str, Any]) -> int | None:
    for place in item.get("places") or []:
        for seance in place.get("seances") or []:
            start = seance.get("start")
            if start:
                return int(start)
    start = item.get("start")
    return int(start) if start else None


def _location(item: dict[str, Any]) -> str | None:
    places = item.get("places") or []
    if not places:
        return "Псков"
    place = places[0]
    name = (place.get("name") or "").strip()
    address = place.get("address") or {}
    city = ((address.get("city") or {}).get("name") or "").strip()
    street = ((address.get("street") or {}).get("name") or "").strip()
    house = ((address.get("house") or {}).get("name") or "").strip()
    parts = [p for p in (name, city, street, house) if p]
    return ", ".join(parts)[:500] if parts else "Псков"


async def fetch_proculture_events(*, limit: int = 60) -> list[dict[str, Any]]:
    """Fetch accepted Pushkin-card events for Pskov locale."""
    if not _api_key():
        return []

    locale_id = await resolve_pskov_locale_id()
    params: dict[str, Any] = {
        "status": "accepted",
        "limit": min(limit, 100),
        "offset": 0,
        "sort": "start",
    }
    if locale_id:
        params["locales"] = locale_id
    else:
        params["nameQuery"] = "Псков"

    data = await _get_json("pushkinsCardEvents", params=params)
    if not data:
        return []
    return list(data.get("pushkinsCardEvents") or data.get("events") or [])


def proculture_item_to_fields(item: dict[str, Any]) -> dict[str, Any] | None:
    start_ms = _first_seance_ms(item)
    if not start_ms:
        return None
    starts_at = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc).astimezone(MOSCOW_TZ)
    title = (item.get("name") or "").strip()
    if len(title) < 3:
        return None
    description = (item.get("shortDescription") or item.get("description") or "").strip()
    genre = ((item.get("extraFields") or {}).get("genre") or "").strip() or None
    category = _map_category(item)
    location = _location(item)
    event_id = item.get("_id")
    sale = (item.get("saleLink") or "").strip()
    source_url = sale or f"https://pro.culture.ru/events/{event_id}"

    region = EventRegion.PUSHKIN_GORY if any(
        marker in f"{title} {location}".lower()
        for marker in ("пушкин", "михайловск", "святогор", "пушкиногор")
    ) else EventRegion.PSKOV

    return {
        "title": title[:300],
        "description": description[:2000] if description else None,
        "starts_at": starts_at,
        "location": location,
        "region": region,
        "category": category,
        "genre": genre,
        "source_url": source_url[:1000],
    }
