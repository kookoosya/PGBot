"""Backward-compatible re-exports. Prefer ``app.services.vk.ai_mode``."""

from app.services.vk.ai_mode import enter_ai_mode, exit_ai_mode, is_ai_mode

__all__ = ["enter_ai_mode", "exit_ai_mode", "is_ai_mode"]
