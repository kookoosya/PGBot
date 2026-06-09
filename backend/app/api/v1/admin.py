from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_owner
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.enums import NotificationStatus
from app.models.notification import Notification
from app.models.user import User

router = APIRouter()


@router.get("/audit-logs")
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
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


@router.get("/notifications")
async def get_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    status_filter: NotificationStatus | None = None,
):
    query = select(Notification).order_by(Notification.created_at.desc()).limit(100)
    if status_filter:
        query = query.where(Notification.status == status_filter)
    result = await db.execute(query)
    return [
        {
            "id": n.id,
            "issue_id": n.issue_id,
            "channel": n.channel,
            "priority": n.priority,
            "status": n.status,
            "message": n.message,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "created_at": n.created_at.isoformat(),
        }
        for n in result.scalars().all()
    ]


@router.post("/notifications/process-queue")
async def process_notification_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    from datetime import datetime

    from app.config import get_settings
    from app.services.telegram import send_telegram_message

    settings = get_settings()
    result = await db.execute(select(Notification).where(Notification.status == NotificationStatus.PENDING).limit(50))
    pending = result.scalars().all()
    sent_count = 0

    for notif in pending:
        success = await send_telegram_message(settings.TELEGRAM_ADMIN_CHAT_ID, notif.message)
        if success:
            notif.status = NotificationStatus.SENT
            notif.sent_at = datetime.now(UTC)
            sent_count += 1

    return {"processed": len(pending), "sent": sent_count}
