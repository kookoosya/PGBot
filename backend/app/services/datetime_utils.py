"""Shared datetime formatting helpers for API responses and VK messages."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

DEFAULT_TZ = ZoneInfo("Europe/Moscow")


def format_event_datetime(dt: datetime | None, *, tz: ZoneInfo = DEFAULT_TZ) -> str:
    """Human-readable date/time for event cards."""
    if dt is None:
        return ""
    local = dt.astimezone(tz) if dt.tzinfo else dt.replace(tzinfo=tz)
    return local.strftime("%d.%m.%Y · %H:%M")
