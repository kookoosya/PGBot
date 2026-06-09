"""VK-бот: зеркало сайта, объявления, подписки."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.site_urls import public_site_url
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus
from app.models.vk_subscriber import VkSubscriber
from app.services.vk import send_message
from app.services.vk_subscription import (
    SUBSCRIPTION_PRESETS,
    normalize_subscription_categories,
    subscriber_wants_category,
    subscription_options_text,
)

logger = logging.getLogger(__name__)
settings = get_settings()


async def list_recent_ads(db: AsyncSession, limit: int = 5) -> list[ClassifiedAd]:
    result = await db.execute(
        select(ClassifiedAd)
        .where(
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
        )
        .order_by(ClassifiedAd.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def format_ads_message(db: AsyncSession) -> str:
    ads = await list_recent_ads(db)
    if not ads:
        return (
            "📋 Объявлений пока нет.\n\n"
            f"Подайте первым — кнопка «➕ Объявление» или:\n{public_site_url()}/classifieds\n\n"
            "✨ Размещение бесплатно"
        )
    lines = [f"📋 Свежие объявления ({len(ads)}):\n"]
    for ad in ads:
        cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
        price = f" · {ad.price} {ad.price_unit or '₽'}" if ad.price else ""
        lines.append(f"• [{cat}] {ad.title}{price}")
        lines.append(f"  📞 {ad.phone}")
    lines.append(f"\nВсе объявления: {public_site_url()}/classifieds")
    lines.append(f"💼 Вакансии: {public_site_url()}/jobs")
    lines.append(f"🤝 Сосед помогает: {public_site_url()}/classifieds?neighbor=1")
    lines.append("➕ Подать в боте — кнопка «Объявление»")
    return "\n".join(lines)


async def subscribe_peer(db: AsyncSession, peer_id: int, categories: str = "all") -> str:
    key, label = normalize_subscription_categories(categories)
    result = await db.execute(select(VkSubscriber).where(VkSubscriber.peer_id == peer_id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.categories = key
        await db.flush()
        return f"✅ Подписка обновлена: {label}."
    db.add(VkSubscriber(peer_id=peer_id, categories=key))
    await db.flush()
    return (
        f"🔔 Подписка оформлена: {label}.\n\n"
        f"{subscription_options_text()}"
    )


async def unsubscribe_peer(db: AsyncSession, peer_id: int) -> str:
    result = await db.execute(select(VkSubscriber).where(VkSubscriber.peer_id == peer_id))
    sub = result.scalar_one_or_none()
    if not sub:
        return "Вы не были подписаны."
    await db.delete(sub)
    await db.flush()
    return "🔕 Подписка отменена."


async def notify_subscribers_new_ad(db: AsyncSession, ad: ClassifiedAd) -> int:
    """Разослать подписчикам опубликованное объявление."""
    result = await db.execute(select(VkSubscriber))
    subs = result.scalars().all()
    if not subs:
        return 0
    cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
    price = f"\n💰 {ad.price} {ad.price_unit or '₽'}" if ad.price else ""
    msg = (
        f"📢 Новое объявление!\n\n"
        f"«{ad.title}»\n"
        f"Категория: {cat}{price}\n"
        f"{ad.description[:150]}{'…' if len(ad.description) > 150 else ''}\n\n"
        f"📞 {ad.phone}\n"
        f"Подробнее: {public_site_url()}/classifieds/{ad.id}"
    )
    sent = 0
    for sub in subs:
        if not subscriber_wants_category(sub, ad.category):
            continue
        try:
            await send_message(sub.peer_id, msg)
            sent += 1
        except Exception as exc:
            logger.warning("VK notify subscriber %s failed: %s", sub.peer_id, exc)
    return sent
