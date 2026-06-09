"""Marketing and aggregate statistics for classified ads."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus
from app.services.classified.schemas import ClassifiedMarketingStats

settings = get_settings()


async def build_marketing_stats(db: AsyncSession) -> ClassifiedMarketingStats:
    """Collect classified ad statistics for the owner marketing dashboard."""
    approved_filter = (
        ClassifiedAd.is_active.is_(True),
        ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
    )
    total_ads = (
        await db.execute(select(func.count(ClassifiedAd.id)).where(*approved_filter))
    ).scalar() or 0
    total_views = (
        await db.execute(
            select(func.coalesce(func.sum(ClassifiedAd.views_count), 0)).where(*approved_filter)
        )
    ).scalar() or 0

    cat_rows = await db.execute(
        select(
            ClassifiedAd.category,
            func.count(ClassifiedAd.id),
            func.coalesce(func.sum(ClassifiedAd.views_count), 0),
        )
        .where(*approved_filter)
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
            "roi_percent": round((4800 - fee) / fee * 100) if fee else 0,
        },
        {
            "service": "Стрижка",
            "ad_cost": fee,
            "clients": 6,
            "avg_check": 800,
            "income": 4800,
            "roi_percent": round((4800 - fee) / fee * 100) if fee else 0,
        },
        {
            "service": "Вакансия (строитель)",
            "ad_cost": fee,
            "clients": 2,
            "avg_check": 3500,
            "income": 7000,
            "roi_percent": round((7000 - fee) / fee * 100) if fee else 0,
        },
        {
            "service": "Покос / дрова",
            "ad_cost": fee,
            "clients": 3,
            "avg_check": 2000,
            "income": 6000,
            "roi_percent": round((6000 - fee) / fee * 100) if fee else 0,
        },
    ]

    week_labels = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    base_daily = max(monthly_estimate // 30, 15)
    weekly_views = [
        {"day": label, "views": int(base_daily * mult)}
        for label, mult in zip(week_labels, [0.9, 1.0, 1.1, 1.0, 1.2, 1.4, 1.1], strict=True)
    ]

    return ClassifiedMarketingStats(
        total_ads=total_ads,
        total_views=total_views,
        avg_views_per_ad=avg_views,
        monthly_reach_estimate=monthly_estimate,
        placement_fee=fee,
        period_days=settings.CLASSIFIED_PERIOD_DAYS,
        category_stats=category_stats,
        roi_examples=roi_examples,
        weekly_views=weekly_views,
    )
