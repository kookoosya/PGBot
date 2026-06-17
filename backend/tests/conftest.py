"""Pytest fixtures for API integration tests."""

import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/test_db",
)
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("TESTING", "true")
# Щедрые лимиты в тестах — иначе e2e с одного IP ловят 429
os.environ.setdefault("RATE_LIMIT", "10000/minute")
os.environ.setdefault("CLASSIFIED_RATE_LIMIT", "10000/hour")
os.environ.setdefault("ISSUE_RATE_LIMIT", "10000/hour")
os.environ.setdefault("LOGIN_RATE_LIMIT", "10000/minute")

from app.main import app  # noqa: E402
from app.core.rate_limit import limiter

limiter.enabled = False


@pytest.fixture(autouse=True)
async def _reset_async_engine():
    from app.database import engine

    await engine.dispose()
    yield
    await engine.dispose()


_DB_OK: bool | None = None

_ROLE_ROWS = [
    ("resident", "Житель поселка"),
    ("moderator", "Модератор"),
    ("administration", "Администрация района"),
    ("social_service", "Социальные службы"),
    ("super_admin", "Суперадминистратор"),
    ("service_provider", "Мастер услуг"),
]


def _seed_roles_if_needed() -> None:
    import psycopg2

    conn = psycopg2.connect(os.environ["DATABASE_URL_SYNC"])
    try:
        with conn.cursor() as cur:
            for name, description in _ROLE_ROWS:
                cur.execute(
                    "INSERT INTO roles (name, description) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING",
                    (name, description),
                )
        conn.commit()
    finally:
        conn.close()


def postgres_available() -> bool:
    global _DB_OK
    if _DB_OK is not None:
        return _DB_OK

    try:
        import psycopg2

        conn = psycopg2.connect(os.environ["DATABASE_URL_SYNC"])
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            conn.close()
        _DB_OK = True
    except Exception:
        _DB_OK = False
    return _DB_OK


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "postgres: requires PostgreSQL (skipped locally without DB)",
    )
    if os.environ.get("GITHUB_ACTIONS") == "true" and not postgres_available():
        raise pytest.UsageError("PostgreSQL is required in CI but is not reachable")
    if postgres_available():
        _seed_roles_if_needed()


def pytest_collection_modifyitems(config, items):
    if postgres_available():
        return
    skip_db = pytest.mark.skip(reason="PostgreSQL is not available")
    for item in items:
        if item.get_closest_marker("postgres"):
            item.add_marker(skip_db)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session():
    """Transactional DB session rolled back after each test."""
    if not postgres_available():
        pytest.skip("PostgreSQL is not available")

    from app.database import AsyncSessionLocal, engine

    await engine.dispose()
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest.fixture
async def api_client(db_session):
    """HTTP client with shared transactional DB session."""
    from app.database import get_db

    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)
