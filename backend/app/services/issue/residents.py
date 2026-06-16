"""Resident user lookup and creation for complaint ingest."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import UserRole
from app.models.user import Role, User


async def get_or_create_web_resident(
    db: AsyncSession,
    *,
    user: User | None = None,
    phone: str | None = None,
    full_name: str | None = None,
) -> User:
    """Return an existing web resident or create an anonymous site user."""
    if user:
        return user

    if phone:
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.phone == phone)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    role = await _get_resident_role(db)
    suffix = phone or "web"
    return await _create_resident_user(
        db,
        username=f"web_{suffix.replace('+', '').replace(' ', '')}_{int(datetime.now(timezone.utc).timestamp())}",
        full_name=full_name or "Житель сайта",
        role_id=role.id,
        phone=phone,
    )


async def get_or_create_resident(db: AsyncSession, vk_id: int) -> User:
    """Return an existing VK resident or create a new one linked to ``vk_id``."""
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.vk_id == vk_id)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    role = await _get_resident_role(db)
    return await _create_resident_user(
        db,
        username=f"vk_{vk_id}",
        full_name=f"Житель VK {vk_id}",
        role_id=role.id,
        vk_id=vk_id,
    )


async def _get_resident_role(db: AsyncSession) -> Role:
    result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    return result.scalar_one()


async def _create_resident_user(
    db: AsyncSession,
    *,
    username: str,
    full_name: str,
    role_id: int,
    phone: str | None = None,
    vk_id: int | None = None,
) -> User:
    user = User(
        username=username,
        phone=phone,
        vk_id=vk_id,
        full_name=full_name,
        role_id=role_id,
    )
    db.add(user)
    await db.flush()
    return user
