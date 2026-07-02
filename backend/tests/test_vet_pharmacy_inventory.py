"""Stage 2 increment: vet category and three village pharmacies."""

from app.models.enums import PlaceCategory
from app.services.place_inventory import load_place_inventory


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


def test_vet_category_enum_and_label():
    assert PlaceCategory.VET.value == "vet"
    from app.models.enums import PLACE_CATEGORY_LABELS

    assert PLACE_CATEGORY_LABELS[PlaceCategory.VET] == "Ветеринария"


def test_three_village_pharmacies_in_inventory():
    pharmacies = _village_active("pharmacy")
    keys = {entry["stable_key"] for entry in pharmacies}
    assert keys == {
        "apteka-a-lenina-20a",
        "apteka-a-novorzhevskaya-25",
        "farm-m-lenina-42",
    }


def test_village_vet_clinic_separate_from_hospital():
    vets = _village_active("vet")
    hospitals = _village_active("hospital")
    assert len(vets) == 1
    assert vets[0]["stable_key"] == "vet-sbbzh-stroiteley-3"
    assert len(hospitals) == 1
    assert hospitals[0]["stable_key"] == "hospital-pushkinogorsky-filial"
