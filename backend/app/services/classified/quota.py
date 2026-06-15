"""Placement quota for classified ads."""

from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import ClassifiedPaymentStatus

logger = logging.getLogger(__name__)
settings = get_settings()


async def count_user_ads(
    db: AsyncSession,
    phone: str,
    user_id: Optional[int] = None,
) -> int:
    """Count pending and approved ads for a phone or user."""
    filters: list[Any] = [
        ClassifiedAd.payment_status.in_([
            ClassifiedPaymentStatus.PENDING,
            ClassifiedPaymentStatus.APPROVED,
        ]),
    ]
    if user_id:
        filters.append(or_(ClassifiedAd.phone == phone, ClassifiedAd.user_id == user_id))
    else:
        filters.append(ClassifiedAd.phone == phone)
    q = select(func.count(ClassifiedAd.id)).where(*filters)
    return (await db.execute(q)).scalar() or 0


async def get_classified_quota(
    db: AsyncSession,
    phone: Optional[str],
    user_id: Optional[int] = None,
) -> dict[str, Any]:
    """Return placement quota info for a phone or logged-in user."""
    used = 0
    if phone:
        try:
            used = await count_user_ads(db, phone, user_id)
        except Exception:
            logger.exception(
                "Failed to count classified ads for phone=%r user_id=%s",
                phone,
                user_id,
            )
    return {
        "free_limit": 0,
        "free_used": used,
        "free_remaining": 0,
        "requires_payment": False,
        "amount": 0,
        "period_days": settings.CLASSIFIED_PERIOD_DAYS,
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "message": (
            f"Размещение объявлений бесплатно на {settings.CLASSIFIED_PERIOD_DAYS} дней. "
            "После модерации объявление появится на портале."
        ),
    }
