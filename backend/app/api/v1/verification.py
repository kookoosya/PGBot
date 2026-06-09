from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_client_ip, require_owner
from app.core.rate_limit import limiter
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.user import User
from app.schemas.verification import (
    OfficialRegisterRequest,
    OrganizationRegisterRequest,
    VerificationAction,
    VerificationRequestResponse,
)
from app.services.verification_service import (
    VerificationNotFoundError,
    VerificationValidationError,
    approve_verification,
    list_pending_verifications,
    register_official,
    register_organization,
    reject_verification,
)

router = APIRouter()


@router.post("/register-organization", response_model=VerificationRequestResponse, status_code=201)
@limiter.limit("5/hour")
async def register_organization_endpoint(
    request: Request,
    data: OrganizationRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await register_organization(db, data)
    except VerificationValidationError as exc:
        raise_http_for_service_error(exc)


@router.post("/register-official", response_model=VerificationRequestResponse, status_code=201)
@limiter.limit("5/hour")
async def register_official_endpoint(
    request: Request,
    data: OfficialRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        return await register_official(db, data)
    except VerificationValidationError as exc:
        raise_http_for_service_error(exc)


@router.get("/pending", response_model=list[VerificationRequestResponse])
async def list_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await list_pending_verifications(db)


@router.post("/{user_id}/approve", response_model=VerificationRequestResponse)
async def approve_user(
    user_id: int,
    data: VerificationAction,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    try:
        return await approve_verification(
            db, user_id, data,
            actor_id=current_user.id,
            ip_address=get_client_ip(request),
        )
    except (VerificationNotFoundError, VerificationValidationError) as exc:
        raise_http_for_service_error(exc)


@router.post("/{user_id}/reject", response_model=VerificationRequestResponse)
async def reject_user(
    user_id: int,
    data: VerificationAction,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    try:
        return await reject_verification(
            db, user_id, data,
            actor_id=current_user.id,
            ip_address=get_client_ip(request),
        )
    except (VerificationNotFoundError, VerificationValidationError) as exc:
        raise_http_for_service_error(exc)
