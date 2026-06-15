"""Monitor «Кино в Пскове» block — alert when no real films after sync."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cinema_enrichment import is_real_cinema_event
from app.services.event_service import get_upcoming_events
from app.services.notifications import notify_owner
from app.services.site_urls import public_site_url

logger = logging.getLogger(__name__)

MIN_REAL_CINEMA_FILMS = 1


async def count_real_cinema_in_feed(db: AsyncSession, *, limit: int = 20) -> int:
    """Count actual cinema screenings in the public upcoming-events feed."""
    events = await get_upcoming_events(db, limit=limit, mix_categories=True)
    count = 0
    for event in events:
        category = event.category.value if hasattr(event.category, "value") else str(event.category)
        if is_real_cinema_event(
            title=event.title,
            description=event.description,
            category=category,
            genre=getattr(event, "genre", None),
            source=getattr(event, "source", None),
            location=event.location,
        ):
            count += 1
    return count


async def check_cinema_block_and_alert(
    db: AsyncSession,
    *,
    notify: bool = True,
    min_films: int = MIN_REAL_CINEMA_FILMS,
) -> dict[str, object]:
    """
    Verify the cinema block has real films. Logs warning and notifies owner if empty.
    Returns summary dict for scripts and cron logs.
    """
    count = await count_real_cinema_in_feed(db)
    ok = count >= min_films
    summary: dict[str, object] = {
        "real_cinema_count": count,
        "min_required": min_films,
        "ok": ok,
    }

    if ok:
        logger.info("Cinema monitor OK: %s real film(s) in feed", count)
        return summary

    message = (
        f"⚠️ <b>Киноафиша пуста</b>\n"
        f"После синхронизации в блоке «Кино в Пскове» нет реальных фильмов "
        f"(найдено: {count}, нужно ≥ {min_films}).\n"
        f"Проверьте источники Kinopskov / Мираж / Silver / Orbilet.\n"
        f"🌐 {public_site_url()}/events"
    )
    logger.warning("Cinema monitor ALERT: %s real films (min %s)", count, min_films)

    if notify:
        try:
            await notify_owner(message)
        except Exception as exc:
            logger.error("Cinema alert notification failed: %s", exc)
            summary["notify_error"] = str(exc)

    return summary
