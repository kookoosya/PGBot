"""Public weather endpoint — cached Open-Meteo data for Pushkinskie Gory."""

from fastapi import APIRouter

from app.core.service_http import raise_http_for_service_error
from app.schemas.weather import WeatherResponse
from app.services.weather_service import WeatherFetchError, get_weather

router = APIRouter()


@router.get("", response_model=WeatherResponse)
async def weather_forecast():
    """Current conditions and hourly forecast for the village center."""
    try:
        snapshot = await get_weather()
    except WeatherFetchError as exc:
        raise_http_for_service_error(exc)
    return snapshot.to_response()
