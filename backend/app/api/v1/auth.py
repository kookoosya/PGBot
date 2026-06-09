from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, get_current_user, require_owner
from app.core.rate_limit import limiter
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, Token, UserCreate, UserResponse
from app.services.auth_service import (
    AccountLockedError,
    AuthFailedError,
    AuthValidationError,
    authenticate,
    change_password,
    register_resident,
)
from app.services.user_service import UserValidationError, user_to_response

router = APIRouter()
settings = get_settings()

_AUTH_ERRORS = (AuthFailedError, AuthValidationError, AccountLockedError, UserValidationError)


@router.post("/login", response_model=Token)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(request: Request, data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await authenticate(db, data, ip_address=get_client_ip(request))
    except _AUTH_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.post("/change-password")
async def change_password_endpoint(
    data: ChangePasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        return await change_password(
            db, current_user, data, ip_address=get_client_ip(request),
        )
    except AuthValidationError as exc:
        raise_http_for_service_error(exc)


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/hour")
async def register(request: Request, data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        return await register_resident(db, data)
    except _AUTH_ERRORS as exc:
        raise_http_for_service_error(exc)


@router.get("/owner-check")
async def owner_check(current_user: Annotated[User, Depends(require_owner())]):
    return {"ok": True, "username": current_user.username}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return user_to_response(current_user)
