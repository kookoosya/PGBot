"""Issue status transitions: update, resolve, reopen, archive."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.services.issue.notification import safe_issue_audit, safe_notify_status
from app.services.issue.schemas import IssueActorContext, IssueValidationError

logger = logging.getLogger(__name__)

_REOPEN_TARGET_STATUSES = frozenset({IssueStatus.NEW, IssueStatus.UNDER_REVIEW})


def _status_value(status: IssueStatus | str) -> str:
    return status.value if isinstance(status, IssueStatus) else str(status)


async def _change_issue_status(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    actor: IssueActorContext,
    audit_action: str,
    resolution_text: str | None = None,
    extra_audit: dict[str, Any] | None = None,
    notify: bool = True,
    clear_resolved_at: bool = False,
) -> Issue:
    """Shared status transition: mutate issue, audit, optional VK notify."""
    previous = issue.status
    if _status_value(previous) == status.value:
        return issue

    issue.status = status

    if resolution_text:
        issue.resolution_text = resolution_text
    if status == IssueStatus.RESOLVED:
        issue.resolved_at = datetime.now(UTC)
    elif clear_resolved_at or (
        _status_value(previous) == IssueStatus.RESOLVED.value
        and status not in {IssueStatus.RESOLVED, IssueStatus.REJECTED, IssueStatus.ARCHIVED}
    ):
        issue.resolved_at = None

    details: dict[str, Any] = {
        "status": status.value,
        "previous_status": _status_value(previous),
    }
    if audit_action == "status_change" or resolution_text is not None:
        details["resolution"] = resolution_text
    if extra_audit:
        details.update(extra_audit)

    await safe_issue_audit(db, audit_action, issue.id, actor, details)
    if notify:
        await safe_notify_status(issue)

    logger.info(
        "Issue #%s: %s → %s by user %s",
        issue.id,
        _status_value(previous),
        status.value,
        actor.actor_id,
    )
    return issue


async def update_issue_status(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    resolution_text: str | None,
    actor: IssueActorContext,
) -> Issue:
    """Apply a status change, write audit log and notify the resident."""
    return await _change_issue_status(
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
    resolution_text: str | None,
    actor: IssueActorContext,
) -> Issue:
    """Mark an issue as resolved with optional resolution text."""
    return await _change_issue_status(
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
    """Reopen a closed issue — set status to NEW or UNDER_REVIEW."""
    if target_status not in _REOPEN_TARGET_STATUSES:
        raise IssueValidationError(f"target_status must be NEW or UNDER_REVIEW, got {target_status!r}")
    return await _change_issue_status(
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
    """Archive an issue with audit log and resident notification."""
    return await _change_issue_status(
        db,
        issue,
        status=IssueStatus.ARCHIVED,
        actor=actor,
        audit_action="archive_issue",
    )


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
