"""Smoke tests for place_service facade after package split."""

import app.services.place_service as facade
from app.services.place import complaint as complaint_mod
from app.services.place import details as details_mod
from app.services.place import review as review_mod
from app.services.place import search as search_mod
from app.services.place import stats as stats_mod


def test_facade_exports_search_and_details():
    assert facade.search_places is search_mod.search_places
    assert facade.get_place_details is details_mod.get_place_details


def test_facade_exports_write_paths():
    assert facade.create_place_complaint is complaint_mod.create_place_complaint
    assert facade.add_place_review is review_mod.add_place_review


def test_facade_exports_map_helpers():
    assert facade.get_map_stats is stats_mod.get_map_stats
    assert facade.list_place_category_options is stats_mod.list_place_category_options


def test_facade_schema_types():
    assert facade.PlaceNotFoundError is not None
    assert facade.PlaceSearchParams is not None
    assert facade.MapStatsResult is not None
