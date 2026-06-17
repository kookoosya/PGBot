"""Smoke tests for place package public exports."""

import app.services.place as pkg
from app.services.place import complaint as complaint_mod
from app.services.place import details as details_mod
from app.services.place import review as review_mod
from app.services.place import search as search_mod
from app.services.place import stats as stats_mod


def test_package_exports_search_and_details():
    assert pkg.search_places is search_mod.search_places
    assert pkg.get_place_details is details_mod.get_place_details


def test_package_exports_write_paths():
    assert pkg.create_place_complaint is complaint_mod.create_place_complaint
    assert pkg.add_place_review is review_mod.add_place_review


def test_package_exports_map_helpers():
    assert pkg.get_map_stats is stats_mod.get_map_stats
    assert pkg.list_place_category_options is stats_mod.list_place_category_options


def test_package_schema_types():
    assert pkg.PlaceNotFoundError is not None
    assert pkg.PlaceSearchParams is not None
    assert pkg.MapStatsResult is not None
