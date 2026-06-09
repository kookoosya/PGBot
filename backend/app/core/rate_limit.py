"""Redis-backed rate limiting via SlowAPI and the ``limits`` storage backend."""

from __future__ import annotations

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings
from app.core.redis_client import redis_host_display

logger = logging.getLogger(__name__)


def create_limiter() -> Limiter:
    """Build a SlowAPI limiter using Redis when configured, otherwise in-memory."""
    settings = get_settings()
    kwargs: dict = {
        "key_func": get_remote_address,
        "key_prefix": settings.RATE_LIMIT_KEY_PREFIX,
        "enabled": settings.RATE_LIMIT_ENABLED,
        "in_memory_fallback_enabled": True,
        "in_memory_fallback": [settings.RATE_LIMIT],
        "swallow_errors": False,
    }

    storage_uri = settings.rate_limit_storage_uri
    if storage_uri:
        kwargs["storage_uri"] = storage_uri
        kwargs["storage_options"] = {
            "socket_connect_timeout": str(settings.REDIS_SOCKET_TIMEOUT),
        }
        logger.info("Rate limiting storage: Redis (%s)", redis_host_display(storage_uri))
    else:
        logger.warning(
            "Rate limiting storage: in-memory only (set REDIS_URL for multi-worker deployments)",
        )

    return Limiter(**kwargs)


limiter = create_limiter()
