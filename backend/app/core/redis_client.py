"""Async Redis client for shared infrastructure (rate limits, future caches)."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


def redis_host_display(url: str) -> str:
    """Return a log-safe host/db label for a Redis URL."""
    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    db = parsed.path.lstrip("/") or "0"
    return f"{host}:{port}/{db}"


async def init_redis() -> aioredis.Redis | None:
    """Connect to Redis when ``REDIS_URL`` is configured."""
    global _redis
    settings = get_settings()
    if not settings.REDIS_URL:
        logger.info("REDIS_URL is empty — async Redis client disabled")
        return None

    client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
    )
    await client.ping()
    _redis = client
    logger.info("Redis connected (%s)", redis_host_display(settings.REDIS_URL))
    return client


async def close_redis() -> None:
    """Close the shared async Redis connection."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis | None:
    """Return the shared async Redis client, if initialized."""
    return _redis
