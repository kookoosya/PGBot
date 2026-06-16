"""Tests for VK flow persistence in PostgreSQL."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.enums import ClassifiedCategory
from app.services.vk.flow_store import clear_flow, get_active_flows, get_flow, save_flow
from app.services.vk.flows import handle_flow_message, start_classified_flow, start_wish_flow
from tests.conftest import postgres_available

pytestmark = pytest.mark.skipif(not postgres_available(), reason="PostgreSQL is not available")


@pytest.fixture
async def db_session():
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


async def _cleanup_peer(db: AsyncSession, peer_id: int) -> None:
    await clear_flow(db, peer_id)
    await db.flush()


@pytest.mark.asyncio
async def test_save_get_clear_flow(db_session: AsyncSession):
    peer_id = 9_001_001
    await _cleanup_peer(db_session, peer_id)
    flow = {"kind": "wish", "step": "message", "data": {}}

    assert await get_flow(db_session, peer_id) is None

    await save_flow(db_session, peer_id, flow)
    loaded = await get_flow(db_session, peer_id)
    assert loaded == flow
    assert peer_id in await get_active_flows(db_session)

    await clear_flow(db_session, peer_id)
    assert await get_flow(db_session, peer_id) is None
    assert peer_id not in await get_active_flows(db_session)


@pytest.mark.asyncio
async def test_classified_category_roundtrip(db_session: AsyncSession):
    peer_id = 9_001_002
    await _cleanup_peer(db_session, peer_id)
    flow = {
        "kind": "classified",
        "step": "title",
        "data": {"category": ClassifiedCategory.JOB_TOURISM},
    }
    await save_flow(db_session, peer_id, flow)

    loaded = await get_flow(db_session, peer_id)
    assert loaded is not None
    assert loaded["data"]["category"] == ClassifiedCategory.JOB_TOURISM
    await _cleanup_peer(db_session, peer_id)


@pytest.mark.asyncio
async def test_wish_flow_survives_new_session():
    """Имитация рестарта: после commit новая сессия читает шаг из БД."""
    import os

    if not postgres_available():
        pytest.skip("PostgreSQL is not available")

    peer_id = 9_001_003
    from_id = 42
    url = os.environ["DATABASE_URL"]
    engine = create_async_engine(url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await clear_flow(session, peer_id)
        await session.commit()
        await start_wish_flow(session, peer_id)
        await session.commit()

    async with session_factory() as session:
        loaded = await get_flow(session, peer_id)
        assert loaded is not None
        assert loaded["kind"] == "wish"
        reply = await handle_flow_message(session, peer_id, from_id, "отмена")
        assert reply is not None
        assert "Отменено" in reply
        await clear_flow(session, peer_id)
        await session.commit()

    await engine.dispose()


@pytest.mark.asyncio
async def test_classified_flow_persists_steps(db_session: AsyncSession):
    peer_id = 9_001_004
    await _cleanup_peer(db_session, peer_id)
    await start_classified_flow(db_session, peer_id)

    reply = await handle_flow_message(db_session, peer_id, 1, "Продаю велосипед")
    assert reply is not None
    assert "Шаг 2" in reply

    loaded = await get_flow(db_session, peer_id)
    assert loaded is not None
    assert loaded["step"] == "description"
    assert loaded["data"]["title"] == "Продаю велосипед"
    await _cleanup_peer(db_session, peer_id)
