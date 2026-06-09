"""Semi-automatic event import from VK communities (Pushkin Gory + Pskov).

KudaGo adapter: ``app.services.kudago_service`` (Pskov cinema/concerts).
Future: Yandex.Afisha can follow the same upsert pattern.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants.event_config import EVENT_CATEGORY_KEYWORDS, VK_EVENT_SOURCE_PRESETS
from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.event_service import EventCreateInput, EventValidationError, create_event, update_event, EventUpdateInput
from app.services.vk import vk_api_call

logger = logging.getLogger(__name__)
settings = get_settings()
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

_DATE_RE = re.compile(
    r"(?P<day>\d{1,2})[.\-/](?P<month>\d{1,2})(?:[.\-/](?P<year>\d{2,4}))?"
    r"(?:\s+(?P<hour>\d{1,2})[:.](?P<minute>\d{2}))?",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class EventSyncResult:
    """Summary of a VK sync run."""

    region: str
    fetched: int
    created: int
    updated: int
    skipped: int
    errors: list[str]


def infer_category_from_text(text: str) -> EventCategory:
    """Guess event category from post text keywords."""
    lower = text.lower()
    for category, keywords in EVENT_CATEGORY_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            try:
                return EventCategory(category)
            except ValueError:
                continue
    if any(word in lower for word in ("музей", "пушкин", "михайловск")):
        return EventCategory.CULTURE
    return EventCategory.OTHER


def parse_event_datetime(text: str, *, fallback: datetime) -> datetime | None:
    """Extract the first date/time from VK post text."""
    match = _DATE_RE.search(text)
    if not match:
        return None

    day = int(match.group("day"))
    month = int(match.group("month"))
    year_raw = match.group("year")
    if year_raw:
        year = int(year_raw)
        if year < 100:
            year += 2000
    else:
        year = fallback.year
        candidate = datetime(year, month, day, tzinfo=MOSCOW_TZ)
        if candidate < fallback.astimezone(MOSCOW_TZ) - timedelta(days=30):
            year += 1

    hour = int(match.group("hour") or 12)
    minute = int(match.group("minute") or 0)
    try:
        return datetime(year, month, day, hour, minute, tzinfo=MOSCOW_TZ)
    except ValueError:
        return None


def _post_title(text: str) -> str:
    line = next((part.strip() for part in text.split("\n") if part.strip()), "Событие")
    return line[:300]


async def _resolve_group_id(screen_name: str) -> int | None:
    """Resolve VK screen name to numeric group id."""
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
        logger.exception("Failed to resolve VK group %s", screen_name)
    return None


async def _fetch_wall_posts(group_id: int, *, count: int = 15) -> list[dict]:
    """Fetch recent wall posts from a VK community."""
    response = await vk_api_call("wall.get", {
        "owner_id": -group_id,
        "count": count,
        "filter": "owner",
    })
    return list(response.get("items", []))


async def _upsert_vk_event(
    db: AsyncSession,
    *,
    region: EventRegion,
    post: dict,
    owner_id: int,
    default_location: str,
    actor_id: int | None,
) -> str:
    """Create or update event from a VK wall post. Returns action: created|updated|skipped."""
    post_id = post.get("id")
    if post_id is None:
        return "skipped"

    text = (post.get("text") or "").strip()
    if len(text) < 12:
        return "skipped"

    source_url = f"https://vk.com/wall-{owner_id}_{post_id}"
    result = await db.execute(select(Event).where(Event.source_url == source_url))
    existing = result.scalar_one_or_none()

    post_date = datetime.fromtimestamp(post.get("date", 0), tz=timezone.utc)
    starts_at = parse_event_datetime(text, fallback=post_date) or post_date.astimezone(MOSCOW_TZ)
    if starts_at < datetime.now(MOSCOW_TZ) - timedelta(days=2):
        return "skipped"

    category = infer_category_from_text(text)
    payload = EventCreateInput(
        title=_post_title(text),
        description=text[:2000],
        starts_at=starts_at,
        ends_at=None,
        location=default_location,
        region=region,
        category=category,
        source="vk",
        source_url=source_url,
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


async def sync_events_from_vk(
    db: AsyncSession,
    region: EventRegion,
    *,
    actor_id: int | None = None,
    post_count: int = 15,
) -> EventSyncResult:
    """Import upcoming events from the configured VK community for ``region``."""
    preset = VK_EVENT_SOURCE_PRESETS.get(region)
    if not preset:
        raise EventValidationError(f"Регион {region.value} не настроен для синхронизации")

    group_id = await _resolve_group_id(preset["screen_name"])
    if not group_id:
        raise EventValidationError(
            "VK API недоступен или группа не найдена. Проверьте VK_GROUP_TOKEN."
        )

    errors: list[str] = []
    created = updated = skipped = 0
    posts = await _fetch_wall_posts(group_id, count=post_count)

    for post in posts:
        try:
            action = await _upsert_vk_event(
                db,
                region=region,
                post=post,
                owner_id=group_id,
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
            logger.exception("VK event import failed for post %s", post.get("id"))
            errors.append(str(exc))

    return EventSyncResult(
        region=region.value,
        fetched=len(posts),
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
    )


async def sync_all_vk_event_sources(
    db: AsyncSession,
    *,
    actor_id: int | None = None,
) -> list[EventSyncResult]:
    """Sync events from all configured VK communities."""
    results: list[EventSyncResult] = []
    for region in VK_EVENT_SOURCE_PRESETS:
        try:
            results.append(await sync_events_from_vk(db, region, actor_id=actor_id))
        except EventValidationError as exc:
            results.append(EventSyncResult(
                region=region.value,
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=[exc.detail],
            ))
    return results
