"""Unit tests for place response helpers (no database)."""

from types import SimpleNamespace

from app.services.place.responses import place_rating_meta


def test_place_rating_meta_prefers_external_yandex():
    place = SimpleNamespace(
        external_rating=4.5,
        external_review_count=120,
        external_source="yandex",
        avg_rating=3.0,
        review_count=2,
    )
    meta = place_rating_meta(place)
    assert meta["display_rating"] == 4.5
    assert meta["display_review_count"] == 120
    assert meta["rating_source"] == "yandex"


def test_place_rating_meta_falls_back_to_user_rating():
    place = SimpleNamespace(
        external_rating=0.0,
        external_review_count=0,
        external_source="osm",
        avg_rating=4.2,
        review_count=5,
    )
    meta = place_rating_meta(place)
    assert meta["display_rating"] == 4.2
    assert meta["rating_source"] == "users"


def test_place_rating_meta_reference_without_scores():
    place = SimpleNamespace(
        external_rating=0.0,
        external_review_count=0,
        external_source="reference",
        avg_rating=0.0,
        review_count=0,
    )
    meta = place_rating_meta(place)
    assert meta["rating_source"] == "reference"
    assert meta["display_rating"] == 0.0
