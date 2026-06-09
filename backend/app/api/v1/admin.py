from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.enums import EventRegion, NotificationStatus
from app.models.user import User
from app.schemas.event import EventCreate, EventListResponse, EventResponse, EventSyncResponse, EventUpdate
from app.services.admin_service import list_admin_notifications, list_audit_logs, process_pending_notifications
from app.services.event_service import (
    EventCreateInput,
    EventNotFoundError,
    EventUpdateInput,
    EventValidationError,
    build_event_list_response,
    create_event,
    event_to_response,
    get_event_by_id,
    list_events_admin,
    update_event,
)
from app.services.event_sync_service import sync_all_vk_event_sources, sync_events_from_vk

router = APIRouter()


@router.get("/audit-logs")
async def get_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    return await list_audit_logs(db, page=page, page_size=page_size)


@router.get("/notifications")
async def get_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    status_filter: NotificationStatus | None = None,
):
    return await list_admin_notifications(db, status_filter=status_filter)


@router.post("/notifications/process-queue")
async def process_notification_queue(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await process_pending_notifications(db)


@router.get("/events", response_model=EventListResponse)
async def admin_list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    include_unpublished: bool = Query(True),
    limit: int = Query(50, ge=1, le=100),
):
    events = await list_events_admin(db, include_unpublished=include_unpublished, limit=limit)
    return build_event_list_response(events)


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
                region=data.region,
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
                region=update_data.get("region"),
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


@router.post("/events/sync-vk", response_model=list[EventSyncResponse])
async def admin_sync_vk_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
    region: EventRegion | None = None,
):
    """Import events from official VK communities (Pushkin Gory + Pskov)."""
    try:
        if region:
            results = [await sync_events_from_vk(db, region, actor_id=current_user.id)]
        else:
            results = await sync_all_vk_event_sources(db, actor_id=current_user.id)
    except EventValidationError as exc:
        raise_http_for_service_error(exc)
    return [EventSyncResponse(**result.__dict__) for result in results]
