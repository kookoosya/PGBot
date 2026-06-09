from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import EventRegion
from app.schemas.event import PublicEventListResponse, PublicEventResponse
from app.schemas.today import TodayResponse
from app.services.event_service import (
    event_to_public_response,
    get_public_event_by_id,
    search_public_events,
)
from app.services.site_service import build_public_info
from app.services.today_service import build_today_snapshot

router = APIRouter()


@router.get("/info")
async def public_info():
    return build_public_info()


@router.get("/today", response_model=TodayResponse)
async def today_in_village(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: EventRegion | None = Query(None, description="Filter upcoming events by region"),
):
    """Aggregated landing snapshot: weather, latest ad, map stats, upcoming events."""
    snapshot = await build_today_snapshot(db, event_region=region)
    return snapshot.to_response()


@router.get("/events", response_model=PublicEventListResponse)
async def public_list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    region: EventRegion | None = Query(None),
    search: str | None = Query(None, max_length=100),
    limit: int = Query(30, ge=1, le=50),
):
    """Upcoming published events with optional region and text search."""
    events = await search_public_events(db, region=region, search=search, limit=limit)
    return PublicEventListResponse(
        items=[PublicEventResponse(**event_to_public_response(e)) for e in events],
        total=len(events),
    )


@router.get("/events/{event_id}", response_model=PublicEventResponse)
async def public_get_event(
    event_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Single published event for the public detail page."""
    event = await get_public_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return PublicEventResponse(**event_to_public_response(event))
