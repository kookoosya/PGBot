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


@dataclass(frozen=True, slots=True)
class ClassifiedSearchResult:
    """Paginated classified ad search result."""

    items: list[ClassifiedAd]
    total: int
    page: int
    page_size: int


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
    used = await _count_user_ads(db, phone, user_id) if phone else 0
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
    """Search and filter classified ads with pagination."""
    page = max(1, params.page)
    page_size = max(1, min(params.page_size, 100))
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
        pattern = f"%{params.search}%"
        query = query.where(
            ClassifiedAd.title.ilike(pattern) | ClassifiedAd.description.ilike(pattern),
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(ClassifiedAd.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    logger.debug(
        "Classified search: %s item(s), total=%s page=%s page_size=%s",
        len(items),
        total,
        page,
        page_size,
    )
    return ClassifiedSearchResult(items=items, total=total, page=page, page_size=page_size)


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
        raise ClassifiedValidationError("Объявление не найдено", status_code=404)

    ad.views_count += 1
    logger.debug("Classified ad #%s view count incremented to %s", ad.id, ad.views_count)
    return ad


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
    db.add(ad)
    await db.flush()

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
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
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
