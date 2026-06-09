from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_optional_user, require_owner
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.enums import ClassifiedCategory, ClassifiedPaymentStatus
from app.models.user import User
from app.services.classified_service import (
    ClassifiedActorContext,
    ClassifiedNotFoundError,
    ClassifiedSearchParams,
    ClassifiedValidationError,
    build_marketing_stats,
    classified_to_pending_response,
    classified_to_response,
    create_classified_ad,
    get_classified_quota,
    increment_ad_views,
    list_classified_category_options,
    list_pending_ads,
    moderate_classified_ad,
    search_classifieds,
    to_classified_create_input,
)

router = APIRouter()
settings = get_settings()


class ClassifiedCreate(BaseModel):
    category: ClassifiedCategory
    title: str = Field(min_length=5, max_length=300)
    description: str = Field(min_length=10, max_length=3000)
    price: int | None = Field(None, ge=0)
    price_unit: str | None = None
    phone: str = Field(min_length=10, max_length=20)
    author_name: str = Field(min_length=2, max_length=255)
    address: str | None = None
    contact_telegram: str | None = None
    contact_vk: str | None = Field(None, max_length=100)
    payment_confirmed: bool = False
    payment_reference: str | None = Field(None, max_length=200)
    website_url: str | None = Field(None, max_length=200)
    agree_rules: bool = False


class ClassifiedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: ClassifiedCategory
    category_label: str = ""
    title: str
    description: str
    price: int | None
    price_unit: str | None
    phone: str
    author_name: str
    address: str | None
    contact_telegram: str | None
    views_count: int
    created_at: str


class ClassifiedPendingResponse(ClassifiedResponse):
    payment_status: ClassifiedPaymentStatus
    payment_reference: str | None
    placement_fee: int
    contact_vk: str | None = None


def _raise_http(exc: ClassifiedValidationError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail)


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
    return (await build_marketing_stats(db)).to_dict()


@router.get("/categories")
async def list_categories():
    return list_classified_category_options()


@router.get("")
async def list_ads(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: ClassifiedCategory | None = None,
    search: str | None = Query(None, max_length=100),
    services_only: bool = False,
    jobs_only: bool = False,
    ads_only: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    result = await search_classifieds(
        db,
        ClassifiedSearchParams(
            category=category,
            search=search,
            services_only=services_only,
            jobs_only=jobs_only,
            ads_only=ads_only,
            page=page,
            page_size=page_size,
        ),
    )
    return {
        "items": [ClassifiedResponse(**classified_to_response(ad)) for ad in result.items],
        "total": result.total,
        "page": result.page,
    }


@router.get("/pending")
async def list_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    ads = await list_pending_ads(db)
    return [ClassifiedPendingResponse(**classified_to_pending_response(ad)) for ad in ads]


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
        _raise_http(exc)
    return {"id": result.ad.id, "message": result.message, "free": result.free}


@router.post("/{ad_id}/approve")
async def approve_ad(
    ad_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    try:
        result = await moderate_classified_ad(
            db,
            ad_id,
            action="approve",
            actor=ClassifiedActorContext(actor_id=current_user.id),
        )
    except ClassifiedNotFoundError as exc:
        _raise_http(exc)
    return {"message": result.message, "subscribers_notified": result.subscribers_notified}


@router.post("/{ad_id}/reject")
async def reject_ad(
    ad_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    try:
        result = await moderate_classified_ad(
            db,
            ad_id,
            action="reject",
            actor=ClassifiedActorContext(actor_id=current_user.id),
        )
    except ClassifiedNotFoundError as exc:
        _raise_http(exc)
    return {"message": result.message}


@router.get("/{ad_id}")
@limiter.limit("60/minute")
async def get_ad(ad_id: int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        ad = await increment_ad_views(db, ad_id)
    except ClassifiedNotFoundError as exc:
        _raise_http(exc)
    return ClassifiedResponse(**classified_to_response(ad))
