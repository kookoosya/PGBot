"""Общие фикстуры для API-интеграционных тестов."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from app.config import get_settings
from app.core.security import create_access_token, get_password_hash
from app.database import get_db
from app.main import app
from app.models.enums import UserRole, VerificationStatus
from app.models.user import Role, User
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
)

TEST_PASSWORD = "TestPass123!"
API_PREFIX = "/api/v1"


def xhr_headers(**extra: str) -> dict[str, str]:
    return {"X-Requested-With": "XMLHttpRequest", **extra}


ROLES = [
    (UserRole.RESIDENT, "Житель"),
    (UserRole.MODERATOR, "Модератор"),
    (UserRole.ADMINISTRATION, "Администрация"),
    (UserRole.SOCIAL_SERVICE, "Соцслужбы"),
    (UserRole.SUPER_ADMIN, "Суперадмин"),
    (UserRole.SERVICE_PROVIDER, "Мастер"),
]


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Стабильные настройки и снятые rate limits для тестов."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-pytest-only")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", DATABASE_URL)
    monkeypatch.setenv("LOGIN_RATE_LIMIT", "1000/second")
    monkeypatch.setenv("ISSUE_RATE_LIMIT", "1000/second")
    monkeypatch.setenv("CLASSIFIED_RATE_LIMIT", "1000/second")
    monkeypatch.setenv("RATE_LIMIT", "1000/second")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def mock_external_notifications(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop(*_args, **_kwargs):
        return None

    monkeypatch.setattr("app.services.notifications.notify_owner", noop)
    monkeypatch.setattr("app.services.notifications.notify_issue_status", noop)
    monkeypatch.setattr("app.services.classified_service.notify_owner", noop)


@pytest.fixture(autouse=True)
def mock_issue_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_analyze(text: str, _context: str = "") -> dict:
        return {
            "is_valid": True,
            "category": "utilities",
            "priority": "medium",
            "summary": text[:80],
            "duplicate_probability": 0.0,
            "suggested_department": None,
        }

    monkeypatch.setattr("app.services.issue_processor.analyze_issue", fake_analyze)


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except OSError as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await db_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        await session.close()
        await transaction.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def ensure_roles(db: AsyncSession) -> dict[UserRole, Role]:
    roles: dict[UserRole, Role] = {}
    for name, description in ROLES:
        result = await db.execute(select(Role).where(Role.name == name))
        role = result.scalar_one_or_none()
        if not role:
            role = Role(name=name, description=description)
            db.add(role)
            await db.flush()
        roles[name] = role
    return roles


async def create_user(
    db: AsyncSession,
    *,
    username: str,
    role: UserRole,
    password: str = TEST_PASSWORD,
    full_name: str | None = None,
    phone: str | None = None,
) -> User:
    roles = await ensure_roles(db)
    now = datetime.now(UTC)
    user = User(
        username=username,
        email=f"{username}@test.local",
        hashed_password=get_password_hash(password),
        full_name=full_name or username,
        phone=phone,
        role_id=roles[role].id,
        password_changed_at=now,
        verification_status=VerificationStatus.APPROVED
        if role != UserRole.RESIDENT
        else VerificationStatus.NOT_REQUIRED,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["role"])
    return user


def auth_header(user: User) -> dict[str, str]:
    pwd_ts = int((user.password_changed_at or user.created_at).timestamp())
    role_name = user.role.name.value if hasattr(user.role.name, "value") else user.role.name
    token = create_access_token({"sub": str(user.id), "role": role_name, "pwd": pwd_ts})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def resident_user(db_session: AsyncSession) -> User:
    return await create_user(db_session, username="resident_test", role=UserRole.RESIDENT, phone="+79001112233")


@pytest_asyncio.fixture
async def official_user(db_session: AsyncSession) -> User:
    return await create_user(db_session, username="admin_test", role=UserRole.ADMINISTRATION)


@pytest_asyncio.fixture
async def resident_headers(resident_user: User) -> dict[str, str]:
    return auth_header(resident_user)


@pytest_asyncio.fixture
async def official_headers(official_user: User) -> dict[str, str]:
    return auth_header(official_user)
