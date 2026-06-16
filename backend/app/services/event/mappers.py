"""Event API response mappers."""

from __future__ import annotations

from app.models.enums import EVENT_CATEGORY_LABELS, EVENT_REGION_LABELS, EventCategory, EventRegion
from app.models.event import Event
from app.utils.datetime import format_event_datetime


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
