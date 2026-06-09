"""Map statistics and dashboard aggregates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import PLACE_CATEGORY_LABELS
from app.models.place import Place
from app.schemas.place import MapStatsResponse

settings = get_settings()


@dataclass(frozen=True, slots=True)
class MapStatsResult:
    """Aggregated map dashboard statistics."""

    total_places: int
    by_category: dict[str, int]
    last_sync: datetime | None
    center_lat: float
    center_lng: float

    def to_response(self) -> MapStatsResponse:
        """Serialize to the public API schema."""
        return MapStatsResponse(
            total_places=self.total_places,
            by_category=self.by_category,
            last_sync=self.last_sync,
            center={"lat": self.center_lat, "lng": self.center_lng},
        )


async def get_map_stats(db: AsyncSession) -> MapStatsResult:
    """Collect map dashboard statistics for active places."""
    active_filter = Place.is_active.is_(True)
    total_places = (
        await db.execute(select(func.count(Place.id)).where(active_filter))
    ).scalar() or 0

    cat_rows = await db.execute(
        select(Place.category, func.count(Place.id)).where(active_filter).group_by(Place.category),
    )
    by_category = {
        PLACE_CATEGORY_LABELS.get(row[0], str(row[0])): row[1] for row in cat_rows.all()
    }
    last_sync = (await db.execute(select(func.max(Place.last_synced_at)))).scalar()

    return MapStatsResult(
        total_places=total_places,
        by_category=by_category,
        last_sync=last_sync,
        center_lat=settings.MAP_CENTER_LAT,
        center_lng=settings.MAP_CENTER_LNG,
    )
