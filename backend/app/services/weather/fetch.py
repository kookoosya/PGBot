"""Open-Meteo fetch and in-memory cache."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings

from .meta import weather_meta
from .schemas import LOCATION_NAME, OPEN_METEO_URL, WeatherFetchError, WeatherSnapshot

logger = logging.getLogger(__name__)
settings = get_settings()

_cache: WeatherSnapshot | None = None
_cache_at: float = 0.0
_cache_lock = asyncio.Lock()


def _parse_iso_time(value: str, tz: ZoneInfo) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def _format_day_hour_label(dt: datetime, tz: ZoneInfo) -> str:
    now = datetime.now(tz)
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    tomorrow = now.date().toordinal() + 1 == dt.date().toordinal()
    if tomorrow:
        return f"завтра {dt.strftime('%H:%M')}"
    weekday = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"][dt.weekday()]
    return f"{weekday} {dt.strftime('%H:%M')}"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _build_snapshot(payload: dict[str, Any]) -> WeatherSnapshot:
    from app.schemas.weather import WeatherCurrent, WeatherHourlyItem

    tz_name = str(payload.get("timezone") or settings.WEATHER_TIMEZONE)
    tz = ZoneInfo(tz_name)
    current_raw = payload.get("current") or {}
    hourly_raw = payload.get("hourly") or {}

    code = _safe_int(current_raw.get("weather_code"))
    meta = weather_meta(code)
    current_time = _parse_iso_time(str(current_raw.get("time")), tz)

    current = WeatherCurrent(
        temperature=round(_safe_float(current_raw.get("temperature_2m")), 1),
        apparent_temperature=round(_safe_float(current_raw.get("apparent_temperature")), 1),
        humidity=_safe_int(current_raw.get("relative_humidity_2m")),
        precipitation=round(_safe_float(current_raw.get("precipitation")), 1),
        wind_speed=round(_safe_float(current_raw.get("wind_speed_10m")), 1),
        weather_code=code,
        description=meta["description"],
        icon=meta["icon"],
        time=current_time.isoformat(),
    )

    times = hourly_raw.get("time") or []
    hourly: list[WeatherHourlyItem] = []
    now = datetime.now(tz)

    for idx, time_str in enumerate(times):
        hour_dt = _parse_iso_time(str(time_str), tz)
        if hour_dt < now.replace(minute=0, second=0, microsecond=0):
            continue
        hour_code = _safe_int((hourly_raw.get("weather_code") or [None])[idx])
        hour_meta = weather_meta(hour_code)
        hourly.append(
            WeatherHourlyItem(
                time=hour_dt.isoformat(),
                hour_label=_format_day_hour_label(hour_dt, tz),
                temperature=round(
                    _safe_float((hourly_raw.get("temperature_2m") or [None])[idx]),
                    1,
                ),
                apparent_temperature=round(
                    _safe_float((hourly_raw.get("apparent_temperature") or [None])[idx]),
                    1,
                ),
                precipitation=round(
                    _safe_float((hourly_raw.get("precipitation") or [None])[idx]),
                    1,
                ),
                precipitation_probability=_safe_int(
                    (hourly_raw.get("precipitation_probability") or [None])[idx],
                    default=0,
                ) or None,
                humidity=_safe_int((hourly_raw.get("relative_humidity_2m") or [None])[idx]) or None,
                wind_speed=round(
                    _safe_float((hourly_raw.get("wind_speed_10m") or [None])[idx]),
                    1,
                ),
                weather_code=hour_code,
                description=hour_meta["description"],
                icon=hour_meta["icon"],
            )
        )
        if len(hourly) >= settings.WEATHER_HOURLY_HOURS:
            break

    return WeatherSnapshot(
        location_name=LOCATION_NAME,
        latitude=settings.MAP_CENTER_LAT,
        longitude=settings.MAP_CENTER_LNG,
        timezone=tz_name,
        updated_at=datetime.now(tz),
        current=current,
        hourly=tuple(hourly),
    )


async def _fetch_open_meteo() -> WeatherSnapshot:
    params = {
        "latitude": settings.MAP_CENTER_LAT,
        "longitude": settings.MAP_CENTER_LNG,
        "timezone": settings.WEATHER_TIMEZONE,
        "forecast_days": settings.WEATHER_FORECAST_DAYS,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
            ]
        ),
        "hourly": ",".join(
            [
                "temperature_2m",
                "apparent_temperature",
                "precipitation",
                "precipitation_probability",
                "weather_code",
                "relative_humidity_2m",
                "wind_speed_10m",
            ]
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        logger.exception("Open-Meteo request failed")
        raise WeatherFetchError() from exc

    if not payload.get("current") or not payload.get("hourly"):
        logger.error("Open-Meteo returned incomplete payload: %s", payload.keys())
        raise WeatherFetchError("Неполный ответ сервиса погоды")

    snapshot = _build_snapshot(payload)
    logger.debug(
        "Weather loaded: %s°C, %s hourly slots",
        snapshot.current.temperature,
        len(snapshot.hourly),
    )
    return snapshot


async def get_weather(*, force_refresh: bool = False) -> WeatherSnapshot:
    """Return cached weather snapshot, refreshing from Open-Meteo when stale."""
    global _cache, _cache_at

    async with _cache_lock:
        age = time.monotonic() - _cache_at
        if not force_refresh and _cache is not None and age < settings.WEATHER_CACHE_TTL_SECONDS:
            return _cache

        snapshot = await _fetch_open_meteo()
        _cache = snapshot
        _cache_at = time.monotonic()
        return snapshot


async def refresh_weather_cache() -> None:
    """Background pre-warm — keeps cache fresh without user-triggered fetches."""
    try:
        await get_weather(force_refresh=True)
    except WeatherFetchError:
        logger.warning("Weather cache refresh failed; stale data kept if available")
