import logging
import os

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.router import api_router
from app.config import get_settings
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.startup import lifespan
from app.database import get_db
from app.services.event_source_health import build_event_sources_health
from app.services.share_pages import build_event_share_html, garnect_share_html

logging.basicConfig(level=logging.INFO)
settings = get_settings()
limiter.default_limits = [settings.RATE_LIMIT]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
if not os.environ.get("TESTING"):
    app.add_middleware(SlowAPIMiddleware)

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
    payload = {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
    if settings.REDIS_URL.strip():
        try:
            import redis

            redis.from_url(settings.REDIS_URL, socket_connect_timeout=1).ping()
            payload["redis"] = "ok"
        except Exception:
            payload["redis"] = "error"
    payload["event_sources"] = build_event_sources_health()
    return payload


@app.get("/share/festival/garnect", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def share_festival_garnect(request: Request):
    return HTMLResponse(garnect_share_html())


@app.get("/share/events/{event_id}", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def share_event(
    event_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    html = await build_event_share_html(db, event_id)
    if not html:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return HTMLResponse(html)


@app.get("/")
async def root():
    payload = {"app": settings.APP_NAME, "version": settings.APP_VERSION}
    if settings.DEBUG:
        payload["docs"] = "/api/docs"
    return payload
