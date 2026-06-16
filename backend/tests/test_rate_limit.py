"""Rate limiter storage configuration."""

from app.config import get_settings
from app.core.rate_limit import _storage_uri, limiter


def test_limiter_exists():
    assert limiter is not None


def test_storage_uri_empty_without_redis(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "")
    get_settings.cache_clear()
    _storage_uri.cache_clear()
    assert _storage_uri() is None


def test_storage_uri_uses_redis_url(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    get_settings.cache_clear()
    _storage_uri.cache_clear()
    assert _storage_uri() == "redis://redis:6379/0"
