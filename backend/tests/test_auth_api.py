"""Auth API: login, register validation, protected routes."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers.db_factories import TEST_PASSWORD, auth_headers_for, create_user, unique_username

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(api_client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, role_name=UserRole.RESIDENT)
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_returns_token(api_client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, role_name=UserRole.RESIDENT)
    response = await api_client.post(
        "/api/v1/auth/login",
        json={"username": user.username, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_returns_current_user(api_client: AsyncClient, db_session: AsyncSession):
    user = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Иван Тестов")
    response = await api_client.get("/api/v1/auth/me", headers=auth_headers_for(user))
    assert response.status_code == 200
    assert response.json()["username"] == user.username
    assert response.json()["full_name"] == "Иван Тестов"


@pytest.mark.asyncio
async def test_me_requires_auth(api_client: AsyncClient):
    response = await api_client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_owner_check_requires_owner(api_client: AsyncClient, db_session: AsyncSession):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    response = await api_client.get("/api/v1/auth/owner-check", headers=auth_headers_for(resident))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_rejects_short_password(api_client: AsyncClient):
    response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": unique_username("reg"),
            "password": "123",
            "full_name": "Новый житель",
            "phone": "+79001112233",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_creates_resident(api_client: AsyncClient):
    username = unique_username("reg")
    response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": TEST_PASSWORD,
            "full_name": "Новый житель",
            "phone": "+79001112233",
        },
    )
    assert response.status_code == 201
    assert response.json()["username"] == username
