from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.services.user_service import (
    UserNotFoundError,
    UserValidationError,
    create_user,
    list_users,
    update_user,
    user_to_response,
)

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: UserRole | None = None,
):
    result = await list_users(db, page=page, page_size=page_size, role=role)
    return [user_to_response(user) for user in result.items]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        user = await create_user(db, data)
    except UserValidationError as exc:
        raise_http_for_service_error(exc)
    return user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: int,
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        user = await update_user(db, user_id, data)
    except UserNotFoundError as exc:
        raise_http_for_service_error(exc)
    return user_to_response(user)
