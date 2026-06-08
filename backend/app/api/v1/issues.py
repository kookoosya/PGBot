from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.deps import (
    can_manage_issues,
    get_client_ip,
    get_current_user,
    get_optional_user,
    is_official_user,
    is_owner_user,
    require_owner_or_official,
)
from app.database import get_db
from app.models.enums import IssueCategory, IssueStatus, UserRole
from app.models.issue import Issue, IssueComment
from app.models.user import User
from app.schemas.issue import (
    IssueCommentCreate,
    IssueCommentResponse,
    IssueCreate,
    IssueListResponse,
    IssueResponse,
    IssueStatusUpdate,
    IssueUpdate,
)
from app.core.rate_limit import limiter
from app.services.audit import log_action
from app.services.issue_processor import process_web_complaint

router = APIRouter()
settings = get_settings()

JKH_CATEGORIES = {
    IssueCategory.UTILITIES,
    IssueCategory.WATER,
    IssueCategory.SEWERAGE,
}


def _issue_to_response(issue: Issue) -> IssueResponse:
    return IssueResponse.model_validate(issue)


def _official_category_filter(user: User):
    if user.role.name == UserRole.SOCIAL_SERVICE:
        conditions = [Issue.category.in_(JKH_CATEGORIES)]
        if user.department_id:
            conditions.append(Issue.department_id == user.department_id)
        return or_(*conditions)
    return None


def _can_view_issue(user: User, issue: Issue) -> bool:
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


@router.post("", response_model=IssueResponse, status_code=201)
@limiter.limit(settings.ISSUE_RATE_LIMIT)
async def create_issue(
    request: Request,
    data: IssueCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
):
    if data.website_url:
        raise HTTPException(status_code=400, detail="Не удалось отправить форму. Обновите страницу.")

    if not current_user and (not data.phone or not data.full_name):
        raise HTTPException(
            status_code=400,
            detail="Укажите имя и телефон или войдите в кабинет",
        )

    category_value = data.category.value if data.category else None
    issue = await process_web_complaint(
        db,
        data.description,
        user=current_user,
        phone=data.phone or (current_user.phone if current_user else None),
        full_name=data.full_name or (current_user.full_name if current_user else None),
        address=data.address,
        category=category_value,
    )

    if issue.is_spam:
        raise HTTPException(
            status_code=400,
            detail="Обращение не принято. Опишите конкретную проблему без рекламы и оскорблений.",
        )

    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.photos), selectinload(Issue.ai_analysis))
        .where(Issue.id == issue.id)
    )
    return _issue_to_response(result.scalar_one())


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
    elif can_manage_issues(current_user):
        cat_filter = _official_category_filter(current_user)
        if cat_filter is not None:
            query = query.where(cat_filter)
    else:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

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
    if not _can_view_issue(current_user, issue):
        raise HTTPException(status_code=403, detail="Access denied")
    return _issue_to_response(issue)


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    data: IssueUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.photos), selectinload(Issue.ai_analysis))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not _can_view_issue(current_user, issue):
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = data.model_dump(exclude_unset=True)
    if not is_owner_user(current_user):
        update_data.pop("department_id", None)
        update_data.pop("assignee_id", None)

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
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.photos), selectinload(Issue.ai_analysis))
        .where(Issue.id == issue_id)
    )
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not _can_view_issue(current_user, issue):
        raise HTTPException(status_code=403, detail="Access denied")

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

    from app.services.notifications import notify_issue_status
    await notify_issue_status(issue)

    return _issue_to_response(issue)


@router.post("/{issue_id}/comments", response_model=IssueCommentResponse, status_code=201)
async def add_comment(
    issue_id: int,
    data: IssueCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Issue).where(Issue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if not _can_view_issue(current_user, issue):
        raise HTTPException(status_code=403, detail="Access denied")

    comment = IssueComment(
        issue_id=issue_id,
        author_id=current_user.id,
        text=data.text,
        is_internal=data.is_internal and can_manage_issues(current_user),
    )
    db.add(comment)
    await db.flush()
    return IssueCommentResponse.model_validate(comment)
