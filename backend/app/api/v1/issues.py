from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_client_ip, get_current_user, require_roles
from app.database import get_db
from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue, IssueComment
from app.models.user import User
from app.schemas.issue import (
    IssueCommentCreate,
    IssueCommentResponse,
    IssueListResponse,
    IssueResponse,
    IssueStatusUpdate,
    IssueUpdate,
)
from app.services.audit import log_action

router = APIRouter()


def _issue_to_response(issue: Issue) -> IssueResponse:
    return IssueResponse.model_validate(issue)


@router.get("", response_model=IssueListResponse)
async def list_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: IssueStatus | None = None,
    category: str | None = None,
    search: str | None = None,
):
    query = select(Issue).options(
        selectinload(Issue.photos),
        selectinload(Issue.ai_analysis),
    )

    if current_user.role.name == UserRole.RESIDENT:
        query = query.where(Issue.resident_id == current_user.id)

    if status_filter:
        query = query.where(Issue.status == status_filter)
    if category:
        query = query.where(Issue.category == category)
    if search:
        query = query.where(Issue.description.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Issue.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    issues = result.scalars().all()

    return IssueListResponse(
        items=[_issue_to_response(i) for i in issues],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.photos), selectinload(Issue.ai_analysis))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if current_user.role.name == UserRole.RESIDENT and issue.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _issue_to_response(issue)


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    data: IssueUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(
        UserRole.MODERATOR, UserRole.ADMINISTRATION, UserRole.SOCIAL_SERVICE, UserRole.SUPER_ADMIN
    ))],
):
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.photos), selectinload(Issue.ai_analysis))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)

    await log_action(
        db, "update_issue", "issue", issue.id,
        user_id=current_user.id, details=update_data, ip_address=get_client_ip(request),
    )
    return _issue_to_response(issue)


@router.patch("/{issue_id}/status", response_model=IssueResponse)
async def update_issue_status(
    issue_id: int,
    data: IssueStatusUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(
        UserRole.MODERATOR, UserRole.ADMINISTRATION, UserRole.SOCIAL_SERVICE, UserRole.SUPER_ADMIN
    ))],
):
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.photos), selectinload(Issue.ai_analysis))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.status = data.status
    if data.resolution_text:
        issue.resolution_text = data.resolution_text
    if data.status == IssueStatus.RESOLVED:
        issue.resolved_at = datetime.now(timezone.utc)

    await log_action(
        db, "status_change", "issue", issue.id,
        user_id=current_user.id,
        details={"status": data.status.value, "resolution": data.resolution_text},
        ip_address=get_client_ip(request),
    )
    return _issue_to_response(issue)


@router.post("/{issue_id}/comments", response_model=IssueCommentResponse, status_code=201)
async def add_comment(
    issue_id: int,
    data: IssueCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Issue not found")

    comment = IssueComment(
        issue_id=issue_id,
        author_id=current_user.id,
        text=data.text,
        is_internal=data.is_internal,
    )
    db.add(comment)
    await db.flush()
    return IssueCommentResponse.model_validate(comment)
