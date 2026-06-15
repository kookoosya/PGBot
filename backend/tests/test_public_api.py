"""Integration tests for public API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_public_info_keys(client: AsyncClient):
    response = await client.get("/api/v1/public/info")
    assert response.status_code == 200
    data = response.json()
    for key in ("site_url", "vk_url", "map_url"):
        assert key in data


@pytest.mark.asyncio
async def test_public_today_schema(client: AsyncClient):
    response = await client.get("/api/v1/public/today")
    assert response.status_code == 200
    data = response.json()
    assert "map" in data
    assert "updated_at" in data
    assert isinstance(data["map"], dict)
    assert "total_places" in data["map"]


@pytest.mark.asyncio
async def test_public_events_search(client: AsyncClient):
    response = await client.get("/api/v1/public/events", params={"search": "концерт"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_create_issue_validation(client: AsyncClient):
    response = await client.post("/api/v1/issues", json={"description": "abc"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_public_info(client: AsyncClient):
    response = await client.get("/api/v1/public/info")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_public_events_region_filter(client: AsyncClient):
    response = await client.get("/api/v1/public/events", params={"region": "pushkin_gory"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


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
async def test_public_classifieds_neighbor_filter(client: AsyncClient):
    response = await client.get("/api/v1/classifieds", params={"neighbor_only": "true"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_public_events_limit(client: AsyncClient):
    response = await client.get("/api/v1/public/events", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_public_event_not_found(client: AsyncClient):
    response = await client.get("/api/v1/public/events/999999999")
    assert response.status_code == 404
