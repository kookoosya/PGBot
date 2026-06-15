"""Backward-compatible re-exports. Prefer ``app.services.vk.command_router``."""

from app.services.vk.command_router import (
    VkRouteContext,
    route_ai_message,
    route_complaint,
    route_free_chat,
    route_vk_message,
    route_welcome,
    send_fallback_message,
)

__all__ = [
    "VkRouteContext",
    "route_ai_message",
    "route_complaint",
    "route_free_chat",
    "route_vk_message",
    "route_welcome",
    "send_fallback_message",
]
