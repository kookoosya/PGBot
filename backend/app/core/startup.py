import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.core.background_tasks import start_background_tasks, stop_background_tasks

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    validate_security_config(settings)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    tasks = start_background_tasks(settings)
    yield
    await stop_background_tasks(tasks)
    logger.info("Shutting down")
