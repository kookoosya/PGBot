"""Отправка VK-сообщений с inline-ссылками на сайт."""

from app.config import get_settings
from app.services.vk import get_inline_links_keyboard, get_welcome_keyboard, send_message

settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def send_with_site_links(peer_id: int, message: str, *paths: tuple[str, str]) -> None:
    """Отправить текст и кнопки-ссылки на разделы портала."""
    links = [(label, f"{_SITE}{path}") for label, path in paths]
    kb = get_inline_links_keyboard(links) if links else get_welcome_keyboard()
    await send_message(peer_id, message, keyboard=kb)
