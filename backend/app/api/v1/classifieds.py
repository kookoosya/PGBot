from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, get_optional_user, require_owner
from app.core.service_http import raise_http_for_service_error
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.enums import ClassifiedCategory, ClassifiedPaymentStatus
from app.models.user import User
from app.schemas.classified import ClassifiedCreate, ClassifiedListResponse, ClassifiedPendingResponse, ClassifiedResponse
from app.services.classified_service import (
    ClassifiedActorContext,
    ClassifiedSearchParams,
    ClassifiedSortField,
    ClassifiedSortOrder,
    ClassifiedValidationError,
    build_classified_list_response,
    build_marketing_stats,
    classified_to_pending_response,
    classified_to_response,
    create_classified_ad,
    get_classified_quota,
    increment_ad_views,
    list_classified_category_options,
    moderate_classified_ad,
    search_classifieds,
    to_classified_create_input,
)

router = APIRouter()
settings = get_settings()


def _classified_actor(request: Request, user: User) -> ClassifiedActorContext:
    return ClassifiedActorContext(actor_id=user.id, ip_address=get_client_ip(request))


@router.get("/payment-info")
async def payment_info(
    db: Annotated[AsyncSession, Depends(get_db)],
    phone: str | None = Query(None, min_length=10, max_length=20),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    return await get_classified_quota(db, phone, current_user.id if current_user else None)


@router.get("/marketing-stats")
async def marketing_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    stats = await build_marketing_stats(db)
    return stats.to_dict()


@router.get("/categories")
async def list_categories():
    return list_classified_category_options()


@router.get("", response_model=ClassifiedListResponse)
async def list_ads(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: ClassifiedCategory | None = None,
    search: str | None = Query(None, max_length=100),
    services_only: bool = False,
    jobs_only: bool = False,
    ads_only: bool = False,
    neighbor_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: ClassifiedSortField = Query("created_at"),
    sort_order: ClassifiedSortOrder = Query("desc"),
):
    result = await search_classifieds(
        db,
        ClassifiedSearchParams(
            category=category,
            search=search,
            services_only=services_only,
            jobs_only=jobs_only,
            ads_only=ads_only,
            neighbor_only=neighbor_only,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
    return build_classified_list_response(result)


@router.get("/pending", response_model=list[ClassifiedPendingResponse])
async def list_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await search_classifieds(
        db,
        ClassifiedSearchParams(
            payment_status=ClassifiedPaymentStatus.PENDING,
            is_active=None,
            page=1,
            page_size=100,
        ),
    )
    return [classified_to_pending_response(ad) for ad in result.items]


@router.post("", status_code=201)
@limiter.limit(settings.CLASSIFIED_RATE_LIMIT)
async def create_ad(
    request: Request,
    data: ClassifiedCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    try:
        result = await create_classified_ad(
            db,
            to_classified_create_input(data),
            user=current_user,
        )
    except ClassifiedValidationError as exc:
        raise_http_for_service_error(exc)

    return {"id": result.ad.id, "message": result.message, "free": result.free}


@router.post("/{ad_id}/approve")
async def approve_ad(
    ad_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner())],
):
    try:
        result = await moderate_classified_ad(
            db,
            ad_id,
            action="approve",
            actor=_classified_actor(request, owner),
        )
    except ClassifiedValidationError as exc:
        raise_http_for_service_error(exc)

    return {"message": result.message, "subscribers_notified": result.subscribers_notified}


@router.post("/{ad_id}/reject")
async def reject_ad(
    ad_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    owner: Annotated[User, Depends(require_owner())],
):
    try:
        result = await moderate_classified_ad(
            db,
            ad_id,
            action="reject",
            actor=_classified_actor(request, owner),
        )
    except ClassifiedValidationError as exc:
        raise_http_for_service_error(exc)

    return {"message": result.message}


@router.get("/{ad_id}", response_model=ClassifiedResponse)
@limiter.limit("60/minute")
async def get_ad(ad_id: int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        ad = await increment_ad_views(db, ad_id)
    except ClassifiedValidationError as exc:
        raise_http_for_service_error(exc)

    return classified_to_response(ad)
