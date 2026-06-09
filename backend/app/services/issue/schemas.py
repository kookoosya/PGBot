"""Internal dataclasses, errors, access control and response mappers."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_

from app.constants.issue_config import JKH_CATEGORIES
from app.core.deps import is_official_user, is_owner_user
from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue
from app.models.user import User
from app.services.service_errors import ServiceError


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
    ip_address: str | None = None


@dataclass(frozen=True, slots=True)
class IssueSearchParams:
    """Filters for ``search_issues``."""

    status: IssueStatus | None = None
    category: str | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class IssueSearchResult:
    """Paginated issue search result."""

    items: list[Issue]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


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


def official_category_filter(user: User):
    """Return SQLAlchemy filter for social-service users, or None."""
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
            return issue.category in JKH_CATEGORIES or (
                user.department_id and issue.department_id == user.department_id
            )
        return True
    return False


def build_issue_actor(*, actor_id: int, ip_address: str | None = None) -> IssueActorContext:
    """Build actor context for audit logging from request metadata."""
    return IssueActorContext(actor_id=actor_id, ip_address=ip_address)


def issue_to_response(issue: Issue):
    """Map an ``Issue`` ORM instance to API response schema."""
    from app.schemas.issue import IssueResponse

    return IssueResponse.model_validate(issue)


def issue_to_my_response(issue: Issue, timeline: list[IssueStatusEvent]):
    """Map an issue plus status timeline to resident-facing response schema."""
    from app.schemas.issue import IssueMyResponse, IssueStatusEventResponse

    return IssueMyResponse(
        **issue_to_response(issue).model_dump(),
        status_timeline=[
            IssueStatusEventResponse(
                status=event.status,
                label=event.label,
                at=event.at,
                previous_status=event.previous_status,
            )
            for event in timeline
        ],
    )


def build_issue_list_response(result: IssueSearchResult):
    """Convert search result to paginated API response."""
    from app.schemas.issue import IssueListResponse

    return IssueListResponse(
        items=[issue_to_response(issue) for issue in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )
