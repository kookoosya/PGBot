import logging
import re

from app.config import get_settings
from app.services.telegram import send_telegram_message
from app.services.vk import send_message

logger = logging.getLogger(__name__)
settings = get_settings()

_VK_ID_RE = re.compile(r"(?:vk\.com/)?(?:id|club)?(\d+)", re.I)


def parse_vk_id(value: str | None) -> int | None:
    if not value:
        return None
    raw = value.strip()
    if raw.isdigit():
        return int(raw)
    match = _VK_ID_RE.search(raw)
    return int(match.group(1)) if match else None


async def notify_owner_vk(message: str) -> bool:
    peer_id = settings.VK_ADMIN_PEER_ID.strip()
    if not peer_id or not settings.VK_GROUP_TOKEN:
        logger.info("VK owner notification skipped (not configured)")
        return False
    try:
        await send_message(int(peer_id), message)
        return True
    except Exception as exc:
        logger.error("VK owner notification failed: %s", exc)
        return False


async def notify_owner_telegram(message: str) -> bool:
    chat_id = settings.TELEGRAM_ADMIN_CHAT_ID.strip()
    if not chat_id:
        return False
    return await send_telegram_message(chat_id, message)


async def notify_owner(message: str) -> None:
    """Send immediate alert to site owner via VK (primary) and Telegram (fallback)."""
    vk_sent = await notify_owner_vk(message)
    if not vk_sent:
        await notify_owner_telegram(message)


ISSUE_STATUS_LABELS = {
    "new": "🆕 Новая",
    "under_review": "🔍 На рассмотрении",
    "assigned": "👤 Назначена",
    "in_progress": "🔧 В работе",
    "resolved": "✅ Решена",
    "rejected": "❌ Отклонена",
    "archived": "📦 В архиве",
}


async def notify_issue_status(issue) -> bool:
    """Уведомить автора жалобы в VK об изменении статуса."""
    peer_id = getattr(issue, "vk_peer_id", None)
    if not peer_id:
        return False
    status = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
    label = ISSUE_STATUS_LABELS.get(status, status)
    lines = [
        f"📋 Обращение #{issue.id}",
        f"Статус: {label}",
    ]
    if issue.resolution_text:
        lines.append(f"\nОтвет:\n{issue.resolution_text[:500]}")
    lines.append(f"\n🌐 {settings.PUBLIC_SITE_URL.rstrip('/')}/complaints")
    return await notify_vk_user(int(peer_id), "\n".join(lines))


async def notify_vk_user(vk_ref: str | int | None, message: str) -> bool:
    if vk_ref is None:
        return False
    peer_id = parse_vk_id(str(vk_ref)) if not isinstance(vk_ref, int) else vk_ref
    if not peer_id or not settings.VK_GROUP_TOKEN:
        return False
    try:
        await send_message(peer_id, message)
        return True
    except Exception as exc:
        logger.error("VK user notification failed for %s: %s", vk_ref, exc)
        return False
