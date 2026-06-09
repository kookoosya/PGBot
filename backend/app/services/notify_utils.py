"""Backward-compatible re-export — prefer ``app.utils.notify``."""

from app.utils.notify import safe_notify_owner

__all__ = ["safe_notify_owner"]
