"""Shared rate limiting — Redis on prod (multi-worker), in-memory fallback for dev."""

from functools import lru_cache

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings


@lru_cache
def _storage_uri() -> str | None:
    url = get_settings().REDIS_URL.strip()
    return url or None


limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri())
