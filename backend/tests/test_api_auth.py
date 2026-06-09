"""Интеграционные тесты auth API."""

import pytest
from httpx import AsyncClient

from tests.conftest import API_PREFIX, TEST_PASSWORD

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


async def test_login_and_me(client: AsyncClient, resident_user, resident_headers):
    login = await client.post(
        f"{API_PREFIX}/auth/login",
        json={"username": resident_user.username, "password": TEST_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert token

    me = await client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    profile = me.json()
    assert profile["username"] == resident_user.username
    assert profile["role"] == "resident"

    me_cached = await client.get(f"{API_PREFIX}/auth/me", headers=resident_headers)
    assert me_cached.status_code == 200
    assert me_cached.json()["id"] == resident_user.id
