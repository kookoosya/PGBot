"""Форматирование афиши для VK-бота."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.cinema_enrichment import is_real_cinema_event
from app.services.event_service import (
    event_category_label,
    event_region_label,
    get_upcoming_events,
    search_public_events,
)
from app.services.site_urls import public_site_url
from app.utils.datetime import format_event_datetime

DEFAULT_EVENTS_LIMIT = 6
DEFAULT_CINEMA_LIMIT = 8
INLINE_EVENT_BUTTONS = 2


def _event_category_value(event: Event) -> str:
    category = event.category
    return category.value if hasattr(category, "value") else str(category)


def _is_cinema_screening(event: Event) -> bool:
    return is_real_cinema_event(
        title=event.title,
        description=event.description,
        category=_event_category_value(event),
        genre=getattr(event, "genre", None),
        source=getattr(event, "source", None),
        location=event.location,
    )


def _event_detail_path(event: Event) -> str:
    return f"/events/{event.id}"


def _inline_event_label(event: Event, *, prefix: str = "📅") -> str:
    title = event.title.strip()
    if len(title) > 35:
        title = f"{title[:34]}…"
    return f"{prefix} {title}"


def events_inline_buttons(
    events: list[Event],
    *,
    max_buttons: int = INLINE_EVENT_BUTTONS,
    prefix: str = "📅",
) -> list[tuple[str, str]]:
    """Top events as inline keyboard paths (label, site path)."""
    buttons: list[tuple[str, str]] = []
    for event in events[:max_buttons]:
        buttons.append((_inline_event_label(event, prefix=prefix), _event_detail_path(event)))
    return buttons


def format_events_message_from_list(events: list[Event]) -> str:
    """Render upcoming events list for VK chat."""
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
        lines.append(f"  → {site}{_event_detail_path(event)}")

    lines.append(f"\nВся афиша: {site}/events")
    return "\n".join(lines)


async def load_upcoming_events_preview(
    db: AsyncSession,
    *,
    limit: int = DEFAULT_EVENTS_LIMIT,
) -> list[Event]:
    return await get_upcoming_events(db, limit=limit, mix_categories=True)


async def format_events_message(db: AsyncSession, *, limit: int = DEFAULT_EVENTS_LIMIT) -> str:
    """Список ближайших событий для команды «Афиша»."""
    events = await load_upcoming_events_preview(db, limit=limit)
    return format_events_message_from_list(events)


async def load_cinema_screenings(
    db: AsyncSession,
    *,
    limit: int = DEFAULT_CINEMA_LIMIT,
) -> list[Event]:
    """Upcoming real cinema screenings in Pskov."""
    raw = await search_public_events(
        db,
        region=EventRegion.PSKOV,
        category=EventCategory.CINEMA,
        limit=limit * 3,
    )
    films: list[Event] = []
    for event in raw:
        if not _is_cinema_screening(event):
            continue
        films.append(event)
        if len(films) >= limit:
            break
    return films


def format_cinema_message_from_list(films: list[Event]) -> str:
    site = public_site_url()
    if not films:
        return (
            "🎬 Кино в Пскове пока нет в афише.\n\n"
            "Расписание появится после синхронизации Kinopskov / Мираж / Silver / Orbilet.\n"
            f"Следите на сайте:\n{site}/events?region=pskov&category=cinema"
        )

    lines = [f"🎬 Кино в Пскове ({len(films)}):\n"]
    for event in films:
        when = format_event_datetime(event.starts_at)
        loc = f" · {event.location}" if event.location else ""
        genre = f" · {event.genre}" if event.genre else ""
        lines.append(f"• {when} — {event.title}{genre}")
        lines.append(f"  {loc.strip(' · ') if loc else 'Псков'}")
        lines.append(f"  → {site}{_event_detail_path(event)}")

    lines.append(f"\nВсе сеансы: {site}/events?region=pskov&category=cinema")
    return "\n".join(lines)


async def format_cinema_message(db: AsyncSession, *, limit: int = DEFAULT_CINEMA_LIMIT) -> str:
    """Список киносеансов для команды «Кино»."""
    films = await load_cinema_screenings(db, limit=limit)
    return format_cinema_message_from_list(films)


async def format_events_digest_lines(db: AsyncSession, *, limit: int = 3) -> list[str]:
    """Короткий блок афиши для ежедневной сводки."""
    events = await load_upcoming_events_preview(db, limit=limit)
    if not events:
        return []

    site = public_site_url()
    lines = ["📅 Ближайшие события:"]
    for event in events:
        when = format_event_datetime(event.starts_at)
        lines.append(f"• {when} — {event.title}")
        lines.append(f"  → {site}{_event_detail_path(event)}")
    lines.append(f"→ {site}/events")
    return lines
