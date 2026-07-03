"""Stage 2 regression: Yandex + 2GIS inventory, Pushkin quotes, afisha invariants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.services.ai_chat import CHAT_SYSTEM_PROMPT
from app.services.map_routes import get_map_routes
from app.services.place.responses import build_place_response
from app.services.place_inventory import (
    ALLOWED_SOURCE_TYPES,
    entry_source_types,
    load_place_inventory,
    primary_verification_url,
    verification_label,
)
from app.services.pushkin_places_seed import CLOSED_STABLE_KEYS, VILLAGE_PLACES, seed_village_places
from app.services.pushkin_quotes import load_verified_quotes

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"
SEARCH_LOG = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-search-log.md"
PORTAL_COPY = REPO_ROOT / "shared" / "portal_copy.json"
PUSHKIN_QUOTES = REPO_ROOT / "shared" / "pushkin_quotes.json"
AI_CHAT = REPO_ROOT / "backend" / "app" / "services" / "ai_chat.py"

COMMERCIAL_CATEGORIES = frozenset({
    "supermarket", "shop", "pharmacy", "cafe", "restaurant", "tyre", "auto", "gas",
    "beauty", "hotel",
})

FORBIDDEN_MISQUOTES = (
    "Ученье — свет, а неученье — тьма",
    "Труд — вот лучшая зарядка для юности",
    "Здесь любил я первый жизни глас",
    "Береги минуту — час сбережёшь",
    "Всё, что ни делается, — к лучшему",
    "Счастье то, что дух просветляет",
)

TRUSTED_SOURCE_TYPES = frozenset({"YANDEX", "TWO_GIS", "OWNER", "OFFICIAL_PRIMARY", "OFFICIAL_WEBSITE", "OSM"})


def _active_seed_entries():
    return [
        p for p in load_place_inventory()
        if p["decision"] in ("KEEP", "RESTORE")
        and p.get("active_status") != "CLOSED_CONFIRMED"
        and p.get("seed_as_reference", True)
    ]


def test_runtime_and_docs_inventory_identical():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_inventory_not_limited_to_three_places():
    village = [p for p in load_place_inventory() if p["scope"] == "VILLAGE" and p["decision"] in ("KEEP", "RESTORE")]
    assert len(village) > 3
    assert len(VILLAGE_PLACES) > 3


def test_active_curated_entries_have_trusted_source():
    for entry in _active_seed_entries():
        types = entry_source_types(entry)
        assert types & TRUSTED_SOURCE_TYPES, entry["stable_key"]


def test_sources_use_allowed_types_not_raw_urls():
    for entry in load_place_inventory():
        for src in entry.get("sources") or []:
            assert src["type"] in ALLOWED_SOURCE_TYPES, entry["stable_key"]
            assert "http" in src["url"] or src["type"] in ("OWNER", "OSM"), entry["stable_key"]
        assert "source_types" not in entry or not entry.get("source_types")


def test_commercial_categories_have_yandex_or_2gis_in_log():
    log = SEARCH_LOG.read_text(encoding="utf-8").lower()
    assert "yandex" in log and "2gis" in log
    for cat in ("supermarket", "pharmacy", "cafe", "tyre", "hotel", "gas"):
        assert cat in log


def test_search_log_documents_both_services():
    log = SEARCH_LOG.read_text(encoding="utf-8")
    assert "Pass 1" in log and "Pass 2" in log
    assert log.count("| Yandex |") >= 5
    assert log.count("| 2GIS |") >= 5


def test_tire_shop_owner_confirmed_active():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert entry["existence_status"] == "OWNER_CONFIRMED"
    assert entry["active_status"] == "ACTIVE"
    assert entry["address"] == "ул. Аэродромная, 23"
    assert entry["phone"] == "+7 (906) 221-03-54"


def test_tire_shop_has_owner_source():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert "OWNER" in entry_source_types(entry)


def test_tire_shop_has_yandex_source():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert "YANDEX" in entry_source_types(entry)


def test_tire_shop_has_two_gis_source():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert "TWO_GIS" in entry_source_types(entry)
    urls = json.dumps(entry["sources"])
    assert "70000001075370090" in urls


def test_tire_shop_auto2_absent():
    blob = json.dumps(load_place_inventory(), ensure_ascii=False).lower()
    assert "auto2" not in blob
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert entry.get("verification_note") is None
    assert "+7 (981) 783-86-67" not in blob


def test_tire_shop_phone_published():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert entry["phone"] == "+7 (906) 221-03-54"
    assert entry["phone_status"] == "OWNER_CONFIRMED"


def test_inventory_allows_missing_phone_and_website():
    for entry in load_place_inventory():
        if not entry.get("seed_as_reference", True):
            continue
        if entry.get("phone") is None or entry.get("website") is None:
            assert entry["decision"] in ("KEEP", "RESTORE"), entry["stable_key"]


def test_separate_chain_branches_not_merged():
    magnit = [p for p in load_place_inventory() if p["public_name"] == "Магнит" and p["scope"] == "VILLAGE"]
    assert len(magnit) >= 2
    assert len({p["address"] for p in magnit}) >= 2


def test_yandex_only_label():
    assert verification_label("YANDEX_ACTIVE") == "Данные Яндекс Карт — уточняйте перед визитом"
    place = Place(
        id=1, name="Пример", category=PlaceCategory.SHOP,
        latitude=57.0, longitude=28.9, external_source="reference",
        external_rating=0, external_review_count=0,
        verification_status="YANDEX_ACTIVE",
        verification_source_url="https://yandex.ru/maps/org/example/1/",
        verified_at=None, avg_rating=0, review_count=0, complaint_count=0,
    )
    resp = build_place_response(place)
    assert "официально" not in (resp.verification_label or "").lower()


def test_two_gis_only_label():
    assert verification_label("TWO_GIS_ACTIVE") == "Данные 2GIS — уточняйте перед визитом"


def test_multisource_label():
    assert verification_label("MULTISOURCE_CONFIRMED") == "Данные подтверждены Яндекс Картами и 2GIS"


def test_conflicting_not_deleted():
    conflicting = [p for p in load_place_inventory() if p.get("existence_status") == "CONFLICTING" or p.get("conflict_notes")]
    for entry in conflicting:
        if not entry.get("seed_as_reference", True):
            continue
        assert entry["decision"] in ("KEEP", "RESTORE"), entry["stable_key"]


def test_closed_confirmed_requires_explicit_list():
    closed = [p for p in load_place_inventory() if p.get("active_status") == "CLOSED_CONFIRMED"]
    for entry in closed:
        assert entry["stable_key"] in CLOSED_STABLE_KEYS


def test_verified_pushkin_quotes_have_academic_metadata():
    for quote in load_verified_quotes():
        assert quote["work"]
        assert quote["year"]
        assert quote["source_url"].startswith("https://rvb.ru/")


@pytest.mark.parametrize("forbidden", FORBIDDEN_MISQUOTES)
def test_forbidden_misquotes_absent_from_repo(forbidden: str):
    for path in (PORTAL_COPY, PUSHKIN_QUOTES, AI_CHAT):
        assert forbidden not in path.read_text(encoding="utf-8"), path.name


def test_hero_quote_verified_derevnya():
    hero = json.loads(PORTAL_COPY.read_text(encoding="utf-8"))["landing_hero"]
    assert hero["quote"] == "Приют спокойствия, трудов и вдохновенья"
    assert hero["quote_work"] == "Деревня"
    assert hero["quote_year"] == 1819
    assert "rvb.ru" in hero["quote_source_url"]


def test_ai_chat_has_no_random_pushkin_quotes_array():
    assert "PUSHKIN_QUOTES" not in AI_CHAT.read_text(encoding="utf-8")


def test_ai_prompt_forbids_invented_quotes():
    assert "Не выдумывай цитаты Пушкина" in CHAT_SYSTEM_PROMPT


def test_map_routes_include_restored_stops():
    names = {stop["name"] for route in get_map_routes() for stop in route["stops"]}
    assert "Шиномонтаж" in names
    assert "Автовокзал Пушкинские Горы" in names
    assert "Пятёрочка" in names


def test_primary_verification_url_prefers_owner():
    entry = next(p for p in load_place_inventory() if p["stable_key"] == "shinomontazh-aerodromnaya-23")
    assert primary_verification_url(entry) == "owner:project"


def test_public_api_includes_verification_fields():
    place = Place(
        id=2, name="Шиномонтаж", category=PlaceCategory.TYRE,
        latitude=57.0173, longitude=28.9335, external_source="reference",
        external_rating=0, external_review_count=0,
        verification_status="OWNER_CONFIRMED",
        verification_source_url="https://2gis.ru/firm/70000001075370090",
        verified_at=None, avg_rating=0, review_count=0, complaint_count=0,
    )
    resp = build_place_response(place)
    assert resp.verification_status == "OWNER_CONFIRMED"
    assert resp.verification_source_url


def test_events_hide_past_external_events_function():
    from app.services.event_dedupe_service import unpublish_past_external_events

    assert callable(unpublish_past_external_events)


def test_event_models_expect_source_url_field():
    from app.models.event import Event

    assert "source_url" in Event.__table__.columns
    assert "source" in Event.__table__.columns


def test_events_audit_doc_exists():
    path = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-events-source-audit.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "pushkinland" in text
    assert "read-only" in text.lower() or "No parser" in text


@pytest.mark.postgres
async def test_seed_keeps_org_without_phone(db_session):
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
