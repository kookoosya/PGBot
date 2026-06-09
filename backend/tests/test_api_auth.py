"""Интеграционные тесты auth API."""

import pytest
from app.core.auth_cookies import REFRESH_COOKIE_USER
from httpx import AsyncClient

from tests.conftest import API_PREFIX, TEST_PASSWORD, xhr_headers

pytestmark = pytest.mark.asyncio


async def test_register_resident(client: AsyncClient):
    payload = {
        "username": "new_resident",
        "password": TEST_PASSWORD,
        "full_name": "Иван Житель",
        "phone": "+79001234567",
        "role": "resident",
    }
    response = await client.post(f"{API_PREFIX}/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_resident"
    assert data["role"] == "resident"
    assert data["full_name"] == "Иван Житель"


async def test_login_sets_refresh_cookie_and_me(client: AsyncClient, resident_user):
    login = await client.post(
        f"{API_PREFIX}/auth/login?client=user",
        json={"username": resident_user.username, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token
    assert REFRESH_COOKIE_USER in login.cookies

    me = await client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    profile = me.json()
    assert profile["username"] == resident_user.username
    assert profile["role"] == "resident"


async def test_refresh_rotates_access_token(client: AsyncClient, resident_user):
    login = await client.post(
        f"{API_PREFIX}/auth/login?client=user",
        json={"username": resident_user.username, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    old_access = login.json()["access_token"]

    refresh = await client.post(
        f"{API_PREFIX}/auth/refresh?client=user",
        headers=xhr_headers(),
    )
    assert refresh.status_code == 200
    new_access = refresh.json()["access_token"]
    assert new_access
    assert new_access != old_access
    assert REFRESH_COOKIE_USER in refresh.cookies

    me = await client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200


async def test_logout_clears_refresh_cookie(client: AsyncClient, resident_user):
    login = await client.post(
        f"{API_PREFIX}/auth/login?client=user",
        json={"username": resident_user.username, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200

    logout = await client.post(
        f"{API_PREFIX}/auth/logout?client=user",
        headers=xhr_headers(),
    )
    assert logout.status_code == 200

    refresh = await client.post(
        f"{API_PREFIX}/auth/refresh?client=user",
        headers=xhr_headers(),
    )
    assert refresh.status_code == 401
