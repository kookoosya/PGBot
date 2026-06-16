"""VK and digest weather text formatters."""

from __future__ import annotations

from .schemas import WeatherSnapshot


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


def format_weather_digest_lines(snapshot: WeatherSnapshot) -> list[str]:
    """Compact weather block for the daily VK digest."""
    cur = snapshot.current
    lines = [
        f"🌤 Сейчас: {cur.icon} {cur.temperature:+.0f}°C, {cur.description.lower()}",
        f"Ощущается {cur.apparent_temperature:+.0f}°C · ветер {cur.wind_speed:.0f} м/с",
    ]
    if snapshot.hourly:
        parts = [
            f"{hour.hour_label} {hour.icon}{hour.temperature:+.0f}°"
            for hour in snapshot.hourly[:4]
        ]
        lines.append("Ближайшие часы: " + " · ".join(parts))
    return lines
