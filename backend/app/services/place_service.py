"""Place search, details, reviews, complaints and map stats.

Public API
----------
- ``search_places`` / ``get_place_details`` — read paths
- ``create_place_complaint`` / ``add_place_review`` — write paths
- ``list_active_taxi`` / ``get_map_stats`` — map dashboard
- ``build_place_response`` / ``build_complaint_response`` — response mappers

Errors: ``PlaceNotFoundError``, ``PlaceValidationError`` (subclasses of ``ServiceError``).
"""

from __future__ import annotations

from app.services.place.complaint import create_place_complaint
from app.services.place.crud import get_place_details, load_place, search_places
from app.services.place.review import add_place_review, review_to_response
from app.services.place.schemas import (
    PlaceComplaintInput,
    PlaceNotFoundError,
    PlaceReviewInput,
    PlaceSearchParams,
    PlaceSortField,
    PlaceValidationError,
    build_complaint_response,
    build_place_response,
    list_place_category_options,
    to_complaint_input,
    to_review_input,
)
from app.services.place.stats import MapStatsResult, get_map_stats
from app.services.place.taxi import list_active_taxi

__all__ = [
    "MapStatsResult",
    "PlaceComplaintInput",
    "PlaceNotFoundError",
    "PlaceReviewInput",
    "PlaceSearchParams",
    "PlaceSortField",
    "PlaceValidationError",
    "add_place_review",
    "build_complaint_response",
    "build_place_response",
    "create_place_complaint",
    "get_map_stats",
    "get_place_details",
    "list_active_taxi",
    "list_place_category_options",
    "load_place",
    "review_to_response",
    "search_places",
    "to_complaint_input",
    "to_review_input",
]
