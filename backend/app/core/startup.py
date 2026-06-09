import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.core.background_tasks import start_background_tasks, stop_background_tasks
from app.core.redis_client import close_redis, init_redis

logger = logging.getLogger(__name__)


def validate_security_config(app_settings: Settings) -> None:
    weak_secret = app_settings.SECRET_KEY in (
        "",
        "change-me-in-production-use-long-random-string",
        "change-me-use-openssl-rand-hex-32",
    )
    if not app_settings.DEBUG and weak_secret:
        raise RuntimeError("SECRET_KEY must be set to a strong random value in production")
    if app_settings.VK_GROUP_TOKEN and not app_settings.VK_SECRET_KEY:
        raise RuntimeError("VK_SECRET_KEY must be set when VK_GROUP_TOKEN is configured")


def validate_rate_limit_config(app_settings: Settings) -> None:
    if not app_settings.DEBUG and not app_settings.rate_limit_storage_uri:
        logger.warning(
            "REDIS_URL is not configured — rate limits are stored in memory per worker",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_security_config(settings)
    validate_rate_limit_config(settings)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    try:
        await init_redis()
    except Exception:
        logger.exception("Redis initialization failed — continuing without async Redis client")
    tasks = start_background_tasks(settings)
    yield
    await stop_background_tasks(tasks)
    await close_redis()
    logger.info("Shutting down")
