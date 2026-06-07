import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.config import get_settings
from app.core.security_headers import SecurityHeadersMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


async def _background_map_sync():
    """Auto-sync map data from OpenStreetMap every MAP_AUTO_SYNC_HOURS."""
    from app.database import AsyncSessionLocal
    from app.services.osm_sync import seed_pushkin_landmarks, sync_places_from_osm

    while True:
        try:
            async with AsyncSessionLocal() as db:
                await seed_pushkin_landmarks(db)
                result = await sync_places_from_osm(db)
                await db.commit()
                logger.info("Map auto-sync: %s", result)
        except Exception as e:
            logger.error("Map auto-sync error: %s", e)
        await asyncio.sleep(settings.MAP_AUTO_SYNC_HOURS * 3600)


def _validate_security_config() -> None:
    weak_secret = settings.SECRET_KEY in (
        "",
        "change-me-in-production-use-long-random-string",
        "change-me-use-openssl-rand-hex-32",
    )
    if not settings.DEBUG and weak_secret:
        raise RuntimeError("SECRET_KEY must be set to a strong random value in production")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _validate_security_config()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    sync_task = asyncio.create_task(_background_map_sync())
    yield
    sync_task.cancel()
    logger.info("Shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
@limiter.limit("30/minute")
async def health(request: Request):
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }
