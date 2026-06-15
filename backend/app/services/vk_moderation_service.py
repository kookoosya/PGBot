"""Backward-compatible re-exports. Prefer ``app.services.vk.moderation``."""

from app.services.vk.moderation import (
    ModerationCheckResult,
    ViolationResult,
    check_user_allowed,
    detect_profanity,
    detect_spam,
    evaluate_message_violation_for_user,
    list_moderation_logs,
    list_moderation_states,
    process_incoming_moderation,
    record_violation,
    unblock_vk_user,
)

__all__ = [
    "ModerationCheckResult",
    "ViolationResult",
    "check_user_allowed",
    "detect_profanity",
    "detect_spam",
    "evaluate_message_violation_for_user",
    "list_moderation_logs",
    "list_moderation_states",
    "process_incoming_moderation",
    "record_violation",
    "unblock_vk_user",
]
