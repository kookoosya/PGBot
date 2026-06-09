"""CRUD operations for classified ads."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import (
    JOB_CLASSIFIED_CATEGORIES,
    SERVICE_CLASSIFIED_CATEGORIES,
    ClassifiedPaymentStatus,
)
from app.models.user import User
from app.services.classified.schemas import (
    ClassifiedCreateInput,
    ClassifiedNotFoundError,
    ClassifiedSearchParams,
    ClassifiedSearchResult,
)
from app.services.notifications import parse_vk_id

settings = get_settings()


async def search_classifieds(
    db: AsyncSession,
    params: ClassifiedSearchParams,
) -> ClassifiedSearchResult:
    """Search and filter classified ads with pagination."""
    query = select(ClassifiedAd)

    if params.payment_status is not None:
        query = query.where(ClassifiedAd.payment_status == params.payment_status)
    if params.is_active is not None:
        query = query.where(ClassifiedAd.is_active.is_(params.is_active))
    if params.services_only:
        query = query.where(ClassifiedAd.category.in_(SERVICE_CLASSIFIED_CATEGORIES))
    if params.jobs_only:
        query = query.where(ClassifiedAd.category.in_(JOB_CLASSIFIED_CATEGORIES))
    elif params.ads_only:
        query = query.where(ClassifiedAd.category.notin_(JOB_CLASSIFIED_CATEGORIES))
    if params.category is not None:
        query = query.where(ClassifiedAd.category == params.category)
    if params.search:
        pattern = f"%{params.search.strip()}%"
        query = query.where(
            ClassifiedAd.title.ilike(pattern) | ClassifiedAd.description.ilike(pattern),
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(ClassifiedAd.created_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    )
    items = list(result.scalars().all())
    return ClassifiedSearchResult(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


async def list_pending_ads(db: AsyncSession) -> list[ClassifiedAd]:
    """Return ads awaiting moderation, newest first."""
    result = await db.execute(
        select(ClassifiedAd)
        .where(ClassifiedAd.payment_status == ClassifiedPaymentStatus.PENDING)
        .order_by(ClassifiedAd.created_at.desc())
    )
    return list(result.scalars().all())


async def increment_ad_views(db: AsyncSession, ad_id: int) -> ClassifiedAd:
    """Increment the view counter for an active, approved ad."""
    result = await db.execute(
        select(ClassifiedAd).where(
            ClassifiedAd.id == ad_id,
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
        )
    )
    ad = result.scalar_one_or_none()
    if ad is None:
        raise ClassifiedNotFoundError()
    ad.views_count += 1
    return ad


async def persist_classified_ad(
    db: AsyncSession,
    data: ClassifiedCreateInput,
    *,
    user: User | None = None,
    placement_fee: int = 0,
) -> ClassifiedAd:
    """Create and persist a pending classified ad."""
    vk_id = parse_vk_id(data.contact_vk)
    ad = ClassifiedAd(
        category=data.category,
        title=data.title,
        description=data.description,
        price=data.price,
        price_unit=data.price_unit,
        phone=data.phone.strip(),
        author_name=data.author_name,
        address=data.address,
        contact_telegram=data.contact_telegram,
        contact_vk=data.contact_vk,
        vk_id=vk_id,
        user_id=user.id if user else None,
        is_active=False,
        payment_status=ClassifiedPaymentStatus.PENDING,
        payment_reference=data.payment_reference,
        placement_fee=placement_fee,
    )
    db.add(ad)
    await db.flush()
    return ad
