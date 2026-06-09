from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_current_user, require_owner
from app.core.rate_limit import limiter
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.enums import ServiceType
from app.models.user import User
from app.schemas.service import (
    AppointmentResponse,
    BookAppointmentRequest,
    BusyBlockCreate,
    BusyBlockResponse,
    ProviderDetailResponse,
    ProviderListItem,
    ProviderRegisterRequest,
    ProviderServiceResponse,
    ServiceItemInput,
    SlotsResponse,
    UpdateScheduleRequest,
)
from app.services.provider_service import (
    ProviderAccessDeniedError,
    ProviderNotFoundError,
    ProviderValidationError,
    add_busy_block,
    add_provider_service,
    approve_provider,
    book_appointment,
    build_provider_detail_response,
    delete_busy_block,
    get_provider_details,
    get_provider_for_user,
    get_provider_slots_response,
    list_busy_blocks,
    list_pending_providers,
    list_provider_appointments,
    list_service_types,
    register_provider,
    reject_provider,
    search_providers,
    update_provider_schedule,
)

router = APIRouter()
settings = get_settings()

_PROVIDER_ERRORS = (ProviderNotFoundError, ProviderValidationError, ProviderAccessDeniedError)


@router.get("/types")
async def list_service_types_endpoint():
    return list_service_types()


@router.post("/register", status_code=201)
@limiter.limit("5/hour")
async def register_provider_endpoint(
    request: Request,
    data: ProviderRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await register_provider(db, data)
    except ProviderValidationError as exc:
        raise_http_for_service_error(exc)


@router.get("/providers", response_model=list[ProviderListItem])
async def list_providers(
    db: Annotated[AsyncSession, Depends(get_db)],
    service_type: ServiceType | None = None,
):
    return await search_providers(db, service_type=service_type)


@router.get("/providers/pending/list")
async def list_pending_providers_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await list_pending_providers(db)


@router.post("/providers/{provider_id}/approve")
async def approve_provider_endpoint(
    provider_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        return await approve_provider(db, provider_id)
    except ProviderNotFoundError as exc:
        raise_http_for_service_error(exc)


@router.post("/providers/{provider_id}/reject")
async def reject_provider_endpoint(
    provider_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    reason: str = "Не подтверждены данные",
):
    try:
        return await reject_provider(db, provider_id, reason=reason)
    except ProviderNotFoundError as exc:
        raise_http_for_service_error(exc)


@router.get("/providers/{provider_id}", response_model=ProviderDetailResponse)
async def get_provider(provider_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await get_provider_details(db, provider_id)
    except ProviderNotFoundError as exc:
        raise_http_for_service_error(exc)


@router.get("/providers/{provider_id}/slots", response_model=SlotsResponse)
async def get_slots(
    provider_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    appointment_date: date = Query(...),
    service_id: int = Query(...),
):
    try:
        return await get_provider_slots_response(
            db, provider_id, appointment_date=appointment_date, service_id=service_id,
        )
    except ProviderNotFoundError as exc:
        raise_http_for_service_error(exc)


@router.post("/providers/{provider_id}/book", response_model=AppointmentResponse, status_code=201)
@limiter.limit(settings.BOOKING_RATE_LIMIT)
async def book_appointment_endpoint(
    request: Request,
    provider_id: int,
    data: BookAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await book_appointment(db, provider_id, data)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.get("/my/profile", response_model=ProviderDetailResponse)
async def my_profile(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        provider = await get_provider_for_user(db, current_user)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)
    return await build_provider_detail_response(db, provider)


@router.post("/my/busy", response_model=BusyBlockResponse, status_code=201)
async def add_busy_block_endpoint(
    data: BusyBlockCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await add_busy_block(db, current_user, data)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.get("/my/busy", response_model=list[BusyBlockResponse])
async def list_busy_blocks_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await list_busy_blocks(db, current_user)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.delete("/my/busy/{block_id}")
async def delete_busy_block_endpoint(
    block_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await delete_busy_block(db, current_user, block_id)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.post("/my/services", response_model=ProviderServiceResponse, status_code=201)
async def add_my_service(
    data: ServiceItemInput,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await add_provider_service(db, current_user, data)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.patch("/my/schedule")
async def update_my_schedule(
    data: UpdateScheduleRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await update_provider_schedule(db, current_user, data)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.get("/my/appointments", response_model=list[AppointmentResponse])
async def my_appointments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await list_provider_appointments(db, current_user)
    except _PROVIDER_ERRORS as exc:
        raise_http_for_service_error(exc)
