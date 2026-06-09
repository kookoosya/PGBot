"""Issue CRUD, search and access control."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import is_owner_user
from app.models.audit_log import AuditLog
from app.models.enums import OFFICIAL_ROLES, IssueStatus, UserRole
from app.models.issue import Issue
from app.models.user import User
from app.services.audit import log_action
from app.services.issue.notification import safe_issue_audit
from app.services.issue.schemas import (
    IssueAccessDeniedError,
    IssueActorContext,
    IssueNotFoundError,
    IssueSearchParams,
    IssueSearchResult,
    IssueStatusEvent,
    IssueValidationError,
    can_view_issue,
    official_category_filter,
)
from app.services.notifications import ISSUE_STATUS_LABELS
from app.services.pagination_utils import normalize_pagination

logger = logging.getLogger(__name__)

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


def _apply_issue_access_filter(query, user: User):
    """Restrict query to issues visible to ``user``."""
    if user.role.name == UserRole.RESIDENT:
        return query.where(Issue.resident_id == user.id)
    if user.role.name in OFFICIAL_ROLES or user.role.name == UserRole.MODERATOR:
        cat_filter = official_category_filter(user)
        if cat_filter is not None:
            return query.where(cat_filter)
        return query
    raise IssueValidationError("Недостаточно прав", status_code=403)


async def get_issue_details(db: AsyncSession, issue_id: int) -> Issue | None:
    """Load an issue with photos, AI analysis and comments eagerly fetched."""
    result = await db.execute(
        select(Issue).options(*_ISSUE_DETAIL_LOADS).where(Issue.id == issue_id),
    )
    return result.scalar_one_or_none()


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


async def search_issues(
    db: AsyncSession,
    user: User,
    params: IssueSearchParams,
) -> IssueSearchResult:
    """Search issues visible to ``user`` with pagination."""
    query = select(Issue).options(*_ISSUE_LIST_LOADS)
    query = _apply_issue_access_filter(query, user)

    if params.status is not None:
        query = query.where(Issue.status == params.status)
    if params.category:
        query = query.where(Issue.category == params.category)
    if params.search:
        query = query.where(Issue.description.ilike(f"%{params.search.strip()}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    page, offset, page_size, total_pages, has_prev, has_next = normalize_pagination(
        page=params.page,
        page_size=params.page_size,
        total=total,
    )
    result = await db.execute(
        query.order_by(Issue.created_at.desc()).offset(offset).limit(page_size),
    )
    items = list(result.scalars().all())
    return IssueSearchResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
    )


async def get_issues_for_user(
    db: AsyncSession,
    user: User,
    *,
    status: IssueStatus | None = None,
    limit: int = 50,
) -> list[Issue]:
    """Return issues submitted by ``user``, newest first."""
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

    result = await db.execute(query)
    return list(result.scalars().all())


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
    await safe_issue_audit(
        db,
        "assign_issue",
        issue.id,
        actor,
        {"assignee_id": assignee_id, "previous_assignee_id": previous},
    )
    return issue


def _status_value(status: IssueStatus | str) -> str:
    return status.value if isinstance(status, IssueStatus) else str(status)


async def get_issue_status_timeline(db: AsyncSession, issue: Issue) -> list[IssueStatusEvent]:
    """Build resident-visible status history from audit logs and creation time."""
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "issue",
            AuditLog.entity_id == issue.id,
            AuditLog.action.in_(_STATUS_AUDIT_ACTIONS),
        )
        .order_by(AuditLog.created_at.asc()),
    )
    entries = list(result.scalars().all())

    events: list[IssueStatusEvent] = []
    for entry in entries:
        details = entry.details or {}
        status = details.get("status")
        if not status:
            continue
        events.append(
            IssueStatusEvent(
                status=str(status),
                label=ISSUE_STATUS_LABELS.get(str(status), str(status)),
                at=entry.created_at.isoformat(),
                previous_status=details.get("previous_status"),
            ),
        )

    if not events:
        created_status = _status_value(issue.status)
        events.append(
            IssueStatusEvent(
                status=created_status,
                label=ISSUE_STATUS_LABELS.get(created_status, created_status),
                at=issue.created_at.isoformat(),
            ),
        )
    elif events[0].previous_status is None and events[0].status != IssueStatus.NEW.value:
        events.insert(
            0,
            IssueStatusEvent(
                status=IssueStatus.NEW.value,
                label=ISSUE_STATUS_LABELS.get(IssueStatus.NEW.value, IssueStatus.NEW.value),
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
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "issue",
            AuditLog.entity_id.in_(issue_ids),
            AuditLog.action.in_(_STATUS_AUDIT_ACTIONS),
        )
        .order_by(AuditLog.created_at.asc()),
    )
    entries = list(result.scalars().all())

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
                label=ISSUE_STATUS_LABELS.get(str(status), str(status)),
                at=entry.created_at.isoformat(),
                previous_status=details.get("previous_status"),
            ),
        )

    for issue in issues:
        events = by_issue.get(issue.id, [])
        if not events:
            created_status = _status_value(issue.status)
            by_issue[issue.id] = [
                IssueStatusEvent(
                    status=created_status,
                    label=ISSUE_STATUS_LABELS.get(created_status, created_status),
                    at=issue.created_at.isoformat(),
                ),
            ]
        elif events[0].previous_status is None and events[0].status != IssueStatus.NEW.value:
            events.insert(
                0,
                IssueStatusEvent(
                    status=IssueStatus.NEW.value,
                    label=ISSUE_STATUS_LABELS.get(IssueStatus.NEW.value, IssueStatus.NEW.value),
                    at=issue.created_at.isoformat(),
                ),
            )
    return by_issue
