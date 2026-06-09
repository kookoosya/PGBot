from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, require_owner
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackItem, FeedbackListResponse
from app.services.feedback_service import list_feedback, submit_feedback

router = APIRouter()
settings = get_settings()


@router.post("", response_model=FeedbackItem, status_code=201)
@limiter.limit(settings.FEEDBACK_RATE_LIMIT)
async def submit_feedback_endpoint(
    data: FeedbackCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await submit_feedback(
        db,
        data,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.get("", response_model=FeedbackListResponse)
async def list_feedback_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return await list_feedback(db, status=status, limit=limit, offset=offset)
