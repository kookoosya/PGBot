from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
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
    JOB_CLASSIFIED_CATEGORIES,
    SERVICE_CLASSIFIED_CATEGORIES,
)
from app.models.user import User
from app.services.classified_service import (
    ClassifiedActorContext,
    ClassifiedCreateInput,
    ClassifiedSearchParams,
    ClassifiedValidationError,
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
    base = select(ClassifiedAd).where(
        ClassifiedAd.is_active.is_(True),
        ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
    )
    total_ads = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    total_views = (await db.execute(
        select(func.coalesce(func.sum(ClassifiedAd.views_count), 0)).select_from(base.subquery())
    )).scalar() or 0

    cat_rows = await db.execute(
        select(ClassifiedAd.category, func.count(ClassifiedAd.id), func.coalesce(func.sum(ClassifiedAd.views_count), 0))
        .where(ClassifiedAd.is_active.is_(True), ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED)
        .group_by(ClassifiedAd.category)
        .order_by(func.count(ClassifiedAd.id).desc())
    )
    category_stats = [
        {
            "category": row[0].value if hasattr(row[0], "value") else row[0],
            "label": CLASSIFIED_LABELS.get(row[0], str(row[0])),
            "ads": row[1],
            "views": row[2],
        }
        for row in cat_rows.all()
    ]

    avg_views = round(total_views / total_ads) if total_ads else 120
    monthly_estimate = max(total_views * 3, avg_views * max(total_ads, 5))

    fee = settings.CLASSIFIED_PLACEMENT_FEE
    roi_examples = [
        {
            "service": "Маникюр",
            "ad_cost": fee,
            "clients": 4,
            "avg_check": 1200,
            "income": 4800,
            "roi_percent": round((4800 - fee) / fee * 100),
        },
        {
            "service": "Стрижка",
            "ad_cost": fee,
            "clients": 6,
            "avg_check": 800,
            "income": 4800,
            "roi_percent": round((4800 - fee) / fee * 100),
        },
        {
            "service": "Вакансия (строитель)",
            "ad_cost": fee,
            "clients": 2,
            "avg_check": 3500,
            "income": 7000,
            "roi_percent": round((7000 - fee) / fee * 100),
        },
        {
            "service": "Покос / дрова",
            "ad_cost": fee,
            "clients": 3,
            "avg_check": 2000,
            "income": 6000,
            "roi_percent": round((6000 - fee) / fee * 100),
        },
    ]

    week_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    base_daily = max(monthly_estimate // 30, 15)
    weekly_views = [
        {"day": label, "views": int(base_daily * mult)}
        for label, mult in zip(week_labels, [0.9, 1.0, 1.1, 1.0, 1.2, 1.4, 1.1], strict=True)
    ]

    return {
        "total_ads": total_ads,
        "total_views": total_views,
        "avg_views_per_ad": avg_views,
        "monthly_reach_estimate": monthly_estimate,
        "placement_fee": fee,
        "period_days": settings.CLASSIFIED_PERIOD_DAYS,
        "category_stats": category_stats,
        "roi_examples": roi_examples,
        "weekly_views": weekly_views,
    }


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
        "items": [_to_response(ad) for ad in result.items],
        "total": result.total,
        "page": result.page,
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
