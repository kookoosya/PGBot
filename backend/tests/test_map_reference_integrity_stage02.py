"""Stage 2 regression: restored village directory and Pushkin quotes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.services.ai_chat import CHAT_SYSTEM_PROMPT
from app.services.map_routes import get_map_routes
from app.services.place.responses import build_place_response
from app.services.place_inventory import load_place_inventory
from app.services.pushkin_places_seed import VILLAGE_PLACES, seed_village_places
from app.services.pushkin_quotes import load_verified_quotes

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_JSON = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"
PORTAL_COPY = REPO_ROOT / "shared" / "portal_copy.json"
PUSHKIN_QUOTES = REPO_ROOT / "shared" / "pushkin_quotes.json"
AI_CHAT = REPO_ROOT / "backend" / "app" / "services" / "ai_chat.py"

FORBIDDEN_MISQUOTES = (
    "Ученье — свет, а неученье — тьма",
    "Труд — вот лучшая зарядка для юности",
    "Здесь любил я первый жизни глас",
)

PLACEHOLDER_PHONES = (
    "+7 (81146) 2-01-01",
    "+7 (81146) 2-02-02",
    "+7 (81146) 2-05-05",
    "+7 (921) 000-28-28",
)


def test_inventory_not_limited_to_three_places():
    inventory = load_place_inventory()
    village = [p for p in inventory if p["scope"] == "VILLAGE" and p["decision"] in ("KEEP", "RESTORE")]
    assert len(village) > 3
    assert len(VILLAGE_PLACES) > 3


def test_tire_shop_owner_confirmed_in_inventory():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert entry["existence_status"] == "OWNER_CONFIRMED"
    assert entry["address"] == "ул. Аэродромная, 23"
    assert entry["phone"] == "+7 (906) 221-03-54"


def test_active_curated_entries_have_source():
    for entry in load_place_inventory():
        if entry["decision"] not in ("KEEP", "RESTORE"):
            continue
        if not entry.get("seed_as_reference", True):
            continue
        assert entry.get("source_types"), entry["stable_key"]


def test_inventory_allows_missing_phone_and_website():
    for entry in load_place_inventory():
        if entry.get("phone") is None:
            assert entry["decision"] in ("KEEP", "RESTORE"), entry["stable_key"]
        if entry.get("website") is None:
            assert entry["decision"] in ("KEEP", "RESTORE"), entry["stable_key"]


def test_yandex_only_not_labeled_officially_verified():
    place = Place(
        id=1,
        name="Пример",
        category=PlaceCategory.SHOP,
        latitude=57.0,
        longitude=28.9,
        external_source="reference",
        external_rating=0,
        external_review_count=0,
        verification_status="YANDEX_ACTIVE",
        verification_source_url="https://yandex.ru/maps/org/example/1/",
        verified_at=None,
        avg_rating=0,
        review_count=0,
        complaint_count=0,
    )
    resp = build_place_response(place)
    assert resp.verification_label == "Данные Яндекс Карт"
    assert "официально подтверждено" not in (resp.verification_label or "").lower()


def test_closed_confirmed_requires_explicit_list():
    from app.services.pushkin_places_seed import CLOSED_STABLE_KEYS

    closed = [p for p in load_place_inventory() if p.get("active_status") == "CLOSED_CONFIRMED"]
    for entry in closed:
        assert entry["stable_key"] in CLOSED_STABLE_KEYS


def test_separate_chain_branches_not_merged():
    magnit = [p for p in load_place_inventory() if p["public_name"] == "Магнит" and p["scope"] == "VILLAGE"]
    assert len(magnit) >= 2
    addresses = {p["address"] for p in magnit}
    assert len(addresses) >= 2


def test_no_placeholder_phones_in_inventory_seed():
    blob = json.dumps(load_place_inventory(), ensure_ascii=False)
    for phone in PLACEHOLDER_PHONES:
        assert phone not in blob


def test_public_api_includes_verification_fields():
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
        verification_source_url="https://2gis.ru/firm/70000001075370090",
        verified_at=None,
        avg_rating=0,
        review_count=0,
        complaint_count=0,
    )
    resp = build_place_response(place)
    assert resp.verification_status == "OWNER_CONFIRMED"
    assert resp.verification_source_url


def test_verified_pushkin_quotes_have_academic_metadata():
    for quote in load_verified_quotes():
        assert quote["work"]
        assert quote["year"]
        assert quote["source_url"].startswith("https://rvb.ru/")


@pytest.mark.parametrize("forbidden", FORBIDDEN_MISQUOTES)
def test_forbidden_misquotes_absent_from_repo(forbidden: str):
    targets = [PORTAL_COPY, PUSHKIN_QUOTES, AI_CHAT]
    for path in targets:
        assert forbidden not in path.read_text(encoding="utf-8"), path.name


def test_hero_quote_verified_derevnya():
    hero = json.loads(PORTAL_COPY.read_text(encoding="utf-8"))["landing_hero"]
    assert hero["quote"] == "Приют спокойствия, трудов и вдохновенья"
    assert hero["quote_work"] == "Деревня"
    assert hero["quote_year"] == 1819
    assert "rvb.ru" in hero["quote_source_url"]


def test_ai_chat_has_no_random_pushkin_quotes_array():
    text = AI_CHAT.read_text(encoding="utf-8")
    assert "PUSHKIN_QUOTES" not in text


def test_ai_prompt_forbids_invented_quotes():
    assert "Не выдумывай цитаты Пушкина" in CHAT_SYSTEM_PROMPT


def test_map_routes_include_restored_stops():
    names = {stop["name"] for route in get_map_routes() for stop in route["stops"]}
    assert "Шиномонтаж" in names
    assert "Автовокзал Пушкинские Горы" in names
    assert "Пятёрочка" in names


@pytest.mark.postgres
async def test_seed_keeps_org_without_phone(db_session):
    from app.services.pushkin_places_seed import seed_village_places

    place = Place(
        name="Автовокзал Пушкинские Горы",
        category=PlaceCategory.TRANSPORT,
        latitude=57.0212461,
        longitude=28.9350885,
        address="ул. Новоржевская, 30",
        phone=None,
        yandex_id="ref_avtovokzal-novorzhevskaya-30",
        external_source="reference",
        is_active=False,
    )
    db_session.add(place)
    await db_session.flush()
    await seed_village_places(db_session)
    await db_session.refresh(place)
    assert place.is_active is True
