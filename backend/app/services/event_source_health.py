"""Readiness labels for optional event import sources."""

from __future__ import annotations

from app.config import get_settings
from app.services.event_sources.vk_token_policy import vk_wall_health_status


def _token_ready(value: str) -> bool:
    token = (value or "").strip()
    return bool(token) and not token.startswith("your-")


def timepad_health_status() -> str:
    settings = get_settings()
    return "ready" if _token_ready(settings.TIMEPAD_API_TOKEN) else "needs_token"


def proculture_health_status() -> str:
    settings = get_settings()
    return "ready" if _token_ready(settings.PROCULTURE_API_KEY) else "needs_token"


def build_event_sources_health() -> dict[str, str]:
    return {
        "vk_wall": vk_wall_health_status(),
        "timepad": timepad_health_status(),
        "proculture": proculture_health_status(),
    }
