"""Classified ad moderation: approve and reject."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus
from app.services.classified.schemas import (
    ClassifiedActorContext,
    ClassifiedNotFoundError,
    ModerationAction,
    ModerationResult,
)
from app.services.notifications import notify_vk_user

settings = get_settings()


async def _load_ad(db: AsyncSession, ad_id: int) -> ClassifiedAd:
    """Load ad by id or raise ``ClassifiedNotFoundError``."""
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise ClassifiedNotFoundError()
    return ad


async def approve_ad(
    db: AsyncSession,
    ad_id: int,
    *,
    actor: ClassifiedActorContext,
) -> ModerationResult:
    """Approve a pending ad, notify author and subscribers."""
    ad = await _load_ad(db, ad_id)
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

    from app.services.vk_bot import notify_subscribers_new_ad

    subscribers_notified = await notify_subscribers_new_ad(db, ad)
    return ModerationResult(
        ad=ad,
        message="Объявление опубликовано",
        subscribers_notified=subscribers_notified,
    )


async def reject_ad(
    db: AsyncSession,
    ad_id: int,
    *,
    actor: ClassifiedActorContext,
) -> ModerationResult:
    """Reject a pending ad and notify the author."""
    ad = await _load_ad(db, ad_id)
    ad.is_active = False
    ad.payment_status = ClassifiedPaymentStatus.REJECTED

    await notify_vk_user(
        ad.contact_vk or ad.vk_id,
        f"❌ Объявление «{ad.title}» не прошло модерацию.\n"
        "Проверьте оплату и текст. Можно подать заново.",
    )
    return ModerationResult(ad=ad, message="Объявление отклонено")


async def moderate_classified_ad(
    db: AsyncSession,
    ad_id: int,
    *,
    action: ModerationAction,
    actor: ClassifiedActorContext,
) -> ModerationResult:
    """Approve or reject a pending classified ad."""
    if action == "approve":
        return await approve_ad(db, ad_id, actor=actor)
    return await reject_ad(db, ad_id, actor=actor)
