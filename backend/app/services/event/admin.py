"""Admin event CRUD."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.audit import log_action
from app.services.event_enrichment_service import enrich_event_fields, resolve_cinema_location_from_text
from app.services.poster_service import resolve_event_poster

from .schemas import EventCreateInput, EventUpdateInput, EventValidationError

logger = logging.getLogger(__name__)


async def _attach_event_poster(event: Event, *, vk_poster_url: str | None = None) -> None:
    if (event.poster_url or "").strip():
        return
    poster = await resolve_event_poster(
        title=event.title,
        category=event.category,
        vk_poster_url=vk_poster_url,
    )
    if poster:
        event.poster_url = poster


def _apply_event_enrichment(
    *,
    title: str,
    description: str | None,
    category: EventCategory,
    genre: str | None,
    location: str | None,
    region: EventRegion,
) -> tuple[str, str | None, str | None]:
    return enrich_event_fields(
        title=title,
        description=description,
        category=category,
        genre=genre,
        location=location,
        region=region,
    )


def _validate_event_times(starts_at, ends_at) -> None:
    if ends_at is not None and ends_at < starts_at:
        raise EventValidationError("Дата окончания не может быть раньше начала")


async def list_events_admin(
    db: AsyncSession,
    *,
    include_unpublished: bool = True,
    limit: int = 50,
) -> list[Event]:
    """Return events for the admin panel, newest first."""
    query = select(Event).order_by(Event.starts_at.desc()).limit(max(1, min(limit, 100)))
    if not include_unpublished:
        query = query.where(Event.is_published.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_event_by_id(db: AsyncSession, event_id: int) -> Event | None:
    """Load a single event by primary key."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    return result.scalar_one_or_none()


async def create_event(
    db: AsyncSession,
    data: EventCreateInput,
    *,
    actor_id: int | None = None,
) -> Event:
    """Create and persist a new village event."""
    _validate_event_times(data.starts_at, data.ends_at)
    location = (data.location or "").strip() or None
    if data.category == EventCategory.CINEMA and location:
        location = resolve_cinema_location_from_text(location, region=data.region) or location
    title, genre, description = _apply_event_enrichment(
        title=data.title.strip(),
        description=(data.description or "").strip() or None,
        category=data.category,
        genre=data.genre,
        location=location,
        region=data.region,
    )
    event = Event(
        title=title,
        description=description,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        location=location,
        region=data.region.value,
        category=data.category.value,
        genre=genre,
        poster_url=(data.poster_url or "").strip() or None,
        source=(data.source or "manual").strip() or "manual",
        source_url=(data.source_url or "").strip() or None,
        is_published=data.is_published,
    )
    db.add(event)
    await db.flush()
    await _attach_event_poster(event)
    if event.poster_url:
        await db.flush()
    if actor_id:
        await log_action(db, "create_event", "event", event.id, user_id=actor_id, details={"title": event.title})
    logger.info("Event #%s created: %s", event.id, event.title)
    return event


async def update_event(
    db: AsyncSession,
    event: Event,
    data: EventUpdateInput,
    *,
    actor_id: int | None = None,
) -> Event:
    """Apply partial updates to an existing event."""
    if data.title is not None:
        event.title = data.title.strip()
    if data.description is not None:
        event.description = data.description.strip() or None
    if data.genre is not None:
        event.genre = data.genre.strip() or None
    if data.poster_url is not None:
        event.poster_url = data.poster_url.strip() or None
    if data.starts_at is not None:
        event.starts_at = data.starts_at
    if data.ends_at is not None:
        event.ends_at = data.ends_at
    if data.location is not None:
        event.location = data.location.strip() or None
    if data.region is not None:
        event.region = data.region.value
    if data.category is not None:
        event.category = data.category.value
    if data.source is not None:
        event.source = data.source.strip() or None
    if data.source_url is not None:
        event.source_url = data.source_url.strip() or None
    if data.is_published is not None:
        event.is_published = data.is_published

    _validate_event_times(event.starts_at, event.ends_at)
    region = EventRegion(event.region)
    title, genre, description = _apply_event_enrichment(
        title=event.title,
        description=event.description,
        category=EventCategory(event.category),
        genre=event.genre,
        location=event.location,
        region=region,
    )
    event.title = title
    event.genre = genre
    event.description = description
    if event.category == EventCategory.CINEMA.value and event.location:
        event.location = resolve_cinema_location_from_text(event.location, region=region) or event.location
    await _attach_event_poster(event)
    await db.flush()
    if actor_id:
        await log_action(db, "update_event", "event", event.id, user_id=actor_id)
    return event
