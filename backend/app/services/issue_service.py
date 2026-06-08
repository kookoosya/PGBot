"""Issue management operations (status, comments) — extracted from API layer."""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus
from app.models.issue import Issue, IssueComment
from app.models.user import User
from app.services.audit import log_action
from app.services.notifications import notify_issue_status


async def update_issue_status(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    resolution_text: str | None,
    actor_id: int,
    ip_address: str | None = None,
) -> Issue:
    """Apply status change, audit log and notify the resident in VK."""
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
        user_id=actor_id,
        details={"status": status.value, "resolution": resolution_text},
        ip_address=ip_address,
    )
    await notify_issue_status(issue)
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
    return comment
