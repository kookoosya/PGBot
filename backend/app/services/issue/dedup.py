"""Complaint deduplication helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.enums import IssueStatus
from app.models.issue import Issue, IssueDuplicate

settings = get_settings()


async def find_similar_issues(db: AsyncSession, text: str, category: str | None) -> list[Issue]:
    """Find open parent issues that may be duplicates of the complaint text."""
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


def should_link_duplicate_issue(duplicate_probability: float, *, has_existing: bool) -> bool:
    """Business rule: link new complaint to an open issue when AI confidence is high."""
    return duplicate_probability >= settings.DUPLICATE_THRESHOLD and has_existing


async def handle_deduplication(
    db: AsyncSession,
    existing: list[Issue],
    duplicate_prob: float,
) -> Issue | None:
    """Link complaint to an existing issue when duplicate probability is high."""
    if not should_link_duplicate_issue(duplicate_prob, has_existing=bool(existing)):
        return None
    parent_issue = existing[0]
    parent_issue.confirmation_count += 1
    db.add(
        IssueDuplicate(
            issue_id=parent_issue.id,
            duplicate_of_id=parent_issue.id,
            similarity_score=duplicate_prob,
        )
    )
    return parent_issue
