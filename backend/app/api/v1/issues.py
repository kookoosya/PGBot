from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, get_current_user, get_optional_user, require_owner_or_official
from app.core.service_http import raise_http_for_service_error, raise_http_for_service_errors
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.enums import IssueStatus
from app.models.user import User
from app.schemas.issue import (
    IssueCommentCreate,
    IssueCommentResponse,
    IssueCreate,
    IssueListResponse,
    IssueMyListResponse,
    IssueReopen,
    IssueResponse,
    IssueStatusUpdate,
    IssueUpdate,
)
from app.services.issue_service import (
    IssueAccessDeniedError,
    IssueNotFoundError,
    IssueSearchParams,
    IssueValidationError,
    add_comment_for_user,
    apply_issue_status_update,
    archive_issue,
    build_issue_actor,
    build_issue_list_response,
    build_my_issues_response,
    create_issue_from_web,
    issue_to_response,
    reopen_issue,
    require_issue_for_user,
    search_issues,
    update_issue_fields,
)

router = APIRouter()
settings = get_settings()

_ISSUE_ACCESS_ERRORS = (IssueNotFoundError, IssueAccessDeniedError)


@router.post("", response_model=IssueResponse, status_code=201)
@limiter.limit(settings.ISSUE_RATE_LIMIT)
async def create_issue(
    request: Request,
    data: IssueCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)],
):
    try:
        issue = await create_issue_from_web(db, data, user=current_user)
    except IssueValidationError as exc:
        raise_http_for_service_error(exc)
    return issue_to_response(issue)


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
    return build_issue_list_response(result)


@router.get("/my", response_model=IssueMyListResponse)
async def my_issues(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: IssueStatus | None = None,
    limit: int = Query(50, ge=1, le=100),
):
    try:
        return await build_my_issues_response(
            db,
            current_user,
            status=status_filter,
            limit=limit,
        )
    except IssueAccessDeniedError as exc:
        raise_http_for_service_error(exc)


@router.get("/{issue_id}", response_model=IssueResponse)
async def get_issue(
    issue_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except _ISSUE_ACCESS_ERRORS as exc:
        raise_http_for_service_errors(exc, *_ISSUE_ACCESS_ERRORS)
    return issue_to_response(issue)


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
    except _ISSUE_ACCESS_ERRORS as exc:
        raise_http_for_service_errors(exc, *_ISSUE_ACCESS_ERRORS)

    issue = await update_issue_fields(
        db,
        issue,
        current_user,
        data.model_dump(exclude_unset=True),
        actor=build_issue_actor(actor_id=current_user.id, ip_address=get_client_ip(request)),
    )
    return issue_to_response(issue)


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
    except _ISSUE_ACCESS_ERRORS as exc:
        raise_http_for_service_errors(exc, *_ISSUE_ACCESS_ERRORS)

    await apply_issue_status_update(
        db,
        issue,
        status=data.status,
        resolution_text=data.resolution_text,
        actor=build_issue_actor(actor_id=current_user.id, ip_address=get_client_ip(request)),
    )
    return issue_to_response(issue)


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
    except _ISSUE_ACCESS_ERRORS as exc:
        raise_http_for_service_errors(exc, *_ISSUE_ACCESS_ERRORS)

    try:
        await reopen_issue(
            db,
            issue,
            actor=build_issue_actor(actor_id=current_user.id, ip_address=get_client_ip(request)),
            target_status=data.target_status,
        )
    except IssueValidationError as exc:
        raise_http_for_service_error(exc)
    return issue_to_response(issue)


@router.patch("/{issue_id}/archive", response_model=IssueResponse)
async def archive_issue_endpoint(
    issue_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner_or_official())],
):
    try:
        issue = await require_issue_for_user(db, issue_id, current_user)
    except _ISSUE_ACCESS_ERRORS as exc:
        raise_http_for_service_errors(exc, *_ISSUE_ACCESS_ERRORS)

    await archive_issue(
        db,
        issue,
        actor=build_issue_actor(actor_id=current_user.id, ip_address=get_client_ip(request)),
    )
    return issue_to_response(issue)


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
    except _ISSUE_ACCESS_ERRORS as exc:
        raise_http_for_service_errors(exc, *_ISSUE_ACCESS_ERRORS)
    return IssueCommentResponse.model_validate(comment)
