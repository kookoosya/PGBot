"""Village events — upcoming list and admin CRUD.

Public API
----------
- ``get_upcoming_events`` — public landing feed
- ``create_event`` / ``update_event`` / ``list_events_admin`` — admin CRUD
- ``event_to_response`` — API response mapper

Errors: ``EventNotFoundError``, ``EventValidationError`` (subclasses of ``ServiceError``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EVENT_CATEGORY_LABELS, EVENT_REGION_LABELS, EventCategory, EventRegion
from app.models.event import Event
from app.services.audit import log_action
from app.services.event_dedupe_service import dedupe_display_events, group_events_by_show
from app.services.event_title_utils import normalize_event_title
from app.services.event_enrichment_service import enrich_event_fields, resolve_cinema_location_from_text
from app.services.poster_service import resolve_event_poster
from app.services.datetime_utils import format_event_datetime
from app.services.service_errors import ServiceError

logger = logging.getLogger(__name__)


class EventNotFoundError(ServiceError):
    """Raised when an event cannot be found."""

    def __init__(self, detail: str = "Событие не найдено") -> None:
        super().__init__(detail, status_code=404)


class EventValidationError(ServiceError):
    """Raised when event input fails validation."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


@dataclass(frozen=True, slots=True)
class EventCreateInput:
    """Validated payload for creating a village event."""

    title: str
    description: Optional[str]
    starts_at: datetime
    ends_at: Optional[datetime]
    location: Optional[str]
    category: EventCategory
    source: Optional[str]
    source_url: Optional[str]
    region: EventRegion = EventRegion.PUSHKIN_GORY
    genre: Optional[str] = None
    poster_url: Optional[str] = None
    is_published: bool = True


@dataclass(frozen=True, slots=True)
class EventUpdateInput:
    """Partial update payload for a village event."""

    title: Optional[str] = None
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    region: Optional[EventRegion] = None
    category: Optional[EventCategory] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    genre: Optional[str] = None
    poster_url: Optional[str] = None
    is_published: Optional[bool] = None


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
    description: Optional[str],
    category: EventCategory,
    genre: Optional[str],
    location: Optional[str],
    region: EventRegion,
) -> tuple[str, Optional[str], Optional[str]]:
    return enrich_event_fields(
        title=title,
        description=description,
        category=category,
        genre=genre,
        location=location,
        region=region,
    )


def _validate_event_times(starts_at: datetime, ends_at: Optional[datetime]) -> None:
    if ends_at is not None and ends_at < starts_at:
        raise EventValidationError("Дата окончания не может быть раньше начала")


async def get_upcoming_events(
    db: AsyncSession,
    *,
    limit: int = 6,
    region: EventRegion | None = None,
) -> list[Event]:
    """Return published events that haven't ended yet, nearest first.

  When ``region`` is set, only events from that region are returned.
    """
    now = datetime.now(timezone.utc)
    safe_limit = max(1, min(limit, 20))
    conditions = [
        Event.is_published.is_(True),
        or_(Event.ends_at.is_(None), Event.ends_at >= now),
        Event.starts_at >= now - timedelta(days=14),
    ]
    if region is not None:
        conditions.append(Event.region == region.value)
    try:
        result = await db.execute(
            select(Event)
            .where(*conditions)
            .order_by(Event.starts_at.asc())
            .limit(safe_limit * 3)
        )
        events = dedupe_display_events(list(result.scalars().all()))
        events = group_events_by_show(events)
        return events[:safe_limit]
    except Exception:
        logger.exception("Failed to load upcoming events")
        raise


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


async def get_public_event_by_id(db: AsyncSession, event_id: int) -> Event | None:
    """Load a published event for the public detail page."""
    result = await db.execute(
        select(Event).where(Event.id == event_id, Event.is_published.is_(True))
    )
    return result.scalar_one_or_none()


async def get_related_event_sessions(db: AsyncSession, event: Event) -> list[Event]:
    """Other upcoming sessions with the same title and venue."""
    now = datetime.now(timezone.utc)
    title_key = normalize_event_title(event.title)
    loc_key = " ".join((event.location or "").lower().split())

    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.id != event.id,
            Event.region == event.region,
            Event.starts_at >= now - timedelta(days=1),
            or_(Event.ends_at.is_(None), Event.ends_at >= now),
        ).order_by(Event.starts_at.asc())
    )
    related: list[Event] = []
    for candidate in result.scalars().all():
        if normalize_event_title(candidate.title) != title_key:
            continue
        cand_loc = " ".join((candidate.location or "").lower().split())
        if loc_key and cand_loc and loc_key != cand_loc:
            continue
        related.append(candidate)
    return related[:12]


async def search_public_events(
    db: AsyncSession,
    *,
    region: EventRegion | None = None,
    category: EventCategory | None = None,
    search: str | None = None,
    limit: int = 30,
) -> list[Event]:
    """Return upcoming published events for the public events page."""
    now = datetime.now(timezone.utc)
    safe_limit = max(1, min(limit, 60))
    conditions = [
        Event.is_published.is_(True),
        or_(Event.ends_at.is_(None), Event.ends_at >= now),
        Event.starts_at >= now - timedelta(days=14),
    ]
    if region is not None:
        conditions.append(Event.region == region.value)
    if category is not None:
        conditions.append(Event.category == category.value)
    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                Event.title.ilike(term),
                Event.description.ilike(term),
                Event.genre.ilike(term),
            )
        )

    result = await db.execute(
        select(Event)
        .where(*conditions)
        .order_by(Event.starts_at.asc())
        .limit(safe_limit * 3)
    )
    events = dedupe_display_events(list(result.scalars().all()))
    return events[:safe_limit]


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


def event_category_label(category: str | None) -> str:
    """Return a human-readable label for an event category code."""
    if not category:
        return EVENT_CATEGORY_LABELS.get(EventCategory.OTHER, "Событие")
    try:
        return EVENT_CATEGORY_LABELS.get(EventCategory(category), category)
    except ValueError:
        return category


def event_region_label(region: str | None) -> str:
    """Return a human-readable label for an event region code."""
    if not region:
        return EVENT_REGION_LABELS.get(EventRegion.PUSHKIN_GORY, "Пушкинские Горы")
    try:
        return EVENT_REGION_LABELS.get(EventRegion(region), region)
    except ValueError:
        return region


def event_to_response(event: Event) -> dict:
    """Build API payload with formatted labels."""
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "starts_at_label": format_event_datetime(event.starts_at),
        "ends_at_label": format_event_datetime(event.ends_at) if event.ends_at else None,
        "location": event.location,
        "region": event.region,
        "region_label": event_region_label(event.region),
        "category": event.category,
        "category_label": event_category_label(event.category),
        "genre": event.genre,
        "poster_url": event.poster_url,
        "source": event.source,
        "source_url": event.source_url,
        "is_published": event.is_published,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def event_to_public_response(event: Event) -> dict:
    """Build public API payload without admin-only fields."""
    payload = event_to_response(event)
    for key in ("is_published", "created_at", "updated_at"):
        payload.pop(key, None)
    return payload


def build_event_list_response(events: list[Event]) -> dict:
    """Convert event ORM rows to admin list API payload."""
    from app.schemas.event import EventListResponse, EventResponse

    return EventListResponse(
        items=[EventResponse(**event_to_response(event)) for event in events],
        total=len(events),
    ).model_dump()
