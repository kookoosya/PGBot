import logging

import httpx

from app.config import get_settings
from app.models.enums import NotificationPriority

logger = logging.getLogger(__name__)
settings = get_settings()

TELEGRAM_API = "https://api.telegram.org/bot{token}"


async def send_telegram_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.warning("Telegram not configured, skipping notification")
        return False

    url = f"{TELEGRAM_API.format(token=settings.TELEGRAM_BOT_TOKEN)}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error("Failed to send Telegram message: %s", e)
        return False


def format_issue_notification(
    issue_id: int,
    summary: str,
    category: str | None,
    priority: str,
    address: str | None = None,
) -> str:
    priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(priority, "🟡")
    lines = [
        f"{priority_emoji} <b>Новое обращение #{issue_id}</b>",
        f"📋 {summary}",
    ]
    if category:
        lines.append(f"📁 Категория: {category}")
    if address:
        lines.append(f"📍 Адрес: {address}")
    return "\n".join(lines)


async def notify_about_issue(
    issue_id: int,
    summary: str,
    category: str | None,
    priority: str,
    address: str | None,
    department_chat_id: str | None,
    priority_level: NotificationPriority = NotificationPriority.NORMAL,
) -> bool:
    message = format_issue_notification(issue_id, summary, category, priority, address)
    chat_id = department_chat_id or settings.TELEGRAM_ADMIN_CHAT_ID
    if not chat_id:
        return False
    return await send_telegram_message(chat_id, message)
