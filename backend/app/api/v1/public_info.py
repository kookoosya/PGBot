from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.enums import EventRegion
from app.schemas.today import TodayResponse
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
