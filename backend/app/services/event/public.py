"""Public event queries — upcoming feed and search."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.cinema_enrichment import is_real_cinema_event
from app.services.event_dedupe_service import dedupe_display_events, group_events_by_show
from app.services.event_title_utils import normalize_event_title

logger = logging.getLogger(__name__)


def _upcoming_base_conditions(now: datetime) -> list:
    return [
        Event.is_published.is_(True),
        or_(Event.ends_at.is_(None), Event.ends_at >= now),
        Event.starts_at >= now - timedelta(days=14),
    ]


async def _load_upcoming_grouped(
    db: AsyncSession,
    *,
    now: datetime,
    limit: int,
    region: EventRegion | None = None,
    category: EventCategory | None = None,
    exclude_category: EventCategory | None = None,
) -> list[Event]:
    """Load deduplicated show groups for one slice of the feed."""
    conditions = _upcoming_base_conditions(now)
    if region is not None:
        conditions.append(Event.region == region.value)
    if category is not None:
        conditions.append(Event.category == category.value)
    if exclude_category is not None:
        conditions.append(Event.category != exclude_category.value)

    fetch_limit = max(limit * 4, 12)
    result = await db.execute(
        select(Event)
        .where(*conditions)
        .order_by(Event.starts_at.asc())
        .limit(fetch_limit)
    )
    events = dedupe_display_events(list(result.scalars().all()))
    if category == EventCategory.CINEMA:
        events = [
            e for e in events
            if is_real_cinema_event(
                title=e.title,
                description=e.description,
                category=e.category,
                genre=e.genre,
                source=e.source,
                location=e.location,
            )
        ]
    return group_events_by_show(events)[:limit]


async def get_upcoming_events(
    db: AsyncSession,
    *,
    limit: int = 6,
    region: EventRegion | None = None,
    mix_categories: bool = False,
) -> list[Event]:
    """Return published events that haven't ended yet, nearest first.

    When ``region`` is set, only events from that region are returned.
    """
    now = datetime.now(timezone.utc)
    safe_limit = max(1, min(limit, 20))
    try:
        if not mix_categories:
            grouped = await _load_upcoming_grouped(
                db,
                now=now,
                limit=safe_limit,
                region=region,
            )
            return grouped

        pushkin_cap = max(4, safe_limit - 2)
        cinema_cap = 2
        pushkin = await _load_upcoming_grouped(
            db,
            now=now,
            limit=pushkin_cap,
            region=EventRegion.PUSHKIN_GORY,
        )
        cinema = await _load_upcoming_grouped(
            db,
            now=now,
            limit=cinema_cap,
            region=EventRegion.PSKOV,
            category=EventCategory.CINEMA,
        )
        used_ids = {e.id for e in (*pushkin, *cinema)}
        pskov_other_cap = max(0, safe_limit - len(pushkin) - len(cinema))
        pskov_other: list[Event] = []
        if pskov_other_cap:
            pskov_other = await _load_upcoming_grouped(
                db,
                now=now,
                limit=pskov_other_cap,
                region=EventRegion.PSKOV,
                exclude_category=EventCategory.CINEMA,
            )
            pskov_other = [e for e in pskov_other if e.id not in used_ids]

        mixed = pushkin + pskov_other + cinema
        return mixed[:safe_limit]
    except Exception:
        logger.exception("Failed to load upcoming events")
        raise


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
    safe_limit = max(1, min(limit, 100 if category == EventCategory.CINEMA else 60))
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
