"""Create classified ads (web and VK)."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedCategory, ClassifiedPaymentStatus
from app.models.user import User
from app.services.classified.quota import get_classified_quota
from app.services.classified.schemas import (
    ClassifiedCreateInput,
    ClassifiedCreateResult,
    ClassifiedValidationError,
)
from app.services.classified.validation import validate_create_input
from app.services.notify_utils import safe_notify_owner
from app.services.notifications import parse_vk_id
from app.services.site_urls import public_site_url

logger = logging.getLogger(__name__)
settings = get_settings()


async def notify_owner_new_ad(
    ad: ClassifiedAd,
    data: ClassifiedCreateInput,
    *,
    placement_fee: int,
) -> bool:
    """Notify site owner about a new pending ad."""
    cat_label = CLASSIFIED_LABELS.get(data.category, data.category)
    fee_line = f"💳 {placement_fee} ₽" if placement_fee else "🆓 Бесплатное размещение"
    return await safe_notify_owner(
        "📢 НОВОЕ ОБЪЯВЛЕНИЕ\n\n"
        f"#{ad.id} · {cat_label}\n"
        f"«{data.title}»\n"
        f"{data.description[:200]}{'…' if len(data.description) > 200 else ''}\n\n"
        f"👤 {data.author_name}\n"
        f"📞 {data.phone}\n"
        f"{fee_line}\n\n"
        f"Модерация: {public_site_url()}/admin/classifieds",
        context="classified_create",
        resource="classified",
        resource_id=ad.id,
    )


async def create_classified_ad(
    db: AsyncSession,
    data: ClassifiedCreateInput,
    *,
    user: Optional[User] = None,
) -> ClassifiedCreateResult:
    """Validate, persist a pending ad and notify the site owner."""
    await validate_create_input(db, data)

    user_id = user.id if user else None
    is_neighbor_help = data.category == ClassifiedCategory.NEIGHBOR_HELP
    quota = await get_classified_quota(db, data.phone, user_id)
    requires_payment = False if is_neighbor_help else quota["requires_payment"]
    placement_fee = 0 if is_neighbor_help else (settings.CLASSIFIED_PLACEMENT_FEE if requires_payment else 0)

    if requires_payment and not data.payment_confirmed:
        raise ClassifiedValidationError(
            f"Подтвердите оплату {settings.CLASSIFIED_PLACEMENT_FEE} ₽ за размещение объявления",
        )

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
        user_id=user_id,
        is_active=False,
        payment_status=ClassifiedPaymentStatus.PENDING,
        payment_reference=data.payment_reference,
        placement_fee=placement_fee,
    )
    db.add(ad)
    await db.flush()

    owner_notified = await notify_owner_new_ad(ad, data, placement_fee=placement_fee)
    message = (
        "Заявка «Сосед помогает» принята бесплатно! Появится после быстрой модерации."
        if is_neighbor_help
        else "Заявка принята бесплатно! Объявление появится после модерации."
    )
    return ClassifiedCreateResult(
        ad=ad,
        message=message,
        free=True,
        owner_notified=owner_notified,
    )


async def create_classified_ad_from_vk(
    db: AsyncSession,
    *,
    from_id: int,
    category: ClassifiedCategory,
    title: str,
    description: str,
    phone: str,
    author_name: str,
) -> ClassifiedCreateResult:
    """Создать объявление из VK-бота — та же валидация и уведомления, что на сайте."""
    return await create_classified_ad(
        db,
        ClassifiedCreateInput(
            category=category,
            title=title,
            description=description,
            phone=phone,
            author_name=author_name,
            contact_vk=str(from_id),
            agree_rules=True,
        ),
    )
