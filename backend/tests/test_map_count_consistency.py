"""Map stats catalog/mappable counts and category sum consistency."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.place_scope import MUNICIPAL_DISTRICT, VILLAGE
from app.models.enums import PlaceCategory
from app.services.place.stats import get_map_stats
from tests.helpers.db_factories import create_place

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_map_stats_category_sum_matches_catalog_total(
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    await create_place(db_session, name="A1", category=PlaceCategory.PHARMACY, scope=VILLAGE)
    await create_place(db_session, name="A2", category=PlaceCategory.PHARMACY, scope=VILLAGE)
    await create_place(
        db_session,
        name="District FAP",
        category=PlaceCategory.HOSPITAL,
        scope=MUNICIPAL_DISTRICT,
    )

    stats = await get_map_stats(db_session, scope=VILLAGE)
    assert stats.catalog_places == stats.total_places
    assert sum(stats.by_category.values()) == stats.catalog_places
    assert stats.mappable_places <= stats.catalog_places

    response = await api_client.get("/api/v1/places/map/stats", params={"scope": "VILLAGE"})
    data = response.json()
    assert data["catalog_places"] == data["total_places"]
    assert sum(data["by_category"].values()) == data["catalog_places"]
    assert "mappable_places" in data


@pytest.mark.asyncio
async def test_map_stats_reference_places_respects_scope(
    db_session: AsyncSession,
):
    village = await create_place(
        db_session,
        name="Village ref",
        category=PlaceCategory.SHOP,
        scope=VILLAGE,
    )
    village.external_source = "reference"
    district = await create_place(
        db_session,
        name="District ref",
        category=PlaceCategory.SHOP,
        scope=MUNICIPAL_DISTRICT,
    )
    district.external_source = "reference"
    await db_session.flush()

    stats = await get_map_stats(db_session, scope=VILLAGE)
    assert stats.reference_places == 1
