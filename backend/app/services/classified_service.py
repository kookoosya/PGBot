"""Classified ads — thin orchestrator over domain modules.

Public API
----------
- ``search_classifieds`` / ``increment_ad_views`` — read paths
- ``create_classified_ad`` / ``moderate_classified_ad`` — write paths
- ``get_classified_quota`` / ``build_marketing_stats`` — auxiliary
- ``classified_to_response`` / ``list_classified_category_options`` — response helpers
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import CLASSIFIED_LABELS
from app.models.user import User
from app.services.classified.crud import (
    increment_ad_views,
    list_pending_ads,
    persist_classified_ad,
    search_classifieds,
)
from app.services.classified.moderation import moderate_classified_ad
from app.services.classified.quota import get_classified_quota
from app.services.classified.schemas import (
    ClassifiedActorContext,
    ClassifiedCreateInput,
    ClassifiedCreateResult,
    ClassifiedMarketingStats,
    ClassifiedNotFoundError,
    ClassifiedSearchParams,
    ClassifiedSearchResult,
    ClassifiedValidationError,
    ModerationAction,
    ModerationResult,
    classified_to_pending_response,
    classified_to_response,
    list_classified_category_options,
    to_classified_create_input,
)
from app.services.classified.stats import build_marketing_stats
from app.services.classified.validation import validate_create_input
from app.services.notifications import notify_owner

settings = get_settings()

__all__ = [
    "ClassifiedActorContext",
    "ClassifiedCreateInput",
    "ClassifiedCreateResult",
    "ClassifiedMarketingStats",
    "ClassifiedNotFoundError",
    "ClassifiedSearchParams",
    "ClassifiedSearchResult",
    "ClassifiedValidationError",
    "ModerationAction",
    "ModerationResult",
    "build_marketing_stats",
    "classified_to_pending_response",
    "classified_to_response",
    "create_classified_ad",
    "get_classified_quota",
    "increment_ad_views",
    "list_classified_category_options",
    "list_pending_ads",
    "moderate_classified_ad",
    "search_classifieds",
    "to_classified_create_input",
]


async def create_classified_ad(
    db: AsyncSession,
    data: ClassifiedCreateInput,
    *,
    user: User | None = None,
) -> ClassifiedCreateResult:
    """Validate, persist a pending ad and notify the site owner."""
    await validate_create_input(db, data)

    user_id = user.id if user else None
    quota = await get_classified_quota(db, data.phone, user_id)
    requires_payment = quota["requires_payment"]
    placement_fee = settings.CLASSIFIED_PLACEMENT_FEE if requires_payment else 0

    if requires_payment and not data.payment_confirmed:
        raise ClassifiedValidationError(
            f"Подтвердите оплату {settings.CLASSIFIED_PLACEMENT_FEE} ₽ за размещение объявления",
        )

    ad = await persist_classified_ad(db, data, user=user, placement_fee=placement_fee)

    cat_label = CLASSIFIED_LABELS.get(data.category, data.category)
    fee_line = f"💳 {placement_fee} ₽" if requires_payment else "🆓 Бесплатное размещение"
    site = settings.PUBLIC_SITE_URL.rstrip("/")
    await notify_owner(
        "📢 НОВОЕ ОБЪЯВЛЕНИЕ\n\n"
        f"#{ad.id} · {cat_label}\n"
        f"«{data.title}»\n"
        f"{data.description[:200]}{'…' if len(data.description) > 200 else ''}\n\n"
        f"👤 {data.author_name}\n"
        f"📞 {data.phone}\n"
        f"{fee_line}\n\n"
        f"Модерация: {site}/admin/classifieds"
    )

    return ClassifiedCreateResult(
        ad=ad,
        message="Заявка принята бесплатно! Объявление появится после модерации.",
        free=True,
    )
