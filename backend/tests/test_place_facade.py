"""Smoke tests for place_service facade after package split."""

import app.services.place_service as facade
from app.services.place import complaint as complaint_mod
from app.services.place import details as details_mod
from app.services.place import responses as responses_mod
from app.services.place import review as review_mod
from app.services.place import search as search_mod
from app.services.place import stats as stats_mod
from app.services.place import taxi as taxi_mod


def test_facade_exports_search():
    assert facade.search_places is search_mod.search_places


def test_facade_exports_details():
    assert facade.get_place_details is details_mod.get_place_details


def test_facade_exports_review_and_complaint():
    assert facade.add_place_review is review_mod.add_place_review
    assert facade.create_place_complaint is complaint_mod.create_place_complaint


def test_facade_exports_stats_and_taxi():
    assert facade.get_map_stats is stats_mod.get_map_stats
    assert facade.list_active_taxi is taxi_mod.list_active_taxi
    assert facade.list_place_category_options is stats_mod.list_place_category_options


def test_facade_exports_responses():
    assert facade.build_place_response is responses_mod.build_place_response
    assert facade.place_rating_meta is responses_mod.place_rating_meta


def test_facade_schema_types():
    assert facade.PlaceNotFoundError is not None
    assert facade.PlaceSearchParams is not None
    assert facade.PlaceComplaintInput is not None
