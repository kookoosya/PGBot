"""Health and root endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "Пушкин" in data["app"]


@pytest.mark.asyncio
async def test_api_root_redirects_or_ok(client: AsyncClient):
    response = await client.get("/api/v1/public/info", follow_redirects=True)
    assert response.status_code == 200
    data = response.json()
    assert "site_url" in data
    assert "sslip.io" in data["site_url"]
