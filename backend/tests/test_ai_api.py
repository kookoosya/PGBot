"""Public AI endpoints — status and models without upstream calls."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_status(client: AsyncClient):
    response = await client.get("/api/v1/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_ai_models_list(client: AsyncClient):
    response = await client.get("/api/v1/ai/models")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["chat_models"], list)
    assert len(data["chat_models"]) >= 1
    assert isinstance(data["capabilities"], list)


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_ai_usage_anonymous(api_client: AsyncClient):
    response = await api_client.get("/api/v1/ai/usage")
    assert response.status_code == 200
    data = response.json()
    assert "daily_limit" in data
    assert "remaining" in data
