"""Форматирование афиши для VK-бота."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_service import (
    event_category_label,
    event_region_label,
    get_upcoming_events,
)
from app.services.site_urls import public_site_url
from app.utils.datetime import format_event_datetime


async def format_events_message(db: AsyncSession, *, limit: int = 6) -> str:
    """Список ближайших событий для команды «Афиша»."""
    events = await get_upcoming_events(db, limit=limit, mix_categories=True)
    site = public_site_url()
    if not events:
        return (
            "📅 Афиша пока пуста.\n\n"
            "Концерты, праздники и кино появятся после синхронизации.\n"
            f"Следите на сайте:\n{site}/events"
        )

    lines = [f"📅 Ближайшие события ({len(events)}):\n"]
    for event in events:
        when = format_event_datetime(event.starts_at)
        cat = event_category_label(event.category)
        region = event_region_label(event.region)
        loc = f" · {event.location}" if event.location else ""
        lines.append(f"• {when} — {event.title}")
        lines.append(f"  {cat} · {region}{loc}")

    lines.append(f"\nВся афиша: {site}/events")
    return "\n".join(lines)


async def format_events_digest_lines(db: AsyncSession, *, limit: int = 3) -> list[str]:
    """Короткий блок афиши для ежедневной сводки."""
    events = await get_upcoming_events(db, limit=limit, mix_categories=True)
    if not events:
        return []

    lines = ["📅 Ближайшие события:"]
    for event in events:
        when = format_event_datetime(event.starts_at)
        lines.append(f"• {when} — {event.title}")
    lines.append(f"→ {public_site_url()}/events")
    return lines
