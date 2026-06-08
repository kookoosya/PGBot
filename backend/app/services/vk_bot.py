"""VK-бот: зеркало сайта, объявления, подписки."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus
from app.models.vk_subscriber import VkSubscriber
from app.services.vk import send_message

logger = logging.getLogger(__name__)
settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


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
            f"Подайте первым на сайте:\n{_SITE}/classifieds\n\n"
            "✨ Размещение бесплатно"
        )
    lines = [f"📋 Свежие объявления ({len(ads)}):\n"]
    for ad in ads:
        cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
        price = f" · {ad.price} {ad.price_unit or '₽'}" if ad.price else ""
        lines.append(f"• [{cat}] {ad.title}{price}")
        lines.append(f"  📞 {ad.phone}")
    lines.append(f"\nВсе объявления: {_SITE}/classifieds")
    lines.append(f"Подать бесплатно: {_SITE}/classifieds")
    return "\n".join(lines)


async def subscribe_peer(db: AsyncSession, peer_id: int) -> str:
    result = await db.execute(select(VkSubscriber).where(VkSubscriber.peer_id == peer_id))
    if result.scalar_one_or_none():
        return "✅ Вы уже подписаны на новые объявления."
    db.add(VkSubscriber(peer_id=peer_id))
    await db.flush()
    return "🔔 Подписка оформлена! Буду присылать новые объявления соседей."


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
        f"Подробнее: {_SITE}/classifieds"
    )
    sent = 0
    for sub in subs:
        try:
            await send_message(sub.peer_id, msg)
            sent += 1
        except Exception as exc:
            logger.warning("VK notify subscriber %s failed: %s", sub.peer_id, exc)
    return sent
