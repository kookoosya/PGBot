"""Backward-compatible re-export — use ``app.services.vk.messages``."""

from app.services.vk.messages import (
    SEP,
    ai_enter_text,
    ai_limit_text,
    ai_reply_footer,
    box,
    help_text,
    looks_like_ai_question,
    looks_like_complaint,
    welcome_text,
)

__all__ = [
    "SEP",
    "ai_enter_text",
    "ai_limit_text",
    "ai_reply_footer",
    "box",
    "help_text",
    "looks_like_ai_question",
    "looks_like_complaint",
    "welcome_text",
]
