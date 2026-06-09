from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.database import get_db
from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.models.user import User
from app.schemas.statistics import CategoryStat, MonthlyStat, StatisticsResponse, StreetStat

router = APIRouter()


@router.get("", response_model=StatisticsResponse)
async def get_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    total = (await db.execute(select(func.count(Issue.id)))).scalar() or 0
    resolved = (
        await db.execute(select(func.count(Issue.id)).where(Issue.status == IssueStatus.RESOLVED))
    ).scalar() or 0
    in_progress = (
        await db.execute(
            select(func.count(Issue.id)).where(
                Issue.status.in_([IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS, IssueStatus.UNDER_REVIEW])
            )
        )
    ).scalar() or 0
    rejected = (
        await db.execute(select(func.count(Issue.id)).where(Issue.status == IssueStatus.REJECTED))
    ).scalar() or 0

    avg_hours = None
    avg_result = await db.execute(
        select(func.avg(func.extract("epoch", Issue.resolved_at - Issue.created_at) / 3600)).where(
            Issue.resolved_at.isnot(None)
        )
    )
    avg_val = avg_result.scalar()
    if avg_val:
        avg_hours = round(float(avg_val), 1)

    cat_result = await db.execute(
        select(Issue.category, func.count(Issue.id))
        .where(Issue.category.isnot(None))
        .group_by(Issue.category)
        .order_by(func.count(Issue.id).desc())
        .limit(10)
    )
    top_categories = [CategoryStat(category=str(row[0]), count=row[1]) for row in cat_result.all()]

    street_result = await db.execute(
        select(Issue.address, func.count(Issue.id))
        .where(Issue.address.isnot(None))
        .group_by(Issue.address)
        .order_by(func.count(Issue.id).desc())
        .limit(10)
    )
    top_streets = [StreetStat(street=row[0] or "Не указан", count=row[1]) for row in street_result.all()]

    monthly_result = await db.execute(
        select(
            extract("year", Issue.created_at),
            extract("month", Issue.created_at),
            func.count(Issue.id),
        )
        .group_by(extract("year", Issue.created_at), extract("month", Issue.created_at))
        .order_by(extract("year", Issue.created_at), extract("month", Issue.created_at))
        .limit(12)
    )
    monthly_dynamics = []
    for row in monthly_result.all():
        year, month, count = int(row[0]), int(row[1]), row[2]
        resolved_count = (
            await db.execute(
                select(func.count(Issue.id)).where(
                    extract("year", Issue.created_at) == year,
                    extract("month", Issue.created_at) == month,
                    Issue.status == IssueStatus.RESOLVED,
                )
            )
        ).scalar() or 0
        monthly_dynamics.append(MonthlyStat(month=f"{year}-{month:02d}", count=count, resolved=resolved_count))

    return StatisticsResponse(
        total_issues=total,
        resolved_issues=resolved,
        in_progress_issues=in_progress,
        rejected_issues=rejected,
        avg_resolution_hours=avg_hours,
        top_categories=top_categories,
        top_streets=top_streets,
        monthly_dynamics=monthly_dynamics,
    )
