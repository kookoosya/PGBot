"""Backward-compatible re-export — prefer ``app.utils.errors``."""

from app.utils.errors import ServiceError

__all__ = ["ServiceError"]
