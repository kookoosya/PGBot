from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_optional_user, require_owner
from app.database import get_db
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedCategory, ClassifiedPaymentStatus
from app.models.user import User
from app.services.notifications import notify_owner, notify_vk_user, parse_vk_id

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


def get_classified_payment_info() -> dict:
    fee = settings.CLASSIFIED_PLACEMENT_FEE
    return {
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "amount": fee,
        "period_days": settings.CLASSIFIED_PERIOD_DAYS,
        "message": (
            f"{fee} ₽ за каждое объявление на {settings.CLASSIFIED_PERIOD_DAYS} дней. "
            "Хотите 10 объявлений — платите 10 раз по 150 ₽. "
            "Вы зарабатываете на услугах и вакансиях — а портал посёлка нужно развивать."
        ),
    }


@router.get("/payment-info")
async def payment_info():
    return get_classified_payment_info()


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
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = select(ClassifiedAd).where(
        ClassifiedAd.is_active.is_(True),
        ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
    )
    if category:
        query = query.where(ClassifiedAd.category == category)
    if search:
        query = query.where(ClassifiedAd.title.ilike(f"%{search}%") | ClassifiedAd.description.ilike(f"%{search}%"))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(ClassifiedAd.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [
        ClassifiedResponse(
            id=a.id, category=a.category,
            category_label=CLASSIFIED_LABELS.get(a.category, a.category),
            title=a.title, description=a.description,
            price=a.price, price_unit=a.price_unit,
            phone=a.phone, author_name=a.author_name,
            address=a.address, contact_telegram=a.contact_telegram,
            views_count=a.views_count, created_at=a.created_at.isoformat(),
        )
        for a in result.scalars().all()
    ]
    return {"items": items, "total": total, "page": page}


@router.get("/pending")
async def list_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(
        select(ClassifiedAd)
        .where(ClassifiedAd.payment_status == ClassifiedPaymentStatus.PENDING)
        .order_by(ClassifiedAd.created_at.desc())
    )
    return [
        ClassifiedPendingResponse(
            id=a.id, category=a.category,
            category_label=CLASSIFIED_LABELS.get(a.category, a.category),
            title=a.title, description=a.description,
            price=a.price, price_unit=a.price_unit,
            phone=a.phone, author_name=a.author_name,
            address=a.address, contact_telegram=a.contact_telegram,
            views_count=a.views_count, created_at=a.created_at.isoformat(),
            payment_status=a.payment_status,
            payment_reference=a.payment_reference,
            placement_fee=a.placement_fee,
            contact_vk=a.contact_vk,
        )
        for a in result.scalars().all()
    ]


@router.post("", status_code=201)
async def create_ad(
    data: ClassifiedCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    if not data.payment_confirmed:
        raise HTTPException(
            status_code=400,
            detail=f"Подтвердите оплату {settings.CLASSIFIED_PLACEMENT_FEE} ₽ за размещение объявления",
        )

    vk_id = parse_vk_id(data.contact_vk)
    ad = ClassifiedAd(
        category=data.category,
        title=data.title,
        description=data.description,
        price=data.price,
        price_unit=data.price_unit,
        phone=data.phone,
        author_name=data.author_name,
        address=data.address,
        contact_telegram=data.contact_telegram,
        contact_vk=data.contact_vk,
        vk_id=vk_id,
        user_id=current_user.id if current_user else None,
        is_active=False,
        payment_status=ClassifiedPaymentStatus.PENDING,
        payment_reference=data.payment_reference,
        placement_fee=settings.CLASSIFIED_PLACEMENT_FEE,
    )
    db.add(ad)
    await db.flush()

    cat_label = CLASSIFIED_LABELS.get(data.category, data.category)
    await notify_owner(
        "📢 Новое объявление на модерации\n\n"
        f"#{ad.id} · {cat_label}\n"
        f"«{data.title}»\n"
        f"👤 {data.author_name} · 📞 {data.phone}\n"
        f"💳 {settings.CLASSIFIED_PLACEMENT_FEE} ₽\n\n"
        "Проверьте оплату и опубликуйте в админ-панели."
    )

    payment = get_classified_payment_info()
    return {
        "id": ad.id,
        "message": (
            "Заявка принята! Уведомление отправлено. "
            "Объявление появится после проверки оплаты. "
            f"Карта: {payment['card_number']} — {payment['amount']} ₽."
        ),
    }


@router.post("/{ad_id}/approve")
async def approve_ad(
    ad_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    ad.is_active = True
    ad.payment_status = ClassifiedPaymentStatus.APPROVED

    cat_label = CLASSIFIED_LABELS.get(ad.category, ad.category)
    vk_msg = (
        f"✅ Ваше объявление опубликовано!\n\n"
        f"«{ad.title}»\n"
        f"Категория: {cat_label}\n"
        f"Срок: {settings.CLASSIFIED_PERIOD_DAYS} дней\n\n"
        "Жители посёлка уже видят его на портале. Удачных сделок!"
    )
    await notify_vk_user(ad.contact_vk or ad.vk_id, vk_msg)

    return {"message": "Объявление опубликовано"}


@router.post("/{ad_id}/reject")
async def reject_ad(
    ad_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    ad.is_active = False
    ad.payment_status = ClassifiedPaymentStatus.REJECTED

    await notify_vk_user(
        ad.contact_vk or ad.vk_id,
        f"❌ Объявление «{ad.title}» не прошло модерацию.\n"
        "Проверьте оплату и текст. Можно подать заново.",
    )

    return {"message": "Объявление отклонено"}


@router.get("/{ad_id}")
async def get_ad(ad_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(ClassifiedAd).where(
            ClassifiedAd.id == ad_id,
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
        )
    )
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    ad.views_count += 1
    return ClassifiedResponse(
        id=ad.id, category=ad.category,
        category_label=CLASSIFIED_LABELS.get(ad.category, ad.category),
        title=ad.title, description=ad.description,
        price=ad.price, price_unit=ad.price_unit,
        phone=ad.phone, author_name=ad.author_name,
        address=ad.address, contact_telegram=ad.contact_telegram,
        views_count=ad.views_count, created_at=ad.created_at.isoformat(),
    )
