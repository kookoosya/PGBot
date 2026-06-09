from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_owner
from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import Role, User
from app.schemas.auth import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    role: UserRole | None = None,
):
    query = select(User).options(selectinload(User.role))
    if role:
        query = query.join(Role).where(Role.name == role)
    query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            vk_id=u.vk_id,
            role=u.role.name,
            department_id=u.department_id,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    role_result = await db.execute(select(Role).where(Role.name == data.role))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")

    ok, msg = validate_password(data.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

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
        created_at=user.created_at,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    if "role" in update_data:
        role_result = await db.execute(select(Role).where(Role.name == update_data.pop("role")))
        role = role_result.scalar_one_or_none()
        if role:
            user.role_id = role.id

    for field, value in update_data.items():
        setattr(user, field, value)

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
        created_at=user.created_at,
    )
