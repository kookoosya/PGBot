"""Issue lifecycle operations — thin orchestrator over domain modules.

Creation and AI analysis live in ``issue_processor``.

Public API
----------
- ``search_issues`` / ``get_issue_details`` / ``get_issues_for_user`` — read paths
- ``require_issue_for_user`` / ``can_view_issue`` — access control
- ``update_issue_fields`` / ``update_issue_status`` / ``resolve_issue`` / ``reopen_issue`` / ``archive_issue`` — writes
- ``create_issue_from_web`` / ``apply_issue_status_update`` / ``build_my_issues_response`` — router helpers
- ``issue_to_response`` / ``build_issue_list_response`` — response mappers
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.issue import Issue
from app.models.user import User
from app.services.issue.comment import add_comment_for_user, add_issue_comment
from app.services.issue.crud import (
    assign_issue,
    get_issue_details,
    get_issue_status_timeline,
    get_issues_for_user,
    get_status_timelines_for_issues,
    require_issue_for_user,
    search_issues,
    update_issue_fields,
)
from app.services.issue.schemas import (
    IssueAccessDeniedError,
    IssueActorContext,
    IssueNotFoundError,
    IssueSearchParams,
    IssueSearchResult,
    IssueStatusEvent,
    IssueValidationError,
    build_issue_actor,
    build_issue_list_response,
    can_view_issue,
    issue_to_my_response,
    issue_to_response,
)
from app.services.issue.status import (
    apply_issue_status_update,
    archive_issue,
    reopen_issue,
    resolve_issue,
    update_issue_status,
)
from app.services.issue.validation import find_similar_issues, reject_if_spam, validate_web_create_form

__all__ = [
    "IssueAccessDeniedError",
    "IssueActorContext",
    "IssueNotFoundError",
    "IssueSearchParams",
    "IssueSearchResult",
    "IssueStatusEvent",
    "IssueValidationError",
    "add_comment_for_user",
    "add_issue_comment",
    "apply_issue_status_update",
    "archive_issue",
    "assign_issue",
    "build_issue_actor",
    "build_issue_list_response",
    "build_my_issues_response",
    "can_view_issue",
    "create_issue_from_web",
    "find_similar_issues",
    "get_issue_details",
    "get_issue_status_timeline",
    "get_issues_for_user",
    "get_status_timelines_for_issues",
    "issue_to_my_response",
    "issue_to_response",
    "reopen_issue",
    "require_issue_for_user",
    "resolve_issue",
    "search_issues",
    "update_issue_fields",
    "update_issue_status",
]


async def create_issue_from_web(
    db: AsyncSession,
    data,
    *,
    user: User | None,
) -> Issue:
    """Validate web form input, create issue and reject spam."""
    from app.services.issue_processor import process_web_complaint

    validate_web_create_form(data, user=user)

    category_value = data.category.value if data.category else None
    issue = await process_web_complaint(
        db,
        data.description,
        user=user,
        phone=data.phone or (user.phone if user else None),
        full_name=data.full_name or (user.full_name if user else None),
        address=data.address,
        category=category_value,
    )

    reject_if_spam(issue)

    loaded = await get_issue_details(db, issue.id)
    return loaded or issue


async def build_my_issues_response(
    db: AsyncSession,
    user: User,
    *,
    status=None,
    limit: int = 50,
):
    """Load resident issues with status timelines for ``/issues/my``."""
    from app.schemas.issue import IssueMyListResponse

    if user.role.name != UserRole.RESIDENT:
        raise IssueAccessDeniedError("Only residents can use /my")

    safe_limit = max(1, min(limit, 100))
    issues = await get_issues_for_user(db, user, status=status, limit=safe_limit)
    timelines = await get_status_timelines_for_issues(db, issues)
    return IssueMyListResponse(
        items=[issue_to_my_response(issue, timelines.get(issue.id, [])) for issue in issues],
        total=len(issues),
        page=1,
        page_size=safe_limit,
    )
