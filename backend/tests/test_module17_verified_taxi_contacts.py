"""Module 17: verified taxi contacts OSINT — no verified taxi found scenario."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.map_routes import TYRE_ROUTE_NAME, get_map_routes, route_stop_names
from app.services.place import PlaceSearchParams, search_places
from app.services.place_inventory import load_place_inventory
from app.services.pushkin_places_seed import TAXI_SEED, _public_phone, seed_taxi_services, seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DOC = REPO_ROOT / "docs" / "factual-integrity" / "module-17-verified-taxi-contacts.md"

WORK_TAXI_KEY = "work-taxi-candidate"
EXPECTED_VILLAGE_COUNT = 45
EXPECTED_VERIFIED_PHONE_COUNT = 20


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def _village_places() -> list[dict]:
    return [
        p
        for p in load_place_inventory()
        if p.get("decision") in {"KEEP", "RESTORE"}
        and p.get("active_status") != "CLOSED_CONFIRMED"
        and p.get("seed_as_reference", True)
        and p.get("scope") == "VILLAGE"
    ]


def test_module17_audit_doc_exists():
    assert AUDIT_DOC.is_file()
    text = AUDIT_DOC.read_text(encoding="utf-8")
    assert "NOT_FOUND" in text
    assert "work-taxi-candidate" in text
    assert "OSINT" in text


def test_module17_taxi_seed_still_empty():
    assert TAXI_SEED == []


def test_module17_work_taxi_still_rejected():
    taxi = _entry(WORK_TAXI_KEY)
    assert taxi["decision"] == "NOT_PUBLIC_SERVICE"
    assert taxi.get("phone") is None
    assert taxi.get("latitude") is None
    assert not taxi.get("seed_as_reference", True)


def test_module17_no_verified_taxi_in_inventory():
    taxi_places = [
        p
        for p in load_place_inventory()
        if p.get("category") == "taxi" and p.get("decision") in {"KEEP", "RESTORE"}
    ]
    assert taxi_places == []


def test_module17_no_inventory_phone_for_work_taxi():
    assert _public_phone(_entry(WORK_TAXI_KEY)) is None


def test_module17_catalog_count_unchanged():
    assert len(_village_places()) == EXPECTED_VILLAGE_COUNT


def test_module17_verified_phone_count_unchanged():
    verified = [p for p in _village_places() if _public_phone(p)]
    assert len(verified) == EXPECTED_VERIFIED_PHONE_COUNT


def test_module17_routes_unchanged():
    assert len(get_map_routes()) == 11
    assert TYRE_ROUTE_NAME not in route_stop_names()


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module17_taxi_api_empty(db_session: AsyncSession, api_client: AsyncClient):
    await seed_village_places(db_session)
    await seed_taxi_services(db_session)
    resp = await api_client.get("/api/v1/places/taxi")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module17_seed_deactivates_legacy_taxi(db_session: AsyncSession):
    from app.models.taxi import TaxiService

    legacy = TaxiService(
        name="Наше такси",
        phone="+7 (921) 000-28-28",
        description="legacy placeholder",
        is_active=True,
    )
    db_session.add(legacy)
    await db_session.flush()
    await seed_taxi_services(db_session)
    await db_session.refresh(legacy)
    assert legacy.is_active is False


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module17_kdc_and_stolovaya_searchable(db_session: AsyncSession):
    await seed_village_places(db_session)
    kdc = await search_places(db_session, PlaceSearchParams(search="КДЦ", scope="VILLAGE"))
    stolovaya = await search_places(
        db_session, PlaceSearchParams(search="столовая", scope="VILLAGE")
    )
    assert kdc.total >= 1
    assert stolovaya.total >= 1


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module17_school_count_two(db_session: AsyncSession):
    from sqlalchemy import select

    from app.models.enums import PlaceCategory
    from app.models.place import Place

    await seed_village_places(db_session)
    schools = (
        await db_session.execute(
            select(Place).where(Place.category == PlaceCategory.SCHOOL, Place.scope == "VILLAGE")
        )
    ).scalars().all()
    assert len(schools) == 2
