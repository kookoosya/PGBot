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
@patch("app.api.v1.vk_webhook.route_welcome", new_callable=AsyncMock, return_value=True)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_secret_mismatch_is_ignored(_mock_mod, _welcome, vk_client: AsyncClient):
    from app.services.vk.moderation import ModerationCheckResult

    _mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json={
            "type": "message_new",
            "secret": "invalid",
            "object": {"message": {"text": "меню", "from_id": 1, "peer_id": 1, "id": 1, "attachments": []}},
        },
    )
    assert response.status_code == 200
    assert response.text == "ok"


@pytest.mark.asyncio
@patch("app.services.vk.ai_history.clear_ai_history", new_callable=AsyncMock)
@patch("app.services.vk.flow_store.clear_flow", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
async def test_vk_menu_welcome(mock_send, mock_mod, _clear_flow, _clear_ai, vk_client: AsyncClient):
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


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.services.vk.helpers.subscribe_peer", new_callable=AsyncMock, return_value="Подписка оформлена")
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_subscribe_command(
    mock_mod, mock_subscribe, mock_send, _flow, _ai, _free, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="подписаться"),
    )
    assert response.status_code == 200
    mock_subscribe.assert_awaited_once()
    mock_send.assert_awaited()


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.send_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_classified_flow_handles_message(
    mock_mod, mock_flow, mock_send, _ai, _free, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    mock_flow.return_value = "Шаг 2/5: опишите объявление"
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="продаю велосипед в хорошем состоянии"),
    )
    assert response.status_code == 200
    mock_flow.assert_awaited_once()
    mock_send.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.services.vk.message_handler.process_incoming_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_complaint_routes_to_issue_processor(
    mock_mod, mock_process, _send, _flow, _ai, _free, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    complaint = "не работает фонарь на улице Ленина, уже неделю темно"
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text=complaint, peer_id=2002, from_id=55),
    )
    assert response.status_code == 200
    mock_process.assert_awaited_once()
    assert mock_process.await_args.kwargs["vk_id"] == 55
    assert "фонарь" in mock_process.await_args.kwargs["text"]


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.services.vk.commands.handlers.unsubscribe_peer", new_callable=AsyncMock, return_value="Вы отписаны")
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_unsubscribe_command(
    mock_mod, mock_unsub, _send, _flow, _ai, _free, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="отписаться"),
    )
    assert response.status_code == 200
    mock_unsub.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.services.vk.message_handler.process_incoming_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_short_message_skips_complaint_route(
    mock_mod, mock_process, _send, _flow, _ai, _free, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="спасибо"),
    )
    assert response.status_code == 200
    mock_process.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_vk_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=True)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_ai_question_routes_to_ai_handler(
    mock_mod, _send, _flow, mock_ai, _free, _vk_msg, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="какие мероприятия будут на выходных в пушкинских горах?"),
    )
    assert response.status_code == 200
    mock_ai.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.services.vk.helpers.send_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_help_command(mock_mod, mock_send, _flow, _ai, _free, vk_client: AsyncClient):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="помощь"),
    )
    assert response.status_code == 200
    mock_send.assert_awaited()
    assert "справка" in mock_send.await_args.args[1].lower()


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.api.v1.vk_webhook.route_complaint", new_callable=AsyncMock, return_value=False)
@patch("app.services.vk.message_handler.dispatch_command", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_my_issues_command(
    mock_mod, mock_dispatch, _complaint, _flow, _ai, _free, vk_client: AsyncClient
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="мои обращения", peer_id=4004, from_id=88),
    )
    assert response.status_code == 200
    mock_dispatch.assert_awaited_once()
    assert mock_dispatch.await_args.args[1] == "my_issues"


@pytest.mark.asyncio
@patch("app.api.v1.vk_webhook.transcribe_audio_url", new_callable=AsyncMock, return_value="сделайте карту лучше")
@patch("app.api.v1.vk_webhook.extract_audio_url", return_value="https://audio.test/file.ogg")
@patch("app.api.v1.vk_webhook.route_welcome", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.handle_flow_message", new_callable=AsyncMock, return_value=None)
@patch("app.api.v1.vk_webhook.route_vk_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_ai_message", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_complaint", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.route_free_chat", new_callable=AsyncMock, return_value=False)
@patch("app.api.v1.vk_webhook.send_fallback_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.send_message", new_callable=AsyncMock)
@patch("app.api.v1.vk_webhook.process_incoming_moderation", new_callable=AsyncMock)
async def test_vk_voice_message_transcribe_path(
    mock_mod,
    mock_send,
    mock_fallback,
    _free,
    _complaint,
    _ai,
    _vk,
    _flow,
    _welcome,
    _extract,
    _transcribe,
    vk_client: AsyncClient,
):
    from app.services.vk.moderation import ModerationCheckResult

    mock_mod.return_value = ModerationCheckResult(allowed=True)
    response = await vk_client.post(
        "/api/v1/vk/callback",
        json=_message_new_payload(text="", peer_id=3003, from_id=77),
    )
    assert response.status_code == 200
    mock_send.assert_awaited()
    assert "Распознано" in mock_send.await_args.args[1]
    mock_fallback.assert_awaited_once()
