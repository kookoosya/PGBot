"""Place search with geo filters and pagination."""

from __future__ import annotations

import logging
import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.constants.place_scope import VILLAGE
from app.models.place import Place
from app.utils.pagination import normalize_pagination

from .schemas import (
    EFFECTIVE_RATING,
    EFFECTIVE_REVIEWS,
    LODGING_CATEGORIES,
    MAX_PAGE_SIZE,
    SHOP_CATEGORIES,
    SOURCE_PRIORITY,
    USEFUL_CATEGORIES,
    PlaceNotFoundError,
    PlaceSearchParams,
    PlaceSearchResult,
    PlaceSortField,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def radius_bbox(radius_km: float) -> tuple[float, float, float, float]:
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * math.cos(math.radians(settings.MAP_CENTER_LAT)))
    return (
        settings.MAP_CENTER_LAT - lat_delta,
        settings.MAP_CENTER_LAT + lat_delta,
        settings.MAP_CENTER_LNG - lng_delta,
        settings.MAP_CENTER_LNG + lng_delta,
    )


def settlement_bbox() -> tuple[float, float, float, float]:
    return radius_bbox(8.0)


def district_bbox() -> tuple[float, float, float, float]:
    return radius_bbox(settings.MAP_SYNC_RADIUS_KM)


def normalize_place_pagination(
    *,
    page: int,
    page_size: int,
    total: int,
    offset: int | None = None,
) -> tuple[int, int, int, int, bool, bool]:
    """Return clamped pagination metadata for place search."""
    return normalize_pagination(
        page=page,
        page_size=page_size,
        total=total,
        offset=offset,
        max_page_size=MAX_PAGE_SIZE,
    )


def apply_bbox_filter(query: Any, params: PlaceSearchParams) -> Any:
    if all(v is not None for v in (params.south, params.west, params.north, params.east)):
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


def apply_search_sort(query: Any, *, sort_by: PlaceSortField) -> Any:
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

        if params.scope:
            query = query.where(Place.scope == params.scope)
        elif not params.district and params.category not in LODGING_CATEGORIES:
            query = query.where(Place.scope == VILLAGE)

        query = apply_bbox_filter(query, params)

        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
        page, offset, page_size, total_pages, has_prev, has_next = normalize_place_pagination(
            page=params.page,
            page_size=params.page_size,
            total=total,
            offset=params.offset,
        )
        result = await db.execute(
            apply_search_sort(query, sort_by=params.sort_by).offset(offset).limit(page_size)
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
