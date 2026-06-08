"""Weather for Pushkinskie Gory via Open-Meteo (free, no API key).

Public API
----------
- ``get_weather`` — cached snapshot for site and VK bot
- ``format_weather_vk_current`` / ``format_weather_vk_hourly`` — bot text formatters

Data refreshes automatically via in-memory TTL cache and a background pre-warm task.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict
from zoneinfo import ZoneInfo

import httpx

from app.config import get_settings
from app.schemas.weather import (
    WeatherCurrent,
    WeatherHourlyItem,
    WeatherResponse,
)
from app.services.service_errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
LOCATION_NAME = "Пушкинские Горы"

# WMO weather interpretation codes (Open-Meteo)
WEATHER_META: dict[int, tuple[str, str]] = {
    0: ("Ясно", "☀️"),
    1: ("Преимущественно ясно", "🌤"),
    2: ("Переменная облачность", "⛅"),
    3: ("Пасмурно", "☁️"),
    45: ("Туман", "🌫"),
    48: ("Изморозь", "🌫"),
    51: ("Морось", "🌦"),
    53: ("Морось", "🌦"),
    55: ("Морось", "🌦"),
    56: ("Ледяная морось", "🌧"),
    57: ("Ледяная морось", "🌧"),
    61: ("Дождь", "🌧"),
    63: ("Дождь", "🌧"),
    65: ("Ливень", "🌧"),
    66: ("Ледяной дождь", "🌧"),
    67: ("Ливень", "🌧"),
    71: ("Снег", "🌨"),
    73: ("Снег", "🌨"),
    75: ("Снегопад", "❄️"),
    77: ("Снежная крупа", "❄️"),
    80: ("Ливень", "🌦"),
    81: ("Ливень", "🌦"),
    82: ("Сильный ливень", "⛈"),
    85: ("Снег", "🌨"),
    86: ("Снегопад", "❄️"),
    95: ("Гроза", "⛈"),
    96: ("Гроза с градом", "⛈"),
    99: ("Гроза с градом", "⛈"),
}


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


_cache: WeatherSnapshot | None = None
_cache_at: float = 0.0
_cache_lock = asyncio.Lock()


def weather_meta(code: int | None) -> WeatherMeta:
    """Map WMO code to Russian label and emoji."""
    description, icon = WEATHER_META.get(int(code or 0), ("Неизвестно", "🌡"))
    return {"description": description, "icon": icon}


def _parse_iso_time(value: str, tz: ZoneInfo) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


    now = datetime.now(tz)
    if dt.date() == now.date():
        return dt.strftime("%H:%M")
    tomorrow = now.date().toordinal() + 1 == dt.date().toordinal()
    if tomorrow:
        return f"завтра {dt.strftime('%H:%M')}"
    weekday = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"][dt.weekday()]
    return f"{weekday} {dt.strftime('%H:%M')}"


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


def format_weather_vk_current(snapshot: WeatherSnapshot) -> str:
    """Compact VK message — current conditions + next 6 hours."""
    cur = snapshot.current
    lines = [
        f"{cur.icon} {snapshot.location_name}",
        f"Сейчас: {cur.temperature:+.0f}°C (ощущается {cur.apparent_temperature:+.0f}°C)",
        f"{cur.description} · влажность {cur.humidity}% · ветер {cur.wind_speed:.0f} м/с",
    ]
    if cur.precipitation > 0:
        lines.append(f"Осадки сейчас: {cur.precipitation:.1f} мм")

    if snapshot.hourly:
        lines.append("")
        lines.append("Ближайшие часы:")
        for hour in snapshot.hourly[:6]:
            precip = ""
            if hour.precipitation > 0:
                precip = f", {hour.precipitation:.1f} мм"
            elif hour.precipitation_probability:
                precip = f", дождь {hour.precipitation_probability}%"
            lines.append(
                f"{hour.hour_label}: {hour.icon} {hour.temperature:+.0f}°C{precip}"
            )

    lines.append("")
    lines.append("«Почасовая погода» — прогноз на сутки")
    return "\n".join(lines)


def format_weather_vk_hourly(snapshot: WeatherSnapshot, *, hours: int = 24) -> str:
    """Detailed VK message — hourly forecast."""
    cur = snapshot.current
    lines = [
        f"🕐 Почасовой прогноз · {snapshot.location_name}",
        f"Сейчас: {cur.icon} {cur.temperature:+.0f}°C · {cur.description}",
        "",
    ]

    for hour in snapshot.hourly[:hours]:
        parts = [f"{hour.hour_label}: {hour.icon} {hour.temperature:+.0f}°C"]
        if hour.apparent_temperature != hour.temperature:
            parts.append(f"(ощ. {hour.apparent_temperature:+.0f}°C)")
        if hour.precipitation > 0:
            parts.append(f"осадки {hour.precipitation:.1f} мм")
        elif hour.precipitation_probability:
            parts.append(f"дождь {hour.precipitation_probability}%")
        if hour.wind_speed >= 4:
            parts.append(f"ветер {hour.wind_speed:.0f} м/с")
        lines.append(" · ".join(parts))

    lines.append("")
    lines.append(f"Обновлено: {snapshot.updated_at.strftime('%d.%m %H:%M')}")
    return "\n".join(lines)


def looks_like_hourly_weather(text_lower: str) -> bool:
    """Detect requests for detailed hourly forecast in VK."""
    markers = (
        "почасов",
        "по часам",
        "на завтра",
        "на сутки",
        "на 24",
        "прогноз на",
        "на день",
    )
    return any(marker in text_lower for marker in markers)
