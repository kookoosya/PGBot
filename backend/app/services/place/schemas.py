"""Types, DTOs, errors and shared query constants for place service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional, TypedDict

from sqlalchemy import case

from app.models.enums import PlaceCategory, ShopComplaintType
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.models.issue import Issue
from app.schemas.place import MapStatsResponse, PlaceDetailResponse
from app.models.user import User
from app.utils.errors import ServiceError

PlaceSortField = Literal["rating", "name"]


class PlaceRatingMeta(TypedDict):
    """Display rating fields attached to place API responses."""

    display_rating: float
    display_review_count: int
    rating_source: str | None


SHOP_CATEGORIES = {
    PlaceCategory.SHOP,
    PlaceCategory.SUPERMARKET,
    PlaceCategory.PHARMACY,
    PlaceCategory.TYRE,
    PlaceCategory.AUTO,
}

LODGING_CATEGORIES = {PlaceCategory.HOTEL}

LANDMARK_CATEGORIES = {PlaceCategory.CULTURE}

USEFUL_CATEGORIES = {
    PlaceCategory.BANK,
    PlaceCategory.POST,
    PlaceCategory.GOVERNMENT,
    PlaceCategory.HOSPITAL,
    PlaceCategory.VET,
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
REVIEW_DUPLICATE_HOURS = 24
COMPLAINT_DUPLICATE_HOURS = 24


@dataclass(frozen=True, slots=True)
class PlaceActorContext:
    """Actor submitting a place review or complaint."""

    actor_id: Optional[int] = None
    ip_address: Optional[str] = None


@dataclass(frozen=True, slots=True)
class PlaceComplaintInput:
    """Validated payload for creating a place complaint."""

    complaint_type: ShopComplaintType
    description: str
    price_tagged: Optional[str] = None
    price_charged: Optional[str] = None
    receipt_info: Optional[str] = None
    author_name: Optional[str] = None


@dataclass(frozen=True, slots=True)
class PlaceReviewInput:
    """Validated payload for creating a place review."""

    rating: int
    text: Optional[str] = None
    author_name: Optional[str] = None


@dataclass(frozen=True, slots=True)
class PlaceSearchParams:
    """Filters for ``search_places``."""

    category: Optional[PlaceCategory] = None
    search: Optional[str] = None
    shops_only: bool = False
    useful_only: bool = False
    min_rating: Optional[float] = None
    south: Optional[float] = None
    west: Optional[float] = None
    north: Optional[float] = None
    east: Optional[float] = None
    district: bool = False
    scope: str | None = None
    page: int = 1
    page_size: int = 100
    offset: Optional[int] = None
    sort_by: PlaceSortField = "rating"


@dataclass(frozen=True, slots=True)
class PlaceSearchResult:
    """Paginated place search result."""

    items: list[Place]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    offset: int


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
    issue: Issue
    owner_notified: bool = True


@dataclass(frozen=True, slots=True)
class PlaceReviewResult:
    """Result of submitting a place review."""

    review: PlaceReview
    place: Place


@dataclass(frozen=True, slots=True)
class MapStatsResult:
    """Aggregated map dashboard statistics."""

    total_places: int
    by_category: dict[str, int]
    last_sync: datetime | None
    center_lat: float
    center_lng: float
    total_reviews: int
    total_complaints: int
    active_complaints: int
    avg_rating_by_category: dict[str, float]
    active_taxi_count: int
    route_count: int
    auto_sync_hours: int = 6
    yandex_live: bool = False
    reference_places: int = 0
    scope: str = "VILLAGE"
    village_places: int = 0
    nearby_places: int = 0
    district_places: int = 0

    def to_response(self) -> MapStatsResponse:
        """Serialize to the public API schema."""
        return MapStatsResponse(
            total_places=self.total_places,
            by_category=self.by_category,
            last_sync=self.last_sync,
            center={"lat": self.center_lat, "lng": self.center_lng},
            total_reviews=self.total_reviews,
            total_complaints=self.total_complaints,
            active_complaints=self.active_complaints,
            avg_rating_by_category=self.avg_rating_by_category,
            active_taxi_count=self.active_taxi_count,
            route_count=self.route_count,
            auto_sync_hours=self.auto_sync_hours,
            yandex_live=self.yandex_live,
            reference_places=self.reference_places,
            scope=self.scope,
            village_places=self.village_places,
            nearby_places=self.nearby_places,
            district_places=self.district_places,
        )


class PlaceNotFoundError(ServiceError):
    """Business error when a place cannot be loaded."""

    def __init__(self, detail: str = "Место не найдено") -> None:
        super().__init__(detail, status_code=404)


class PlaceValidationError(ServiceError):
    """Business validation failure for place actions."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


def resolve_author_name(data_author: Optional[str], user: Optional[User]) -> str:
    """Pick display name from form data or authenticated user."""
    if data_author:
        return data_author
    if user and user.full_name:
        return user.full_name
    return "Житель"
