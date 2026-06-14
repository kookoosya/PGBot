#!/usr/bin/env python3
"""Re-enrich existing events with genre and cinema descriptions."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.enums import EventCategory
from app.models.event import Event
from app.services.cinema_enrichment import enrich_cinema_fields


async def enrich() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    updated = 0
    async with Session() as db:
        result = await db.execute(select(Event))
        for event in result.scalars().all():
            try:
                category = EventCategory(event.category)
            except ValueError:
                continue
            genre, description = enrich_cinema_fields(
                title=event.title,
                description=event.description,
                category=category,
                genre=event.genre,
                location=event.location,
            )
            if genre != event.genre or description != event.description:
                event.genre = genre
                event.description = description
                updated += 1
        await db.commit()
    print(f"Enriched {updated} events")


if __name__ == "__main__":
    asyncio.run(enrich())
