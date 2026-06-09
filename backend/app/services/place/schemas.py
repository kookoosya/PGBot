"""Internal dataclasses, errors, constants and response mappers for places."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import case

from app.config import get_settings
from app.models.enums import MAP_REPORT_LABELS, PLACE_CATEGORY_LABELS, SHOP_COMPLAINT_LABELS, PlaceCategory
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.schemas.place import (
    PlaceComplaintResponse,
    PlaceDetailResponse,
    PlaceResponse,
    PlaceReviewResponse,
)
from app.services.schedule import format_opening_hours
from app.services.service_errors import ServiceError

settings = get_settings()

PlaceSortField = Literal["rating", "name"]

SHOP_CATEGORIES = {
    PlaceCategory.SHOP,
    PlaceCategory.SUPERMARKET,
    PlaceCategory.PHARMACY,
    PlaceCategory.TYRE,
    PlaceCategory.AUTO,
}

LODGING_CATEGORIES = {PlaceCategory.HOTEL}

USEFUL_CATEGORIES = {
    PlaceCategory.BANK,
    PlaceCategory.POST,
    PlaceCategory.GOVERNMENT,
    PlaceCategory.HOSPITAL,
    PlaceCategory.TRANSPORT,
    PlaceCategory.PARKING,
}

SOURCE_PRIORITY = case(
    (Place.external_source == "reference", 0),
    (Place.external_source == "yandex", 1),
    (Place.external_source == "seed", 2),
    (Place.external_source == "osm", 3),
    else_=4,
)

EFFECTIVE_RATING = case(
    (Place.external_rating > 0, Place.external_rating),
    else_=Place.avg_rating,
)

EFFECTIVE_REVIEWS = case(
    (Place.external_review_count > 0, Place.external_review_count),
    else_=Place.review_count,
)

MAX_PAGE_SIZE = 500
REVIEWS_LIMIT = 10
COMPLAINTS_LIMIT = 5


class PlaceNotFoundError(ServiceError):
    """Business error when a place cannot be loaded."""

    def __init__(self, detail: str = "Место не найдено") -> None:
        super().__init__(detail, status_code=404)


class PlaceValidationError(ServiceError):
    """Business validation failure for place actions."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


@dataclass(frozen=True, slots=True)
class PlaceComplaintInput:
    """Validated payload for creating a place complaint."""

    complaint_type: str
    description: str
    price_tagged: str | None = None
    price_charged: str | None = None
    receipt_info: str | None = None
    author_name: str | None = None


@dataclass(frozen=True, slots=True)
class PlaceReviewInput:
    """Validated payload for creating a place review."""

    rating: int
    text: str | None = None
    author_name: str | None = None


@dataclass(frozen=True, slots=True)
class PlaceSearchParams:
    """Filters for ``search_places``."""

    category: PlaceCategory | None = None
    search: str | None = None
    shops_only: bool = False
    useful_only: bool = False
    min_rating: float | None = None
    south: float | None = None
    west: float | None = None
    north: float | None = None
    east: float | None = None
    district: bool = False
    page: int = 1
    page_size: int = 100
    sort_by: PlaceSortField = "rating"


@dataclass(frozen=True, slots=True)
class PlaceSearchResult:
    """Paginated place search result."""

    items: list[Place]
    total: int


@dataclass(frozen=True, slots=True)
class PlaceDetailResult:
    """Loaded place with recent reviews and complaints."""

    place: Place
    reviews: list[PlaceReview]
    recent_complaints: list[PlaceComplaint]
    response: PlaceDetailResponse


@dataclass(frozen=True, slots=True)
class PlaceComplaintResult:
    """Result of submitting a place complaint."""

    complaint: PlaceComplaint


@dataclass(frozen=True, slots=True)
class PlaceReviewResult:
    """Result of submitting a place review."""

    review: PlaceReview


def radius_bbox(radius_km: float) -> tuple[float, float, float, float]:
    """Return lat/lng bounds for a square bbox around the map center."""
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * math.cos(math.radians(settings.MAP_CENTER_LAT)))
    return (
        settings.MAP_CENTER_LAT - lat_delta,
        settings.MAP_CENTER_LAT + lat_delta,
        settings.MAP_CENTER_LNG - lng_delta,
        settings.MAP_CENTER_LNG + lng_delta,
    )


def settlement_bbox() -> tuple[float, float, float, float]:
    """BBox for the settlement view (~8 km)."""
    return radius_bbox(8.0)


def district_bbox() -> tuple[float, float, float, float]:
    """BBox for the wider district view."""
    return radius_bbox(settings.MAP_SYNC_RADIUS_KM)


def resolve_author_name(data_author: str | None, user) -> str:
    """Pick display name from form data or authenticated user."""
    if data_author:
        return data_author
    if user and user.full_name:
        return user.full_name
    return "Житель"


def complaint_label(complaint: PlaceComplaint) -> str:
    """Human-readable label for a complaint type."""
    return (
        MAP_REPORT_LABELS.get(complaint.complaint_type)
        or SHOP_COMPLAINT_LABELS.get(complaint.complaint_type, complaint.complaint_type)
    )


def place_rating_meta(place: Place) -> dict[str, float | int | str | None]:
    """Return display rating fields for API responses."""
    if place.external_rating > 0:
        source = "yandex" if place.external_source == "yandex" else "reference"
        return {
            "display_rating": place.external_rating,
            "display_review_count": place.external_review_count,
            "rating_source": source,
        }
    if place.avg_rating > 0:
        return {
            "display_rating": place.avg_rating,
            "display_review_count": place.review_count,
            "rating_source": "users",
        }
    return {"display_rating": 0.0, "display_review_count": 0, "rating_source": None}


def build_place_response(place: Place) -> PlaceResponse:
    """Map a ``Place`` ORM instance to ``PlaceResponse``."""
    meta = place_rating_meta(place)
    return PlaceResponse(
        id=place.id,
        name=place.name,
        category=place.category,
        category_label=PLACE_CATEGORY_LABELS.get(place.category, place.category),
        description=place.description,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        phone=place.phone,
        website=place.website,
        opening_hours=format_opening_hours(place.opening_hours) or place.opening_hours,
        avg_rating=place.avg_rating,
        review_count=place.review_count,
        external_rating=place.external_rating,
        external_review_count=place.external_review_count,
        yandex_url=place.yandex_url,
        complaint_count=place.complaint_count,
        last_synced_at=place.last_synced_at,
        **meta,
    )


def build_complaint_response(complaint: PlaceComplaint) -> PlaceComplaintResponse:
    """Map a ``PlaceComplaint`` ORM instance to ``PlaceComplaintResponse``."""
    return PlaceComplaintResponse(
        id=complaint.id,
        complaint_type=complaint.complaint_type,
        complaint_label=complaint_label(complaint),
        description=complaint.description,
        price_tagged=complaint.price_tagged,
        price_charged=complaint.price_charged,
        status=complaint.status,
        created_at=complaint.created_at,
    )


def build_place_detail_response(
    place: Place,
    *,
    reviews: list[PlaceReview],
    recent_complaints: list[PlaceComplaint],
) -> PlaceDetailResponse:
    """Build a full place detail payload for the API."""
    base = build_place_response(place)
    return PlaceDetailResponse(
        **base.model_dump(),
        reviews=[PlaceReviewResponse.model_validate(review) for review in reviews],
        recent_complaints=[build_complaint_response(complaint) for complaint in recent_complaints],
    )


def list_place_category_options() -> list[dict[str, str]]:
    """Return category enum options for the map UI."""
    return [{"value": category.value, "label": PLACE_CATEGORY_LABELS[category]} for category in PlaceCategory]


def to_complaint_input(data) -> PlaceComplaintInput:
    """Convert API schema to service-layer complaint input."""
    return PlaceComplaintInput(
        complaint_type=data.complaint_type,
        description=data.description,
        price_tagged=data.price_tagged,
        price_charged=data.price_charged,
        receipt_info=data.receipt_info,
        author_name=data.author_name,
    )


def to_review_input(data) -> PlaceReviewInput:
    """Convert API schema to service-layer review input."""
    return PlaceReviewInput(
        rating=data.rating,
        text=data.text,
        author_name=data.author_name,
    )
