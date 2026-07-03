"""Map stats must respect territorial scope (village vs district)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.place_scope import MUNICIPAL_DISTRICT, VILLAGE
from app.models.enums import PlaceCategory
from app.models.place import Place
from app.services.place.stats import get_map_stats
from app.services.pushkin_places_seed import sync_inventory_scopes
from tests.helpers.db_factories import create_place

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_map_stats_village_excludes_district_hospitals(
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    await create_place(
        db_session,
        name="Филиал больницы",
        category=PlaceCategory.HOSPITAL,
        scope=VILLAGE,
    )
    await create_place(
        db_session,
        name="ФАП д.Блажи",
        category=PlaceCategory.HOSPITAL,
        scope=MUNICIPAL_DISTRICT,
    )
    fap_null = Place(
        name="ФАП д.Крылово",
        category=PlaceCategory.HOSPITAL,
        latitude=57.07,
        longitude=29.0,
        is_active=True,
        scope=None,
        external_source="osm",
        osm_id="node/28",
    )
    db_session.add(fap_null)
    await db_session.flush()

    stats = await get_map_stats(db_session, scope=VILLAGE)
    assert stats.by_category.get("hospital") == 1
    assert stats.total_places == 1
    assert stats.catalog_places == 1
    assert sum(stats.by_category.values()) == stats.catalog_places
    assert stats.village_places == 1
    assert stats.district_places == 1

    response = await api_client.get("/api/v1/places/map/stats", params={"scope": "VILLAGE"})
    assert response.status_code == 200
    data = response.json()
    assert data["scope"] == "VILLAGE"
    assert data["by_category"].get("hospital") == 1
    assert data["village_places"] == 1
    assert data["district_places"] == 1


@pytest.mark.asyncio
async def test_sync_inventory_scopes_patches_osm_faps(db_session: AsyncSession):
    fap = Place(
        name="ФАП д.Блажи",
        category=PlaceCategory.HOSPITAL,
        latitude=57.0855884,
        longitude=28.8787536,
        is_active=True,
        scope=None,
        external_source="osm",
        osm_id="node/27",
    )
    db_session.add(fap)
    await db_session.flush()

    updated = await sync_inventory_scopes(db_session)
    assert updated >= 1
    assert fap.scope == MUNICIPAL_DISTRICT


@pytest.mark.asyncio
async def test_places_search_defaults_to_village_scope(
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    await create_place(
        db_session,
        name="Посёлковая аптека",
        category=PlaceCategory.PHARMACY,
        scope=VILLAGE,
    )
    await create_place(
        db_session,
        name="ФАП аптека",
        category=PlaceCategory.PHARMACY,
        scope=MUNICIPAL_DISTRICT,
    )

    response = await api_client.get("/api/v1/places", params={"page_size": "100"})
    assert response.status_code == 200
    names = {item["name"] for item in response.json()["items"]}
    assert "Посёлковая аптека" in names
    assert "ФАП аптека" not in names
