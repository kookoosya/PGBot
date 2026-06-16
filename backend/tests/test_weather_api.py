"""Weather API — mocked Open-Meteo fetch."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.weather import WeatherCurrent, WeatherHourlyItem
from app.services.weather.schemas import WeatherSnapshot


def _sample_snapshot() -> WeatherSnapshot:
    now = datetime.now(timezone.utc)
    time_str = now.isoformat()
    return WeatherSnapshot(
        location_name="Пушкинские Горы",
        latitude=57.0267,
        longitude=28.91,
        timezone="Europe/Moscow",
        updated_at=now,
        current=WeatherCurrent(
            temperature=12.5,
            apparent_temperature=11.0,
            humidity=70,
            precipitation=0.0,
            wind_speed=3.2,
            weather_code=1,
            description="Переменная облачность",
            icon="⛅",
            time=time_str,
        ),
        hourly=(
            WeatherHourlyItem(
                time=time_str,
                hour_label="12:00",
                temperature=12.0,
                apparent_temperature=11.0,
                precipitation=0.0,
                precipitation_probability=10,
                humidity=68,
                wind_speed=3.0,
                weather_code=1,
                description="Облачно",
                icon="⛅",
            ),
        ),
    )


@pytest.mark.asyncio
@patch("app.api.v1.weather.get_weather", new_callable=AsyncMock)
async def test_weather_forecast_ok(mock_get: AsyncMock, client: AsyncClient):
    mock_get.return_value = _sample_snapshot()
    response = await client.get("/api/v1/weather")
    assert response.status_code == 200
    data = response.json()
    assert data["location_name"] == "Пушкинские Горы"
    assert data["current"]["temperature"] == 12.5
    assert len(data["hourly"]) == 1


@pytest.mark.asyncio
@patch("app.api.v1.weather.get_weather", new_callable=AsyncMock)
async def test_weather_forecast_upstream_error(mock_get: AsyncMock, client: AsyncClient):
    from app.services.weather_service import WeatherFetchError

    mock_get.side_effect = WeatherFetchError("upstream down")
    response = await client.get("/api/v1/weather")
    assert response.status_code == 503
