from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import EventCategory, EventRegion
from app.schemas.event import PublicEventDetailResponse, PublicEventListResponse, PublicEventResponse
from app.schemas.today import TodayResponse
from app.services.event_service import (
    event_to_public_response,
    get_public_event_by_id,
    get_related_event_sessions,
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
    category: EventCategory | None = Query(None),
    search: str | None = Query(None, max_length=100),
    limit: int = Query(40, ge=1, le=60),
):
    """Upcoming published events with optional region, category and text search."""
    events = await search_public_events(
        db, region=region, category=category, search=search, limit=limit,
    )
    return PublicEventListResponse(
        items=[PublicEventResponse(**event_to_public_response(e)) for e in events],
        total=len(events),
    )


@router.get("/events/{event_id}", response_model=PublicEventDetailResponse)
async def public_get_event(
    event_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Single published event for the public detail page."""
    event = await get_public_event_by_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    related = await get_related_event_sessions(db, event)
    payload = event_to_public_response(event)
    payload["related_sessions"] = [
        event_to_public_response(item) for item in related
    ]
    return PublicEventDetailResponse(**payload)
