"""Unit tests for Redis-backed rate limit configuration."""

from __future__ import annotations

import pytest
from app.config import Settings


def test_rate_limit_storage_auto_uses_redis_when_url_set():
    settings = Settings(REDIS_URL="redis://redis:6379/0", RATE_LIMIT_STORAGE="auto")
    assert settings.rate_limit_storage_uri == "redis://redis:6379/0"


def test_rate_limit_storage_auto_falls_back_to_memory_without_redis():
    settings = Settings(REDIS_URL="", RATE_LIMIT_STORAGE="auto")
    assert settings.rate_limit_storage_uri is None


def test_rate_limit_storage_memory_forces_in_process_counters():
    settings = Settings(REDIS_URL="redis://redis:6379/0", RATE_LIMIT_STORAGE="memory")
    assert settings.rate_limit_storage_uri is None


def test_rate_limit_storage_redis_requires_url():
    settings = Settings(REDIS_URL="", RATE_LIMIT_STORAGE="redis")
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        _ = settings.rate_limit_storage_uri


def test_create_limiter_uses_memory_in_tests():
    from app.core.rate_limit import limiter

    assert limiter._storage is not None
    assert "memory" in type(limiter._storage).__name__.lower()
