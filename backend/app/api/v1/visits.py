import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.rate_limit import limiter
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_client_ip, require_owner
from app.database import get_db
from app.models.page_visit import PageVisit
from app.models.user import User
from app.schemas.visits import DailyVisitStat, PageStat, VisitStatsResponse, VisitTrackRequest

router = APIRouter()

PAGE_LABELS = {
    "/": "Главная",
    "/map": "Карта",
    "/classifieds": "Объявления",
    "/services": "Услуги",
    "/ai": "ИИ",
    "/register": "Регистрация",
    "/signup": "Регистрация жителя",
    "/cabinet": "Личный кабинет",
    "/services/cabinet": "Кабинет мастера",
    "/services/register": "Регистрация мастера",
}


def _visitor_key(ip: str, user_agent: str | None) -> str:
    raw = f"{ip}|{(user_agent or '')[:120]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.post("/track", status_code=204)
@limiter.limit("120/minute")
async def track_visit(
    data: VisitTrackRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    path = data.path.split("?")[0].strip() or "/"
    if path.startswith("/admin"):
        return

    ip = get_client_ip(request)
    db.add(PageVisit(
        path=path[:255],
        visitor_key=_visitor_key(ip, request.headers.get("user-agent")),
        user_agent=(request.headers.get("user-agent") or "")[:300] or None,
    ))


@router.get("/stats", response_model=VisitStatsResponse)
async def visit_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
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
