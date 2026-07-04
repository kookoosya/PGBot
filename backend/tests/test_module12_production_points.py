"""Module 12: remaining production map point verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.schemas.place import PlaceResponse
from app.services.place import PlaceSearchParams, search_places
from app.services.place.responses import build_place_response
from app.services.place_inventory import (
    build_public_description,
    inventory_village_places,
    load_place_inventory,
    primary_verification_url,
)
from app.services.place.stats import get_map_stats
from app.services.pushkin_places_seed import seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"

TYRE_KEY = "shinomontazh-aerodromnaya-23"
KDC_KEY = "kdc-sadovaya-1"
TURBAZA_KEY = "turbaza-pushkinogorye"
STOLOVAYA_KEY = "stolovaya-pushkinogorye-turbaza"
MODULE11_SCHOOL_KEYS = frozenset({"school-1-lenina-30", "art-school-geychenko-pushkinskaya-3"})


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def _ref_key(stable_key: str) -> str:
    return f"ref_{stable_key}"


def test_runtime_and_docs_inventory_identical():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_tyre_aerodromnaya_exists_once():
    tyres = [
        p
        for p in load_place_inventory()
        if p.get("category") == "tyre" and "Аэродромная" in (p.get("address") or "")
    ]
    assert len(tyres) == 1
    assert tyres[0]["stable_key"] == TYRE_KEY


def test_tyre_phone_in_inventory():
    entry = _entry(TYRE_KEY)
    assert entry["phone"] == "+7 (906) 221-03-54"
    assert entry["phone_status"] == "OWNER_CONFIRMED"


def test_tyre_owner_confirmed_evidence_in_inventory():
    entry = _entry(TYRE_KEY)
    assert entry["existence_status"] == "OWNER_CONFIRMED"
    assert primary_verification_url(entry) == "owner:project"


def test_public_api_exposes_verification_fields_for_owner_confirmed():
    place = Place(
        id=2,
        name="Шиномонтаж",
        category=PlaceCategory.TYRE,
        latitude=57.0173,
        longitude=28.9335,
        external_source="reference",
        external_rating=0,
        external_review_count=0,
        verification_status="OWNER_CONFIRMED",
        verification_source_url="owner:project",
        verified_at=None,
        avg_rating=0,
        review_count=0,
        complaint_count=0,
    )
    resp: PlaceResponse = build_place_response(place)
    assert resp.verification_status == "OWNER_CONFIRMED"
    assert resp.verification_label == "Подтверждено владельцем"
    assert resp.phone == place.phone


def test_kdc_is_separate_map_point_in_inventory():
    kdc = _entry(KDC_KEY)
    assert kdc["category"] == "culture"
    assert kdc["active_status"] == "ACTIVE"
    assert kdc.get("seed_as_reference", True)
    assert "КДЦ" in (kdc.get("aliases") or [""])[0]


def test_kdc_description_includes_alias_for_search():
    kdc = _entry(KDC_KEY)
    desc = build_public_description(kdc)
    assert desc is not None
    assert "КДЦ" in desc


def test_stolovaya_is_separate_map_point_not_duplicate_of_turbaza():
    stolovaya = _entry(STOLOVAYA_KEY)
    turbaza = _entry(TURBAZA_KEY)
    assert stolovaya["category"] == "restaurant"
    assert turbaza["category"] == "hotel"
    assert stolovaya["yandex_id"] != turbaza["yandex_id"]
    assert stolovaya["stable_key"] != turbaza["stable_key"]
    assert "столовая" in stolovaya["public_name"].lower()


def test_module12_audit_exists():
    audit = REPO_ROOT / "docs" / "factual-integrity" / "module-12-production-point-verification.md"
    assert audit.is_file()
    text = audit.read_text(encoding="utf-8")
    assert TYRE_KEY in text
    assert KDC_KEY in text
    assert STOLOVAYA_KEY in text
    assert "5329246" in text


def test_school_count_still_two_module11():
    schools = [
        e
        for e in inventory_village_places()
        if e.get("scope") == "VILLAGE" and e.get("category") == "school"
    ]
    assert len(schools) == 2
    assert {s["stable_key"] for s in schools} == MODULE11_SCHOOL_KEYS


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_seed_kdc_searchable_by_kdc_alias(db_session: AsyncSession):
    await seed_village_places(db_session)
    result = await search_places(db_session, PlaceSearchParams(search="КДЦ", scope="VILLAGE"))
    assert result.total >= 1
    assert any(p.yandex_id == _ref_key(KDC_KEY) for p in result.items)


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_seed_stolovaya_searchable_by_stolovaya_and_turbaza(db_session: AsyncSession):
    await seed_village_places(db_session)
    by_stolovaya = await search_places(
        db_session, PlaceSearchParams(search="столовая", scope="VILLAGE")
    )
    by_turbaza = await search_places(
        db_session, PlaceSearchParams(search="Турбаза", scope="VILLAGE")
    )
    assert any(p.yandex_id == _ref_key(STOLOVAYA_KEY) for p in by_stolovaya.items)
    stolovaya_ids = {p.yandex_id for p in by_turbaza.items if p.yandex_id == _ref_key(STOLOVAYA_KEY)}
    turbaza_ids = {p.yandex_id for p in by_turbaza.items if p.yandex_id == _ref_key(TURBAZA_KEY)}
    assert stolovaya_ids == {_ref_key(STOLOVAYA_KEY)}
    assert turbaza_ids == {_ref_key(TURBAZA_KEY)}


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_seed_tyre_has_owner_phone_and_status(db_session: AsyncSession):
    await seed_village_places(db_session)
    result = await db_session.execute(
        select(Place).where(Place.yandex_id == _ref_key(TYRE_KEY))
    )
    place = result.scalars().one()
    assert place.phone == "+7 (906) 221-03-54"
    assert place.verification_status == "OWNER_CONFIRMED"


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_map_stats_category_sum_unchanged_after_module12_seed(db_session: AsyncSession):
    await seed_village_places(db_session)
    stats = await get_map_stats(db_session, scope="VILLAGE")
    assert stats.catalog_places == stats.total_places
    assert sum(stats.by_category.values()) == stats.catalog_places
    summary = json.loads(DOCS_INVENTORY.read_text(encoding="utf-8"))["summary"]
    assert summary["village_active"] == 45
