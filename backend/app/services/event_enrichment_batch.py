"""Batch re-enrichment of events in DB — runs after sync and on schedule."""

from __future__ import annotations

import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.cinema_catalog import is_generic_cinema_title, lookup_film
from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.event_enrichment_service import MIN_DESCRIPTION_LEN, enrich_event_fields
from app.services.poster_service import (
    _is_planetarium_event,
    fetch_kinopoisk_poster_for_event,
    is_real_poster_url,
    is_stock_gallery_poster,
    resolve_event_poster,
    strip_invalid_cinema_poster,
)

logger = logging.getLogger(__name__)


def _needs_enrichment(event: Event) -> bool:
    desc = (event.description or "").strip()
    if len(desc) < MIN_DESCRIPTION_LEN:
        return True
    try:
        if EventCategory(event.category) == EventCategory.CINEMA:
            if not event.genre:
                return True
            if is_generic_cinema_title(event.title):
                return True
    except ValueError:
        pass
    return False


async def recategorize_planetarium_from_cinema(db: AsyncSession, *, limit: int = 200) -> int:
    """Planetarium full-dome shows are culture, not commercial cinema."""
    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == EventCategory.CINEMA.value,
        ).limit(limit)
    )
    updated = 0
    for event in result.scalars().all():
        if _is_planetarium_event(event.title, event.location):
            event.category = EventCategory.CULTURE.value
            updated += 1
    if updated:
        await db.flush()
        logger.info("Recategorized %s planetarium events from cinema to culture", updated)
    return updated


async def recategorize_other_events(db: AsyncSession, *, limit: int = 100) -> int:
    """Move miscategorized Orbilet/VK events out of ``other``."""
    from app.services.event_sources.text_utils import infer_category_from_text

    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == EventCategory.OTHER.value,
        ).limit(limit)
    )
    updated = 0
    for event in result.scalars().all():
        inferred = infer_category_from_text(
            f"{event.title} {event.description or ''} {event.location or ''}"
        )
        if inferred != EventCategory.OTHER and inferred.value != event.category:
            event.category = inferred.value
            updated += 1
    if updated:
        await db.flush()
        logger.info("Recategorized %s events from other", updated)
    return updated


async def enrich_stale_events(db: AsyncSession) -> int:
    """Re-enrich published events with thin or missing metadata."""
    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            or_(
                Event.description.is_(None),
                Event.description == "",
            ),
        )
    )
    candidates = list(result.scalars().all())

    # Also pick events with short descriptions or cinema without genre.
    all_published = await db.execute(select(Event).where(Event.is_published.is_(True)))
    for event in all_published.scalars().all():
        if event not in candidates and _needs_enrichment(event):
            candidates.append(event)

    updated = 0
    for event in candidates:
        try:
            category = EventCategory(event.category)
            region = EventRegion(event.region)
        except ValueError:
            continue

        title, genre, description = enrich_event_fields(
            title=event.title,
            description=event.description,
            category=category,
            genre=event.genre,
            location=event.location,
            region=region,
        )

        changed = False
        if title != event.title:
            event.title = title
            changed = True
        if genre != event.genre:
            event.genre = genre
            changed = True
        if description != event.description:
            event.description = description
            changed = True

        if (
            category == EventCategory.CINEMA
            and is_generic_cinema_title(event.title)
            and not lookup_film(f"{event.title} {event.description or ''}")
        ):
            event.is_published = False
            changed = True

        if changed:
            updated += 1

    if updated:
        await db.flush()
        logger.info("Batch event enrichment: updated %s events", updated)
    return updated


async def enrich_missing_posters(db: AsyncSession, *, limit: int = 60) -> int:
    """Attach posters/images to published events that lack one."""
    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            or_(Event.poster_url.is_(None), Event.poster_url == ""),
        ).limit(limit)
    )
    updated = 0
    for event in result.scalars().all():
        poster = await resolve_event_poster(
            title=event.title,
            category=event.category,
        )
        if poster:
            event.poster_url = poster
            updated += 1
    if updated:
        await db.flush()
        logger.info("Batch poster enrichment: updated %s events", updated)
    return updated


async def strip_bad_cinema_posters(db: AsyncSession) -> int:
    """Drop gallery placeholders from cinema — they are not film posters."""
    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == EventCategory.CINEMA.value,
        )
    )
    cleared = 0
    for event in result.scalars().all():
        fixed = strip_invalid_cinema_poster(event.poster_url, category=event.category)
        if fixed != event.poster_url:
            event.poster_url = fixed
            cleared += 1
    if cleared:
        await db.flush()
        logger.info("Cleared %s bad cinema posters", cleared)
    return cleared


async def refresh_orbilet_posters(db: AsyncSession) -> int:
    """Attach official Orbilet promo images to imported sessions."""
    from app.services.orbilet_service import fetch_orbilet_events

    orbilet_items = await fetch_orbilet_events()
    if not orbilet_items:
        return 0

    by_session: dict[str, str] = {}
    by_title: dict[str, str] = {}
    for item in orbilet_items:
        if not item.poster_url:
            continue
        by_session[item.source_url.rstrip("/")] = item.poster_url
        key = " ".join(item.title.lower().split())
        by_title[key] = item.poster_url

    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.source == "orbilet",
        )
    )
    updated = 0
    for event in result.scalars().all():
        poster = None
        if event.source_url:
            poster = by_session.get(event.source_url.rstrip("/"))
        if not poster:
            poster = by_title.get(" ".join(event.title.lower().split()))
        if poster and poster != event.poster_url:
            event.poster_url = poster
            updated += 1
    if updated:
        await db.flush()
        logger.info("Orbilet poster refresh: updated %s events", updated)
    return updated


async def refresh_cinema_posters(db: AsyncSession, *, limit: int = 120) -> int:
    """Refresh cinema posters — Orbilet art first, Kinopoisk for commercial cinemas."""
    await refresh_orbilet_posters(db)

    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == EventCategory.CINEMA.value,
        ).limit(limit)
    )
    updated = 0
    for event in result.scalars().all():
        if not is_real_poster_url(event.poster_url, category=event.category):
            event.poster_url = None
            updated += 1
        if is_real_poster_url(event.poster_url, category=event.category):
            continue
        if event.source == "orbilet":
            continue
        poster = await fetch_kinopoisk_poster_for_event(
            event.title,
            location=event.location,
        )
        if poster and poster != event.poster_url:
            event.poster_url = poster
            updated += 1
    if updated:
        await db.flush()
        logger.info("Cinema poster refresh: updated %s events", updated)
    return updated
