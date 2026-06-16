"""Issue status transitions and assignment."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus
from app.models.issue import Issue

from .notification import safe_audit, safe_notify_status, status_value
from .schemas import IssueActorContext, IssueValidationError, _REOPEN_TARGET_STATUSES

logger = logging.getLogger(__name__)


async def change_issue_status(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    actor: IssueActorContext,
    audit_action: str,
    resolution_text: Optional[str] = None,
    extra_audit: Optional[dict[str, Any]] = None,
    notify: bool = True,
    clear_resolved_at: bool = False,
) -> Issue:
    """Shared status transition: mutate issue, audit, optional VK notify."""
    previous = issue.status
    if status_value(previous) == status.value:
        logger.debug("Issue #%s status unchanged (%s), skipping transition", issue.id, status.value)
        return issue

    issue.status = status

    if resolution_text:
        issue.resolution_text = resolution_text
    if status == IssueStatus.RESOLVED:
        issue.resolved_at = datetime.now(timezone.utc)
    elif clear_resolved_at or (
        status_value(previous) == IssueStatus.RESOLVED.value
        and status not in {IssueStatus.RESOLVED, IssueStatus.REJECTED, IssueStatus.ARCHIVED}
    ):
        issue.resolved_at = None

    details: dict[str, Any] = {
        "status": status.value,
        "previous_status": status_value(previous),
    }
    if audit_action == "status_change" or resolution_text is not None:
        details["resolution"] = resolution_text
    if extra_audit:
        details.update(extra_audit)

    audited = await safe_audit(db, audit_action, issue.id, actor, details)
    if not audited:
        logger.warning(
            "Issue #%s status changed to %s but audit action %s was not logged (actor=%s)",
            issue.id,
            status.value,
            audit_action,
            actor.actor_id,
        )
    if notify:
        notified = await safe_notify_status(issue, previous_status=status_value(previous))
        if not notified:
            logger.warning(
                "Issue #%s status changed to %s but resident was not notified (peer_id=%s)",
                issue.id,
                status.value,
                issue.vk_peer_id,
            )

    logger.info(
        "Issue #%s: %s → %s by user %s",
        issue.id,
        status_value(previous),
        status.value,
        actor.actor_id,
    )
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
    return await change_issue_status(
        db,
        issue,
        status=status,
        actor=actor,
        audit_action="status_change",
        resolution_text=resolution_text,
    )


async def resolve_issue(
    db: AsyncSession,
    issue: Issue,
    *,
    resolution_text: Optional[str],
    actor: IssueActorContext,
) -> Issue:
    """Mark an issue as resolved with optional resolution text and timestamp."""
    return await change_issue_status(
        db,
        issue,
        status=IssueStatus.RESOLVED,
        actor=actor,
        audit_action="status_change",
        resolution_text=resolution_text,
    )


async def reopen_issue(
    db: AsyncSession,
    issue: Issue,
    *,
    actor: IssueActorContext,
    target_status: IssueStatus = IssueStatus.UNDER_REVIEW,
) -> Issue:
    """Reopen a closed issue — set status to ``NEW`` or ``UNDER_REVIEW``.

    Raises ``IssueValidationError`` when ``target_status`` is not allowed.
    """
    if target_status not in _REOPEN_TARGET_STATUSES:
        raise IssueValidationError(
            f"target_status must be NEW or UNDER_REVIEW, got {target_status!r}"
        )
    return await change_issue_status(
        db,
        issue,
        status=target_status,
        actor=actor,
        audit_action="reopen_issue",
        clear_resolved_at=True,
        extra_audit={"target_status": target_status.value},
    )


async def archive_issue(
    db: AsyncSession,
    issue: Issue,
    *,
    actor: IssueActorContext,
) -> Issue:
    """Archive an issue (status ``ARCHIVED``) with audit log and resident notification."""
    return await change_issue_status(
        db,
        issue,
        status=IssueStatus.ARCHIVED,
        actor=actor,
        audit_action="archive_issue",
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

    audited = await safe_audit(
        db,
        "assign_issue",
        issue.id,
        actor,
        {"assignee_id": assignee_id, "previous_assignee_id": previous},
    )
    if not audited:
        logger.warning(
            "Issue #%s assigned to user %s but audit was not logged (actor=%s)",
            issue.id,
            assignee_id,
            actor.actor_id,
        )
    logger.info(
        "Issue #%s assigned to user %s by user %s",
        issue.id,
        assignee_id,
        actor.actor_id,
    )
    return issue


async def apply_issue_status_update(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    resolution_text: str | None,
    actor: IssueActorContext,
) -> Issue:
    """Apply status transition, routing resolved issues through ``resolve_issue``."""
    if status == IssueStatus.RESOLVED:
        return await resolve_issue(
            db,
            issue,
            resolution_text=resolution_text,
            actor=actor,
        )
    return await update_issue_status(
        db,
        issue,
        status=status,
        resolution_text=resolution_text,
        actor=actor,
    )
