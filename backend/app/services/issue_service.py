"""Issue lifecycle operations — reads and updates on existing issues.

Creation and AI analysis live in ``issue_processor``.

Public API: ``get_issue_details``, ``get_issues_for_user``, ``update_issue_status``,
``resolve_issue``, ``reopen_issue``, ``archive_issue``, ``assign_issue``, ``add_issue_comment``.

Errors: ``IssueNotFoundError``, ``IssueValidationError`` (subclasses of ``ServiceError``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.core.deps import can_manage_issues, is_official_user, is_owner_user
from app.models.enums import OFFICIAL_ROLES, IssueCategory, IssueStatus, UserRole
from app.models.issue import Issue, IssueComment
from app.models.user import User
from app.services.audit import log_action
from app.services.notifications import issue_status_label, notify_issue_status
from app.services.service_errors import ServiceError

logger = logging.getLogger(__name__)

_REOPEN_TARGET_STATUSES = frozenset({IssueStatus.NEW, IssueStatus.UNDER_REVIEW})

_ISSUE_DETAIL_LOADS = (
    selectinload(Issue.photos),
    selectinload(Issue.ai_analysis),
    selectinload(Issue.comments),
)

_ISSUE_LIST_LOADS = (
    selectinload(Issue.photos),
    selectinload(Issue.ai_analysis),
)

_STATUS_AUDIT_ACTIONS = frozenset({"status_change", "reopen_issue", "archive_issue"})

JKH_CATEGORIES = frozenset(
    {IssueCategory.UTILITIES, IssueCategory.WATER, IssueCategory.SEWERAGE}
)


@dataclass(frozen=True, slots=True)
class IssueStatusEvent:
    """Single status transition visible to the resident."""

    status: str
    label: str
    at: str
    previous_status: str | None = None


@dataclass(frozen=True, slots=True)
class IssueActorContext:
    """Actor performing an issue action (used for audit logging)."""

    actor_id: int
    ip_address: Optional[str] = None


class IssueNotFoundError(ServiceError):
    """Business error when an issue cannot be loaded."""

    def __init__(self, detail: str = "Issue not found") -> None:
        super().__init__(detail, status_code=404)


class IssueValidationError(ServiceError):
    """Business validation failure for issue lifecycle actions."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class IssueAccessDeniedError(ServiceError):
    """Raised when a user cannot view or modify an issue."""

    def __init__(self, detail: str = "Access denied") -> None:
        super().__init__(detail, status_code=403)


@dataclass(frozen=True, slots=True)
class IssueSearchParams:
    """Filters for ``search_issues``."""

    status: Optional[IssueStatus] = None
    category: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class IssueSearchResult:
    items: list[Issue]
    total: int
    page: int
    page_size: int


def _official_category_filter(user: User):
    if user.role.name == UserRole.SOCIAL_SERVICE:
        conditions = [Issue.category.in_(JKH_CATEGORIES)]
        if user.department_id:
            conditions.append(Issue.department_id == user.department_id)
        return or_(*conditions)
    return None


def can_view_issue(user: User, issue: Issue) -> bool:
    """Return whether ``user`` may read or comment on ``issue``."""
    if user.role.name == UserRole.RESIDENT:
        return issue.resident_id == user.id
    if is_owner_user(user):
        return True
    if is_official_user(user):
        if user.role.name == UserRole.SOCIAL_SERVICE:
            return (
                issue.category in JKH_CATEGORIES
                or (user.department_id and issue.department_id == user.department_id)
            )
        return True
    return False


async def require_issue_for_user(
    db: AsyncSession,
    issue_id: int,
    user: User,
) -> Issue:
    """Load an issue and enforce read access for ``user``."""
    issue = await get_issue_details(db, issue_id)
    if not issue:
        raise IssueNotFoundError()
    if not can_view_issue(user, issue):
        raise IssueAccessDeniedError()
    return issue


async def update_issue_fields(
    db: AsyncSession,
    issue: Issue,
    user: User,
    update_data: dict[str, Any],
    *,
    actor: IssueActorContext,
) -> Issue:
    """Apply partial field updates with role-based field restrictions."""
    if not is_owner_user(user):
        update_data.pop("department_id", None)
        update_data.pop("assignee_id", None)

    for field, value in update_data.items():
        setattr(issue, field, value)

    await log_action(
        db,
        "update_issue",
        "issue",
        issue.id,
        user_id=actor.actor_id,
        details=update_data,
        ip_address=actor.ip_address,
    )
    return issue


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


def _apply_issue_access_filter(query, user: User):
    if user.role.name == UserRole.RESIDENT:
        return query.where(Issue.resident_id == user.id)
    if user.role.name in OFFICIAL_ROLES or user.role.name == UserRole.MODERATOR:
        cat_filter = _official_category_filter(user)
        if cat_filter is not None:
            return query.where(cat_filter)
        return query
    raise IssueValidationError("Недостаточно прав", status_code=403)


async def _safe_audit(
    db: AsyncSession,
    action: str,
    issue_id: int,
    actor: IssueActorContext,
    details: dict[str, Any],
) -> bool:
    """Write audit log; return ``True`` on success."""
    try:
        await log_action(
            db,
            action,
            "issue",
            issue_id,
            user_id=actor.actor_id,
            details=details,
            ip_address=actor.ip_address,
        )
        return True
    except Exception:
        logger.exception(
            "Audit log failed for issue #%s: action=%s actor_id=%s ip=%s",
            issue_id,
            action,
            actor.actor_id,
            actor.ip_address,
        )
        return False


async def _safe_notify_status(issue: Issue, *, previous_status: str | None = None) -> bool:
    """Notify resident in VK about status change; return ``True`` on success."""
    peer_id = getattr(issue, "vk_peer_id", None)
    try:
        await notify_issue_status(issue, previous_status=previous_status)
        return True
    except Exception:
        logger.exception(
            "VK status notification failed for issue #%s (status=%s peer_id=%s)",
            issue.id,
            _status_value(issue.status),
            peer_id,
        )
        return False


def _status_value(status: IssueStatus | str) -> str:
    """Return enum value as string for logging and audit payloads."""
    return status.value if isinstance(status, IssueStatus) else str(status)


async def _change_issue_status(
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
    if _status_value(previous) == status.value:
        logger.debug("Issue #%s status unchanged (%s), skipping transition", issue.id, status.value)
        return issue

    issue.status = status

    if resolution_text:
        issue.resolution_text = resolution_text
    if status == IssueStatus.RESOLVED:
        issue.resolved_at = datetime.now(timezone.utc)
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

    audited = await _safe_audit(db, audit_action, issue.id, actor, details)
    if not audited:
        logger.warning(
            "Issue #%s status changed to %s but audit action %s was not logged (actor=%s)",
            issue.id,
            status.value,
            audit_action,
            actor.actor_id,
        )
    if notify:
        notified = await _safe_notify_status(issue, previous_status=_status_value(previous))
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
        _status_value(previous),
        status.value,
        actor.actor_id,
    )
    return issue


async def get_issue_details(db: AsyncSession, issue_id: int) -> Issue | None:
    """Load an issue with photos, AI analysis and comments eagerly fetched."""
    try:
        result = await db.execute(
            select(Issue)
            .options(*_ISSUE_DETAIL_LOADS)
            .where(Issue.id == issue_id)
        )
        issue = result.scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load issue #%s", issue_id)
        raise
    if issue is None:
        logger.debug("Issue %s not found", issue_id)
    return issue


async def get_issues_for_user(
    db: AsyncSession,
    user: User,
    *,
    status: IssueStatus | None = None,
    limit: int = 50,
) -> list[Issue]:
    """Return issues submitted by ``user``, newest first, with optional status filter."""
    safe_limit = max(1, min(limit, 100))
    query = (
        select(Issue)
        .options(*_ISSUE_LIST_LOADS)
        .where(Issue.resident_id == user.id)
        .order_by(Issue.created_at.desc())
        .limit(safe_limit)
    )
    if status is not None:
        query = query.where(Issue.status == status)

    try:
        result = await db.execute(query)
        issues = list(result.scalars().all())
    except Exception:
        logger.exception(
            "Failed to load issues for user %s (status=%s, limit=%s)",
            user.id,
            status.value if status else None,
            safe_limit,
        )
        raise
    logger.debug(
        "Loaded %s issue(s) for user %s (status=%s, limit=%s)",
        len(issues),
        user.id,
        status.value if status else None,
        safe_limit,
    )
    return issues


async def search_issues(
    db: AsyncSession,
    user: User,
    params: IssueSearchParams,
) -> IssueSearchResult:
    """Search issues visible to ``user`` with pagination."""
    page = max(1, params.page)
    page_size = max(1, min(params.page_size, 100))

    query = select(Issue).options(*_ISSUE_LIST_LOADS)
    query = _apply_issue_access_filter(query, user)

    if params.status is not None:
        query = query.where(Issue.status == params.status)
    if params.category:
        query = query.where(Issue.category == params.category)
    if params.search:
        query = query.where(Issue.description.ilike(f"%{params.search.strip()}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(Issue.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return IssueSearchResult(items=items, total=total, page=page, page_size=page_size)


async def get_issue_status_timeline(db: AsyncSession, issue: Issue) -> list[IssueStatusEvent]:
    """Build resident-visible status history from audit logs and creation time."""
    try:
        result = await db.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == "issue",
                AuditLog.entity_id == issue.id,
                AuditLog.action.in_(_STATUS_AUDIT_ACTIONS),
            )
            .order_by(AuditLog.created_at.asc())
        )
        entries = list(result.scalars().all())
    except Exception:
        logger.exception("Failed to load status timeline for issue #%s", issue.id)
        raise

    events: list[IssueStatusEvent] = []
    for entry in entries:
        details = entry.details or {}
        status = details.get("status")
        if not status:
            continue
        events.append(
            IssueStatusEvent(
                status=str(status),
                label=issue_status_label(str(status)),
                at=entry.created_at.isoformat(),
                previous_status=details.get("previous_status"),
            )
        )

    if not events:
        created_status = _status_value(issue.status)
        events.append(
            IssueStatusEvent(
                status=created_status,
                label=issue_status_label(created_status),
                at=issue.created_at.isoformat(),
            )
        )
    elif events[0].previous_status is None and events[0].status != IssueStatus.NEW.value:
        events.insert(
            0,
            IssueStatusEvent(
                status=IssueStatus.NEW.value,
                label=issue_status_label(IssueStatus.NEW.value),
                at=issue.created_at.isoformat(),
            ),
        )

    return events


async def get_status_timelines_for_issues(
    db: AsyncSession,
    issues: list[Issue],
) -> dict[int, list[IssueStatusEvent]]:
    """Batch-load status timelines for a list of issues."""
    if not issues:
        return {}

    issue_ids = [issue.id for issue in issues]
    try:
        result = await db.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == "issue",
                AuditLog.entity_id.in_(issue_ids),
                AuditLog.action.in_(_STATUS_AUDIT_ACTIONS),
            )
            .order_by(AuditLog.created_at.asc())
        )
        entries = list(result.scalars().all())
    except Exception:
        logger.exception("Failed to batch-load issue status timelines")
        raise

    by_issue: dict[int, list[IssueStatusEvent]] = {issue_id: [] for issue_id in issue_ids}
    for entry in entries:
        if entry.entity_id is None:
            continue
        details = entry.details or {}
        status = details.get("status")
        if not status:
            continue
        by_issue.setdefault(entry.entity_id, []).append(
            IssueStatusEvent(
                status=str(status),
                label=issue_status_label(str(status)),
                at=entry.created_at.isoformat(),
                previous_status=details.get("previous_status"),
            )
        )

    for issue in issues:
        events = by_issue.get(issue.id, [])
        if not events:
            created_status = _status_value(issue.status)
            by_issue[issue.id] = [
                IssueStatusEvent(
                    status=created_status,
                    label=issue_status_label(created_status),
                    at=issue.created_at.isoformat(),
                )
            ]
        elif events[0].previous_status is None and events[0].status != IssueStatus.NEW.value:
            events.insert(
                0,
                IssueStatusEvent(
                    status=IssueStatus.NEW.value,
                    label=issue_status_label(IssueStatus.NEW.value),
                    at=issue.created_at.isoformat(),
                ),
            )
    return by_issue


async def update_issue_status(
    db: AsyncSession,
    issue: Issue,
    *,
    status: IssueStatus,
    resolution_text: Optional[str],
    actor: IssueActorContext,
) -> Issue:
    """Apply a status change, write audit log and notify the resident in VK."""
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
    resolution_text: Optional[str],
    actor: IssueActorContext,
) -> Issue:
    """Mark an issue as resolved with optional resolution text and timestamp."""
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
    """Reopen a closed issue — set status to ``NEW`` or ``UNDER_REVIEW``.

    Raises ``IssueValidationError`` when ``target_status`` is not allowed.
    """
    if target_status not in _REOPEN_TARGET_STATUSES:
        raise IssueValidationError(
            f"target_status must be NEW or UNDER_REVIEW, got {target_status!r}"
        )
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
    """Archive an issue (status ``ARCHIVED``) with audit log and resident notification."""
    return await _change_issue_status(
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

    audited = await _safe_audit(
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
    try:
        db.add(comment)
        await db.flush()
    except Exception:
        logger.exception(
            "Failed to add comment to issue #%s by user %s",
            issue.id,
            author.id,
        )
        raise
    logger.debug(
        "Comment added to issue #%s by user %s (internal=%s)",
        issue.id,
        author.id,
        is_internal,
    )
    return comment
