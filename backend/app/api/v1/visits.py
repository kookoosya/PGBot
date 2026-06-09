from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_client_ip, require_owner
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.visits import VisitStatsResponse, VisitTrackRequest
from app.services.visit_service import build_visit_statistics, track_page_visit

router = APIRouter()


@router.post("/track", status_code=204)
@limiter.limit("120/minute")
async def track_visit(
    data: VisitTrackRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await track_page_visit(
        db,
        data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/stats", response_model=VisitStatsResponse)
async def visit_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await build_visit_statistics(db)
