import json
import logging
import random
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

VK_API_URL = "https://api.vk.com/method"
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")

PUSHKIN_WELCOME = (
    "🪶 Портал Пушкинские Горы — ваш помощник в VK!\n\n"
    "То же, что на сайте:\n"
    "📋 Объявления (3 бесплатно)\n"
    "🗺 Карта магазинов и заведений\n"
    "🛠 Услуги соседей\n"
    "🤖 ИИ — ответит на всё + картинки\n"
    "📝 Обращения жителей\n\n"
    f"🌐 {_SITE}"
)

PUSHKIN_AI_HINT = (
    "🤖 ИИ-помощник включён!\n\n"
    "Могу всё: советы, тексты, идеи, расчёты.\n"
    "Картинки — на сайте в разделе ИИ (Nano Banana, Flux…).\n"
    "Лимит: {limit} сообщений/день.\n\n"
    "«Выйти из ИИ» — обратно в меню."
)


async def vk_api_call(method: str, params: dict[str, Any]) -> dict:
    params["access_token"] = settings.VK_GROUP_TOKEN
    params["v"] = settings.VK_API_VERSION

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{VK_API_URL}/{method}", data=params)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            logger.error("VK API error: %s", data["error"])
            raise RuntimeError(data["error"].get("error_msg", "VK API error"))
        return data.get("response", {})


async def send_message(peer_id: int, message: str, keyboard: dict | None = None) -> int:
    params: dict[str, Any] = {
        "peer_id": peer_id,
        "message": message,
        "random_id": random.randint(1, 2**31),
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)

    result = await vk_api_call("messages.send", params)
    return result if isinstance(result, int) else 0


def parse_vk_message(event: dict) -> dict | None:
    obj = event.get("object", {})
    message = obj.get("message", obj)
    if not message:
        return None

    text = message.get("text", "").strip()
    from_id = message.get("from_id") or message.get("user_id")
    peer_id = message.get("peer_id")
    message_id = message.get("id") or message.get("conversation_message_id")

    photos = []
    for att in message.get("attachments", []):
        if att.get("type") == "photo":
            photo = att.get("photo", {})
            sizes = photo.get("sizes", [])
            if sizes:
                best = max(sizes, key=lambda s: s.get("width", 0) * s.get("height", 0))
                url = best.get("url")
                if url:
                    photos.append({"url": url, "vk_photo_id": str(photo.get("id", ""))})

    return {
        "text": text,
        "from_id": from_id,
        "peer_id": peer_id,
        "message_id": message_id,
        "photos": photos,
    }


def get_welcome_keyboard() -> dict:
    return {
        "one_time": False,
        "inline": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "📋 Объявления"}, "color": "primary"},
                {"action": {"type": "text", "label": "🗺 Карта"}, "color": "primary"},
            ],
            [
                {"action": {"type": "text", "label": "🛠 Услуги"}, "color": "primary"},
                {"action": {"type": "text", "label": "🤖 ИИ-помощник"}, "color": "positive"},
            ],
            [
                {"action": {"type": "text", "label": "🌐 Сайт"}, "color": "secondary"},
                {"action": {"type": "text", "label": "🔔 Подписаться"}, "color": "secondary"},
            ],
            [
                {"action": {"type": "text", "label": "📋 Мои обращения"}, "color": "default"},
                {"action": {"type": "text", "label": "ℹ️ Помощь"}, "color": "default"},
            ],
        ],
    }


def get_ai_keyboard() -> dict:
    return {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "🎨 Картинки на сайте"}, "color": "primary"},
                {"action": {"type": "text", "label": "🚪 Выйти из ИИ"}, "color": "negative"},
            ],
        ],
    }


def get_welcome_message() -> str:
    return PUSHKIN_WELCOME
