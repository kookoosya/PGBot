"""Ежедневная сводка для подписчиков VK."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.site_urls import public_site_url
from app.models.classified import ClassifiedAd
from app.models.enums import (
    CLASSIFIED_LABELS,
    ClassifiedPaymentStatus,
    JOB_CLASSIFIED_CATEGORIES,
)
from app.models.vk_subscriber import VkSubscriber
from app.services.vk import send_message, get_welcome_keyboard
from app.services.weather_service import WeatherFetchError, format_weather_digest_lines, get_weather

logger = logging.getLogger(__name__)
settings = get_settings()

DIGEST_HOUR_UTC = 6  # 09:00 МСК зимой / 09:00 летом ≈


def _subscriber_wants_category(sub: VkSubscriber, category) -> bool:
    cats = (sub.categories or "all").lower()
    if cats == "all":
        return True
    if cats == "jobs":
        return category in JOB_CLASSIFIED_CATEGORIES
    return category.value in cats.split(",") or str(category) in cats.split(",")


async def send_daily_digest(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    if now.hour != DIGEST_HOUR_UTC:
        return 0

    since = now - timedelta(hours=24)
    result = await db.execute(select(VkSubscriber))
    subs = list(result.scalars().all())
    if not subs:
        return 0

    ads_result = await db.execute(
        select(ClassifiedAd)
        .where(
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
            ClassifiedAd.created_at >= since,
        )
        .order_by(ClassifiedAd.created_at.desc())
    )
    recent_ads = list(ads_result.scalars().all())

    total_count = (await db.execute(
        select(func.count(ClassifiedAd.id)).where(
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
        )
    )).scalar() or 0

    jobs_count = sum(1 for a in recent_ads if a.category in JOB_CLASSIFIED_CATEGORIES)

    weather_lines: list[str] = []
    try:
        weather = await get_weather()
        weather_lines = format_weather_digest_lines(weather)
    except WeatherFetchError:
        logger.warning("Daily digest: weather unavailable")

    sent = 0

    for sub in subs:
        if sub.last_digest_at and sub.last_digest_at.date() >= now.date():
            continue

        relevant = [a for a in recent_ads if _subscriber_wants_category(sub, a.category)]
        lines = [
            "🪶 Сводка за сутки\n",
        ]
        if weather_lines:
            lines.extend(weather_lines)
            lines.append("")
        lines.extend([
            f"📋 Всего на доске: {total_count}",
            f"🆕 За 24 ч: {len(relevant)} по вашей подписке",
        ])
        if jobs_count and (sub.categories or "all").lower() in ("all", "jobs"):
            lines.append(f"💼 Вакансий за сутки: {jobs_count}")

        if relevant:
            lines.append("\nСвежие:")
            for ad in relevant[:3]:
                cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
                lines.append(f"• [{cat}] {ad.title}")

        lines.append(f"\n🌐 {public_site_url()}/classifieds")
        try:
            await send_message(sub.peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
            sub.last_digest_at = now
            sent += 1
        except Exception as exc:
            logger.warning("Digest to %s failed: %s", sub.peer_id, exc)

    if sent:
        await db.flush()
    return sent
