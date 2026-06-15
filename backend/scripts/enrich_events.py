#!/usr/bin/env python3
"""Re-enrich existing events with genre, titles and teaser descriptions."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.event_enrichment_batch import enrich_missing_posters, enrich_stale_events


async def enrich() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        updated = await enrich_stale_events(db)
        posters = await enrich_missing_posters(db, limit=80)
        await db.commit()
    print(f"Enriched {updated} events, posters {posters}")


if __name__ == "__main__":
    asyncio.run(enrich())
