"""Weather API schemas (Open-Meteo snapshot)."""

from pydantic import BaseModel, Field


class WeatherCurrent(BaseModel):
    temperature: float
    apparent_temperature: float
    humidity: int
    precipitation: float
    wind_speed: float
    weather_code: int
    description: str
    icon: str
    time: str


class WeatherHourlyItem(BaseModel):
    time: str
    hour_label: str
    temperature: float
    apparent_temperature: float
    precipitation: float
    precipitation_probability: int | None = None
    humidity: int | None = None
    wind_speed: float
    weather_code: int
    description: str
    icon: str


class WeatherResponse(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    timezone: str
    updated_at: str
    current: WeatherCurrent
    hourly: list[WeatherHourlyItem] = Field(default_factory=list)
    cache_ttl_seconds: int = 1800
