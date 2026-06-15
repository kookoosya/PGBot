"""Backward-compatible re-exports. Prefer ``app.services.vk.subscription``."""

from app.services.vk.subscription import (
    normalize_subscription_categories,
    subscriber_wants_category,
    subscription_options_text,
)

__all__ = [
    "normalize_subscription_categories",
    "subscriber_wants_category",
    "subscription_options_text",
]
