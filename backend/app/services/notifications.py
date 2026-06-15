import logging
import re

from app.config import get_settings
from app.constants.portal_copy import ISSUE_STATUS_HINTS, LINK_COMPLAINTS
from app.services.site_urls import public_site_url
from app.services.telegram import send_telegram_message
from app.services.vk import get_inline_links_keyboard, send_message

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
    "NEW": "🆕 Новая",
    "UNDER_REVIEW": "🔍 На рассмотрении",
    "ASSIGNED": "👤 Назначена",
    "IN_PROGRESS": "🔧 В работе",
    "RESOLVED": "✅ Решена",
    "REJECTED": "❌ Отклонена",
    "ARCHIVED": "📦 В архиве",
}

ISSUE_STATUS_TEXT = {
    "NEW": "Новая",
    "UNDER_REVIEW": "На рассмотрении",
    "ASSIGNED": "Назначена",
    "IN_PROGRESS": "В работе",
    "RESOLVED": "Решена",
    "REJECTED": "Отклонена",
    "ARCHIVED": "В архиве",
}


def issue_status_label(status: str | None) -> str:
    if not status:
        return "—"
    return ISSUE_STATUS_LABELS.get(status, status)


def issue_status_text(status: str | None) -> str:
    if not status:
        return "—"
    return ISSUE_STATUS_TEXT.get(status, status)


def issue_status_hint(status: str | None) -> str:
    if not status:
        return ""
    return ISSUE_STATUS_HINTS.get(status, "")


async def notify_issue_status(issue, *, previous_status: str | None = None) -> bool:
    """Уведомить автора жалобы в VK об изменении статуса."""
    peer_id = getattr(issue, "vk_peer_id", None)
    if not peer_id:
        return False
    status = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
    hint = issue_status_hint(status)
    lines = [
        f"📋 Обращение #{issue.id}: «{issue_status_text(status)}»",
    ]
    if hint:
        lines.append(hint)
    if previous_status and previous_status != status:
        lines.insert(1, f"Было: {issue_status_label(previous_status)}")
    if issue.resolution_text:
        lines.append(f"\nОтвет службы:\n{issue.resolution_text[:500]}")
    path = f"/complaints?issue={issue.id}"
    return await notify_vk_user_with_links(int(peer_id), "\n".join(lines), (LINK_COMPLAINTS, path))


async def notify_vk_user(vk_ref: str | int | None, message: str) -> bool:
    return await notify_vk_user_with_links(vk_ref, message)


async def notify_vk_user_with_links(
    vk_ref: str | int | None,
    message: str,
    *link_pairs: tuple[str, str],
) -> bool:
    """VK DM с кнопками-ссылками на портал. link_pairs: (label, path)."""
    if vk_ref is None:
        return False
    peer_id = parse_vk_id(str(vk_ref)) if not isinstance(vk_ref, int) else vk_ref
    if not peer_id or not settings.VK_GROUP_TOKEN:
        return False
    try:
        site = public_site_url()
        links = [(label, f"{site}{path}") for label, path in link_pairs]
        keyboard = get_inline_links_keyboard(links) if links else None
        await send_message(peer_id, message, keyboard=keyboard)
        return True
    except Exception as exc:
        logger.error("VK user notification failed for %s: %s", vk_ref, exc)
        return False
