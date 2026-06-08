from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, get_optional_user, require_owner
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.classified import ClassifiedAd
from app.models.enums import (
    CLASSIFIED_LABELS,
    ClassifiedCategory,
    ClassifiedPaymentStatus,
)
from app.models.user import User
from app.services.classified_service import (
    ClassifiedActorContext,
    ClassifiedCreateInput,
    ClassifiedSearchParams,
    ClassifiedSortField,
    ClassifiedSortOrder,
    ClassifiedValidationError,
    build_marketing_stats,
    create_classified_ad,
    get_classified_quota,
    increment_ad_views,
    moderate_classified_ad,
    search_classifieds,
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


def _to_create_input(data: ClassifiedCreate) -> ClassifiedCreateInput:
    return ClassifiedCreateInput(
        category=data.category,
        title=data.title,
        description=data.description,
        phone=data.phone,
        author_name=data.author_name,
        price=data.price,
        price_unit=data.price_unit,
        address=data.address,
        contact_telegram=data.contact_telegram,
        contact_vk=data.contact_vk,
        payment_confirmed=data.payment_confirmed,
        payment_reference=data.payment_reference,
        website_url=data.website_url,
        agree_rules=data.agree_rules,
    )


def _classified_actor(request: Request, user: User) -> ClassifiedActorContext:
    return ClassifiedActorContext(actor_id=user.id, ip_address=get_client_ip(request))


def _to_response(ad: ClassifiedAd) -> ClassifiedResponse:
    return ClassifiedResponse(
        id=ad.id,
        category=ad.category,
        category_label=CLASSIFIED_LABELS.get(ad.category, ad.category),
        title=ad.title,
        description=ad.description,
        price=ad.price,
        price_unit=ad.price_unit,
        phone=ad.phone,
        author_name=ad.author_name,
        address=ad.address,
        contact_telegram=ad.contact_telegram,
        views_count=ad.views_count,
        created_at=ad.created_at.isoformat(),
    )


def _to_pending_response(ad: ClassifiedAd) -> ClassifiedPendingResponse:
    return ClassifiedPendingResponse(
        id=ad.id,
        category=ad.category,
        category_label=CLASSIFIED_LABELS.get(ad.category, ad.category),
        title=ad.title,
        description=ad.description,
        price=ad.price,
        price_unit=ad.price_unit,
        phone=ad.phone,
        author_name=ad.author_name,
        address=ad.address,
        contact_telegram=ad.contact_telegram,
        views_count=ad.views_count,
        created_at=ad.created_at.isoformat(),
        payment_status=ad.payment_status,
        payment_reference=ad.payment_reference,
        placement_fee=ad.placement_fee,
        contact_vk=ad.contact_vk,
    )


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
    return [{"value": c.value, "label": CLASSIFIED_LABELS[c]} for c in ClassifiedCategory]


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
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        ),
    )
    return {
        "items": [_to_response(ad) for ad in result.items],
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "total_pages": result.total_pages,
        "has_next": result.has_next,
        "has_prev": result.has_prev,
    }


@router.get("/pending")
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
    return [_to_pending_response(ad) for ad in result.items]


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
            _to_create_input(data),
            user=current_user,
        )
    except ClassifiedValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

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
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

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
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return {"message": result.message}


@router.get("/{ad_id}")
@limiter.limit("60/minute")
async def get_ad(ad_id: int, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        ad = await increment_ad_views(db, ad_id)
    except ClassifiedValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return _to_response(ad)
