"""Publish relevant site events to the VK community wall."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import EVENT_CATEGORY_LABELS, EVENT_REGION_LABELS, EventCategory, EventRegion
from app.models.event import Event
from app.services.event_relevance import is_wall_worthy, score_event_for_promotion
from app.services.datetime_utils import format_event_datetime
from app.services.site_urls import public_site_url
from app.services.vk import vk_api_call

logger = logging.getLogger(__name__)
settings = get_settings()

_GROUP_ID_RE = re.compile(r"(?:sel=-|club)(\d+)")


def _parse_group_id() -> int | None:
    raw = (getattr(settings, "VK_GROUP_ID", "") or "").strip()
    if raw.isdigit():
        return int(raw)
    url = (settings.VK_GROUP_URL or "").strip()
    match = _GROUP_ID_RE.search(url)
    if match:
        return int(match.group(1))
    return None


def _category_emoji(category: str) -> str:
    return {
        EventCategory.CINEMA.value: "🎬",
        EventCategory.CULTURE.value: "🎭",
        EventCategory.HOLIDAY.value: "🎉",
        EventCategory.TOURISM.value: "🧭",
        EventCategory.SPORT.value: "⚽",
        EventCategory.EDUCATION.value: "📚",
    }.get(category, "📅")


def format_wall_post(event: Event) -> str:
    """Build VK wall post text for an event."""
    site = public_site_url().rstrip("/")
    try:
        cat = EventCategory(event.category)
        cat_label = EVENT_CATEGORY_LABELS.get(cat, event.category)
    except ValueError:
        cat_label = event.category
    try:
        region_label = EVENT_REGION_LABELS.get(EventRegion(event.region), event.region)
    except ValueError:
        region_label = event.region or ""

    emoji = _category_emoji(event.category)
    lines = [
        f"{emoji} {event.title.strip()}",
        "",
        f"🗓 {format_event_datetime(event.starts_at) if event.starts_at else 'скоро'}",
    ]
    if event.location:
        lines.append(f"📍 {event.location.strip()}")
    if event.genre:
        lines.append(f"Жанр: {event.genre}")
    if region_label:
        lines.append(f"Регион: {region_label} · {cat_label}")

    body = (event.description or "").strip()
    if body:
        teaser = body if len(body) <= 280 else body[:277].rsplit(" ", 1)[0] + "…"
        lines.extend(["", teaser])

    lines.extend([
        "",
        f"Подробнее на портале: {site}/events/{event.id}",
    ])
    if event.source_url:
        lines.append(f"Билеты / источник: {event.source_url}")
    lines.append("")
    lines.append("#ПушкинскиеГоры #Псков #афиша")
    return "\n".join(lines)


async def publish_event_to_wall(db: AsyncSession, event: Event) -> bool:
    """Post a single event to VK wall. Returns True on success."""
    token = (settings.VK_GROUP_TOKEN or "").strip()
    if not token or token.startswith("your-"):
        return False
    if event.vk_posted_at:
        return False

    group_id = _parse_group_id()
    if not group_id:
        logger.warning("VK wall post skipped: set VK_GROUP_ID or VK_GROUP_URL with club id")
        return False

    message = format_wall_post(event)
    params: dict = {
        "owner_id": -group_id,
        "from_group": 1,
        "message": message,
    }

    try:
        result = await vk_api_call("wall.post", params)
        post_id = result if isinstance(result, int) else (result.get("post_id") if isinstance(result, dict) else None)
        event.vk_posted_at = datetime.now(timezone.utc)
        if post_id:
            event.vk_post_id = str(post_id)
        await db.flush()
        logger.info("VK wall: posted event #%s (post_id=%s)", event.id, post_id)
        return True
    except Exception as exc:
        logger.warning("VK wall post failed for event #%s: %s", event.id, exc)
        return False


async def publish_relevant_events_to_wall(db: AsyncSession) -> int:
    """Post top unscored events that pass relevance threshold."""
    if not getattr(settings, "VK_WALL_POST_ENABLED", False):
        return 0

    max_posts = max(1, min(getattr(settings, "VK_WALL_POST_MAX_PER_RUN", 1), 10))
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.vk_posted_at.is_(None),
            Event.starts_at >= now,
        )
    )
    candidates = [
        e for e in result.scalars().all()
        if is_wall_worthy(e, min_score=getattr(settings, "VK_WALL_POST_MIN_SCORE", 65))
    ]
    candidates.sort(key=score_event_for_promotion, reverse=True)

    posted = 0
    for event in candidates[:max_posts]:
        if await publish_event_to_wall(db, event):
            posted += 1
    return posted
