#!/usr/bin/env python3
"""One-shot map/taxi sync after deploy."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import AsyncSessionLocal
from app.services.map_sync import sync_all_map_data


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await sync_all_map_data(db)
        await db.commit()
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
