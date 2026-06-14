"""KudaGo API adapter — cinema and concerts for Pskov.

Docs: https://kudago.com/public-api/v1.4/
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.event_config import KUDAGO_CATEGORY_MAP, KUDAGO_LOCATION_PRESETS
from app.models.enums import EventCategory, EventRegion
from app.services.event_service import (
    EventCreateInput,
    EventUpdateInput,
    EventValidationError,
    create_event,
    update_event,
)
from app.services.event_sources.base import EventSyncResult
from app.services.event_sources.dedup import find_existing_event
from app.services.event_sources.text_utils import infer_category_from_text

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
KUDAGO_API_BASE = "https://kudago.com/public-api/v1.4"


def map_kudago_category(item: dict[str, Any]) -> EventCategory:
    """Map KudaGo categories to internal event category."""
    for slug in item.get("categories", []):
        mapped = KUDAGO_CATEGORY_MAP.get(slug)
        if mapped:
            try:
                return EventCategory(mapped)
            except ValueError:
                continue
    title = item.get("title", "")
    description = item.get("description", "")
    return infer_category_from_text(f"{title} {description}")


def parse_kudago_datetime(item: dict[str, Any]) -> datetime | None:
    """Extract the nearest future start time from a KudaGo event."""
    now_ts = int(datetime.now(MOSCOW_TZ).timestamp())
    best: int | None = None
    for block in item.get("dates", []):
        start = block.get("start")
        if start is None:
            continue
        if start >= now_ts - 86_400:
            if best is None or start < best:
                best = start
    if best is None:
        return None
    return datetime.fromtimestamp(best, tz=MOSCOW_TZ)


def kudago_event_url(item: dict[str, Any]) -> str:
    """Build a stable source URL for deduplication."""
    site_url = (item.get("site_url") or "").strip()
    if site_url:
        return site_url
    event_id = item.get("id")
    return f"https://kudago.com/pskov/event/{event_id}/"


async def fetch_kudago_events(
    location_slug: str,
    *,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Fetch upcoming events from KudaGo for a location slug."""
    actual_since = int(datetime.now(timezone.utc).timestamp())
    params = {
        "location": location_slug,
        "actual_since": actual_since,
        "page_size": page_size,
        "fields": "id,title,dates,place,description,site_url,categories",
        "order_by": "start_date",
        "expand": "place",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{KUDAGO_API_BASE}/events/", params=params)
        response.raise_for_status()
        payload = response.json()
    return list(payload.get("results", []))


async def _upsert_kudago_event(
    db: AsyncSession,
    *,
    region: EventRegion,
    item: dict[str, Any],
    default_location: str,
    actor_id: int | None,
) -> str:
    """Create or update event from a KudaGo item. Returns created|updated|skipped."""
    starts_at = parse_kudago_datetime(item)
    if starts_at is None:
        return "skipped"

    title = (item.get("title") or "").strip()
    if len(title) < 3:
        return "skipped"

    source_url = kudago_event_url(item)
    existing = await find_existing_event(
        db,
        source_url=source_url,
        title=title,
        starts_at=starts_at,
    )

    place = item.get("place") or {}
    location = (place.get("title") or default_location).strip()
    description = (item.get("description") or "")[:2000] or None
    category = map_kudago_category(item)

    ends_at = None
    for block in item.get("dates", []):
        if block.get("start") == int(starts_at.timestamp()) and block.get("end"):
            ends_at = datetime.fromtimestamp(block["end"], tz=MOSCOW_TZ)
            break

    payload = EventCreateInput(
        title=title[:300],
        description=description,
        starts_at=starts_at,
        ends_at=ends_at,
        location=location,
        category=category,
        source="kudago",
        source_url=source_url,
        region=region,
        is_published=True,
    )

    if existing:
        await update_event(
            db,
            existing,
            EventUpdateInput(
                title=payload.title,
                description=payload.description,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                location=payload.location,
                region=region,
                category=payload.category,
                is_published=True,
            ),
            actor_id=actor_id,
        )
        return "updated"

    await create_event(db, payload, actor_id=actor_id)
    return "created"


async def sync_events_from_kudago(
    db: AsyncSession,
    region: EventRegion,
    *,
    actor_id: int | None = None,
    page_size: int = 20,
) -> EventSyncResult:
    """Import upcoming events from KudaGo for the configured region."""
    preset = KUDAGO_LOCATION_PRESETS.get(region)
    if not preset:
        raise EventValidationError(f"Регион {region.value} не настроен для KudaGo")

    errors: list[str] = []
    created = updated = skipped = 0

    try:
        items = await fetch_kudago_events(preset["location_slug"], page_size=page_size)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            logger.warning(
                "KudaGo location %r unavailable (API: %s)",
                preset["location_slug"],
                exc.response.text[:200],
            )
            return EventSyncResult(
                source="kudago",
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[f"Локация KudaGo «{preset['label']}» недоступна в API"],
            )
        logger.exception("KudaGo API request failed for %s", region.value)
        raise EventValidationError(f"KudaGo API недоступен: {exc}") from exc
    except httpx.HTTPError as exc:
        logger.exception("KudaGo API request failed for %s", region.value)
        raise EventValidationError(f"KudaGo API недоступен: {exc}") from exc

    for item in items:
        try:
            action = await _upsert_kudago_event(
                db,
                region=region,
                item=item,
                default_location=preset["default_location"],
                actor_id=actor_id,
            )
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
            else:
                skipped += 1
        except Exception as exc:
            logger.exception("KudaGo event import failed for item %s", item.get("id"))
            errors.append(str(exc))

    return EventSyncResult(
        source="kudago",
        region=region.value,
        fetched=len(items),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )


async def sync_all_kudago_sources(
    db: AsyncSession,
    *,
    actor_id: int | None = None,
) -> list[EventSyncResult]:
    """Sync events from all configured KudaGo locations."""
    results: list[EventSyncResult] = []
    for region in KUDAGO_LOCATION_PRESETS:
        try:
            results.append(await sync_events_from_kudago(db, region, actor_id=actor_id))
        except EventValidationError as exc:
            results.append(EventSyncResult(
                source="kudago",
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[exc.detail],
            ))
    return results
