"""Admin panel operations — audit logs and notification queue."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.audit_log import AuditLog
from app.models.enums import NotificationStatus
from app.models.notification import Notification
from app.services.service_errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


class AdminServiceError(ServiceError):
    """Base error for admin service operations."""


async def list_audit_logs(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
) -> list[dict]:
    """Return paginated audit log entries for the admin panel."""
    safe_page = max(1, page)
    safe_size = max(1, min(page_size, 100))
    result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .offset((safe_page - 1) * safe_size)
        .limit(safe_size)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "user": log.user.username if log.user else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


async def list_admin_notifications(
    db: AsyncSession,
    *,
    status_filter: NotificationStatus | None = None,
    limit: int = 100,
) -> list[dict]:
    """Return recent notifications for the admin panel."""
    query = select(Notification).order_by(Notification.created_at.desc()).limit(max(1, min(limit, 200)))
    if status_filter:
        query = query.where(Notification.status == status_filter)
    result = await db.execute(query)
    return [
        {
            "id": notification.id,
            "issue_id": notification.issue_id,
            "channel": notification.channel,
            "priority": notification.priority,
            "status": notification.status,
            "message": notification.message,
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
            "created_at": notification.created_at.isoformat(),
        }
        for notification in result.scalars().all()
    ]


async def process_pending_notifications(db: AsyncSession, *, limit: int = 50) -> dict[str, int]:
    """Send pending Telegram notifications and mark them as sent."""
    from app.services.telegram import send_telegram_message

    result = await db.execute(
        select(Notification).where(Notification.status == NotificationStatus.PENDING).limit(max(1, min(limit, 100)))
    )
    pending = result.scalars().all()
    sent_count = 0

    for notification in pending:
        success = await send_telegram_message(settings.TELEGRAM_ADMIN_CHAT_ID, notification.message)
        if success:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            sent_count += 1

    logger.info("Processed %s pending notifications, sent %s", len(pending), sent_count)
    return {"processed": len(pending), "sent": sent_count}
