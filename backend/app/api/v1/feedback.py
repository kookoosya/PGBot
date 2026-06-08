import hashlib
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, require_owner
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.site_feedback import SiteFeedback
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackItem, FeedbackListResponse

router = APIRouter()
settings = get_settings()


def _visitor_key(ip: str, user_agent: str | None) -> str:
    raw = f"{ip}|{(user_agent or '')[:120]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.post("", response_model=FeedbackItem, status_code=201)
@limiter.limit(settings.FEEDBACK_RATE_LIMIT)
async def submit_feedback(
    data: FeedbackCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ip = get_client_ip(request)
    row = SiteFeedback(
        message=data.message.strip(),
        contact=(data.contact or "").strip() or None,
        page=(data.page or "").strip()[:120] or None,
        visitor_key=_visitor_key(ip, request.headers.get("user-agent")),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    q = select(SiteFeedback).order_by(SiteFeedback.created_at.desc())
    count_q = select(func.count(SiteFeedback.id))
    if status:
        q = q.where(SiteFeedback.status == status)
        count_q = count_q.where(SiteFeedback.status == status)

    total = (await db.execute(count_q)).scalar() or 0
    rows = (await db.execute(q.offset(offset).limit(limit))).scalars().all()
    return FeedbackListResponse(items=rows, total=total)
