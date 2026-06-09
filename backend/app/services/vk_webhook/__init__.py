"""Модули обработки VK Callback API (разбиение бывшего vk_webhook.py)."""

from app.services.vk_webhook.handler import handle_message_new

__all__ = ["handle_message_new"]
