"""Places and map metadata API tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.db_factories import create_place

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_list_places_includes_seeded_place(db_session: AsyncSession, api_client: AsyncClient):
    place = await create_place(db_session, name="Аптека интеграционная")
    response = await api_client.get("/api/v1/places", params={"page_size": "100"})
    assert response.status_code == 200
    data = response.json()
    names = {item["name"] for item in data["items"]}
    assert place.name in names


@pytest.mark.asyncio
async def test_get_place_detail(db_session: AsyncSession, api_client: AsyncClient):
    place = await create_place(db_session, name="Магазин деталей")
    response = await api_client.get(f"/api/v1/places/{place.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Магазин деталей"
    assert "reviews" in response.json()


@pytest.mark.asyncio
async def test_get_place_not_found(api_client: AsyncClient):
    response = await api_client.get("/api/v1/places/999999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_map_stats_returns_center(api_client: AsyncClient):
    response = await api_client.get("/api/v1/places/map/stats")
    assert response.status_code == 200
    data = response.json()
    assert "center" in data
    assert data["center"]["lat"]
