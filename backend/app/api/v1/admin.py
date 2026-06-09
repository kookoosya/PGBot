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
from app.services.event_sources.coordinator import sync_all_event_sources, sync_event_source

router = APIRouter()


def _sync_responses(results) -> list[EventSyncResponse]:
    return [EventSyncResponse(**result.__dict__) for result in results]


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
                genre=data.genre,
                poster_url=data.poster_url,
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
                genre=update_data.get("genre"),
                poster_url=update_data.get("poster_url"),
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
    """Import events from VK communities (Pushkin Gory + Pskov)."""
    try:
        results = await sync_event_source(db, "vk", region=region, actor_id=current_user.id)
    except EventValidationError as exc:
        raise_http_for_service_error(exc)
    return _sync_responses(results)


@router.post("/events/sync-kudago", response_model=list[EventSyncResponse])
async def admin_sync_kudago_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
    region: EventRegion | None = None,
):
    """Import cinema and concerts from KudaGo (Pskov)."""
    try:
        results = await sync_event_source(db, "kudago", region=region, actor_id=current_user.id)
    except EventValidationError as exc:
        raise_http_for_service_error(exc)
    return _sync_responses(results)


@router.post("/events/sync-timepad", response_model=list[EventSyncResponse])
async def admin_sync_timepad_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
    region: EventRegion | None = None,
):
    """Import events from TimePad (Pskov region)."""
    try:
        results = await sync_event_source(db, "timepad", region=region, actor_id=current_user.id)
    except EventValidationError as exc:
        raise_http_for_service_error(exc)
    return _sync_responses(results)


@router.post("/events/sync-orbilet", response_model=list[EventSyncResponse])
async def admin_sync_orbilet_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    """Import Pskov events from orbilet.ru."""
    results = await sync_event_source(db, "orbilet", actor_id=current_user.id)
    return _sync_responses(results)


@router.post("/events/sync-proculture", response_model=list[EventSyncResponse])
async def admin_sync_proculture_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
    region: EventRegion | None = None,
):
    """Import from PRO.Культура.РФ (requires PROCULTURE_API_KEY)."""
    results = await sync_event_source(db, "proculture", region=region, actor_id=current_user.id)
    return _sync_responses(results)


@router.post("/events/sync-all", response_model=list[EventSyncResponse])
async def admin_sync_all_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    """Sync from all configured sources: VK, TimePad, Orbilet, PRO.Культура, KudaGo."""
    results = await sync_all_event_sources(db, actor_id=current_user.id)
    return _sync_responses(results)


@router.get("/vk-moderation")
async def admin_vk_moderation_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    limit: int = Query(100, ge=1, le=200),
):
    """VK chat moderation states and recent violation logs."""
    from app.schemas.vk_moderation import (
        VkModerationLogResponse,
        VkModerationOverviewResponse,
        VkModerationStateResponse,
    )
    from app.services.vk_moderation_service import list_moderation_logs, list_moderation_states

    states = await list_moderation_states(db, limit=limit)
    logs = await list_moderation_logs(db, limit=limit)
    return VkModerationOverviewResponse(
        states=[VkModerationStateResponse.model_validate(s) for s in states],
        recent_logs=[VkModerationLogResponse.model_validate(log) for log in logs],
    )


@router.post("/vk-moderation/{vk_user_id}/unblock")
async def admin_unblock_vk_user(
    vk_user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    """Clear ban and reset warnings for a VK user."""
    from app.services.vk_moderation_service import unblock_vk_user

    state = await unblock_vk_user(db, vk_user_id)
    if not state:
        raise_http_for_service_error(EventNotFoundError("Пользователь VK не найден в модерации"))
    return {"ok": True, "vk_user_id": vk_user_id}
