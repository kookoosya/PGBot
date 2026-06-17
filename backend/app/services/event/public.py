"""Public event queries — upcoming feed and search."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.cinema_enrichment import is_real_cinema_event
from app.services.event_dedupe_service import dedupe_display_events, group_events_by_show, polish_public_event_feed
from app.services.event_title_utils import normalize_event_title

logger = logging.getLogger(__name__)

_FESTIVAL_PROGRAM_RE = re.compile(r"бугровский\s+гарнец|гарнец", re.IGNORECASE)


def collapse_festival_program_feed(events: list[Event]) -> list[Event]:
    """Keep one representative per festival program URL in compact feeds."""
    by_url: dict[str, list[Event]] = {}
    passthrough: list[Event] = []

    for event in events:
        url = (event.source_url or "").strip()
        title = event.title or ""
        if (
            event.source == "pushkinland"
            and "/news/" in url.lower()
            and _FESTIVAL_PROGRAM_RE.search(title)
        ):
            by_url.setdefault(url, []).append(event)
        else:
            passthrough.append(event)

    collapsed: list[Event] = []
    for group in by_url.values():
        group.sort(key=lambda item: item.starts_at)
        collapsed.append(group[0])

    merged = collapsed + passthrough
    merged.sort(key=lambda item: item.starts_at)
    return merged


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


async def load_mixed_public_events(
    db: AsyncSession,
    *,
    limit: int,
    now: datetime | None = None,
) -> list[Event]:
    """Settlement-first mixed feed for the public events page."""
    moment = now or datetime.now(timezone.utc)
    safe_limit = max(1, min(limit, 80))
    pushkin_cap = max(safe_limit // 2, min(24, safe_limit))
    cinema_cap = min(12, max(4, safe_limit // 4))
    pushkin = await _load_upcoming_grouped(
        db,
        now=moment,
        limit=pushkin_cap,
        region=EventRegion.PUSHKIN_GORY,
    )
    pushkin = collapse_festival_program_feed(pushkin)
    cinema = await _load_upcoming_grouped(
        db,
        now=moment,
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
            now=moment,
            limit=pskov_other_cap,
            region=EventRegion.PSKOV,
            exclude_category=EventCategory.CINEMA,
        )
        pskov_other = [e for e in pskov_other if e.id not in used_ids]
    return (pushkin + pskov_other + cinema)[:safe_limit]


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
            if region in (None, EventRegion.PUSHKIN_GORY):
                grouped = collapse_festival_program_feed(grouped)
            return grouped[:safe_limit]

        pushkin_cap = max(4, safe_limit - 2)
        cinema_cap = 2
        pushkin = await _load_upcoming_grouped(
            db,
            now=now,
            limit=pushkin_cap,
            region=EventRegion.PUSHKIN_GORY,
        )
        pushkin = collapse_festival_program_feed(pushkin)
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
    source: str | None = None,
    search: str | None = None,
    limit: int = 30,
) -> list[Event]:
    """Return upcoming published events for the public events page."""
    now = datetime.now(timezone.utc)
    safe_limit = max(1, min(limit, 100 if category == EventCategory.CINEMA else 80))

    if region is None and category is None and not source and not search:
        return await load_mixed_public_events(db, limit=safe_limit, now=now)

    conditions = [
        Event.is_published.is_(True),
        or_(Event.ends_at.is_(None), Event.ends_at >= now),
        Event.starts_at >= now - timedelta(days=14),
    ]
    if region is not None:
        conditions.append(Event.region == region.value)
    if category is not None:
        conditions.append(Event.category == category.value)
    if source and source.strip():
        conditions.append(Event.source == source.strip().lower())
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
        .limit(safe_limit * 4)
    )
    events = polish_public_event_feed(list(result.scalars().all()))
    if category == EventCategory.CINEMA or region == EventRegion.PSKOV:
        events = [
            e for e in events
            if e.category != EventCategory.CINEMA.value
            or is_real_cinema_event(
                title=e.title,
                description=e.description,
                category=e.category,
                genre=e.genre,
                source=e.source,
                location=e.location,
            )
        ]
    if region in (None, EventRegion.PUSHKIN_GORY) and category is None:
        events = collapse_festival_program_feed(events)
    return events[:safe_limit]
