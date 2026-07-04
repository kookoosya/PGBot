"""Module 14: map routes completeness and tire service route exclusion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.schemas.place import PlaceResponse
from app.services.map_routes import (
    TYRE_ROUTE_NAME,
    get_map_routes,
    route_stop_names,
)
from app.services.place import PlaceSearchParams, search_places
from app.services.place.responses import build_place_response
from app.services.place_inventory import load_place_inventory
from app.services.pushkin_places_seed import seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"

TYRE_KEY = "shinomontazh-aerodromnaya-23"
MIN_ROUTE_COUNT = 8

FOOD_STOP_NAMES = frozenset(
    {
        "Кафе «Пушкинъ»",
        "Святогоръ",
        "Сиежка",
        "Пушкин-Парк",
    }
)
HOTEL_STOP_NAMES = frozenset(
    {
        "Дружба",
        "Усадьба Тригорская",
        "Дом Классика",
        "Пушкиногорье",
    }
)
PHARMACY_STOP_NAMES = frozenset(
    {
        "Аптека-А",
        "Фарм-М",
    }
)


def _village_seed() -> list[dict]:
    return [
        p
        for p in load_place_inventory()
        if p.get("decision") in {"KEEP", "RESTORE"}
        and p.get("active_status") != "CLOSED_CONFIRMED"
        and p.get("seed_as_reference", True)
        and p.get("scope") == "VILLAGE"
    ]


def test_module14_route_count_at_least_minimum():
    routes = get_map_routes()
    assert len(routes) >= MIN_ROUTE_COUNT
    ids = {route["id"] for route in routes}
    assert "auto-aerodromnaya" not in ids


def test_module14_tyre_not_in_route_stops():
    names = route_stop_names()
    assert TYRE_ROUTE_NAME not in names
    blob = json.dumps(get_map_routes(), ensure_ascii=False)
    assert "aerodromnaya" not in blob.lower()
    assert "auto-aerodromnaya" not in blob


def test_module14_tyre_remains_in_inventory():
    tyres = [p for p in load_place_inventory() if p.get("stable_key") == TYRE_KEY]
    assert len(tyres) == 1
    assert tyres[0].get("category") == "tyre"
    assert tyres[0].get("seed_as_reference") is True


def test_module14_food_route_includes_verified_stops():
    food = next(r for r in get_map_routes() if r["id"] == "village-food")
    names = {stop["name"] for stop in food["stops"]}
    assert FOOD_STOP_NAMES <= names


def test_module14_hotels_route_includes_verified_stops():
    hotels = next(r for r in get_map_routes() if r["id"] == "village-hotels")
    names = {stop["name"] for stop in hotels["stops"]}
    assert HOTEL_STOP_NAMES <= names


def test_module14_pharmacy_route_includes_verified_stops():
    health = next(r for r in get_map_routes() if r["id"] == "pharmacy-health")
    names = {stop["name"] for stop in health["stops"]}
    assert PHARMACY_STOP_NAMES <= names
    assert "Пушкиногорская межрайонная больница" in names


def test_module14_no_duplicate_village_inventory_by_stable_key():
    keys: set[str] = set()
    for entry in load_place_inventory():
        if entry.get("decision") not in {"KEEP", "RESTORE"}:
            continue
        if not entry.get("seed_as_reference", True):
            continue
        if entry.get("scope") != "VILLAGE":
            continue
        sk = entry["stable_key"]
        assert sk not in keys, f"duplicate stable_key {sk!r}"
        keys.add(sk)


def test_module14_inventory_runtime_matches_docs():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_module14_village_catalog_count_unchanged():
    assert len(_village_seed()) == 45


def test_module14_verified_phones_serialize_in_api():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == TYRE_KEY)
    place = Place(
        id=326,
        name=entry["public_name"],
        category=PlaceCategory.TYRE,
        latitude=entry["latitude"],
        longitude=entry["longitude"],
        phone=entry["phone"],
        external_source="reference",
        external_rating=0,
        external_review_count=0,
        verification_status=entry.get("existence_status"),
        verification_source_url="owner:project",
        avg_rating=0,
        review_count=0,
        complaint_count=0,
    )
    resp = build_place_response(place)
    assert isinstance(resp, PlaceResponse)
    assert resp.phone == "+7 (906) 221-03-54"


@pytest.mark.asyncio
async def test_module14_search_finds_cafe_by_common_name(db_session: AsyncSession):
    await seed_village_places(db_session)
    for term in ("Пушкинъ", "Святогоръ", "кафе"):
        result = await search_places(db_session, PlaceSearchParams(search=term, scope="VILLAGE"))
        assert result.total >= 1, f"no results for {term!r}"


@pytest.mark.asyncio
async def test_module14_search_finds_hotels(db_session: AsyncSession):
    await seed_village_places(db_session)
    for term in ("Дружба", "Пушкиногорье", "Тригорская"):
        result = await search_places(db_session, PlaceSearchParams(search=term, scope="VILLAGE"))
        assert result.total >= 1, f"no results for {term!r}"


@pytest.mark.asyncio
async def test_module14_search_finds_pharmacy(db_session: AsyncSession):
    await seed_village_places(db_session)
    result = await search_places(db_session, PlaceSearchParams(search="аптека", scope="VILLAGE"))
    assert result.total >= 2


@pytest.mark.asyncio
async def test_module14_search_finds_tyre_on_map(db_session: AsyncSession):
    await seed_village_places(db_session)
    result = await search_places(db_session, PlaceSearchParams(search="Шиномонтаж", scope="VILLAGE"))
    assert result.total == 1
    assert result.items[0].name == TYRE_ROUTE_NAME
