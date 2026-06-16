"""Pytest fixtures for API integration tests."""

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# CI provides postgres; local runs may skip DB-dependent tests.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://postgres:postgres@localhost:5432/test_db",
)
os.environ.setdefault("DEBUG", "true")

from app.main import app  # noqa: E402

_DB_OK: bool | None = None


def postgres_available() -> bool:
    global _DB_OK
    if _DB_OK is not None:
        return _DB_OK

    url = os.environ["DATABASE_URL"]

    async def _ping() -> bool:
        engine = create_async_engine(url, pool_pre_ping=True)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await engine.dispose()

    import asyncio

    _DB_OK = asyncio.run(_ping())
    return _DB_OK


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "postgres: requires PostgreSQL (skipped locally without DB)",
    )
    if os.environ.get("GITHUB_ACTIONS") == "true" and not postgres_available():
        raise pytest.UsageError("PostgreSQL is required in CI but is not reachable")


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

    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


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
