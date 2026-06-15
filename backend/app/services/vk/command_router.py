"""Тонкий слой маршрутизации VK-бота — публичный API для webhook."""

from app.services.vk.ai_handler import route_ai_message, route_free_chat
from app.services.vk.context import VkRouteContext
from app.services.vk.message_handler import (
    route_complaint,
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
