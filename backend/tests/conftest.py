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


def pytest_collection_modifyitems(config, items):
    if postgres_available():
        return
    skip = pytest.mark.skip(reason="PostgreSQL is not available")
    for item in items:
        if "test_public_api" in item.nodeid:
            item.add_marker(skip)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
