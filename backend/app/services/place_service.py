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

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional, TypedDict

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.enums import (
    MAP_REPORT_LABELS,
    PLACE_CATEGORY_LABELS,
    SHOP_COMPLAINT_LABELS,
    IssueCategory,
    IssueStatus,
    PlaceCategory,
    Priority,
    ShopComplaintType,
)
from app.models.issue import Issue
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.models.taxi import TaxiService
from app.models.user import User
from app.schemas.place import (
    MapStatsResponse,
    PlaceComplaintResponse,
    PlaceDetailResponse,
    PlaceResponse,
    PlaceReviewResponse,
)
from app.constants.map_config import MAP_FILTER_MODES, MapFilterMode, get_map_filter_modes
from app.services.map_routes import get_map_routes
from app.services.notify_utils import safe_notify_owner
from app.services.pagination_utils import normalize_pagination
from app.services.schedule import format_opening_hours
from app.services.service_errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()

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
_REVIEW_DUPLICATE_HOURS = 24
_COMPLAINT_DUPLICATE_HOURS = 24


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
        )


class PlaceNotFoundError(ServiceError):
    """Business error when a place cannot be loaded."""

    def __init__(self, detail: str = "Место не найдено") -> None:
        super().__init__(detail, status_code=404)


class PlaceValidationError(ServiceError):
    """Business validation failure for place actions."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


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
) -> tuple[int, int, int, int, bool, bool]:
    """Return clamped pagination metadata for place search."""
    return normalize_pagination(
        page=page,
        page_size=page_size,
        total=total,
        offset=offset,
        max_page_size=_MAX_PAGE_SIZE,
    )


async def _load_place(db: AsyncSession, place_id: int) -> Place:
    """Load a place by id or raise ``PlaceNotFoundError``."""
    try:
        result = await db.execute(select(Place).where(Place.id == place_id))
        place = result.scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load place #%s", place_id)
        raise
    if place is None:
        raise PlaceNotFoundError()
    return place


async def _safe_notify_owner(message: str, *, context: str, place_id: int) -> bool:
    """Notify site owner about a place-related event; return ``True`` on success."""
    return await safe_notify_owner(
        message,
        context=context,
        resource="place",
        resource_id=place_id,
    )


def _resolve_author_name(data_author: Optional[str], user: Optional[User]) -> str:
    """Pick display name from form data or authenticated user."""
    if data_author:
        return data_author
    if user and user.full_name:
        return user.full_name
    return "Житель"


async def _check_duplicate_review(
    db: AsyncSession,
    place_id: int,
    *,
    user_id: Optional[int],
    author_name: str,
) -> None:
    """Reject duplicate reviews from the same user or anonymous author."""
    try:
        if user_id is not None:
            existing = await db.execute(
                select(PlaceReview.id)
                .where(PlaceReview.place_id == place_id, PlaceReview.user_id == user_id)
                .limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                raise PlaceValidationError(
                    "Вы уже оставляли отзыв об этом месте",
                    status_code=409,
                )
            return

        since = datetime.now(timezone.utc) - timedelta(hours=_REVIEW_DUPLICATE_HOURS)
        recent = await db.execute(
            select(PlaceReview.id)
            .where(
                PlaceReview.place_id == place_id,
                PlaceReview.user_id.is_(None),
                PlaceReview.author_name == author_name,
                PlaceReview.created_at >= since,
            )
            .limit(1)
        )
        if recent.scalar_one_or_none() is not None:
            raise PlaceValidationError(
                "Отзыв с этим именем уже отправляли недавно — попробуйте позже",
                status_code=429,
            )
    except PlaceValidationError:
        raise
    except Exception:
        logger.exception(
            "Duplicate review check failed for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise


async def _check_duplicate_complaint(
    db: AsyncSession,
    place_id: int,
    *,
    user_id: Optional[int],
    author_name: str,
) -> None:
    """Reject repeated complaints on the same place within the cooldown window."""
    since = datetime.now(timezone.utc) - timedelta(hours=_COMPLAINT_DUPLICATE_HOURS)
    try:
        query = select(PlaceComplaint.id).where(
            PlaceComplaint.place_id == place_id,
            PlaceComplaint.created_at >= since,
        )
        if user_id is not None:
            query = query.where(PlaceComplaint.user_id == user_id)
        else:
            query = query.where(
                PlaceComplaint.user_id.is_(None),
                PlaceComplaint.author_name == author_name,
            )
        existing = await db.execute(query.limit(1))
        if existing.scalar_one_or_none() is not None:
            raise PlaceValidationError(
                "Вы уже отправляли жалобу на это место недавно — попробуйте позже",
                status_code=429,
            )
    except PlaceValidationError:
        raise
    except Exception:
        logger.exception(
            "Duplicate complaint check failed for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise


async def _recalculate_place_rating(db: AsyncSession, place: Place) -> None:
    """Update ``avg_rating`` and ``review_count`` from persisted reviews."""
    try:
        avg_result = await db.execute(
            select(func.avg(PlaceReview.rating), func.count(PlaceReview.id)).where(
                PlaceReview.place_id == place.id
            )
        )
        avg_row = avg_result.one()
        place.avg_rating = round(float(avg_row[0] or 0), 1)
        place.review_count = avg_row[1] or 0
    except Exception:
        logger.exception("Failed to recalculate rating for place #%s", place.id)
        raise


def build_complaint_response(
    complaint: PlaceComplaint,
    *,
    owner_notified: bool | None = None,
) -> PlaceComplaintResponse:
    """Map a ``PlaceComplaint`` ORM instance to ``PlaceComplaintResponse``."""
    return PlaceComplaintResponse(
        id=complaint.id,
        complaint_type=complaint.complaint_type,
        complaint_label=_complaint_label(complaint),
        description=complaint.description,
        price_tagged=complaint.price_tagged,
        price_charged=complaint.price_charged,
        status=complaint.status,
        created_at=complaint.created_at,
        owner_notified=owner_notified,
    )


def place_rating_meta(place: Place) -> PlaceRatingMeta:
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


async def create_place_complaint(
    db: AsyncSession,
    place_id: int,
    data: PlaceComplaintInput,
    *,
    user: Optional[User] = None,
) -> PlaceComplaintResult:
    """Create a complaint, linked issue and notify the site owner safely.

    Raises ``PlaceNotFoundError`` if the place is missing and
    ``PlaceValidationError`` when a duplicate complaint is detected.
    """
    place = await _load_place(db, place_id)
    author_name = _resolve_author_name(data.author_name, user)
    user_id = user.id if user else None

    await _check_duplicate_complaint(
        db,
        place_id,
        user_id=user_id,
        author_name=author_name,
    )

    complaint = PlaceComplaint(
        place_id=place_id,
        complaint_type=data.complaint_type,
        description=data.description,
        price_tagged=data.price_tagged,
        price_charged=data.price_charged,
        receipt_info=data.receipt_info,
        author_name=author_name,
        user_id=user_id,
    )

    type_label = MAP_REPORT_LABELS.get(data.complaint_type) or SHOP_COMPLAINT_LABELS.get(
        data.complaint_type,
        data.complaint_type,
    )
    is_map_report = data.complaint_type in MAP_REPORT_LABELS
    issue_desc = (
        f"{'Ошибка на карте' if is_map_report else 'Жалоба'}: {place.name} ({place.address or ''})\n"
        f"Тип: {type_label}\n"
        f"{data.description}"
    )
    if data.price_tagged or data.price_charged:
        issue_desc += (
            f"\nЦена на ценнике: {data.price_tagged or '—'}, "
            f"на кассе: {data.price_charged or '—'}"
        )

    issue = Issue(
        title=f"{'Карта' if is_map_report else 'Жалоба'}: {place.name}",
        description=issue_desc,
        status=IssueStatus.NEW,
        category=IssueCategory.OTHER,
        priority=Priority.MEDIUM,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        resident_id=user_id,
    )

    try:
        db.add(complaint)
        place.complaint_count += 1
        db.add(issue)
        await db.flush()
        complaint.issue_id = issue.id
    except Exception:
        logger.exception(
            "Failed to persist complaint for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise

    owner_notified = await _safe_notify_owner(
        "⚠️ Жалоба на организацию\n\n"
        f"«{place.name}» — {place.address or 'адрес не указан'}\n"
        f"{SHOP_COMPLAINT_LABELS.get(data.complaint_type, data.complaint_type)}\n"
        f"{data.description[:300]}",
        context="place_complaint",
        place_id=place_id,
    )
    if not owner_notified:
        logger.warning(
            "Place complaint #%s created for place #%s but owner was not notified",
            complaint.id,
            place_id,
        )

    logger.info(
        "Place complaint #%s created for place #%s (issue #%s, user_id=%s)",
        complaint.id,
        place_id,
        issue.id,
        user_id,
    )
    return PlaceComplaintResult(
        complaint=complaint,
        issue=issue,
        owner_notified=owner_notified,
    )


async def add_place_review(
    db: AsyncSession,
    place_id: int,
    data: PlaceReviewInput,
    *,
    user: Optional[User] = None,
) -> PlaceReviewResult:
    """Add a review to a place and recalculate its average rating."""
    place = await _load_place(db, place_id)
    author_name = _resolve_author_name(data.author_name, user)
    user_id = user.id if user else None

    await _check_duplicate_review(
        db,
        place_id,
        user_id=user_id,
        author_name=author_name,
    )

    review = PlaceReview(
        place_id=place_id,
        rating=data.rating,
        text=data.text,
        author_name=author_name,
        user_id=user_id,
    )

    try:
        db.add(review)
        await db.flush()
        await _recalculate_place_rating(db, place)
    except PlaceValidationError:
        raise
    except Exception:
        logger.exception(
            "Failed to persist review for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise

    logger.info(
        "Place review #%s added to place #%s (rating=%s, user_id=%s)",
        review.id,
        place_id,
        data.rating,
        user_id,
    )
    return PlaceReviewResult(review=review, place=place)


async def list_active_taxi(db: AsyncSession) -> list[TaxiService]:
    """Return active taxi services sorted by ``sort_order`` and rating."""
    try:
        result = await db.execute(
            select(TaxiService)
            .where(TaxiService.is_active.is_(True))
            .order_by(TaxiService.sort_order, TaxiService.rating.desc())
        )
        items = list(result.scalars().all())
    except Exception:
        logger.exception("Failed to load active taxi services")
        raise

    logger.debug("Loaded %s active taxi service(s)", len(items))
    return items


async def get_map_stats(db: AsyncSession) -> MapStatsResult:
    """Collect map dashboard statistics for active places and related entities."""
    active_filter = Place.is_active.is_(True)
    try:
        total_places = (
            await db.execute(select(func.count(Place.id)).where(active_filter))
        ).scalar() or 0

        cat_rows = await db.execute(
            select(Place.category, func.count(Place.id))
            .where(active_filter)
            .group_by(Place.category)
        )
        by_category = {
            PLACE_CATEGORY_LABELS.get(row[0], str(row[0])): row[1]
            for row in cat_rows.all()
        }

        rating_rows = await db.execute(
            select(Place.category, func.avg(EFFECTIVE_RATING))
            .where(active_filter, EFFECTIVE_RATING > 0)
            .group_by(Place.category)
        )
        avg_rating_by_category = {
            PLACE_CATEGORY_LABELS.get(row[0], str(row[0])): round(float(row[1]), 1)
            for row in rating_rows.all()
            if row[1] is not None
        }

        total_reviews = (
            await db.execute(
                select(func.count(PlaceReview.id))
                .join(Place, PlaceReview.place_id == Place.id)
                .where(active_filter)
            )
        ).scalar() or 0

        total_complaints = (
            await db.execute(select(func.count(PlaceComplaint.id)))
        ).scalar() or 0
        active_complaints = (
            await db.execute(
                select(func.count(PlaceComplaint.id)).where(PlaceComplaint.status == "new")
            )
        ).scalar() or 0

        active_taxi_count = (
            await db.execute(
                select(func.count(TaxiService.id)).where(TaxiService.is_active.is_(True))
            )
        ).scalar() or 0

        last_sync = (await db.execute(select(func.max(Place.last_synced_at)))).scalar()
    except Exception:
        logger.exception("Failed to build map stats")
        raise

    route_count = len(get_map_routes())
    logger.debug(
        "Map stats: places=%s reviews=%s complaints=%s taxi=%s routes=%s",
        total_places,
        total_reviews,
        total_complaints,
        active_taxi_count,
        route_count,
    )
    return MapStatsResult(
        total_places=total_places,
        by_category=by_category,
        last_sync=last_sync,
        center_lat=settings.MAP_CENTER_LAT,
        center_lng=settings.MAP_CENTER_LNG,
        total_reviews=total_reviews,
        total_complaints=total_complaints,
        active_complaints=active_complaints,
        avg_rating_by_category=avg_rating_by_category,
        active_taxi_count=active_taxi_count,
        route_count=route_count,
    )


def list_place_category_options() -> list[dict[str, str]]:
    """Return place category enum values for map filters."""
    return [{"value": c.value, "label": PLACE_CATEGORY_LABELS[c]} for c in PlaceCategory]


def list_complaint_type_options() -> list[dict[str, str]]:
    """Return shop complaint types available for place reports."""
    return [
        {"value": t.value, "label": SHOP_COMPLAINT_LABELS[t]}
        for t in ShopComplaintType
        if t not in MAP_REPORT_LABELS
    ]


def list_map_report_type_options() -> list[dict[str, str]]:
    """Return map-specific report types (e.g. missing POI)."""
    return [{"value": t.value, "label": MAP_REPORT_LABELS[t]} for t in MAP_REPORT_LABELS]
