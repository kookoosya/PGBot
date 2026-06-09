#!/usr/bin/env python3
"""Seed demo village events when the feed is empty (idempotent)."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.event_service import EventCreateInput, create_event, get_upcoming_events

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

DEMO_EVENTS: list[dict] = [
    {
        "title": "Экскурсия «Михайловское — усадьба Пушкина»",
        "description": "Пешеходная экскурсия по музею-заповеднику. Для жителей и гостей Пушкинских Гор.",
        "days_from_now": 2,
        "hour": 11,
        "duration_hours": 2,
        "location": "Музей-заповедник А.С. Пушкина, Михайловское",
        "region": EventRegion.PUSHKIN_GORY,
        "category": EventCategory.CULTURE,
        "source": "manual",
        "source_url": "https://pushkin.ellink.ru/",
    },
    {
        "title": "Пушкинский вечер у Оленьих вод",
        "description": "Литературно-музыкальная программа в Пушкинском заповеднике.",
        "days_from_now": 5,
        "hour": 18,
        "duration_hours": 2,
        "location": "Пушкинские Горы, НКЦ",
        "region": EventRegion.PUSHKIN_GORY,
        "category": EventCategory.HOLIDAY,
        "source": "manual",
    },
    {
        "title": "Ярмарка местных мастеров",
        "description": "Сувениры, мёд, изделия ремесленников — для туристов и жителей.",
        "days_from_now": 9,
        "hour": 10,
        "duration_hours": 6,
        "location": "Пушкинские Горы, центр посёлка",
        "region": EventRegion.PUSHKIN_GORY,
        "category": EventCategory.TOURISM,
        "source": "manual",
    },
    {
        "title": "Кино в Пскове — премьера недели",
        "description": "Актуальный сеанс в городском кинотеатре. Удобно совместить с поездкой из Пушкинских Гор.",
        "days_from_now": 3,
        "hour": 19,
        "duration_hours": 2,
        "location": "Псков, кинотеатр",
        "region": EventRegion.PSKOV,
        "category": EventCategory.CINEMA,
        "source": "manual",
        "source_url": "https://kudago.com/pskov/",
    },
    {
        "title": "Концерт в Псковском кремле",
        "description": "Живая музыка и вечерняя программа для гостей города.",
        "days_from_now": 7,
        "hour": 19,
        "duration_hours": 2,
        "location": "Псков, Кремль",
        "region": EventRegion.PSKOV,
        "category": EventCategory.CULTURE,
        "source": "manual",
        "source_url": "https://kudago.com/pskov/",
    },
]


async def _try_kudago_sync(db: AsyncSession) -> int:
    """Best-effort KudaGo import; returns created count."""
    try:
        from app.services.kudago_service import sync_events_from_kudago

        result = await sync_events_from_kudago(db, EventRegion.PSKOV)
        return result.created
    except Exception:
        logger.warning("KudaGo sync during seed skipped", exc_info=True)
        return 0


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        upcoming = await get_upcoming_events(db, limit=6)
        if len(upcoming) >= 3:
            logger.info("Events seed skipped: %s upcoming events already", len(upcoming))
            return

        kudago_created = await _try_kudago_sync(db)
        await db.commit()

        upcoming = await get_upcoming_events(db, limit=6)
        if len(upcoming) >= 3:
            logger.info("Events seed done via KudaGo (+%s)", kudago_created)
            return

        now = datetime.now(MOSCOW_TZ)
        created = 0
        for item in DEMO_EVENTS:
            starts_at = (now + timedelta(days=item["days_from_now"])).replace(
                hour=item["hour"], minute=0, second=0, microsecond=0,
            )
            ends_at = starts_at + timedelta(hours=item.get("duration_hours", 2))
            existing = await db.execute(select(Event).where(Event.title == item["title"]))
            if existing.scalar_one_or_none():
                continue
            await create_event(
                db,
                EventCreateInput(
                    title=item["title"],
                    description=item["description"],
                    starts_at=starts_at,
                    ends_at=ends_at,
                    location=item["location"],
                    region=item["region"],
                    category=item["category"],
                    source=item.get("source", "manual"),
                    source_url=item.get("source_url"),
                    is_published=True,
                ),
            )
            created += 1

        await db.commit()
        total = await db.scalar(select(func.count()).select_from(Event).where(Event.is_published.is_(True)))
        logger.info("Events seed: +%s demo, total published=%s", created, total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
