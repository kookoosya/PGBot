from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_client_ip, require_owner
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.enums import NotificationStatus
from app.models.notification import Notification
from app.models.user import User
from app.schemas.event import EventCreate, EventListResponse, EventResponse, EventUpdate
from app.services.event_service import (
    EventCreateInput,
    EventNotFoundError,
    EventUpdateInput,
    EventValidationError,
    create_event,
    event_to_response,
    get_event_by_id,
    list_events_admin,
    update_event,
)

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
    from datetime import datetime, timezone

    from app.services.telegram import send_telegram_message
    from app.config import get_settings

    settings = get_settings()
    result = await db.execute(
        select(Notification).where(Notification.status == NotificationStatus.PENDING).limit(50)
    )
    pending = result.scalars().all()
    sent_count = 0

    for notif in pending:
        success = await send_telegram_message(settings.TELEGRAM_ADMIN_CHAT_ID, notif.message)
        if success:
            notif.status = NotificationStatus.SENT
            notif.sent_at = datetime.now(timezone.utc)
            sent_count += 1

    return {"processed": len(pending), "sent": sent_count}


@router.get("/events", response_model=EventListResponse)
async def admin_list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    include_unpublished: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
):
    events = await list_events_admin(db, include_unpublished=include_unpublished, limit=limit)
    return EventListResponse(
        items=[EventResponse(**event_to_response(event)) for event in events],
        total=len(events),
    )


@router.post("/events", response_model=EventResponse, status_code=201)
async def admin_create_event(
    data: EventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    try:
        event = await create_event(
            db,
            EventCreateInput(
                title=data.title,
                description=data.description,
                starts_at=data.starts_at,
                ends_at=data.ends_at,
                location=data.location,
                category=data.category,
                source=data.source,
                source_url=data.source_url,
                is_published=data.is_published,
            ),
            actor_id=current_user.id,
        )
    except EventValidationError as exc:
        raise_http_for_service_error(exc)
    return EventResponse(**event_to_response(event))


@router.patch("/events/{event_id}", response_model=EventResponse)
async def admin_update_event(
    event_id: int,
    data: EventUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    event = await get_event_by_id(db, event_id)
    if not event:
        raise_http_for_service_error(EventNotFoundError())

    update_data = data.model_dump(exclude_unset=True)
    try:
        event = await update_event(
            db,
            event,
            EventUpdateInput(
                title=update_data.get("title"),
                description=update_data.get("description"),
                starts_at=update_data.get("starts_at"),
                ends_at=update_data.get("ends_at"),
                location=update_data.get("location"),
                category=update_data.get("category"),
                source=update_data.get("source"),
                source_url=update_data.get("source_url"),
                is_published=update_data.get("is_published"),
            ),
            actor_id=current_user.id,
        )
    except EventValidationError as exc:
        raise_http_for_service_error(exc)
    return EventResponse(**event_to_response(event))
