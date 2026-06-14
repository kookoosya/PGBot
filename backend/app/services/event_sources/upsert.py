"""Shared upsert logic for all event sources."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_service import EventCreateInput, EventUpdateInput, create_event, update_event
from app.services.event_sources.base import FetchedEvent
from app.services.event_sources.dedup import find_existing_event


async def upsert_fetched_event(
    db: AsyncSession,
    item: FetchedEvent,
    *,
    actor_id: int | None = None,
) -> str:
    """Create or update event. Returns ``created`` | ``updated`` | ``skipped``."""
    existing = await find_existing_event(
        db,
        source_url=item.source_url,
        title=item.title,
        starts_at=item.starts_at,
    )
    payload = EventCreateInput(
        title=item.title,
        description=item.description,
        starts_at=item.starts_at,
        ends_at=item.ends_at,
        location=item.location,
        region=item.region,
        category=item.category,
        genre=item.genre,
        source=item.source,
        source_url=item.source_url,
        is_published=True,
    )
    if existing:
        await update_event(
            db,
            existing,
            EventUpdateInput(
                title=payload.title,
                description=payload.description,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                location=payload.location,
                region=item.region,
                category=payload.category,
                genre=item.genre,
                source=item.source,
                source_url=item.source_url,
                is_published=True,
            ),
            actor_id=actor_id,
        )
        return "updated"
    await create_event(db, payload, actor_id=actor_id)
    return "created"
