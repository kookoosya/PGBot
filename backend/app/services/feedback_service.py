"""Site feedback — public submission and admin listing.

Public API: ``submit_feedback``, ``list_feedback``, ``feedback_to_response``.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_feedback import SiteFeedback
from app.schemas.feedback import FeedbackCreate, FeedbackItem, FeedbackListResponse
from app.utils.visitor import visitor_key

logger = logging.getLogger(__name__)


def feedback_to_response(row: SiteFeedback) -> FeedbackItem:
    """Map feedback ORM row to API response."""
    return FeedbackItem.model_validate(row)


async def submit_feedback(
    db: AsyncSession,
    data: FeedbackCreate,
    *,
    ip_address: str,
    user_agent: str | None,
) -> FeedbackItem:
    """Persist visitor feedback."""
    row = SiteFeedback(
        message=data.message.strip(),
        contact=(data.contact or "").strip() or None,
        page=(data.page or "").strip()[:120] or None,
        visitor_key=visitor_key(ip_address, user_agent),
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return feedback_to_response(row)


async def list_feedback(
    db: AsyncSession,
    *,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> FeedbackListResponse:
    """Return paginated feedback for the admin panel."""
    query = select(SiteFeedback).order_by(SiteFeedback.created_at.desc())
    count_query = select(func.count(SiteFeedback.id))
    if status:
        query = query.where(SiteFeedback.status == status)
        count_query = count_query.where(SiteFeedback.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    rows = (await db.execute(query.offset(offset).limit(limit))).scalars().all()
    return FeedbackListResponse(items=rows, total=total)
