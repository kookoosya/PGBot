"""Tests for VK Mini App silent token authentication."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app


@pytest.fixture
async def vk_auth_client():
    async def _mock_get_db():
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        user = AsyncMock()
        user.id = 42
        user.username = "vk_1001"
        user.email = None
        user.full_name = "Иван Тестов"
        user.phone = None
        user.vk_id = 1001
        user.department_id = None
        user.is_active = True
        user.organization = None
        user.position = None
        user.verification_status = None
        user.password_changed_at = None
        user.created_at = None
        user.role.name.value = "resident"
        user.role.name = user.role.name

        async def _refresh(obj, attribute_names=None):
            return None

        session.refresh.side_effect = _refresh
        yield session

    app.dependency_overrides[get_db] = _mock_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
@patch("app.api.v1.vk_auth.authenticate_vk_mini_app", new_callable=AsyncMock)
async def test_vk_auth_returns_jwt(mock_auth, vk_auth_client: AsyncClient):
    from datetime import datetime, timezone

    from app.models.enums import UserRole
    from app.schemas.auth import UserResponse

    mock_auth.return_value = (
        "jwt-test-token",
        UserResponse(
            id=42,
            username="vk_1001",
            email=None,
            full_name="Иван",
            phone=None,
            vk_id=1001,
            role=UserRole.RESIDENT,
            department_id=None,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        ),
    )

    response = await vk_auth_client.post(
        "/api/v1/vk/auth",
        json={"silent_token": "silent", "uuid": "uuid-1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "jwt-test-token"
    assert data["user"]["vk_id"] == 1001


@pytest.mark.asyncio
async def test_vk_auth_rejects_empty_token(vk_auth_client: AsyncClient):
    response = await vk_auth_client.post(
        "/api/v1/vk/auth",
        json={"silent_token": "", "uuid": "uuid-1"},
    )
    assert response.status_code == 422
