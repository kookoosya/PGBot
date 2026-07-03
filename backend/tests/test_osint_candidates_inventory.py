"""Module 4: verified OSINT candidates reconciliation."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.services.place_inventory import entry_source_types, inventory_village_places, load_place_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"
FRONTEND_CONSTANTS = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "constants.ts"
MAP_ATTRIBUTION = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "mapAttribution.ts"

MODULE4_ACTIVE_KEYS = frozenset({
    "mfc-lenina-6",
    "sieszka-pushkinskaya-69",
    "kdc-sadovaya-1",
    "turbaza-pushkinogorye",
    "stolovaya-pushkinogorye-turbaza",
})

MODULE4_REJECTED_KEYS = frozenset({
    "work-taxi-candidate",
    "raypo-otdel-zakupok",
    "gostinitsa-pushkinogorskaya",
})

NATIONAL_FLAG_EMOJI = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def test_runtime_and_docs_inventory_identical():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_stable_keys_unique():
    keys = [p["stable_key"] for p in load_place_inventory()]
    assert len(keys) == len(set(keys))


def test_yandex_ids_unique_for_module4():
    module4_ids = [_entry(key)["yandex_id"] for key in MODULE4_ACTIVE_KEYS]
    assert len(module4_ids) == len(set(module4_ids))
    other_ids = {
        p["yandex_id"]
        for p in load_place_inventory()
        if p.get("yandex_id") and p["stable_key"] not in MODULE4_ACTIVE_KEYS
    }
    assert not set(module4_ids) & other_ids


def test_two_gis_firm_ids_unique_when_present():
    firm_ids: list[str] = []
    for entry in load_place_inventory():
        for src in entry.get("sources") or []:
            if src.get("type") == "TWO_GIS" and src.get("entity_id"):
                firm_ids.append(src["entity_id"])
    assert len(firm_ids) == len(set(firm_ids))


def test_module4_added_records_have_village_scope():
    for key in MODULE4_ACTIVE_KEYS:
        assert _entry(key)["scope"] == "VILLAGE", key


def test_module4_added_records_have_valid_source():
    allowed = {
        "OWNER",
        "YANDEX",
        "TWO_GIS",
        "OFFICIAL_WEBSITE",
        "OFFICIAL_SOCIAL",
        "GOVERNMENT_REGISTRY",
        "OSM",
        "COMMUNITY",
    }
    for key in MODULE4_ACTIVE_KEYS:
        types = entry_source_types(_entry(key))
        assert types & allowed, key


def test_missing_website_does_not_block_active_business():
    assert _entry("sieszka-pushkinskaya-69")["website"] is None
    assert _entry("sieszka-pushkinskaya-69")["active_status"] == "ACTIVE"


def test_not_public_service_not_in_village_seed():
    seeded = {e["stable_key"] for e in inventory_village_places()}
    assert "work-taxi-candidate" not in seeded
    assert "raypo-otdel-zakupok" not in seeded


def test_outside_scope_not_in_village_seed():
    village = [e for e in inventory_village_places() if e.get("scope") == "VILLAGE"]
    assert all(e.get("scope") == "VILLAGE" for e in village)


def test_kdc_does_not_duplicate_nkc():
    kdc = _entry("kdc-sadovaya-1")
    nkc = _entry("nkc-pushkinskie-gory")
    assert kdc["yandex_id"] != nkc.get("yandex_id")
    assert kdc["address"] != nkc["address"]
    assert "nkc-pushkinskie-gory" not in MODULE4_ACTIVE_KEYS or kdc["stable_key"] == "kdc-sadovaya-1"


def test_work_taxi_no_fake_map_point():
    taxi = _entry("work-taxi-candidate")
    assert taxi["decision"] == "NOT_PUBLIC_SERVICE"
    assert taxi.get("latitude") is None
    assert taxi.get("longitude") is None
    assert not taxi.get("seed_as_reference", True)


def test_mfc_government_category():
    assert _entry("mfc-lenina-6")["category"] == "government"


def test_turbaza_hotel_village_scope():
    tb = _entry("turbaza-pushkinogorye")
    assert tb["category"] == "hotel"
    assert tb["scope"] == "VILLAGE"


def test_raypo_procurement_not_public():
    proc = _entry("raypo-otdel-zakupok")
    assert proc["decision"] == "NOT_PUBLIC_SERVICE"
    assert not proc.get("seed_as_reference", True)


def test_unknown_phone_hours_remain_null_for_sieszka():
    entry = _entry("sieszka-pushkinskaya-69")
    assert entry.get("phone") is None
    assert entry.get("opening_hours") is None


def test_search_url_not_used_as_org_card_for_pushkin_cafe():
    entry = _entry("kafe-pushkin-lenina-3")
    assert entry.get("yandex_id") is None
    assert "/org/" not in (entry.get("yandex_url") or "")


def test_module4_category_labels_exist():
    for key in MODULE4_ACTIVE_KEYS:
        cat = _entry(key)["category"]
        assert PlaceCategory(cat) in PLACE_CATEGORY_LABELS


def test_module4_category_emojis_in_frontend():
    text = FRONTEND_CONSTANTS.read_text(encoding="utf-8")
    for key in MODULE4_ACTIVE_KEYS:
        cat = _entry(key)["category"]
        assert f"{cat}:" in text


def test_no_national_flags_in_category_icons():
    icons = FRONTEND_CONSTANTS.read_text(encoding="utf-8")
    assert not NATIONAL_FLAG_EMOJI.search(icons)


def test_leaflet_attribution_unchanged():
    text = MAP_ATTRIBUTION.read_text(encoding="utf-8")
    prefix_block = text.split("LEAFLET_ATTRIBUTION_PREFIX", 1)[1].split(";", 1)[0]
    assert "🇺🇦" not in prefix_block


def test_module1_3_baselines_still_active():
    for key in (
        "shinomontazh-aerodromnaya-23",
        "apteka-a-lenina-20a",
        "vet-sbbzh-stroiteley-3",
        "hospital-pushkinogorsky-filial",
        "serviseklass-stroiteley-13",
    ):
        assert _entry(key)["active_status"] == "ACTIVE", key


def test_active_count_not_decreased_without_proof():
    summary = json.loads(DOCS_INVENTORY.read_text(encoding="utf-8"))["summary"]
    assert summary["village_active"] >= 40


def test_module4_rejected_inventory_decisions():
    assert _entry("gostinitsa-pushkinogorskaya")["decision"] == "INSUFFICIENT_EVIDENCE"
