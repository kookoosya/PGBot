"""Module 3: verified village auto services inventory."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.services.place_inventory import entry_source_types, load_place_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"
FRONTEND_CONSTANTS = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "constants.ts"
MAP_ATTRIBUTION = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "mapAttribution.ts"

AUTO_CATEGORIES = frozenset({"auto", "tyre", "car_wash", "auto_parts", "towing"})

NEW_AUTO_KEYS = frozenset({
    "serviseklass-stroiteley-13",
    "avtoservis-pushkinskaya-42b",
    "avtoservis-aerodromnaya-4b",
    "fixcar-lenina-29",
    "avtoservis-novorzhevskaya-47",
    "avtomoyka-pushkinskaya-42b",
    "car-wash-zvyozdnaya",
    "avtozapchasti-lermontova-10",
    "zapchasti-lermontova-14a",
    "avtozapchasti-pushkinskaya-42a",
})

NATIONAL_FLAG_EMOJI = re.compile(
    r"[\U0001F1E6-\U0001F1FF]{2}"
)


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def _village_auto_active() -> list[dict]:
    return [
        e
        for e in load_place_inventory()
        if e.get("scope") == "VILLAGE"
        and e.get("category") in AUTO_CATEGORIES
        and e.get("decision") in ("KEEP", "RESTORE")
        and e.get("active_status") != "CLOSED_CONFIRMED"
        and e.get("seed_as_reference", True)
    ]


def test_shinomontazh_stays_active():
    assert _entry("shinomontazh-aerodromnaya-23")["active_status"] == "ACTIVE"


def test_shinomontazh_owner_confirmed():
    assert _entry("shinomontazh-aerodromnaya-23")["existence_status"] == "OWNER_CONFIRMED"


def test_shinomontazh_phone_unchanged():
    assert _entry("shinomontazh-aerodromnaya-23")["phone"] == "+7 (906) 221-03-54"


def test_auto2_absent_from_inventory():
    blob = json.dumps(load_place_inventory(), ensure_ascii=False).lower()
    assert "auto2" not in blob


def test_new_auto_objects_have_yandex_source():
    for key in NEW_AUTO_KEYS:
        assert "YANDEX" in entry_source_types(_entry(key)), key


def test_missing_website_does_not_block_active():
    for key in NEW_AUTO_KEYS:
        entry = _entry(key)
        assert entry.get("website") is None
        assert entry["active_status"] == "ACTIVE"


def test_missing_phone_does_not_block_active():
    for key in ("avtoservis-novorzhevskaya-47", "avtomoyka-pushkinskaya-42b", "car-wash-zvyozdnaya"):
        entry = _entry(key)
        assert entry.get("phone") is None
        assert entry["active_status"] == "ACTIVE"


def test_missing_hours_does_not_block_active():
    for key in NEW_AUTO_KEYS:
        entry = _entry(key)
        if entry.get("opening_hours") is None:
            assert entry["active_status"] == "ACTIVE"


def test_yandex_only_auto_object_allowed():
    entry = _entry("avtoservis-novorzhevskaya-47")
    assert entry["existence_status"] == "YANDEX_ACTIVE"
    assert "TWO_GIS" not in entry_source_types(entry)


def test_two_gis_only_still_allowed_for_tyre():
    entry = _entry("shinomontazh-aerodromnaya-23")
    assert "TWO_GIS" in entry_source_types(entry)
    assert entry["existence_status"] == "OWNER_CONFIRMED"


def test_stable_keys_unique():
    keys = [p["stable_key"] for p in load_place_inventory()]
    assert len(keys) == len(set(keys))


def test_yandex_ids_unique_for_module3_auto():
    ids = [
        _entry(key)["yandex_id"]
        for key in NEW_AUTO_KEYS | {"shinomontazh-aerodromnaya-23"}
        if _entry(key).get("yandex_id")
    ]
    assert len(ids) == len(set(ids))


def test_two_gis_firm_ids_unique_when_present():
    firm_ids: list[str] = []
    for entry in load_place_inventory():
        for src in entry.get("sources") or []:
            if src.get("type") == "TWO_GIS" and src.get("entity_id"):
                firm_ids.append(src["entity_id"])
    assert len(firm_ids) == len(set(firm_ids))


def test_runtime_and_docs_inventory_identical():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_placeholder_osm_id_not_used_as_proof():
    avto = _entry("avtoremont-lenina")
    assert not any(s.get("entity_id") == "42" for s in avto.get("sources") or [])


def test_car_wash_category_for_pushkinskaya():
    assert _entry("avtomoyka-pushkinskaya-42b")["category"] == "car_wash"


def test_auto_parts_category():
    assert _entry("avtozapchasti-lermontova-10")["category"] == "auto_parts"
    assert _entry("zapchasti-lermontova-14a")["category"] == "auto_parts"


def test_towing_category_enum_exists():
    assert PlaceCategory.TOWING.value == "towing"
    assert PLACE_CATEGORY_LABELS[PlaceCategory.TOWING] == "Эвакуатор"


def test_new_backend_category_labels():
    assert PLACE_CATEGORY_LABELS[PlaceCategory.CAR_WASH] == "Автомойка"
    assert PLACE_CATEGORY_LABELS[PlaceCategory.AUTO_PARTS] == "Автозапчасти"


def test_module3_does_not_remove_existing_active_without_proof():
    before_keys = {
        "shinomontazh-aerodromnaya-23",
        "azs-pskovnefteprodukt-novorzhevskaya-31",
        "apteka-a-lenina-20a",
        "vet-sbbzh-stroiteley-3",
    }
    for key in before_keys:
        entry = _entry(key)
        assert entry["active_status"] == "ACTIVE", key


def test_avtoremont_insufficient_evidence():
    avto = _entry("avtoremont-lenina")
    assert avto["existence_status"] == "INSUFFICIENT_EVIDENCE"
    assert avto.get("phone") is None
    assert avto.get("opening_hours") is None


def test_ten_new_village_auto_services_added():
    active_keys = {e["stable_key"] for e in _village_auto_active()}
    assert NEW_AUTO_KEYS <= active_keys


def test_category_emoji_no_national_flags():
    text = FRONTEND_CONSTANTS.read_text(encoding="utf-8")
    assert not NATIONAL_FLAG_EMOJI.search(text)


def test_category_emoji_for_module3_categories():
    text = FRONTEND_CONSTANTS.read_text(encoding="utf-8")
    assert 'car_wash: "🧽"' in text
    assert 'auto_parts: "⚙️"' in text
    assert 'towing: "🚚"' in text


def test_leaflet_attribution_has_no_ukrainian_flag():
    text = MAP_ATTRIBUTION.read_text(encoding="utf-8")
    prefix_block = text.split("LEAFLET_ATTRIBUTION_PREFIX", 1)[1].split(";", 1)[0]
    assert "🇺🇦" not in prefix_block
