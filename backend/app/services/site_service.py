"""Public site metadata for the landing page and VK bot hints.

Public API: ``build_public_info``.
"""

from __future__ import annotations

from app.config import get_settings

settings = get_settings()


def vk_bot_ready() -> bool:
    """Return whether VK bot credentials are configured."""
    url = (settings.VK_GROUP_URL or "").rstrip("/")
    token = (settings.VK_GROUP_TOKEN or "").strip()
    if not token or token.startswith("your-"):
        return False
    return url not in ("", "https://vk.com", "http://vk.com")


def build_public_info() -> dict:
    """Return public site URLs and VK bot readiness for the frontend."""
    site = settings.PUBLIC_SITE_URL.rstrip("/")
    vk_url = settings.VK_GROUP_URL.rstrip("/") if settings.VK_GROUP_URL else "https://vk.com"
    ready = vk_bot_ready()
    return {
        "site_url": site,
        "vk_url": vk_url,
        "vk_bot_ready": ready,
        "vk_bot_hint": (
            "Напишите «Начать» в сообщениях сообщества — бот ответит кнопками: карта, такси, гостиницы."
            if ready
            else "Бот живёт в личных сообщениях сообщества ВКонтакте. Попросите администратора портала дать прямую ссылку."
        ),
        "map_url": f"{site}/map",
        "yandex_maps_add_org": "https://yandex.ru/sprav/add",
    }
