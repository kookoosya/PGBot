"""Issue validation and duplicate detection."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.models.user import User
from app.services.issue.schemas import IssueValidationError


async def find_similar_issues(db: AsyncSession, text: str, category: str | None) -> list[Issue]:
    """Find open issues that may be duplicates of the incoming complaint."""
    query = (
        select(Issue)
        .options(selectinload(Issue.ai_analysis))
        .where(
            Issue.is_spam.is_(False),
            Issue.status.notin_([IssueStatus.RESOLVED, IssueStatus.REJECTED, IssueStatus.ARCHIVED]),
            Issue.parent_issue_id.is_(None),
        )
        .order_by(Issue.created_at.desc())
        .limit(20)
    )
    if category:
        query = query.where(Issue.category == category)

    result = await db.execute(query)
    return list(result.scalars().all())


def validate_web_create_form(
    data,
    *,
    user: User | None,
) -> None:
    """Validate web complaint form before processing."""
    if data.website_url:
        raise IssueValidationError("Не удалось отправить форму. Обновите страницу.")

    if not user and (not data.phone or not data.full_name):
        raise IssueValidationError("Укажите имя и телефон или войдите в кабинет")


def reject_if_spam(issue: Issue) -> None:
    """Raise when AI marked the submission as spam."""
    if issue.is_spam:
        raise IssueValidationError(
            "Обращение не принято. Опишите конкретную проблему без рекламы и оскорблений.",
        )
