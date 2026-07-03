"""Module 11: village school count reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

from app.services.place_inventory import inventory_village_places, load_place_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_INVENTORY = REPO_ROOT / "docs" / "factual-integrity" / "stage-02-place-inventory.json"
RUNTIME_INVENTORY = REPO_ROOT / "backend" / "app" / "data" / "stage-02-place-inventory.json"

MAIN_SCHOOL_KEY = "school-1-lenina-30"
ART_SCHOOL_KEY = "art-school-geychenko-pushkinskaya-3"
MODULE11_SCHOOL_KEYS = frozenset({MAIN_SCHOOL_KEY, ART_SCHOOL_KEY})


def _entry(stable_key: str) -> dict:
    return next(p for p in load_place_inventory() if p["stable_key"] == stable_key)


def _village_active_schools() -> list[dict]:
    return [
        entry
        for entry in inventory_village_places()
        if entry.get("scope") == "VILLAGE" and entry.get("category") == "school"
    ]


def test_runtime_and_docs_inventory_identical():
    assert RUNTIME_INVENTORY.read_text(encoding="utf-8") == DOCS_INVENTORY.read_text(encoding="utf-8")


def test_school_stable_keys_unique():
    keys = [s["stable_key"] for s in _village_active_schools()]
    assert len(keys) == len(set(keys))


def test_school_yandex_ids_unique():
    ids = [s["yandex_id"] for s in _village_active_schools()]
    assert len(ids) == len(set(ids))
    assert None not in ids


def test_main_school_address_lermontova_13():
    school = _entry(MAIN_SCHOOL_KEY)
    assert school["address"] == "ул. Лермонтова, 13"
    assert school["yandex_id"] == "1040866154"


def test_lenina_30_address_not_used_as_public_school():
    schools = _village_active_schools()
    assert not any("Ленина, 30" in (s.get("address") or "") for s in schools)
    main = _entry(MAIN_SCHOOL_KEY)
    assert "Ленина, 30" in (main.get("conflict_notes") or "")


def test_two_active_schools_are_distinct_institutions():
    schools = {s["stable_key"]: s for s in _village_active_schools()}
    assert set(schools) == MODULE11_SCHOOL_KEYS
    main, art = schools[MAIN_SCHOOL_KEY], schools[ART_SCHOOL_KEY]
    assert main["address"] != art["address"]
    assert main["latitude"] != art["latitude"] or main["longitude"] != art["longitude"]
    assert main["yandex_id"] != art["yandex_id"]
    assert "искусств" in art["public_name"].lower()
    assert "общеобразовательная" in main["public_name"].lower()


def test_art_school_has_official_municipality_source():
    art = _entry(ART_SCHOOL_KEY)
    types = {src.get("type") for src in art.get("sources") or []}
    assert "YANDEX" in types
    assert "OFFICIAL_WEBSITE" in types
    assert art["existence_status"] == "MULTISOURCE_CONFIRMED"


def test_sanatorium_not_in_public_seed():
    keys = {e["stable_key"] for e in inventory_village_places()}
    assert "sanatorium" not in " ".join(keys).lower()
    for entry in load_place_inventory():
        name = (entry.get("public_name") or "").lower()
        if "санатор" in name and "школ" in name:
            assert not entry.get("seed_as_reference", True)


def test_village_school_count_is_two():
    assert len(_village_active_schools()) == 2


def test_other_categories_unchanged_module11():
    summary = json.loads(DOCS_INVENTORY.read_text(encoding="utf-8"))["summary"]
    assert summary["village_active"] == 45
    hospitals = [e for e in inventory_village_places() if e.get("category") == "hospital"]
    assert len(hospitals) == 1
    assert hospitals[0]["stable_key"] == "hospital-pushkinogorsky-filial"


def test_module11_audit_exists():
    audit = REPO_ROOT / "docs" / "factual-integrity" / "module-11-school-count-reconciliation.md"
    assert audit.is_file()
    text = audit.read_text(encoding="utf-8")
    assert "KEEP_BOTH_VERIFIED" in text
    assert ART_SCHOOL_KEY in text
    assert MAIN_SCHOOL_KEY in text
