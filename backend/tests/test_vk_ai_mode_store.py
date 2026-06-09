"""Тесты персистентного хранилища VK AI mode."""

import pytest
from app.services.vk_ai_mode_store import discard_ai_mode, enter_ai_mode, is_ai_mode
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_enter_is_discard_ai_mode(db_session: AsyncSession):
    peer_id = 900_002
    assert not await is_ai_mode(db_session, peer_id)

    await enter_ai_mode(db_session, peer_id)
    assert await is_ai_mode(db_session, peer_id)

    await enter_ai_mode(db_session, peer_id)
    assert await is_ai_mode(db_session, peer_id)

    await discard_ai_mode(db_session, peer_id)
    assert not await is_ai_mode(db_session, peer_id)
