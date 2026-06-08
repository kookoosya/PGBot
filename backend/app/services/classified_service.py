"""Classified ads — creation, moderation, search and quota (extracted from API layer)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import (
    CLASSIFIED_LABELS,
    ClassifiedCategory,
    ClassifiedPaymentStatus,
    JOB_CLASSIFIED_CATEGORIES,
    SERVICE_CLASSIFIED_CATEGORIES,
)
from app.models.user import User
from app.services.audit import log_action
from app.services.classified_antifraud import (
    check_phone_rate_limit,
    check_recent_duplicate,
    find_scam_phrase,
    validate_phone,
)
from app.services.ip_abuse import contains_suspicious_link
from app.services.notifications import notify_owner, notify_vk_user, parse_vk_id
from app.services.site_urls import public_site_url

logger = logging.getLogger(__name__)
settings = get_settings()

ModerationAction = Literal["approve", "reject"]
ClassifiedSortField = Literal["created_at", "views_count", "title"]
ClassifiedSortOrder = Literal["asc", "desc"]

_SORT_COLUMNS: dict[ClassifiedSortField, Any] = {
    "created_at": ClassifiedAd.created_at,
    "views_count": ClassifiedAd.views_count,
    "title": ClassifiedAd.title,
}


@dataclass(frozen=True, slots=True)
class ClassifiedCreateInput:
    """Validated payload for creating a classified ad."""

    category: ClassifiedCategory
    title: str
    description: str
    phone: str
    author_name: str
    price: Optional[int] = None
    price_unit: Optional[str] = None
    address: Optional[str] = None
    contact_telegram: Optional[str] = None
    contact_vk: Optional[str] = None
    payment_confirmed: bool = False
    payment_reference: Optional[str] = None
    website_url: Optional[str] = None
    agree_rules: bool = False


@dataclass(frozen=True, slots=True)
class ClassifiedActorContext:
    """Actor performing moderation (audit logging)."""

    actor_id: int
    ip_address: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ClassifiedSearchParams:
    """Filters for ``search_classifieds``."""

    category: Optional[ClassifiedCategory] = None
    search: Optional[str] = None
    payment_status: Optional[ClassifiedPaymentStatus] = ClassifiedPaymentStatus.APPROVED
    is_active: Optional[bool] = True
    user_id: Optional[int] = None
    phone: Optional[str] = None
    services_only: bool = False
    jobs_only: bool = False
    ads_only: bool = False
    page: int = 1
    page_size: int = 20
    offset: Optional[int] = None
    sort_by: ClassifiedSortField = "created_at"
    sort_order: ClassifiedSortOrder = "desc"


@dataclass(frozen=True, slots=True)
class ClassifiedSearchResult:
    """Paginated classified ad search result."""

    items: list[ClassifiedAd]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    offset: int


@dataclass(frozen=True, slots=True)
class ClassifiedMarketingStats:
    """Marketing dashboard payload for classified ads."""

    total_ads: int
    total_views: int
    avg_views_per_ad: int
    monthly_reach_estimate: int
    placement_fee: int
    period_days: int
    category_stats: list[dict[str, Any]]
    roi_examples: list[dict[str, Any]]
    weekly_views: list[dict[str, Any]]
    status_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to API response dict."""
        return {
            "total_ads": self.total_ads,
            "total_views": self.total_views,
            "avg_views_per_ad": self.avg_views_per_ad,
            "monthly_reach_estimate": self.monthly_reach_estimate,
            "placement_fee": self.placement_fee,
            "period_days": self.period_days,
            "category_stats": self.category_stats,
            "roi_examples": self.roi_examples,
            "weekly_views": self.weekly_views,
            "status_counts": self.status_counts,
        }


@dataclass(frozen=True, slots=True)
class ClassifiedCreateResult:
    """Result of a successful ad submission."""

    ad: ClassifiedAd
    message: str
    free: bool
    owner_notified: bool = True


@dataclass(frozen=True, slots=True)
class ModerationResult:
    """Result of approve/reject moderation."""

    ad: ClassifiedAd
    message: str
    subscribers_notified: int = 0
    vk_notified: bool = True
    audit_logged: bool = True


class ClassifiedValidationError(Exception):
    """Business validation failure when creating or loading an ad."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def _normalize_pagination(
    *,
    page: int,
    page_size: int,
    total: int,
    offset: Optional[int] = None,
) -> tuple[int, int, int, int, bool, bool]:
    """Return clamped page, offset, total_pages, has_prev, has_next."""
    safe_page_size = max(1, min(page_size, 100))
    total_pages = max(1, (total + safe_page_size - 1) // safe_page_size) if total else 1
    if offset is not None:
        safe_offset = max(0, offset)
        safe_page = safe_offset // safe_page_size + 1
    else:
        safe_page = max(1, min(page, total_pages))
        safe_offset = (safe_page - 1) * safe_page_size
    has_prev = safe_offset > 0
    has_next = safe_offset + safe_page_size < total
    return safe_page, safe_offset, safe_page_size, total_pages, has_prev, has_next


def _apply_search_sort(
    query: Any,
    *,
    sort_by: ClassifiedSortField,
    sort_order: ClassifiedSortOrder,
) -> Any:
    """Apply ordering to a classified search query."""
    column = _SORT_COLUMNS.get(sort_by, ClassifiedAd.created_at)
    ordering = column.asc() if sort_order == "asc" else column.desc()
    if sort_by != "created_at":
        return query.order_by(ordering, ClassifiedAd.created_at.desc())
    return query.order_by(ordering)


async def _count_user_ads(
    db: AsyncSession,
    phone: str,
    user_id: Optional[int] = None,
) -> int:
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
    """Return placement quota info for a phone / logged-in user."""
    used = 0
    if phone:
        try:
            used = await _count_user_ads(db, phone, user_id)
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


async def search_classifieds(
    db: AsyncSession,
    params: ClassifiedSearchParams,
) -> ClassifiedSearchResult:
    """Search and filter classified ads with sorting and pagination."""
    try:
        query = select(ClassifiedAd)

        if params.payment_status is not None:
            query = query.where(ClassifiedAd.payment_status == params.payment_status)
        if params.is_active is not None:
            query = query.where(ClassifiedAd.is_active.is_(params.is_active))
        if params.user_id is not None:
            query = query.where(ClassifiedAd.user_id == params.user_id)
        if params.phone is not None:
            query = query.where(ClassifiedAd.phone == params.phone)
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
        page, offset, page_size, total_pages, has_prev, has_next = _normalize_pagination(
            page=params.page,
            page_size=params.page_size,
            total=total,
            offset=params.offset,
        )
        result = await db.execute(
            _apply_search_sort(query, sort_by=params.sort_by, sort_order=params.sort_order)
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
    except ClassifiedValidationError:
        raise
    except Exception:
        logger.exception(
            "Classified search failed: category=%s search=%r page=%s page_size=%s",
            params.category,
            params.search,
            params.page,
            params.page_size,
        )
        raise

    logger.debug(
        "Classified search: %s item(s), total=%s page=%s/%s sort=%s:%s",
        len(items),
        total,
        page,
        total_pages,
        params.sort_by,
        params.sort_order,
    )
    return ClassifiedSearchResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        offset=offset,
    )


async def increment_ad_views(db: AsyncSession, ad_id: int) -> ClassifiedAd:
    """Increment the view counter for an active, approved ad."""
    try:
        result = await db.execute(
            select(ClassifiedAd).where(
                ClassifiedAd.id == ad_id,
                ClassifiedAd.is_active.is_(True),
                ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
            )
        )
        ad = result.scalar_one_or_none()
        if ad is None:
            raise ClassifiedValidationError("Объявление не найдено", status_code=404)

        ad.views_count += 1
    except ClassifiedValidationError:
        raise
    except Exception:
        logger.exception("Failed to increment views for classified ad #%s", ad_id)
        raise

    logger.debug("Classified ad #%s view count incremented to %s", ad.id, ad.views_count)
    return ad


async def build_marketing_stats(db: AsyncSession) -> ClassifiedMarketingStats:
    """Collect classified ad statistics for the owner marketing dashboard."""
    try:
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

        status_rows = await db.execute(
            select(ClassifiedAd.payment_status, func.count(ClassifiedAd.id)).group_by(
                ClassifiedAd.payment_status
            )
        )
        status_counts = {
            (row[0].value if hasattr(row[0], "value") else str(row[0])): row[1]
            for row in status_rows.all()
        }

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
    except Exception:
        logger.exception("Failed to build classified marketing stats")
        raise

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
        status_counts=status_counts,
    )


async def _validate_create_input(db: AsyncSession, data: ClassifiedCreateInput) -> None:
    """Run all submission validations; raise ``ClassifiedValidationError`` on failure."""
    if data.website_url:
        raise ClassifiedValidationError(
            "Не удалось отправить форму. Обновите страницу.",
        )
    if not data.agree_rules:
        raise ClassifiedValidationError(
            "Подтвердите, что объявление честное и без предоплаты незнакомцам",
        )

    phone_err = validate_phone(data.phone)
    if phone_err:
        raise ClassifiedValidationError(phone_err)

    if find_scam_phrase(f"{data.title} {data.description}"):
        raise ClassifiedValidationError(
            "Текст похож на мошенническую схему. Уберите требование предоплаты или перевода.",
        )

    rate_err = await check_phone_rate_limit(db, data.phone)
    if rate_err:
        raise ClassifiedValidationError(rate_err, status_code=429)

    dup_err = await check_recent_duplicate(db, data.phone, data.title)
    if dup_err:
        raise ClassifiedValidationError(dup_err)

    if contains_suspicious_link(data.contact_telegram, data.contact_vk, data.address):
        raise ClassifiedValidationError(
            "Ссылки в контактах не допускаются — укажите телефон.",
        )


async def _notify_owner_new_ad(
    ad: ClassifiedAd,
    data: ClassifiedCreateInput,
    *,
    placement_fee: int,
) -> bool:
    """Notify site owner about a new pending ad; return ``True`` on success."""
    cat_label = CLASSIFIED_LABELS.get(data.category, data.category)
    fee_line = f"💳 {placement_fee} ₽" if placement_fee else "🆓 Бесплатное размещение"
    try:
        await notify_owner(
            "📢 НОВОЕ ОБЪЯВЛЕНИЕ\n\n"
            f"#{ad.id} · {cat_label}\n"
            f"«{data.title}»\n"
            f"{data.description[:200]}{'…' if len(data.description) > 200 else ''}\n\n"
            f"👤 {data.author_name}\n"
            f"📞 {data.phone}\n"
            f"{fee_line}\n\n"
            f"Модерация: {public_site_url()}/admin/classifieds"
        )
        return True
    except Exception:
        logger.exception(
            "Owner notification failed for classified ad #%s (title=%r)",
            ad.id,
            data.title,
        )
        return False


async def _safe_classified_audit(
    db: AsyncSession,
    action: str,
    ad_id: int,
    actor: ClassifiedActorContext,
    details: dict[str, Any],
) -> bool:
    """Write audit log for classified moderation; return ``True`` on success."""
    try:
        await log_action(
            db,
            action,
            "classified",
            ad_id,
            user_id=actor.actor_id,
            details=details,
            ip_address=actor.ip_address,
        )
        return True
    except Exception:
        logger.exception(
            "Audit log failed for classified #%s: action=%s actor_id=%s",
            ad_id,
            action,
            actor.actor_id,
        )
        return False


async def _safe_notify_vk(
    ad: ClassifiedAd,
    message: str,
    *,
    context: str,
) -> bool:
    """Send VK message to ad author; return ``True`` on success."""
    try:
        await notify_vk_user(ad.contact_vk or ad.vk_id, message)
        return True
    except Exception:
        logger.exception(
            "VK notification failed for classified ad #%s during %s",
            ad.id,
            context,
        )
        return False


async def create_classified_ad(
    db: AsyncSession,
    data: ClassifiedCreateInput,
    *,
    user: Optional[User] = None,
) -> ClassifiedCreateResult:
    """Validate, persist a pending ad and notify the site owner."""
    await _validate_create_input(db, data)

    user_id = user.id if user else None
    quota = await get_classified_quota(db, data.phone, user_id)
    requires_payment = quota["requires_payment"]
    placement_fee = settings.CLASSIFIED_PLACEMENT_FEE if requires_payment else 0

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
    try:
        db.add(ad)
        await db.flush()
    except Exception:
        logger.exception(
            "Failed to persist classified ad for user %s (title=%r)",
            user_id,
            data.title,
        )
        raise

    owner_notified = await _notify_owner_new_ad(ad, data, placement_fee=placement_fee)
    if not owner_notified:
        logger.warning(
            "Classified ad #%s created but owner was not notified",
            ad.id,
        )

    logger.info("Classified ad #%s created by user %s", ad.id, user_id)
    return ClassifiedCreateResult(
        ad=ad,
        message="Заявка принята бесплатно! Объявление появится после модерации.",
        free=True,
        owner_notified=owner_notified,
    )


async def moderate_classified_ad(
    db: AsyncSession,
    ad_id: int,
    *,
    action: ModerationAction,
    actor: ClassifiedActorContext,
) -> ModerationResult:
    """Approve or reject a pending classified ad."""
    try:
        result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
        ad = result.scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load classified ad #%s for moderation", ad_id)
        raise
    if not ad:
        raise ClassifiedValidationError("Объявление не найдено", status_code=404)

    if action == "approve":
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
        vk_notified = await _safe_notify_vk(ad, vk_msg, context="approve")

        subscribers_notified = 0
        try:
            from app.services.vk_bot import notify_subscribers_new_ad

            subscribers_notified = await notify_subscribers_new_ad(db, ad)
        except Exception:
            logger.exception(
                "Subscriber notification failed for classified ad #%s on approve",
                ad.id,
            )

        audit_logged = await _safe_classified_audit(
            db,
            "classified_approve",
            ad.id,
            actor,
            {"payment_status": ad.payment_status.value, "vk_notified": vk_notified},
        )
        if not audit_logged:
            logger.warning(
                "Classified ad #%s approved but audit was not logged (actor=%s)",
                ad.id,
                actor.actor_id,
            )

        logger.info("Classified ad #%s approved by user %s", ad.id, actor.actor_id)
        return ModerationResult(
            ad=ad,
            message="Объявление опубликовано",
            subscribers_notified=subscribers_notified,
            vk_notified=vk_notified,
            audit_logged=audit_logged,
        )

    ad.is_active = False
    ad.payment_status = ClassifiedPaymentStatus.REJECTED
    vk_notified = await _safe_notify_vk(
        ad,
        f"❌ Объявление «{ad.title}» не прошло модерацию.\n"
        "Проверьте оплату и текст. Можно подать заново.",
        context="reject",
    )

    audit_logged = await _safe_classified_audit(
        db,
        "classified_reject",
        ad.id,
        actor,
        {"payment_status": ad.payment_status.value, "vk_notified": vk_notified},
    )
    if not audit_logged:
        logger.warning(
            "Classified ad #%s rejected but audit was not logged (actor=%s)",
            ad.id,
            actor.actor_id,
        )

    logger.info("Classified ad #%s rejected by user %s", ad.id, actor.actor_id)
    return ModerationResult(
        ad=ad,
        message="Объявление отклонено",
        vk_notified=vk_notified,
        audit_logged=audit_logged,
    )
