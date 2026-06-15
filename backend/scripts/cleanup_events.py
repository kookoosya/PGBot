#!/usr/bin/env python3
"""Unpublish duplicate events and refresh posters."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.event_dedupe_service import cleanup_duplicate_events, unpublish_stale_demo_cinema
from app.services.event_enrichment_batch import (
    enrich_missing_posters,
    enrich_stale_events,
    refresh_cinema_posters,
)


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        demos = await unpublish_stale_demo_cinema(db)
        removed = await cleanup_duplicate_events(db)
        enriched = await enrich_stale_events(db)
        refreshed = await refresh_cinema_posters(db, limit=80)
        posters = await enrich_missing_posters(db, limit=100)
        await db.commit()
    print(
        f"demo_cinema={demos} dupes={removed} enriched={enriched} "
        f"refreshed={refreshed} posters={posters}"
    )


if __name__ == "__main__":
    asyncio.run(main())
