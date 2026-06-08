"""Issue management operations — extracted from the API layer.

Creation and AI analysis live in ``issue_processor``; this module covers
reads and lifecycle updates on existing issues.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import IssueStatus
from app.models.issue import Issue, IssueComment
from app.models.user import User
from app.services.audit import log_action
from app.services.notifications import notify_issue_status

logger = logging.getLogger(__name__)

_ISSUE_DETAIL_LOADS = (
    selectinload(Issue.photos),
    selectinload(Issue.ai_analysis),
    selectinload(Issue.comments),
)


@dataclass(frozen=True, slots=True)
class IssueActorContext:
    """Actor performing an issue action (used for audit logging)."""

    actor_id: int
    ip_address: Optional[str] = None


async def get_issue_details(db: AsyncSession, issue_id: int) -> Issue | None:
    """Load an issue with photos, AI analysis and comments eagerly fetched."""
    result = await db.execute(
        select(Issue)
        .options(*_ISSUE_DETAIL_LOADS)
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if issue is None:
        logger.debug("Issue %s not found", issue_id)
    return issue


async def update_issue_status(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    resolution_text: Optional[str],
    actor: IssueActorContext,
) -> Issue:
    """Apply a status change, write audit log and notify the resident in VK."""
    issue.status = status
    if resolution_text:
        issue.resolution_text = resolution_text
    if status == IssueStatus.RESOLVED:
        issue.resolved_at = datetime.now(timezone.utc)

    await log_action(
        db,
        "status_change",
        "issue",
        issue.id,
        user_id=actor.actor_id,
        details={"status": status.value, "resolution": resolution_text},
        ip_address=actor.ip_address,
    )

    try:
        await notify_issue_status(issue)
    except Exception:
        logger.exception("Failed to notify resident about issue #%s status change", issue.id)

    logger.info(
        "Issue #%s status updated to %s by user %s",
        issue.id,
        status.value,
        actor.actor_id,
    )
    return issue


async def resolve_issue(
    db: AsyncSession,
    issue: Issue,
    *,
    resolution_text: Optional[str],
    actor: IssueActorContext,
) -> Issue:
    """Mark an issue as resolved with optional resolution text and timestamp."""
    return await update_issue_status(
        db,
        issue,
        status=IssueStatus.RESOLVED,
        resolution_text=resolution_text,
        actor=actor,
    )


async def assign_issue(
    db: AsyncSession,
    issue: Issue,
    *,
    assignee_id: int,
    actor: IssueActorContext,
) -> Issue:
    """Assign a responsible user to an issue and log the change."""
    previous = issue.assignee_id
    issue.assignee_id = assignee_id

    await log_action(
        db,
        "assign_issue",
        "issue",
        issue.id,
        user_id=actor.actor_id,
        details={"assignee_id": assignee_id, "previous_assignee_id": previous},
        ip_address=actor.ip_address,
    )
    logger.info(
        "Issue #%s assigned to user %s by user %s",
        issue.id,
        assignee_id,
        actor.actor_id,
    )
    return issue


async def add_issue_comment(
    db: AsyncSession,
    issue: Issue,
    *,
    author: User,
    text: str,
    is_internal: bool,
) -> IssueComment:
    """Persist a public or internal comment on an issue."""
    comment = IssueComment(
        issue_id=issue.id,
        author_id=author.id,
        text=text,
        is_internal=is_internal,
    )
    db.add(comment)
    await db.flush()
    logger.debug(
        "Comment added to issue #%s by user %s (internal=%s)",
        issue.id,
        author.id,
        is_internal,
    )
    return comment
