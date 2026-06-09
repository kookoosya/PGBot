"""Place search, details and basic CRUD operations."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.place import Place
from app.services.place.schemas import (
    COMPLAINTS_LIMIT,
    EFFECTIVE_RATING,
    EFFECTIVE_REVIEWS,
    LODGING_CATEGORIES,
    REVIEWS_LIMIT,
    SHOP_CATEGORIES,
    SOURCE_PRIORITY,
    USEFUL_CATEGORIES,
    PlaceDetailResult,
    PlaceNotFoundError,
    PlaceSearchParams,
    PlaceSearchResult,
    build_place_detail_response,
    district_bbox,
    settlement_bbox,
)


async def load_place(db: AsyncSession, place_id: int) -> Place:
    """Load a place by id or raise ``PlaceNotFoundError``."""
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    if place is None:
        raise PlaceNotFoundError()
    return place


def _apply_bbox_filter(query: Any, params: PlaceSearchParams) -> Any:
    if all(value is not None for value in (params.south, params.west, params.north, params.east)):
        return query.where(
            Place.latitude >= params.south,
            Place.latitude <= params.north,
            Place.longitude >= params.west,
            Place.longitude <= params.east,
        )

    use_district = params.district or params.category in LODGING_CATEGORIES
    lat_min, lat_max, lng_min, lng_max = district_bbox() if use_district else settlement_bbox()
    return query.where(
        Place.latitude >= lat_min,
        Place.latitude <= lat_max,
        Place.longitude >= lng_min,
        Place.longitude <= lng_max,
    )


def _apply_search_sort(query: Any, *, sort_by: str) -> Any:
    if sort_by == "rating":
        return query.order_by(
            SOURCE_PRIORITY,
            EFFECTIVE_RATING.desc(),
            EFFECTIVE_REVIEWS.desc(),
            Place.name,
        )
    return query.order_by(SOURCE_PRIORITY, Place.name)


async def search_places(db: AsyncSession, params: PlaceSearchParams) -> PlaceSearchResult:
    """Search and filter active places with geo bounds, sorting and pagination."""
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
        query = query.where(params.min_rating <= EFFECTIVE_RATING)

    query = _apply_bbox_filter(query, params)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    page_size = min(max(params.page_size, 1), 500)
    result = await db.execute(
        _apply_search_sort(query, sort_by=params.sort_by)
        .offset((params.page - 1) * page_size)
        .limit(page_size),
    )
    items = list(result.scalars().all())
    return PlaceSearchResult(items=items, total=total)


async def get_place_details(db: AsyncSession, place_id: int) -> PlaceDetailResult:
    """Load a place with reviews and complaints."""
    result = await db.execute(
        select(Place)
        .options(selectinload(Place.reviews), selectinload(Place.complaints))
        .where(Place.id == place_id),
    )
    place = result.scalar_one_or_none()
    if place is None:
        raise PlaceNotFoundError()

    reviews = sorted(place.reviews, key=lambda review: review.created_at, reverse=True)[:REVIEWS_LIMIT]
    recent_complaints = sorted(
        place.complaints,
        key=lambda complaint: complaint.created_at,
        reverse=True,
    )[:COMPLAINTS_LIMIT]

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
