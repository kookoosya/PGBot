"""Tests for map place cleanup rules."""

from app.models.enums import PlaceCategory
from app.services.place_cleanup import (
    _fix_category,
    _is_junk_name,
    should_skip_osm_element,
    should_skip_yandex_org,
)


def test_skip_tbank_yandex():
    assert should_skip_yandex_org("Т-Банк") is True
    assert should_skip_yandex_org("Тинькофф") is True


def test_allow_sber_yandex():
    assert should_skip_yandex_org("Сбербанк") is False
    assert should_skip_yandex_org("Банкомат Сбербанка") is False


def test_skip_osm_atm():
    assert should_skip_osm_element({"amenity": "atm", "addr:street": "Ленина"}, "Т-Банк") is True
    assert should_skip_osm_element({"amenity": "bank"}, "ВТБ") is True


def test_fix_magnit_kosmetik_category():
    assert _fix_category("Магнит Косметик", PlaceCategory.BANK) == PlaceCategory.BEAUTY


def test_junk_names():
    assert _is_junk_name("Т-Банк") is True
    assert _is_junk_name("Пятёрочка") is False


def test_match_reference_import():
    from app.models.place import Place
    from app.services.place_cleanup import match_reference_import

    refs = [
        Place(
            name="М.Косметик",
            category=PlaceCategory.BEAUTY,
            latitude=57.0261,
            longitude=28.9112,
            external_source="reference",
        ),
    ]
    hit = match_reference_import("Магнит Косметик", 57.0261, 28.9112, refs)
    assert hit is not None
    assert hit.name == "М.Косметик"
