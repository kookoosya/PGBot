"""Batch re-enrichment of events in DB — runs after sync and on schedule."""

from __future__ import annotations

import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.cinema_catalog import is_generic_cinema_title, lookup_film
from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.event_enrichment_service import MIN_DESCRIPTION_LEN, enrich_event_fields
from app.services.poster_service import fetch_kinopoisk_poster, resolve_event_poster

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


async def refresh_cinema_posters(db: AsyncSession, *, limit: int = 50) -> int:
    """Re-fetch official Kinopoisk posters for cinema (fixes wrong matches)."""
    result = await db.execute(
        select(Event).where(
            Event.is_published.is_(True),
            Event.category == EventCategory.CINEMA.value,
        ).limit(limit)
    )
    updated = 0
    for event in result.scalars().all():
        poster = await fetch_kinopoisk_poster(event.title)
        if poster and poster != event.poster_url:
            event.poster_url = poster
            updated += 1
    if updated:
        await db.flush()
        logger.info("Cinema poster refresh: updated %s events", updated)
    return updated
