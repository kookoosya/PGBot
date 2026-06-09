"""User administration — list, create and update accounts.

Public API: ``list_users``, ``create_user``, ``update_user``, ``user_to_response``.
Errors: ``UserNotFoundError``, ``UserValidationError``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.models.enums import UserRole
from app.models.user import Role, User
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.utils.errors import ServiceError
from app.utils.pagination import normalize_pagination

logger = logging.getLogger(__name__)


class UserNotFoundError(ServiceError):
    def __init__(self, detail: str = "User not found") -> None:
        super().__init__(detail, status_code=404)


class UserValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


@dataclass(frozen=True, slots=True)
class UserListResult:
    items: list[User]
    total: int
    page: int
    page_size: int


def user_to_response(user: User) -> UserResponse:
    """Map a ``User`` ORM row (with ``role`` loaded) to API response."""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        vk_id=user.vk_id,
        role=user.role.name,
        department_id=user.department_id,
        is_active=user.is_active,
        organization=user.organization,
        position=user.position,
        verification_status=user.verification_status,
        created_at=user.created_at,
    )


async def _get_role(db: AsyncSession, role: UserRole) -> Role:
    result = await db.execute(select(Role).where(Role.name == role))
    found = result.scalar_one_or_none()
    if not found:
        raise UserValidationError("Invalid role")
    return found


async def list_users(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    role: Optional[UserRole] = None,
) -> UserListResult:
    """Return paginated users for the admin panel."""
    query = select(User).options(selectinload(User.role))
    count_query = select(func.count(User.id))
    if role:
        query = query.join(Role).where(Role.name == role)
        count_query = count_query.join(Role).where(Role.name == role)
    query = query.order_by(User.created_at.desc())
    total = (await db.execute(count_query)).scalar() or 0
    safe_page, offset, safe_size, _, _, _ = normalize_pagination(
        page=page, page_size=page_size, total=total,
    )
    result = await db.execute(query.offset(offset).limit(safe_size))
    items = list(result.scalars().all())
    return UserListResult(items=items, total=total, page=safe_page, page_size=safe_size)


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """Create a user account (admin action)."""
    role = await _get_role(db, data.role)
    ok, msg = validate_password(data.password)
    if not ok:
        raise UserValidationError(msg)

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role_id=role.id,
        department_id=data.department_id,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["role"])
    logger.info("User #%s created by admin", user.id)
    return user


async def update_user(db: AsyncSession, user_id: int, data: UserUpdate) -> User:
    """Apply partial updates to a user account."""
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError()

    update_data = data.model_dump(exclude_unset=True)
    if "role" in update_data:
        role = await _get_role(db, update_data.pop("role"))
        user.role_id = role.id

    for field, value in update_data.items():
        setattr(user, field, value)

    return user
