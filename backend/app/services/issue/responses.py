"""API response mappers for issues."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue
from app.models.user import User

from .crud import get_issues_for_user, get_status_timelines_for_issues
from .schemas import IssueAccessDeniedError, IssueActorContext, IssueSearchResult, IssueStatusEvent


def build_issue_actor(*, actor_id: int, ip_address: str | None = None) -> IssueActorContext:
    """Build actor context for audit logging from request metadata."""
    return IssueActorContext(actor_id=actor_id, ip_address=ip_address)


def issue_to_response(issue: Issue):
    """Map an ``Issue`` ORM instance to API response schema."""
    from sqlalchemy import inspect as sa_inspect

    from app.schemas.issue import IssuePhotoResponse, IssueResponse

    insp = sa_inspect(issue)
    payload = {attr.key: getattr(issue, attr.key) for attr in insp.mapper.column_attrs}
    photos = []
    if "photos" not in insp.unloaded:
        photos = [IssuePhotoResponse.model_validate(photo) for photo in issue.photos]
    payload["photos"] = photos
    return IssueResponse.model_validate(payload)


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
                resolution=event.resolution,
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


async def build_my_issues_response(
    db: AsyncSession,
    user: User,
    *,
    status: IssueStatus | None = None,
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
        items=[
            issue_to_my_response(issue, timelines.get(issue.id, []))
            for issue in issues
        ],
        total=len(issues),
        page=1,
        page_size=safe_limit,
    )
