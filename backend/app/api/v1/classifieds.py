from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_optional_user, require_roles
from app.database import get_db
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedCategory, ClassifiedPaymentStatus, UserRole
from app.models.user import User

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


def get_classified_payment_info() -> dict:
    return {
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "card_holder": settings.PAYMENT_CARD_HOLDER,
        "bank_name": settings.PAYMENT_BANK_NAME,
        "description": settings.CLASSIFIED_PAYMENT_DESCRIPTION,
        "amount": settings.CLASSIFIED_PLACEMENT_FEE,
        "contact_email": settings.PAYMENT_CONTACT_EMAIL,
        "message": (
            f"Размещение объявления — {settings.CLASSIFIED_PLACEMENT_FEE} ₽. "
            "Перевод на карту поддерживает портал посёлка Пушкинские Горы. "
            "После оплаты объявление проверяется модератором (обычно в течение суток)."
        ),
    }


@router.get("/payment-info")
async def payment_info():
    return get_classified_payment_info()


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
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.MODERATOR, UserRole.ADMINISTRATION))],
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
        user_id=current_user.id if current_user else None,
        is_active=False,
        payment_status=ClassifiedPaymentStatus.PENDING,
        payment_reference=data.payment_reference,
        placement_fee=settings.CLASSIFIED_PLACEMENT_FEE,
    )
    db.add(ad)
    await db.flush()
    payment = get_classified_payment_info()
    return {
        "id": ad.id,
        "message": (
            "Заявка принята! Объявление появится после проверки оплаты модератором. "
            f"Если ещё не перевели — карта {payment['card_number']}, сумма {payment['amount']} ₽."
        ),
    }


@router.post("/{ad_id}/approve")
async def approve_ad(
    ad_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.MODERATOR, UserRole.ADMINISTRATION))],
):
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    ad.is_active = True
    ad.payment_status = ClassifiedPaymentStatus.APPROVED
    return {"message": "Объявление опубликовано"}


@router.post("/{ad_id}/reject")
async def reject_ad(
    ad_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.MODERATOR, UserRole.ADMINISTRATION))],
):
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise HTTPException(404, "Объявление не найдено")
    ad.is_active = False
    ad.payment_status = ClassifiedPaymentStatus.REJECTED
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
