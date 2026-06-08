import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.config import Settings

logger = logging.getLogger(__name__)


async def run_periodic(
    name: str,
    interval_seconds: float,
    work: Callable[[], Awaitable[None]],
) -> None:
    while True:
        try:
            await work()
        except Exception as e:
            logger.error("%s error: %s", name, e)
        await asyncio.sleep(interval_seconds)


async def _map_sync_work() -> None:
    from app.database import AsyncSessionLocal
    from app.services.map_sync import sync_all_map_data

    async with AsyncSessionLocal() as db:
        result = await sync_all_map_data(db)
        await db.commit()
        logger.info("Map auto-sync: %s", result)


async def _vk_digest_work() -> None:
    from app.database import AsyncSessionLocal
    from app.services.vk_digest import send_daily_digest

    async with AsyncSessionLocal() as db:
        sent = await send_daily_digest(db)
        await db.commit()
        if sent:
            logger.info("VK daily digest sent to %s subscribers", sent)


def start_background_tasks(settings: Settings) -> list[asyncio.Task]:
    tasks = [
        asyncio.create_task(
            run_periodic(
                "Map auto-sync",
                settings.MAP_AUTO_SYNC_HOURS * 3600,
                _map_sync_work,
            )
        ),
        asyncio.create_task(
            run_periodic(
                "VK digest",
                3600,
                _vk_digest_work,
            )
        ),
    ]
    return tasks


async def stop_background_tasks(tasks: list[asyncio.Task]) -> None:
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
