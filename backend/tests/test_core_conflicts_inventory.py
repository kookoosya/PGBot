"""Module 5: AZS, school, and hospital conflict resolution."""

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

MODULE5_KEYS = frozenset({
    "azs-pskovnefteprodukt-novorzhevskaya-31",
    "school-1-lenina-30",
    "hospital-pushkinogorsky-filial",
})

DISTRICT_FAP_KEYS = frozenset({"fap-blazhi", "fap-krylovo"})
NATIONAL_FLAG_EMOJI = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def _village_active(category: str) -> list[dict]:
    return [
        entry
        for entry in load_place_inventory()
        if entry.get("scope") == "VILLAGE"
        and entry.get("category") == category
        and entry.get("decision") in ("KEEP", "RESTORE")
        and entry.get("active_status") != "CLOSED_CONFIRMED"
        and entry.get("seed_as_reference", True)
    ]


def test_runtime_and_docs_inventory_identical():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_stable_keys_unique():
    keys = [p["stable_key"] for p in load_place_inventory()]
    assert len(keys) == len(set(keys))


def test_yandex_ids_unique_for_module5():
    module5_ids = [_entry(key)["yandex_id"] for key in MODULE5_KEYS]
    assert len(module5_ids) == len(set(module5_ids))
    other_ids = {
        p["yandex_id"]
        for p in load_place_inventory()
        if p.get("yandex_id") and p["stable_key"] not in MODULE5_KEYS
    }
    assert not set(module5_ids) & other_ids


def test_two_gis_firm_ids_unique_when_present():
    firm_ids: list[str] = []
    for entry in load_place_inventory():
        for src in entry.get("sources") or []:
            if src.get("type") == "TWO_GIS" and src.get("entity_id"):
                firm_ids.append(src["entity_id"])
    assert len(firm_ids) == len(set(firm_ids))


def test_exactly_one_village_active_hospital():
    hospitals = _village_active("hospital")
    assert len(hospitals) == 1
    assert hospitals[0]["stable_key"] == "hospital-pushkinogorsky-filial"


def test_district_faps_not_in_village_hospital_count():
    hospitals = _village_active("hospital")
    hospital_keys = {h["stable_key"] for h in hospitals}
    assert not hospital_keys & DISTRICT_FAP_KEYS
    for key in DISTRICT_FAP_KEYS:
        fap = _entry(key)
        assert fap["scope"] != "VILLAGE"
        assert not fap.get("seed_as_reference", True)


def test_hospital_stays_active_despite_liquidated_legal_entity():
    hospital = _entry("hospital-pushkinogorsky-filial")
    assert hospital["active_status"] == "ACTIVE"
    assert hospital["decision"] in ("KEEP", "RESTORE")
    assert "ликвидац" in (hospital.get("conflict_notes") or "").lower()
    aliases = hospital.get("aliases") or []
    assert any("Пушкиногорский" in alias and "Островская" in alias for alias in aliases)


def test_hospital_has_verified_public_name():
    hospital = _entry("hospital-pushkinogorsky-filial")
    assert hospital["public_name"] == "Пушкиногорская межрайонная больница"
    assert hospital["name_status"] == "MULTISOURCE_CONFIRMED"
    assert hospital["yandex_id"] == "10683522075"
    assert "/org/" in hospital["yandex_url"]


def test_school_has_one_verified_physical_address():
    school = _entry("school-1-lenina-30")
    assert school["address"] == "ул. Лермонтова, 13"
    assert school["address_status"] == "YANDEX_ACTIVE"
    assert school["yandex_id"] == "1040866154"


def test_school_old_address_does_not_create_duplicate():
    schools = _village_active("school")
    lenina_schools = [s for s in schools if "Ленина" in (s.get("address") or "")]
    assert len(lenina_schools) == 0
    school = _entry("school-1-lenina-30")
    assert "Ленина, 30" in (school.get("conflict_notes") or "")


def test_no_unverified_second_school_campus_from_lenina_conflict():
    lenina_30_schools = [
        s
        for s in _village_active("school")
        if s["stable_key"] != "school-1-lenina-30" and "Ленина, 30" in (s.get("address") or "")
    ]
    assert lenina_30_schools == []


def test_gas_station_not_duplicated_as_number_1_and_31():
    gas = _village_active("gas")
    assert len(gas) == 1
    azs = _entry("azs-pskovnefteprodukt-novorzhevskaya-31")
    assert azs["stable_key"] == gas[0]["stable_key"]
    assert "№1" in (azs.get("conflict_notes") or "")
    assert ", 31" in (azs.get("address") or "")


def test_gas_station_number_not_invented_in_public_name():
    azs = _entry("azs-pskovnefteprodukt-novorzhevskaya-31")
    assert azs["public_name"] == "Сургутнефтегаз"
    assert "№" not in azs["public_name"]
    assert "Cannot be verified" in (azs.get("verification_note") or "")


def test_module5_records_have_village_scope():
    for key in MODULE5_KEYS:
        assert _entry(key)["scope"] == "VILLAGE", key


def test_module5_uses_org_cards_not_search_urls():
    for key in MODULE5_KEYS:
        entry = _entry(key)
        assert entry.get("yandex_id")
        assert "/org/" in (entry.get("yandex_url") or "")
        assert "/search/" not in (entry.get("yandex_url") or "")


def test_unverified_phone_hours_remain_null_where_applicable():
    school = _entry("school-1-lenina-30")
    assert school.get("opening_hours") is None
    assert school["hours_status"] == "UNVERIFIED"
    hospital = _entry("hospital-pushkinogorsky-filial")
    assert hospital.get("opening_hours") is None
    assert hospital["hours_status"] == "UNVERIFIED"


def test_module1_scope_statistics_not_regressed():
    summary = json.loads(DOCS_INVENTORY.read_text(encoding="utf-8"))["summary"]
    assert summary["village_active"] >= 40
    seeded = {e["stable_key"] for e in inventory_village_places()}
    assert "fap-blazhi" not in seeded
    assert "fap-krylovo" not in seeded


def test_module2_pharmacies_and_vet_not_regressed():
    pharmacies = _village_active("pharmacy")
    assert {p["stable_key"] for p in pharmacies} == {
        "apteka-a-lenina-20a",
        "apteka-a-novorzhevskaya-25",
        "farm-m-lenina-42",
    }
    vets = _village_active("vet")
    assert len(vets) == 1
    assert vets[0]["stable_key"] == "vet-sbbzh-stroiteley-3"


def test_module3_auto_services_not_regressed():
    for key in (
        "shinomontazh-aerodromnaya-23",
        "azs-pskovnefteprodukt-novorzhevskaya-31",
        "serviseklass-stroiteley-13",
    ):
        assert _entry(key)["active_status"] == "ACTIVE", key


def test_module4_objects_not_regressed():
    for key in (
        "mfc-lenina-6",
        "sieszka-pushkinskaya-69",
        "kdc-sadovaya-1",
        "turbaza-pushkinogorye",
        "stolovaya-pushkinogorye-turbaza",
    ):
        entry = _entry(key)
        assert entry["active_status"] == "ACTIVE", key
        assert entry["scope"] == "VILLAGE", key


def test_category_emojis_preserved():
    text = FRONTEND_CONSTANTS.read_text(encoding="utf-8")
    for cat in ("gas", "school", "hospital"):
        assert f"{cat}:" in text
        assert PlaceCategory(cat) in PLACE_CATEGORY_LABELS


def test_leaflet_attribution_no_ukrainian_flag():
    text = MAP_ATTRIBUTION.read_text(encoding="utf-8")
    prefix_block = text.split("LEAFLET_ATTRIBUTION_PREFIX", 1)[1].split(";", 1)[0]
    assert "🇺🇦" not in prefix_block
