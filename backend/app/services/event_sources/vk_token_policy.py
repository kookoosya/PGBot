"""VK token selection for event wall import."""

from __future__ import annotations

from app.config import get_settings

settings = get_settings()


def _clean_token(value: str) -> str | None:
    token = (value or "").strip()
    if not token or token.startswith("your-"):
        return None
    return token


def vk_events_access_token() -> str | None:
    """Token for groups.getById and wall.get (prefers user/events token)."""
    return _clean_token(settings.VK_EVENTS_TOKEN) or _clean_token(settings.VK_GROUP_TOKEN)


def vk_wall_access_token(*, group_id: int) -> str | None:
    """Pick token allowed to read ``group_id`` wall."""
    events_token = _clean_token(settings.VK_EVENTS_TOKEN)
    if events_token:
        return events_token
    group_token = _clean_token(settings.VK_GROUP_TOKEN)
    if not group_token:
        return None
    if settings.VK_GROUP_ID and settings.VK_GROUP_ID == group_id:
        return group_token
    return None
