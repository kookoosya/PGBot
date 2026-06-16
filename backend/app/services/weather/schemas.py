"""Weather service errors and snapshot types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict

from app.config import get_settings
from app.schemas.weather import WeatherCurrent, WeatherHourlyItem, WeatherResponse
from app.utils.errors import ServiceError

settings = get_settings()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LOCATION_NAME = "Пушкинские Горы"


class WeatherFetchError(ServiceError):
    """Failed to load weather from upstream provider."""

    def __init__(self, detail: str = "Не удалось загрузить прогноз погоды") -> None:
        super().__init__(detail, status_code=503)


class WeatherMeta(TypedDict):
    description: str
    icon: str


@dataclass(frozen=True, slots=True)
class WeatherSnapshot:
    """Normalized weather payload shared by API and VK formatters."""

    location_name: str
    latitude: float
    longitude: float
    timezone: str
    updated_at: datetime
    current: WeatherCurrent
    hourly: tuple[WeatherHourlyItem, ...]

    def to_response(self) -> WeatherResponse:
        return WeatherResponse(
            location_name=self.location_name,
            latitude=self.latitude,
            longitude=self.longitude,
            timezone=self.timezone,
            updated_at=self.updated_at.isoformat(),
            current=self.current,
            hourly=list(self.hourly),
            cache_ttl_seconds=settings.WEATHER_CACHE_TTL_SECONDS,
        )
