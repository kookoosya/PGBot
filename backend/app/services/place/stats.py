"""Map dashboard statistics and filter option lists."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import (
    MAP_REPORT_LABELS,
    PLACE_CATEGORY_LABELS,
    SHOP_COMPLAINT_LABELS,
    PlaceCategory,
    ShopComplaintType,
)
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.models.taxi import TaxiService
from app.services.map_routes import get_map_routes

from .schemas import EFFECTIVE_RATING, MapStatsResult

logger = logging.getLogger(__name__)
settings = get_settings()


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
            row[0].value: row[1]
            for row in cat_rows.all()
        }

        rating_rows = await db.execute(
            select(Place.category, func.avg(EFFECTIVE_RATING))
            .where(active_filter, EFFECTIVE_RATING > 0)
            .group_by(Place.category)
        )
        avg_rating_by_category = {
            row[0].value: round(float(row[1]), 1)
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
        auto_sync_hours=settings.MAP_AUTO_SYNC_HOURS if settings.MAP_AUTO_SYNC_HOURS > 0 else 6,
        yandex_live=bool(settings.YANDEX_MAPS_API_KEY),
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
