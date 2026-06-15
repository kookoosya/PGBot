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


class TodayEventSnippet(BaseModel):
    id: int
    title: str
    starts_at: str
    starts_at_label: str
    ends_at_label: str | None = None
    location: str | None = None
    region: str
    region_label: str
    category: str
    category_label: str
    genre: str | None = None
    poster_url: str | None = None
    description: str | None = None
    source: str | None = None
    source_url: str | None = None


class TodayResponse(BaseModel):
    weather: WeatherResponse | None = None
    latest_classified: TodayClassifiedSnippet | None = None
    map: TodayMapSnippet
    upcoming_events: list[TodayEventSnippet] = Field(default_factory=list)
    updated_at: str
    cache_ttl_seconds: int = 300
