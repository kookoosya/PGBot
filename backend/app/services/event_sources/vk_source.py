"""VK wall import — multiple communities, smart post filtering."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants.event_config import VK_EVENT_GROUPS, VkGroupPreset
from app.models.enums import EventRegion
from app.services.event_service import EventValidationError
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.text_utils import (
    infer_category_from_text,
    is_relevant_event_post,
    parse_event_datetime,
    post_title,
)
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.vk import vk_api_call

logger = logging.getLogger(__name__)
settings = get_settings()
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


async def _resolve_group_id(screen_name: str) -> int | None:
    token = (settings.VK_GROUP_TOKEN or "").strip()
    if not token or token.startswith("your-"):
        return None
    try:
        response = await vk_api_call("groups.getById", {"group_id": screen_name})
        if isinstance(response, list) and response:
            return int(response[0]["id"])
        if isinstance(response, dict) and "id" in response:
            return int(response["id"])
    except Exception:
        logger.warning("Failed to resolve VK group %s", screen_name, exc_info=True)
    return None


async def _fetch_wall_posts(group_id: int, *, count: int = 20) -> list[dict]:
    response = await vk_api_call("wall.get", {
        "owner_id": -group_id,
        "count": count,
        "filter": "owner",
    })
    return list(response.get("items", []))


def _post_to_fetched(post: dict, *, preset: VkGroupPreset, group_id: int) -> FetchedEvent | None:
    post_id = post.get("id")
    if post_id is None:
        return None

    text = (post.get("text") or "").strip()
    post_date = datetime.fromtimestamp(post.get("date", 0), tz=timezone.utc)
    starts_at = parse_event_datetime(text, fallback=post_date) or post_date.astimezone(MOSCOW_TZ)

    if not is_relevant_event_post(text, parsed_date=parse_event_datetime(text, fallback=post_date)):
        return None
    if starts_at < datetime.now(MOSCOW_TZ) - timedelta(days=2):
        return None

    location = preset.default_location
    if "📍" in text:
        for line in text.split("\n"):
            if "📍" in line:
                location = line.replace("📍", "").strip()[:500]
                break

    return FetchedEvent(
        title=post_title(text),
        description=text[:2000],
        starts_at=starts_at,
        ends_at=None,
        location=location,
        region=preset.region,
        category=infer_category_from_text(text),
        source="vk",
        source_url=f"https://vk.com/wall-{group_id}_{post_id}",
    )


async def fetch_vk_events(region: EventRegion | None = None, *, post_count: int = 20) -> list[FetchedEvent]:
    """Fetch normalized events from configured VK groups."""
    groups = [g for g in VK_EVENT_GROUPS if region is None or g.region == region]
    events: list[FetchedEvent] = []
    for preset in groups:
        group_id = await _resolve_group_id(preset.screen_name)
        if not group_id:
            continue
        for post in await _fetch_wall_posts(group_id, count=post_count):
            item = _post_to_fetched(post, preset=preset, group_id=group_id)
            if item:
                events.append(item)
    return events


async def sync_vk_group(
    db: AsyncSession,
    preset: VkGroupPreset,
    *,
    actor_id: int | None = None,
    post_count: int = 20,
) -> EventSyncResult:
    group_id = await _resolve_group_id(preset.screen_name)
    if not group_id:
        return EventSyncResult(
            source="vk",
            region=preset.region.value,
            fetched=0,
            created=0,
            updated=0,
            skipped=0,
            errors=[f"Группа VK «{preset.label}» ({preset.screen_name}) не найдена"],
        )

    errors: list[str] = []
    created = updated = skipped = 0
    posts = await _fetch_wall_posts(group_id, count=post_count)

    for post in posts:
        try:
            item = _post_to_fetched(post, preset=preset, group_id=group_id)
            if not item:
                skipped += 1
                continue
            action = await upsert_fetched_event(db, item, actor_id=actor_id)
            if action == "created":
                created += 1
            elif action == "updated":
                updated += 1
            else:
                skipped += 1
        except Exception as exc:
            logger.exception("VK import failed for %s post %s", preset.screen_name, post.get("id"))
            errors.append(str(exc))

    return EventSyncResult(
        source="vk",
        region=preset.region.value,
        fetched=len(posts),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )


async def sync_events_from_vk(
    db: AsyncSession,
    region: EventRegion,
    *,
    actor_id: int | None = None,
    post_count: int = 20,
) -> EventSyncResult:
    """Import from all VK groups in ``region``, aggregated into one result."""
    presets = [g for g in VK_EVENT_GROUPS if g.region == region]
    if not presets:
        raise EventValidationError(f"Регион {region.value} не настроен для VK")

    if not (settings.VK_GROUP_TOKEN or "").strip() or settings.VK_GROUP_TOKEN.startswith("your-"):
        raise EventValidationError("VK API недоступен. Проверьте VK_GROUP_TOKEN.")

    merged = EventSyncResult(source="vk", region=region.value, fetched=0, created=0, updated=0, skipped=0)
    errors: list[str] = []
    for preset in presets:
        result = await sync_vk_group(db, preset, actor_id=actor_id, post_count=post_count)
        merged = EventSyncResult(
            source="vk",
            region=region.value,
            fetched=merged.fetched + result.fetched,
            created=merged.created + result.created,
            updated=merged.updated + result.updated,
            skipped=merged.skipped + result.skipped,
            errors=errors,
        )
        errors.extend(result.errors)
    return merged


async def sync_all_vk_event_sources(
    db: AsyncSession,
    *,
    actor_id: int | None = None,
) -> list[EventSyncResult]:
    results: list[EventSyncResult] = []
    for region in EventRegion:
        presets = [g for g in VK_EVENT_GROUPS if g.region == region]
        if not presets:
            continue
        try:
            results.append(await sync_events_from_vk(db, region, actor_id=actor_id))
        except EventValidationError as exc:
            results.append(EventSyncResult(
                source="vk",
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[exc.detail],
            ))
    return results


class VkEventSource(EventSource):
    name = "vk"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        return await fetch_vk_events(region)

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if region:
            return [await sync_events_from_vk(db, region, actor_id=actor_id)]
        return await sync_all_vk_event_sources(db, actor_id=actor_id)
