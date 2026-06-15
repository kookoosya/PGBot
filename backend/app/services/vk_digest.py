"""Backward-compatible re-exports. Prefer ``app.services.vk.digest``."""

from app.services.vk.digest import DIGEST_HOUR_UTC, send_daily_digest

__all__ = ["DIGEST_HOUR_UTC", "send_daily_digest"]
