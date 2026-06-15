"""VK API client and AI mode — safe imports without routing/flows side effects."""

from app.services.vk.ai_mode import enter_ai_mode, exit_ai_mode, is_ai_mode
from app.services.vk.client import (
    get_ai_keyboard,
    get_inline_links_keyboard,
    get_welcome_keyboard,
    get_welcome_message,
    parse_vk_message,
    send_message,
    vk_api_call,
)

__all__ = [
    "enter_ai_mode",
    "exit_ai_mode",
    "get_ai_keyboard",
    "get_inline_links_keyboard",
    "get_welcome_keyboard",
    "get_welcome_message",
    "is_ai_mode",
    "parse_vk_message",
    "send_message",
    "vk_api_call",
]
