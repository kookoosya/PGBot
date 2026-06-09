"""Issue comments."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import can_manage_issues
from app.models.issue import Issue, IssueComment
from app.models.user import User
from app.services.issue.crud import require_issue_for_user

logger = logging.getLogger(__name__)


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


async def add_comment_for_user(
    db: AsyncSession,
    issue_id: int,
    user: User,
    *,
    text: str,
    is_internal: bool,
) -> IssueComment:
    """Add a comment after verifying the user can access the issue."""
    issue = await require_issue_for_user(db, issue_id, user)
    return await add_issue_comment(
        db,
        issue,
        author=user,
        text=text,
        is_internal=is_internal and can_manage_issues(user),
    )
