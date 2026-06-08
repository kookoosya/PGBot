"""Aggregated «Сегодня в посёлке» snapshot for the landing page."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CLASSIFIED_LABELS
from app.schemas.today import TodayResponse
from app.services.classified_service import ClassifiedSearchParams, search_classifieds
from app.services.place_service import get_map_stats
from app.services.weather_service import WeatherFetchError, WeatherSnapshot, get_weather

logger = logging.getLogger(__name__)

TODAY_CACHE_TTL_SECONDS = 300


@dataclass(frozen=True, slots=True)
class TodaySnapshot:
    """Landing dashboard payload assembled from existing services."""

    weather: Optional[WeatherSnapshot]
    latest_classified_id: Optional[int]
    latest_classified_title: Optional[str]
    latest_classified_category_label: Optional[str]
    latest_classified_created_at: Optional[str]
    total_places: int
    total_reviews: int
    active_taxi_count: int
    route_count: int
    updated_at: datetime

    def to_response(self) -> TodayResponse:
        from app.schemas.today import TodayClassifiedSnippet, TodayMapSnippet

        latest = None
        if self.latest_classified_id is not None and self.latest_classified_title:
            latest = TodayClassifiedSnippet(
                id=self.latest_classified_id,
                title=self.latest_classified_title,
                category_label=self.latest_classified_category_label or "",
                created_at=self.latest_classified_created_at or "",
            )

        return TodayResponse(
            weather=self.weather.to_response() if self.weather else None,
            latest_classified=latest,
            map=TodayMapSnippet(
                total_places=self.total_places,
                total_reviews=self.total_reviews,
                active_taxi_count=self.active_taxi_count,
                route_count=self.route_count,
            ),
            updated_at=self.updated_at.isoformat(),
            cache_ttl_seconds=TODAY_CACHE_TTL_SECONDS,
        )


async def build_today_snapshot(db: AsyncSession) -> TodaySnapshot:
    """Compose weather, latest classified ad and map stats for the public landing block."""
    weather: WeatherSnapshot | None = None
    try:
        weather = await get_weather()
    except WeatherFetchError:
        logger.warning("Today snapshot: weather unavailable")

    latest_id: int | None = None
    latest_title: str | None = None
    latest_category: str | None = None
    latest_created: str | None = None

    try:
        classified = await search_classifieds(
            db,
            ClassifiedSearchParams(page=1, page_size=1, sort_by="created_at", sort_order="desc"),
        )
        if classified.items:
            ad = classified.items[0]
            latest_id = ad.id
            latest_title = ad.title
            latest_category = CLASSIFIED_LABELS.get(ad.category, str(ad.category))
            latest_created = ad.created_at.isoformat()
    except Exception:
        logger.exception("Today snapshot: failed to load latest classified")

    total_places = 0
    total_reviews = 0
    active_taxi_count = 0
    route_count = 0
    try:
        stats = await get_map_stats(db)
        total_places = stats.total_places
        total_reviews = stats.total_reviews
        active_taxi_count = stats.active_taxi_count
        route_count = stats.route_count
    except Exception:
        logger.exception("Today snapshot: failed to load map stats")

    return TodaySnapshot(
        weather=weather,
        latest_classified_id=latest_id,
        latest_classified_title=latest_title,
        latest_classified_category_label=latest_category,
        latest_classified_created_at=latest_created,
        total_places=total_places,
        total_reviews=total_reviews,
        active_taxi_count=active_taxi_count,
        route_count=route_count,
        updated_at=datetime.now(timezone.utc),
    )
