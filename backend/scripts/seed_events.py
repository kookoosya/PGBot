#!/usr/bin/env python3
"""Seed demo village events when the feed is thin (idempotent)."""

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
MIN_UPCOMING = int(os.getenv("EVENTS_SEED_MIN_UPCOMING", "5"))

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
    {
        "title": "Святогорский монастырь — экскурсия и хоровой концерт",
        "description": "Программа для паломников и туристов: история обители и живая музыка.",
        "days_from_now": 4,
        "hour": 12,
        "duration_hours": 2,
        "location": "Святогорский монастырь, Пушкинские Горы",
        "region": EventRegion.PUSHKIN_GORY,
        "category": EventCategory.CULTURE,
        "source": "manual",
    },
    {
        "title": "Летний кинопоказ под открытым небом",
        "description": "Семейный вечер у музея-заповедника: классика советского кино на большом экране.",
        "days_from_now": 6,
        "hour": 21,
        "duration_hours": 2,
        "location": "Пушкинские Горы, площадь у НКЦ",
        "region": EventRegion.PUSHKIN_GORY,
        "category": EventCategory.CINEMA,
        "source": "manual",
    },
    {
        "title": "Псковский джазовый вечер",
        "description": "Концерт местных и приглашённых музыкантов в историческом центре города.",
        "days_from_now": 10,
        "hour": 19,
        "duration_hours": 3,
        "location": "Псков, набережная реки Великой",
        "region": EventRegion.PSKOV,
        "category": EventCategory.CULTURE,
        "source": "manual",
    },
]


async def _try_kudago_sync(db: AsyncSession) -> int:
    """Best-effort KudaGo import; returns created count (0 if API unavailable)."""
    try:
        from app.services.kudago_service import sync_events_from_kudago

        result = await sync_events_from_kudago(db, EventRegion.PSKOV)
        if result.errors:
            logger.info("KudaGo sync skipped: %s", "; ".join(result.errors))
        return result.created
    except Exception as exc:
        logger.info("KudaGo sync during seed skipped: %s", exc)
        return 0


async def _insert_demo_events(db: AsyncSession) -> int:
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
                genre=item.get("genre"),
                source=item.get("source", "manual"),
                source_url=item.get("source_url"),
                is_published=True,
            ),
        )
        created += 1
    return created


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        upcoming = await get_upcoming_events(db, limit=20)

        kudago_created = 0
        if len(upcoming) < MIN_UPCOMING:
            kudago_created = await _try_kudago_sync(db)
            await db.commit()
            upcoming = await get_upcoming_events(db, limit=20)

        created = await _insert_demo_events(db)
        await db.commit()
        total = await db.scalar(select(func.count()).select_from(Event).where(Event.is_published.is_(True)))
        upcoming_after = await get_upcoming_events(db, limit=20)
        logger.info(
            "Events seed: +%s demo, upcoming=%s, total published=%s",
            created,
            len(upcoming_after),
            total,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
