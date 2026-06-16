"""Factory helpers for PostgreSQL integration tests."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.security import create_access_token, get_password_hash
from app.models.enums import EventRegion, IssueStatus, PlaceCategory, Priority, UserRole
from app.models.event import Event
from app.models.issue import Issue
from app.models.place import Place
from app.models.user import Role, User

settings = get_settings()
TEST_PASSWORD = "Testpass1234"


def unique_username(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


async def get_or_create_role(db: AsyncSession, role_name: UserRole) -> Role:
    result = await db.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=role_name, description=role_name.value)
        db.add(role)
        await db.flush()
    return role


async def create_user(
    db: AsyncSession,
    *,
    role_name: UserRole,
    username: str | None = None,
    full_name: str = "Test User",
    phone: str | None = None,
) -> User:
    role = await get_or_create_role(db, role_name)
    user = User(
        username=username or unique_username(role_name.value),
        hashed_password=get_password_hash(TEST_PASSWORD),
        full_name=full_name,
        phone=phone,
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user.id)
    )
    return result.scalar_one()


async def create_issue(
    db: AsyncSession,
    *,
    resident: User,
    description: str = "Сломан фонарь на улице Ленина, темно по вечерам",
    status: IssueStatus = IssueStatus.NEW,
) -> Issue:
    issue = Issue(
        description=description,
        status=status,
        priority=Priority.MEDIUM,
        resident_id=resident.id,
        is_spam=False,
    )
    db.add(issue)
    await db.flush()
    return issue


async def create_place(
    db: AsyncSession,
    *,
    name: str = "Тестовый магазин",
    category: PlaceCategory = PlaceCategory.SHOP,
) -> Place:
    place = Place(
        name=name,
        category=category,
        latitude=settings.MAP_CENTER_LAT,
        longitude=settings.MAP_CENTER_LNG,
        is_active=True,
    )
    db.add(place)
    await db.flush()
    return place


async def create_owner_user(db: AsyncSession) -> User:
    username = next(iter(settings.owner_usernames))
    return await create_user(
        db,
        role_name=UserRole.SUPER_ADMIN,
        username=username,
        full_name="Site Owner",
    )


async def create_event(
    db: AsyncSession,
    *,
    title: str,
    region: EventRegion = EventRegion.PUSHKIN_GORY,
    source: str = "vk",
    starts_at: datetime | None = None,
    poster_url: str | None = None,
) -> Event:
    from datetime import timedelta, timezone

    event = Event(
        title=title,
        description="Тестовое событие",
        starts_at=starts_at or datetime.now(timezone.utc) + timedelta(days=3),
        location="Пушкиногорье",
        region=region.value,
        category="culture",
        source=source,
        poster_url=poster_url,
        is_published=True,
    )
    db.add(event)
    await db.flush()
    return event


def auth_headers_for(user: User) -> dict[str, str]:
    pwd_anchor = user.password_changed_at or user.created_at
    pwd_ts = int(pwd_anchor.timestamp()) if pwd_anchor else 0
    token = create_access_token(
        {"sub": str(user.id), "role": user.role.name.value, "pwd": pwd_ts}
    )
    return {"Authorization": f"Bearer {token}"}
