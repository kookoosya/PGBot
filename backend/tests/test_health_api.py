"""Health and root endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient, monkeypatch):
    monkeypatch.setenv("GIT_COMMIT", "abc1234")
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data.get("git_commit") == "abc1234"
    assert "Пушкин" in data["app"]
    # Local test env has no REDIS_URL — field omitted unless configured
    from app.config import get_settings

    if not get_settings().REDIS_URL.strip():
        assert "redis" not in data


@pytest.mark.asyncio
async def test_api_root_redirects_or_ok(client: AsyncClient):
    response = await client.get("/api/v1/public/info", follow_redirects=True)
    assert response.status_code == 200
    data = response.json()
    assert "site_url" in data
    assert "pushkinskie-gory.xyz" in data["site_url"]
