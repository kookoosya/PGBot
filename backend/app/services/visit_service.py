"""Page visit tracking and analytics.

Public API: ``track_page_visit``, ``build_visit_statistics``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.visit_config import PAGE_LABELS
from app.models.page_visit import PageVisit
from app.schemas.visits import DailyVisitStat, PageStat, VisitStatsResponse, VisitTrackRequest
from app.utils.visitor import visitor_key

logger = logging.getLogger(__name__)


async def track_page_visit(
    db: AsyncSession,
    data: VisitTrackRequest,
    *,
    ip_address: str,
    user_agent: str | None,
) -> None:
    """Record a page view; silently skip admin paths."""
    path = data.path.split("?")[0].strip() or "/"
    if path.startswith("/admin"):
        return

    db.add(PageVisit(
        path=path[:255],
        visitor_key=visitor_key(ip_address, user_agent),
        user_agent=(user_agent or "")[:300] or None,
    ))


async def build_visit_statistics(db: AsyncSession) -> VisitStatsResponse:
    """Aggregate visit counts for the admin dashboard."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=6)
    month_start = today_start - timedelta(days=29)

    async def count_since(since: datetime) -> int:
        return (await db.execute(
            select(func.count(PageVisit.id)).where(PageVisit.visited_at >= since)
        )).scalar() or 0

    async def unique_since(since: datetime) -> int:
        return (await db.execute(
            select(func.count(func.distinct(PageVisit.visitor_key)))
            .where(PageVisit.visited_at >= since, PageVisit.visitor_key.isnot(None))
        )).scalar() or 0

    top_result = await db.execute(
        select(PageVisit.path, func.count(PageVisit.id))
        .where(PageVisit.visited_at >= month_start)
        .group_by(PageVisit.path)
        .order_by(func.count(PageVisit.id).desc())
        .limit(10)
    )
    top_pages = [
        PageStat(path=path, label=PAGE_LABELS.get(path, path), count=count)
        for path, count in top_result.all()
    ]

    daily_result = await db.execute(
        select(
            cast(PageVisit.visited_at, Date).label("day"),
            func.count(PageVisit.id),
            func.count(func.distinct(PageVisit.visitor_key)),
        )
        .where(PageVisit.visited_at >= month_start)
        .group_by(cast(PageVisit.visited_at, Date))
        .order_by(cast(PageVisit.visited_at, Date))
    )
    daily = [
        DailyVisitStat(day=str(day), visits=visits, unique_visitors=unique or 0)
        for day, visits, unique in daily_result.all()
    ]

    return VisitStatsResponse(
        today=await count_since(today_start),
        week=await count_since(week_start),
        month=await count_since(month_start),
        total=(await db.execute(select(func.count(PageVisit.id)))).scalar() or 0,
        unique_today=await unique_since(today_start),
        unique_week=await unique_since(week_start),
        top_pages=top_pages,
        daily=daily,
    )
