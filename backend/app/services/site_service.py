"""Public site metadata for the landing page and VK bot hints.

Public API: ``build_public_info``.
"""

from __future__ import annotations

from app.config import get_settings
from app.canonical_site import CANONICAL_SITE_URL

settings = get_settings()


def vk_bot_ready() -> bool:
    """Return whether VK bot credentials are configured."""
    url = (settings.VK_GROUP_URL or "").rstrip("/")
    token = (settings.VK_GROUP_TOKEN or "").strip()
    if not token or token.startswith("your-"):
        return False
    return url not in ("", "https://vk.com", "http://vk.com")


def vk_mini_app_ready() -> bool:
    """Return whether VK Mini App credentials are configured."""
    from app.services.vk.mini_app_auth import vk_mini_app_configured

    return vk_mini_app_configured()


def build_public_info() -> dict:
    """Return public site URLs and VK bot readiness for the frontend."""
    from app.services.event_source_health import build_event_sources_health

    site = (settings.PUBLIC_SITE_URL or CANONICAL_SITE_URL).rstrip("/")
    vk_url = settings.VK_GROUP_URL.rstrip("/") if settings.VK_GROUP_URL else "https://vk.com"
    ready = vk_bot_ready()
    mini_ready = vk_mini_app_ready()
    app_id = (settings.VK_APP_ID or "").strip()
    return {
        "site_url": site,
        "vk_url": vk_url,
        "vk_bot_ready": ready,
        "vk_mini_app_ready": mini_ready,
        "vk_app_id": app_id or None,
        "vk_bot_hint": (
            "Напишите «Начать» в сообщениях сообщества — бот ответит кнопками: карта, такси, гостиницы."
            if ready
            else "Бот живёт в личных сообщениях сообщества ВКонтакте. Попросите администратора портала дать прямую ссылку."
        ),
        "map_url": f"{site}/map",
        "yandex_maps_add_org": "https://yandex.ru/sprav/add",
        "portal_links": {
            "home": site,
            "complaints": f"{site}/complaints",
            "complaints_new": f"{site}/complaints?new=1",
            "classifieds": f"{site}/classifieds",
            "classifieds_new": f"{site}/classifieds?new=1",
            "events": f"{site}/events",
            "events_garnect": f"{site}/events?festival=garnect",
            "events_garnect_share": f"{site}/share/festival/garnect",
            "cabinet": f"{site}/cabinet",
            "map": f"{site}/map",
            "jobs": f"{site}/jobs",
        },
        "event_sources": build_event_sources_health(),
    }
