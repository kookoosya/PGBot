"""Backward-compatible re-exports. Prefer ``app.services.vk.ai_history``."""

from app.services.vk.ai_history import append_ai_turn, clear_ai_history, get_ai_history

__all__ = ["append_ai_turn", "clear_ai_history", "get_ai_history"]
