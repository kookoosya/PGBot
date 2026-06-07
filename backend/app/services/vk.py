import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

VK_API_URL = "https://api.vk.com/method"


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
        "random_id": 0,
    }
    if keyboard:
        import json
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)

    result = await vk_api_call("messages.send", params)
    return result if isinstance(result, int) else 0


async def get_photo_url(photo_attachment: dict) -> str | None:
    photo = photo_attachment.get("photo", photo_attachment)
    sizes = photo.get("sizes", [])
    if not sizes:
        return None
    best = max(sizes, key=lambda s: s.get("width", 0) * s.get("height", 0))
    return best.get("url")


def parse_vk_message(event: dict) -> dict | None:
    """Parse VK Callback API message_new event."""
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
            url = None
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
        "buttons": [
            [{"action": {"type": "text", "label": "📋 Мои обращения"}, "color": "primary"}],
            [{"action": {"type": "text", "label": "ℹ️ Как отправить обращение"}, "color": "secondary"}],
        ],
    }
