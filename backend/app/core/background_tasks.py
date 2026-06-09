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


async def _weather_cache_work() -> None:
    from app.services.weather_service import refresh_weather_cache

    await refresh_weather_cache()


async def _event_sync_work() -> None:
    from app.database import AsyncSessionLocal
    from app.services.event_sources.coordinator import sync_all_event_sources

    async with AsyncSessionLocal() as db:
        results = await sync_all_event_sources(db)
        await db.commit()
        created = sum(r.created for r in results)
        if created:
            logger.info("Event auto-sync: +%s new events", created)


def _create_periodic_task(
    name: str,
    interval_seconds: float,
    work: Callable[[], Awaitable[None]],
) -> asyncio.Task:
    task = asyncio.create_task(run_periodic(name, interval_seconds, work))
    task.set_name(f"periodic:{name}")
    return task


def start_background_tasks(settings: Settings) -> list[asyncio.Task]:
    return [
        _create_periodic_task(
            "Map auto-sync",
            settings.MAP_AUTO_SYNC_HOURS * 3600,
            _map_sync_work,
        ),
        _create_periodic_task(
            "VK digest",
            3600,
            _vk_digest_work,
        ),
        _create_periodic_task(
            "Weather cache",
            settings.WEATHER_CACHE_TTL_SECONDS,
            _weather_cache_work,
        ),
        *(
            [
                _create_periodic_task(
                    "Event sync",
                    settings.EVENT_SYNC_INTERVAL_HOURS * 3600,
                    _event_sync_work,
                )
            ]
            if settings.EVENT_SYNC_INTERVAL_HOURS > 0
            else []
        ),
    ]


async def stop_background_tasks(tasks: list[asyncio.Task]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for task, result in zip(tasks, results):
        if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
            logger.warning(
                "Task %s finished with error during shutdown: %s",
                task.get_name(),
                result,
            )
