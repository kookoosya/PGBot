"""Place search and details — extracted from the API layer."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Any, Literal, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.enums import (
    MAP_REPORT_LABELS,
    PLACE_CATEGORY_LABELS,
    SHOP_COMPLAINT_LABELS,
    PlaceCategory,
)
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.schemas.place import (
    PlaceComplaintResponse,
    PlaceDetailResponse,
    PlaceResponse,
    PlaceReviewResponse,
)
from app.services.schedule import format_opening_hours

logger = logging.getLogger(__name__)
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

_PLACE_DETAIL_LOADS = (
    selectinload(Place.reviews),
    selectinload(Place.complaints),
)

_MAX_PAGE_SIZE = 500
_REVIEWS_LIMIT = 10
_COMPLAINTS_LIMIT = 5


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


class PlaceNotFoundError(Exception):
    """Business error when a place cannot be loaded."""

    def __init__(self, detail: str = "Место не найдено", *, status_code: int = 404) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _radius_bbox(radius_km: float) -> tuple[float, float, float, float]:
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * math.cos(math.radians(settings.MAP_CENTER_LAT)))
    return (
        settings.MAP_CENTER_LAT - lat_delta,
        settings.MAP_CENTER_LAT + lat_delta,
        settings.MAP_CENTER_LNG - lng_delta,
        settings.MAP_CENTER_LNG + lng_delta,
    )


def _settlement_bbox() -> tuple[float, float, float, float]:
    return _radius_bbox(8.0)


def _district_bbox() -> tuple[float, float, float, float]:
    return _radius_bbox(settings.MAP_SYNC_RADIUS_KM)


def _normalize_pagination(
    *,
    page: int,
    page_size: int,
    total: int,
    offset: Optional[int] = None,
    max_page_size: int = _MAX_PAGE_SIZE,
) -> tuple[int, int, int, int, bool, bool]:
    """Return clamped page, offset, page_size, total_pages, has_prev, has_next."""
    safe_page_size = max(1, min(page_size, max_page_size))
    total_pages = max(1, (total + safe_page_size - 1) // safe_page_size) if total else 1
    if offset is not None:
        safe_offset = max(0, offset)
        safe_page = safe_offset // safe_page_size + 1
    else:
        safe_page = max(1, min(page, total_pages))
        safe_offset = (safe_page - 1) * safe_page_size
    has_prev = safe_offset > 0
    has_next = safe_offset + safe_page_size < total
    return safe_page, safe_offset, safe_page_size, total_pages, has_prev, has_next


def place_rating_meta(place: Place) -> dict[str, Any]:
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


def _complaint_label(complaint: PlaceComplaint) -> str:
    return (
        MAP_REPORT_LABELS.get(complaint.complaint_type)
        or SHOP_COMPLAINT_LABELS.get(complaint.complaint_type, complaint.complaint_type)
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
        recent_complaints=[
            PlaceComplaintResponse(
                id=complaint.id,
                complaint_type=complaint.complaint_type,
                complaint_label=_complaint_label(complaint),
                description=complaint.description,
                price_tagged=complaint.price_tagged,
                price_charged=complaint.price_charged,
                status=complaint.status,
                created_at=complaint.created_at,
            )
            for complaint in recent_complaints
        ],
    )


def _apply_bbox_filter(query: Any, params: PlaceSearchParams) -> Any:
    if all(v is not None for v in (params.south, params.west, params.north, params.east)):
        return query.where(
            Place.latitude >= params.south,
            Place.latitude <= params.north,
            Place.longitude >= params.west,
            Place.longitude <= params.east,
        )

    use_district = params.district or params.category in LODGING_CATEGORIES
    lat_min, lat_max, lng_min, lng_max = _district_bbox() if use_district else _settlement_bbox()
    return query.where(
        Place.latitude >= lat_min,
        Place.latitude <= lat_max,
        Place.longitude >= lng_min,
        Place.longitude <= lng_max,
    )


def _apply_search_sort(query: Any, *, sort_by: PlaceSortField) -> Any:
    if sort_by == "rating":
        return query.order_by(
            SOURCE_PRIORITY,
            EFFECTIVE_RATING.desc(),
            EFFECTIVE_REVIEWS.desc(),
            Place.name,
        )
    return query.order_by(SOURCE_PRIORITY, Place.name)


async def search_places(
    db: AsyncSession,
    params: PlaceSearchParams,
) -> PlaceSearchResult:
    """Search and filter active places with geo bounds, sorting and pagination."""
    try:
        query = select(Place).where(Place.is_active.is_(True))

        if params.category is not None:
            query = query.where(Place.category == params.category)
        if params.shops_only:
            query = query.where(Place.category.in_(SHOP_CATEGORIES))
        if params.useful_only:
            query = query.where(Place.category.in_(USEFUL_CATEGORIES))
        if params.search:
            pattern = f"%{params.search.strip()}%"
            query = query.where(Place.name.ilike(pattern) | Place.address.ilike(pattern))
        if params.min_rating is not None:
            query = query.where(EFFECTIVE_RATING >= params.min_rating)

        query = _apply_bbox_filter(query, params)

        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
        page, offset, page_size, total_pages, has_prev, has_next = _normalize_pagination(
            page=params.page,
            page_size=params.page_size,
            total=total,
            offset=params.offset,
        )
        result = await db.execute(
            _apply_search_sort(query, sort_by=params.sort_by).offset(offset).limit(page_size)
        )
        items = list(result.scalars().all())
    except PlaceNotFoundError:
        raise
    except Exception:
        logger.exception(
            "Place search failed: category=%s search=%r page=%s page_size=%s",
            params.category,
            params.search,
            params.page,
            params.page_size,
        )
        raise

    logger.debug(
        "Place search: %s item(s), total=%s page=%s/%s sort=%s",
        len(items),
        total,
        page,
        total_pages,
        params.sort_by,
    )
    return PlaceSearchResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        offset=offset,
    )


async def get_place_details(db: AsyncSession, place_id: int) -> PlaceDetailResult:
    """Load a place with reviews and complaints; raise ``PlaceNotFoundError`` if missing."""
    try:
        result = await db.execute(
            select(Place)
            .options(*_PLACE_DETAIL_LOADS)
            .where(Place.id == place_id)
        )
        place = result.scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load place #%s", place_id)
        raise

    if place is None:
        logger.debug("Place %s not found", place_id)
        raise PlaceNotFoundError()

    reviews = sorted(place.reviews, key=lambda review: review.created_at, reverse=True)[
        :_REVIEWS_LIMIT
    ]
    recent_complaints = sorted(
        place.complaints,
        key=lambda complaint: complaint.created_at,
        reverse=True,
    )[:_COMPLAINTS_LIMIT]

    response = build_place_detail_response(
        place,
        reviews=reviews,
        recent_complaints=recent_complaints,
    )
    return PlaceDetailResult(
        place=place,
        reviews=reviews,
        recent_complaints=recent_complaints,
        response=response,
    )
