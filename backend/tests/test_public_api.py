"""Integration tests for public API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_public_info_keys(client: AsyncClient):
    response = await client.get("/api/v1/public/info")
    assert response.status_code == 200
    data = response.json()
    for key in ("site_url", "vk_url", "map_url", "portal_links"):
        assert key in data
    assert data["site_url"] == "https://192-210-213-135.sslip.io"
    assert data["portal_links"]["home"] == "https://192-210-213-135.sslip.io"


@pytest.mark.asyncio
async def test_public_today_schema(client: AsyncClient):
    response = await client.get("/api/v1/public/today")
    assert response.status_code == 200
    data = response.json()
    assert "map" in data
    assert "updated_at" in data
    assert isinstance(data["map"], dict)
    assert "total_places" in data["map"]


@pytest.mark.postgres
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
async def test_my_issues_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/issues/my")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_classifieds_mine_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/classifieds/mine")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_public_info_portal_links_shape(client: AsyncClient):
    response = await client.get("/api/v1/public/info")
    assert response.status_code == 200
    links = response.json()["portal_links"]
    for key in (
        "home",
        "complaints",
        "complaints_new",
        "classifieds",
        "classifieds_new",
        "events",
        "events_garnect",
        "cabinet",
        "map",
        "jobs",
    ):
        assert key in links
        assert links[key].startswith("http")


@pytest.mark.asyncio
async def test_public_info(client: AsyncClient):
    response = await client.get("/api/v1/public/info")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.postgres
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


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_public_events_list(client: AsyncClient):
    response = await client.get("/api/v1/public/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


@pytest.mark.postgres
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


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_public_classifieds_neighbor_filter(client: AsyncClient):
    response = await client.get("/api/v1/classifieds", params={"neighbor_only": "true"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_public_events_limit(client: AsyncClient):
    response = await client.get("/api/v1/public/events", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_public_events_limit_validation(client: AsyncClient):
    response = await client.get("/api/v1/public/events", params={"limit": 999})
    assert response.status_code == 422


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_public_classifieds_pagination(client: AsyncClient):
    response = await client.get("/api/v1/classifieds", params={"page": 1, "page_size": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert "has_next" in data
    assert "has_prev" in data


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_public_event_not_found(client: AsyncClient):
    response = await client.get("/api/v1/public/events/999999999")
    assert response.status_code == 404
