"""Extensible event import sources — shared types and protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventCategory, EventRegion


@dataclass(frozen=True, slots=True)
class EventSyncResult:
    """Summary of a single source sync run."""

    source: str
    region: str
    fetched: int
    created: int
    updated: int
    skipped: int
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class FetchedEvent:
    """Normalized event payload from an external source before DB upsert."""

    title: str
    description: Optional[str]
    starts_at: datetime
    ends_at: Optional[datetime]
    location: Optional[str]
    region: EventRegion
    category: EventCategory
    source: str
    source_url: str
    genre: str | None = None
    poster_url: str | None = None


class EventSource(ABC):
    """Base class for event import adapters (VK, TimePad, KudaGo, …)."""

    name: str = "unknown"

    @abstractmethod
    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        """Load and normalize events from the external API (no DB writes)."""

    @abstractmethod
    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        """Fetch events and upsert into ``village_events``."""
