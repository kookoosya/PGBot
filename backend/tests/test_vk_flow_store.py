"""Тесты персистентного хранилища VK flows."""

import pytest
from app.models.enums import ClassifiedCategory
from app.services.vk_flow_store import clear_flow, get_flow, save_flow
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_save_get_clear_flow(db_session: AsyncSession):
    peer_id = 900_001
    flow = {
        "kind": "classified",
        "step": "description",
        "data": {"category": ClassifiedCategory.OTHER, "title": "Продам дрова"},
    }
    await save_flow(db_session, peer_id, flow)
    loaded = await get_flow(db_session, peer_id)
    assert loaded is not None
    assert loaded["kind"] == "classified"
    assert loaded["step"] == "description"
    assert loaded["data"]["title"] == "Продам дрова"
    assert loaded["data"]["category"] == ClassifiedCategory.OTHER

    loaded["step"] = "phone"
    loaded["data"]["description"] = "Сухие берёзовые дрова колотые"
    await save_flow(db_session, peer_id, loaded)
    reloaded = await get_flow(db_session, peer_id)
    assert reloaded["step"] == "phone"

    await clear_flow(db_session, peer_id)
    assert await get_flow(db_session, peer_id) is None
