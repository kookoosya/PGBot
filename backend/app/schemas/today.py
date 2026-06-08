"""«Сегодня в посёлке» public snapshot schemas."""

from pydantic import BaseModel, Field

from app.schemas.weather import WeatherResponse


class TodayClassifiedSnippet(BaseModel):
    id: int
    title: str
    category_label: str
    created_at: str


class TodayMapSnippet(BaseModel):
    total_places: int
    total_reviews: int
    active_taxi_count: int
    route_count: int


class TodayResponse(BaseModel):
    weather: WeatherResponse | None = None
    latest_classified: TodayClassifiedSnippet | None = None
    map: TodayMapSnippet
    updated_at: str
    cache_ttl_seconds: int = 300
