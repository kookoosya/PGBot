"""Aggregated «Сегодня в посёлке» snapshot for the landing page."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus, EventRegion
from app.models.place import Place, PlaceReview
from app.models.taxi import TaxiService
from app.schemas.today import TodayResponse
from app.services.datetime_utils import format_event_datetime
from app.services.event_service import (
    event_category_label,
    event_region_label,
    get_upcoming_events,
)
from app.services.map_routes import MAP_ROUTES
from app.services.weather_service import WeatherFetchError, WeatherSnapshot, get_weather

logger = logging.getLogger(__name__)

TODAY_CACHE_TTL_SECONDS = 300


@dataclass(frozen=True, slots=True)
class TodayEventRow:
    id: int
    title: str
    starts_at_label: str
    ends_at_label: str | None
    location: str | None
    region_label: str
    category_label: str
    description: str | None
    source_url: str | None


@dataclass(frozen=True, slots=True)
class TodaySnapshot:
    weather: WeatherSnapshot | None
    latest_classified_id: int | None
    latest_classified_title: str | None
    latest_classified_category_label: str | None
    latest_classified_created_at: str | None
    total_places: int
    total_reviews: int
    active_taxi_count: int
    route_count: int
    upcoming_events: list[TodayEventRow]
    updated_at: datetime

    def to_response(self) -> TodayResponse:
        from app.schemas.today import TodayClassifiedSnippet, TodayEventSnippet, TodayMapSnippet

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
            upcoming_events=[
                TodayEventSnippet(
                    id=event.id,
                    title=event.title,
                    starts_at_label=event.starts_at_label,
                    ends_at_label=event.ends_at_label,
                    location=event.location,
                    region_label=event.region_label,
                    category_label=event.category_label,
                    description=event.description,
                    source_url=event.source_url,
                )
                for event in self.upcoming_events
            ],
            updated_at=self.updated_at.isoformat(),
            cache_ttl_seconds=TODAY_CACHE_TTL_SECONDS,
        )


async def build_today_snapshot(
    db: AsyncSession,
    *,
    event_region: EventRegion | None = None,
) -> TodaySnapshot:
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
        result = await db.execute(
            select(ClassifiedAd)
            .where(
                ClassifiedAd.is_active.is_(True),
                ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
            )
            .order_by(ClassifiedAd.created_at.desc())
            .limit(1)
        )
        ad = result.scalar_one_or_none()
        if ad:
            latest_id = ad.id
            latest_title = ad.title
            latest_category = CLASSIFIED_LABELS.get(ad.category, str(ad.category))
            latest_created = ad.created_at.isoformat()
    except Exception:
        logger.exception("Today snapshot: failed to load latest classified")

    total_places = 0
    total_reviews = 0
    active_taxi_count = 0
    route_count = len(MAP_ROUTES)
    try:
        total_places = (
            await db.execute(select(func.count(Place.id)).where(Place.is_active.is_(True)))
        ).scalar() or 0
        total_reviews = (await db.execute(select(func.count(PlaceReview.id)))).scalar() or 0
        active_taxi_count = (
            await db.execute(
                select(func.count(TaxiService.id)).where(TaxiService.is_active.is_(True))
            )
        ).scalar() or 0
    except Exception:
        logger.exception("Today snapshot: failed to load map stats")

    upcoming: list[TodayEventRow] = []
    try:
        events = await get_upcoming_events(db, limit=6, region=event_region)
        upcoming = [
            TodayEventRow(
                id=event.id,
                title=event.title,
                starts_at_label=format_event_datetime(event.starts_at),
                ends_at_label=format_event_datetime(event.ends_at) if event.ends_at else None,
                location=event.location,
                region_label=event_region_label(event.region),
                category_label=event_category_label(event.category),
                description=event.description,
                source_url=event.source_url,
            )
            for event in events
        ]
    except Exception:
        logger.exception("Today snapshot: failed to load upcoming events")

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
        upcoming_events=upcoming,
        updated_at=datetime.now(timezone.utc),
    )
