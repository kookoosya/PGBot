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
    region: EventRegion = EventRegion.PUSHKIN_GORY
    category: EventCategory
    source: Optional[str]
    source_url: Optional[str]
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
    is_published: Optional[bool] = None


def _validate_event_times(starts_at: datetime, ends_at: Optional[datetime]) -> None:
    if ends_at is not None and ends_at < starts_at:
        raise EventValidationError("Дата окончания не может быть раньше начала")


async def get_upcoming_events(db: AsyncSession, *, limit: int = 6) -> list[Event]:
    """Return published events that haven't ended yet, nearest first (both regions)."""
    now = datetime.now(timezone.utc)
    safe_limit = max(1, min(limit, 20))
    try:
        result = await db.execute(
            select(Event)
            .where(
                Event.is_published.is_(True),
                or_(Event.ends_at.is_(None), Event.ends_at >= now),
                Event.starts_at >= now - timedelta(days=1),
            )
            .order_by(Event.starts_at.asc())
            .limit(safe_limit)
        )
        return list(result.scalars().all())
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


async def create_event(
    db: AsyncSession,
    data: EventCreateInput,
    *,
    actor_id: int | None = None,
) -> Event:
    """Create and persist a new village event."""
    _validate_event_times(data.starts_at, data.ends_at)
    event = Event(
        title=data.title.strip(),
        description=(data.description or "").strip() or None,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        location=(data.location or "").strip() or None,
        region=data.region.value,
        category=data.category.value,
        source=(data.source or "manual").strip() or "manual",
        source_url=(data.source_url or "").strip() or None,
        is_published=data.is_published,
    )
    db.add(event)
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
        "source": event.source,
        "source_url": event.source_url,
        "is_published": event.is_published,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


def build_event_list_response(events: list[Event]) -> dict:
    """Convert event ORM rows to admin list API payload."""
    from app.schemas.event import EventListResponse, EventResponse

    return EventListResponse(
        items=[EventResponse(**event_to_response(event)) for event in events],
        total=len(events),
    ).model_dump()
