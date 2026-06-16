"""Event service schemas and errors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models.enums import EventCategory, EventRegion
from app.utils.errors import ServiceError


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
