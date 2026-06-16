"""Tests for VK AI mode persistence in PostgreSQL."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.services.ai_mode import enter_ai_mode, exit_ai_mode, is_ai_mode
from app.services.vk_ai_mode_store import get_active_ai_peers
from tests.conftest import postgres_available

pytestmark = pytest.mark.postgres


async def _cleanup_peer(db: AsyncSession, peer_id: int) -> None:
    await exit_ai_mode(db, peer_id)
    await db.flush()


@pytest.mark.asyncio
async def test_enter_exit_is_ai_mode(db_session: AsyncSession):
    peer_id = 9_002_001
    await _cleanup_peer(db_session, peer_id)

    assert await is_ai_mode(db_session, peer_id) is False
    assert peer_id not in await get_active_ai_peers(db_session)

    await enter_ai_mode(db_session, peer_id)
    assert await is_ai_mode(db_session, peer_id) is True
    assert peer_id in await get_active_ai_peers(db_session)

    await enter_ai_mode(db_session, peer_id)
    assert await is_ai_mode(db_session, peer_id) is True

    await exit_ai_mode(db_session, peer_id)
    assert await is_ai_mode(db_session, peer_id) is False
    assert peer_id not in await get_active_ai_peers(db_session)


@pytest.mark.asyncio
async def test_ai_mode_survives_new_session():
    """Имитация рестарта: после commit новая сессия видит AI-режим."""
    import os

    if not postgres_available():
        pytest.skip("PostgreSQL is not available")

    peer_id = 9_002_002
    url = os.environ["DATABASE_URL"]
    engine = create_async_engine(url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await exit_ai_mode(session, peer_id)
        await session.commit()
        await enter_ai_mode(session, peer_id)
        await session.commit()

    async with session_factory() as session:
        assert await is_ai_mode(session, peer_id) is True
        await exit_ai_mode(session, peer_id)
        await session.commit()

    await engine.dispose()
