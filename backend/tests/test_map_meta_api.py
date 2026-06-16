"""Map metadata endpoints — no database required."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_place_categories_nonempty(client: AsyncClient):
    response = await client.get("/api/v1/places/categories")
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 5
    assert any(item["value"] == "pharmacy" for item in items)


@pytest.mark.asyncio
async def test_complaint_types_nonempty(client: AsyncClient):
    response = await client.get("/api/v1/places/complaint-types")
    assert response.status_code == 200
    values = {item["value"] for item in response.json()}
    assert "price_tag_fraud" in values


@pytest.mark.asyncio
async def test_map_report_types(client: AsyncClient):
    response = await client.get("/api/v1/places/map-report-types")
    assert response.status_code == 200
    values = {item["value"] for item in response.json()}
    assert "map_wrong_hours" in values


@pytest.mark.asyncio
async def test_map_routes_list(client: AsyncClient):
    response = await client.get("/api/v1/places/routes")
    assert response.status_code == 200
    routes = response.json()
    assert isinstance(routes, list)
    assert routes[0]["id"]


@pytest.mark.asyncio
async def test_map_filter_modes(client: AsyncClient):
    response = await client.get("/api/v1/places/map/modes")
    assert response.status_code == 200
    modes = response.json()
    assert any(m["id"] == "shops" for m in modes)
