#!/usr/bin/env python3
"""Sync events from VK, Orbilet and other configured sources."""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.services.event_sources.coordinator import sync_all_event_sources


async def main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        results = await sync_all_event_sources(db)
        await db.commit()

    for row in results:
        print(
            f"{row.source}/{row.region}: fetched={row.fetched} "
            f"created={row.created} updated={row.updated} skipped={row.skipped}"
        )
        for err in row.errors:
            print(f"  error: {err}")


if __name__ == "__main__":
    asyncio.run(main())
