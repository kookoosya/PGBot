"""Integration tests for public API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"


@pytest.mark.asyncio
async def test_public_today_shape(client: AsyncClient):
    response = await client.get("/api/v1/public/today")
    assert response.status_code == 200
    data = response.json()
    assert "upcoming_events" in data
    assert isinstance(data["upcoming_events"], list)


@pytest.mark.asyncio
async def test_public_events_list(client: AsyncClient):
    response = await client.get("/api/v1/public/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_public_classifieds_list(client: AsyncClient):
    response = await client.get("/api/v1/classifieds")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_public_classifieds_categories(client: AsyncClient):
    response = await client.get("/api/v1/classifieds/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_public_event_not_found(client: AsyncClient):
    response = await client.get("/api/v1/public/events/999999999")
    assert response.status_code == 404
