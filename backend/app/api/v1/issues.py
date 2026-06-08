from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import (
    can_manage_issues,
    get_client_ip,
    get_current_user,
    get_optional_user,
    require_owner_or_official,
)
from app.core.service_http import raise_http_for_service_error
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue
from app.models.user import User
from app.schemas.issue import (
    IssueCommentCreate,
    IssueCommentResponse,
    IssueCreate,
    IssueListResponse,
    IssueMyListResponse,
    IssueMyResponse,
    IssueReopen,
    IssueResponse,
    IssueStatusEventResponse,
    IssueStatusUpdate,
    IssueUpdate,
)
from app.services.issue_processor import process_web_complaint
from app.services.issue_service import (
    IssueAccessDeniedError,
    IssueActorContext,
    IssueNotFoundError,
    IssueSearchParams,
    IssueValidationError,
    add_comment_for_user,
    archive_issue,
    get_issue_details,
    get_issues_for_user,
    get_status_timelines_for_issues,
    reopen_issue,
    require_issue_for_user,
    resolve_issue,
    search_issues,
    update_issue_fields,
    update_issue_status,
)

router = APIRouter()
settings = get_settings()


def _raise_issue_access_error(exc: IssueNotFoundError | IssueAccessDeniedError) -> None:
    raise_http_for_service_error(exc)


def _issue_to_response(issue: Issue) -> IssueResponse:
    return IssueResponse.model_validate(issue)


def _issue_to_my_response(issue: Issue, timeline) -> IssueMyResponse:
    return IssueMyResponse(
        **_issue_to_response(issue).model_dump(),
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


def _actor(request: Request, user: User) -> IssueActorContext:
    return IssueActorContext(actor_id=user.id, ip_address=get_client_ip(request))


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

    loaded = await get_issue_details(db, issue.id)
    return _issue_to_response(loaded or issue)


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
    try:
        result = await search_issues(
            db,
            current_user,
            IssueSearchParams(
                status=status_filter,
                category=category,
                search=search,
                page=page,
                page_size=page_size,
            ),
        )
    except IssueValidationError as exc:
        raise_http_for_service_error(exc)

    return IssueListResponse(
        items=[_issue_to_response(i) for i in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/my", response_model=IssueMyListResponse)
async def my_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: IssueStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
):
    if current_user.role.name != UserRole.RESIDENT:
        raise HTTPException(status_code=403, detail="Only residents can use /my")

    issues = await get_issues_for_user(
        db,
        current_user,
        status=status_filter,
        limit=limit,
    )
    timelines = await get_status_timelines_for_issues(db, issues)
    return IssueMyListResponse(
        items=[
            _issue_to_my_response(issue, timelines.get(issue.id, []))
            for issue in issues
        ],
        total=len(issues),
        page=1,
        page_size=limit,
    )


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except (IssueNotFoundError, IssueAccessDeniedError) as exc:
        _raise_issue_access_error(exc)
    return _issue_to_response(issue)


@router.patch("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: int,
    data: IssueUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except (IssueNotFoundError, IssueAccessDeniedError) as exc:
        _raise_issue_access_error(exc)

    update_data = data.model_dump(exclude_unset=True)
    issue = await update_issue_fields(
        db,
        issue,
        current_user,
        update_data,
        actor=_actor(request, current_user),
    )
    return _issue_to_response(issue)


@router.patch("/{issue_id}/status", response_model=IssueResponse)
async def update_issue_status_endpoint(
    issue_id: int,
    data: IssueStatusUpdate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except (IssueNotFoundError, IssueAccessDeniedError) as exc:
        _raise_issue_access_error(exc)
    actor = _actor(request, current_user)

    if data.status == IssueStatus.RESOLVED:
        await resolve_issue(
            db,
            issue,
            resolution_text=data.resolution_text,
            actor=actor,
        )
    else:
        await update_issue_status(
            db,
            issue,
            status=data.status,
            resolution_text=data.resolution_text,
            actor=actor,
        )
    return _issue_to_response(issue)


@router.patch("/{issue_id}/reopen", response_model=IssueResponse)
async def reopen_issue_endpoint(
    issue_id: int,
    data: IssueReopen,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except (IssueNotFoundError, IssueAccessDeniedError) as exc:
        _raise_issue_access_error(exc)
    actor = _actor(request, current_user)
    try:
        await reopen_issue(
            db,
            issue,
            actor=actor,
            target_status=data.target_status,
        )
    except IssueValidationError as exc:
        raise_http_for_service_error(exc)
    return _issue_to_response(issue)


@router.patch("/{issue_id}/archive", response_model=IssueResponse)
async def archive_issue_endpoint(
    issue_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except (IssueNotFoundError, IssueAccessDeniedError) as exc:
        _raise_issue_access_error(exc)
    await archive_issue(db, issue, actor=_actor(request, current_user))
    return _issue_to_response(issue)


@router.post("/{issue_id}/comments", response_model=IssueCommentResponse, status_code=201)
async def add_comment(
    issue_id: int,
    data: IssueCommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        comment = await add_comment_for_user(
            db,
            issue_id,
            current_user,
            text=data.text,
            is_internal=data.is_internal,
        )
    except (IssueNotFoundError, IssueAccessDeniedError) as exc:
        _raise_issue_access_error(exc)
    return IssueCommentResponse.model_validate(comment)
