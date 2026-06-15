"""Backward-compatible re-exports. Prefer ``app.services.vk.bot``."""

from app.services.vk.bot import (
    format_ads_message,
    list_recent_ads,
    notify_subscribers_new_ad,
    subscribe_peer,
    unsubscribe_peer,
)

__all__ = [
    "format_ads_message",
    "list_recent_ads",
    "notify_subscribers_new_ad",
    "subscribe_peer",
    "unsubscribe_peer",
]
