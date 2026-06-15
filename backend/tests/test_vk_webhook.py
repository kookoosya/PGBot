"""Mock tests for VK webhook callback."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import get_settings
from app.database import get_db
from app.main import app


@pytest.fixture
async def vk_client():
    """Client with mocked DB session for VK webhook tests."""

    async def _mock_get_db():
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        yield session

    app.dependency_overrides[get_db] = _mock_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


def _message_new_payload(*, text: str, peer_id: int = 1001, from_id: int = 42) -> dict:
    return {
        "type": "message_new",
        "object": {
            "message": {
                "text": text,
                "from_id": from_id,
                "peer_id": peer_id,
                "id": 1,
                "attachments": [],
            }
        },
    }


@pytest.mark.asyncio
async def test_vk_confirmation(client: AsyncClient):
    settings = get_settings()
    response = await client.post("/api/v1/vk/callback", json={"type": "confirmation"})
    assert response.status_code == 200
    assert response.text == settings.VK_CONFIRMATION_CODE


@pytest.mark.asyncio
async def test_vk_unknown_event_ok(client: AsyncClient):
    response = await client.post("/api/v1/vk/callback", json={"type": "wall_reply_new"})
    assert response.status_code == 200
    assert response.text == "ok"


@pytest.mark.asyncio
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.services.vk.ai_history.clear_ai_history", new_callable=AsyncMock)
@patch("app.services.vk.flow_store.clear_flow", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_menu_welcome(mock_mod, _clear_flow, _clear_ai, mock_send, vk_client: AsyncClient):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="меню"),
    )
    assert response.status_code == 200
    assert response.text == "ok"
    assert mock_send.await_count >= 1


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.send_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_moderation_blocks_message(mock_mod, mock_send, vk_client: AsyncClient):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(
        allowed=False,
        message="⚠️ Предупреждение",
    )
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="спам спам"),
    )
    assert response.status_code == 200
    mock_send.assert_awaited_once()
