"""Module 15: verified contact visibility — inventory, seed, API contract."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.services.map_routes import TYRE_ROUTE_NAME, get_map_routes, route_stop_names
from app.services.place import PlaceSearchParams, search_places
from app.services.place.responses import build_place_response
from app.services.place_inventory import load_place_inventory
from app.services.pushkin_places_seed import _place_key, _public_phone, seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"

TYRE_KEY = "shinomontazh-aerodromnaya-23"
KDC_KEY = "kdc-sadovaya-1"
STOLOVAYA_KEY = "stolovaya-pushkinogorye-turbaza"
EXPECTED_VILLAGE_COUNT = 45
EXPECTED_VERIFIED_PHONE_COUNT = 20
HIDDEN_TOLL_FREE_KEYS = frozenset(
    {
        "pyaterochka-lenina-20a",
        "pyaterochka-pushkinskaya-11",
        "magnit-lenina-42",
        "magnit-novorzhevskaya-25",
    }
)
PRIORITY_CONTACT_KEYS = frozenset(
    {
        "apteka-a-novorzhevskaya-25",
        "farm-m-lenina-42",
        "hospital-pushkinogorsky-filial",
        "vet-sbbzh-stroiteley-3",
        "mfc-lenina-6",
        KDC_KEY,
        "school-1-lenina-30",
        "art-school-geychenko-pushkinskaya-3",
        TYRE_KEY,
        "serviseklass-stroiteley-13",
        "avtomoyka-pushkinskaya-42b",
        "car-wash-zvyozdnaya",
        "avtozapchasti-lermontova-10",
        "kafe-pushkin-lenina-3",
        "pushkin-park-lenina-42a",
        "druzhba-hotel-lenina-8",
        "turbaza-pushkinogorye",
        "azs-pskovnefteprodukt-novorzhevskaya-31",
        "avtovokzal-novorzhevskaya-30",
    }
)


def _village_places() -> list[dict]:
    return [
        p
        for p in load_place_inventory()
        if p.get("decision") in {"KEEP", "RESTORE"}
        and p.get("active_status") != "CLOSED_CONFIRMED"
        and p.get("seed_as_reference", True)
        and p.get("scope") == "VILLAGE"
    ]


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def _verified_seed_entries() -> list[dict]:
    return [p for p in _village_places() if _public_phone(p)]


def test_module15_inventory_runtime_matches_docs():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_module15_village_place_count_unchanged():
    assert len(_village_places()) == EXPECTED_VILLAGE_COUNT


def test_module15_verified_phone_count_stable():
    verified = _verified_seed_entries()
    assert len(verified) == EXPECTED_VERIFIED_PHONE_COUNT


def test_module15_hidden_toll_free_phones_not_seeded():
    for key in HIDDEN_TOLL_FREE_KEYS:
        entry = _entry(key)
        assert entry.get("phone"), key
        assert entry.get("phone_status") == "UNVERIFIED", key
        assert _public_phone(entry) is None, key


def test_module15_unverified_priority_places_have_no_public_phone():
    for key in (
        "apteka-a-lenina-20a",
        "vet-sbbzh-stroiteley-3",
        "art-school-geychenko-pushkinskaya-3",
        "kafe-pushkin-lenina-3",
        "druzhba-hotel-lenina-8",
        "avtovokzal-novorzhevskaya-30",
    ):
        assert _public_phone(_entry(key)) is None, key


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module15_all_verified_phones_seed_into_db(db_session: AsyncSession):
    await seed_village_places(db_session)
    for entry in _verified_seed_entries():
        key = _place_key(entry["stable_key"])
        place = (
            await db_session.execute(select(Place).where(Place.yandex_id == key))
        ).scalar_one()
        assert place.phone == _public_phone(entry), entry["stable_key"]


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module15_list_and_detail_share_phone_contract(
    db_session: AsyncSession, api_client: AsyncClient
):
    await seed_village_places(db_session)
    tyre = (
        await db_session.execute(select(Place).where(Place.yandex_id == _place_key(TYRE_KEY)))
    ).scalar_one()
    list_resp = await api_client.get("/api/v1/places", params={"search": "Шиномонтаж", "scope": "VILLAGE"})
    detail_resp = await api_client.get(f"/api/v1/places/{tyre.id}")
    assert list_resp.status_code == 200
    assert detail_resp.status_code == 200
    list_phone = list_resp.json()["items"][0]["phone"]
    detail_phone = detail_resp.json()["phone"]
    assert list_phone == detail_phone == "+7 (906) 221-03-54"


def test_module15_public_serializer_keeps_verified_phone():
    entry = _entry(TYRE_KEY)
    place = Place(
        id=326,
        name=entry["public_name"],
        category=PlaceCategory.TYRE,
        latitude=entry["latitude"],
        longitude=entry["longitude"],
        phone=_public_phone(entry),
        external_source="reference",
        external_rating=0,
        external_review_count=0,
        verification_status=entry["existence_status"],
        verification_source_url="owner:project",
        avg_rating=0,
        review_count=0,
        complaint_count=0,
    )
    resp = build_place_response(place)
    assert resp.phone == "+7 (906) 221-03-54"
    assert resp.verification_status == "OWNER_CONFIRMED"


def test_module15_public_serializer_hides_unverified_phone():
    entry = _entry("magnit-lenina-42")
    place = Place(
        id=1,
        name=entry["public_name"],
        category=PlaceCategory.SUPERMARKET,
        latitude=entry["latitude"],
        longitude=entry["longitude"],
        phone=_public_phone(entry),
        external_source="reference",
        external_rating=0,
        external_review_count=0,
        avg_rating=0,
        review_count=0,
        complaint_count=0,
    )
    assert place.phone is None


@pytest.mark.parametrize(
    "stable_key,expected_phone",
    [
        ("apteka-a-novorzhevskaya-25", "+7 (8112) 60-77-11"),
        ("farm-m-lenina-42", "+7 (960) 222-67-76"),
        ("hospital-pushkinogorsky-filial", "+7 (81146) 2-27-06"),
        ("mfc-lenina-6", "+7 (8112) 29-92-98"),
        (KDC_KEY, "+7 (81146) 2-33-03"),
        (TYRE_KEY, "+7 (906) 221-03-54"),
    ],
)
def test_module15_priority_verified_phones_in_inventory(stable_key: str, expected_phone: str):
    entry = _entry(stable_key)
    assert _public_phone(entry) == expected_phone


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module15_pharmacy_verified_phones_seed(db_session: AsyncSession):
    await seed_village_places(db_session)
    for key in ("apteka-a-novorzhevskaya-25", "farm-m-lenina-42"):
        entry = _entry(key)
        place = (
            await db_session.execute(select(Place).where(Place.yandex_id == _place_key(key)))
        ).scalar_one()
        assert place.phone == _public_phone(entry)


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module15_kdc_and_stolovaya_searchable(db_session: AsyncSession):
    await seed_village_places(db_session)
    kdc = await search_places(db_session, PlaceSearchParams(search="КДЦ", scope="VILLAGE"))
    stolovaya = await search_places(
        db_session, PlaceSearchParams(search="столовая", scope="VILLAGE")
    )
    assert kdc.total >= 1
    assert stolovaya.total >= 1


def test_module15_routes_unchanged_from_module14():
    assert len(get_map_routes()) == 11
    assert TYRE_ROUTE_NAME not in route_stop_names()


def test_module15_priority_keys_present_in_inventory():
    village_keys = {p["stable_key"] for p in _village_places()}
    assert PRIORITY_CONTACT_KEYS <= village_keys


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module15_school_count_two(db_session: AsyncSession):
    await seed_village_places(db_session)
    schools = (
        await db_session.execute(
            select(Place).where(Place.category == PlaceCategory.SCHOOL, Place.scope == "VILLAGE")
        )
    ).scalars().all()
    assert len(schools) == 2
