"""Place search, details, reviews, complaints and map stats — thin facade.

Public API is unchanged; implementation lives in submodules.
"""

from app.constants.map_config import get_map_filter_modes
from app.services.place.complaint import create_place_complaint
from app.services.place.details import get_place_details
from app.services.place.responses import (
    build_complaint_response,
    build_place_detail_response,
    build_place_response,
    place_rating_meta,
)
from app.services.place.review import add_place_review
from app.services.place.schemas import (
    MapStatsResult,
    PlaceActorContext,
    PlaceComplaintInput,
    PlaceComplaintResult,
    PlaceDetailResult,
    PlaceNotFoundError,
    PlaceRatingMeta,
    PlaceReviewInput,
    PlaceReviewResult,
    PlaceSearchParams,
    PlaceSearchResult,
    PlaceSortField,
    PlaceValidationError,
)
from app.services.place.search import search_places
from app.services.place.stats import (
    get_map_stats,
    list_complaint_type_options,
    list_map_report_type_options,
    list_place_category_options,
)
from app.services.place.taxi import list_active_taxi

__all__ = [
    "MapStatsResult",
    "PlaceActorContext",
    "PlaceComplaintInput",
    "PlaceComplaintResult",
    "PlaceDetailResult",
    "PlaceNotFoundError",
    "PlaceRatingMeta",
    "PlaceReviewInput",
    "PlaceReviewResult",
    "PlaceSearchParams",
    "PlaceSearchResult",
    "PlaceSortField",
    "PlaceValidationError",
    "add_place_review",
    "build_complaint_response",
    "build_place_detail_response",
    "build_place_response",
    "create_place_complaint",
    "get_map_filter_modes",
    "get_map_stats",
    "get_place_details",
    "list_active_taxi",
    "list_complaint_type_options",
    "list_map_report_type_options",
    "list_place_category_options",
    "place_rating_meta",
    "search_places",
]
