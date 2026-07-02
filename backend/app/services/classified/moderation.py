"""Approve/reject classified ads."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.portal_copy import (
    CLASSIFIED_APPROVED_VK,
    CLASSIFIED_REJECTED_VK,
    LINK_CLASSIFIED,
    LINK_SUBMIT_CLASSIFIED,
)
from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus
from app.services.audit import log_action
from app.services.classified.schemas import (
    ClassifiedActorContext,
    ClassifiedNotFoundError,
    ModerationAction,
    ModerationResult,
)
from app.services.notifications import notify_vk_user_with_links

logger = logging.getLogger(__name__)


async def safe_classified_audit(
    db: AsyncSession,
    action: str,
    ad_id: int,
    actor: ClassifiedActorContext,
    details: dict[str, Any],
) -> bool:
    try:
        await log_action(
            db,
            action,
            "classified",
            ad_id,
            user_id=actor.actor_id if actor.actor_id > 0 else None,
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


async def safe_notify_vk(
    ad: ClassifiedAd,
    message: str,
    *,
    context: str,
    links: tuple[tuple[str, str], ...] = (),
) -> bool:
    try:
        await notify_vk_user_with_links(ad.contact_vk or ad.vk_id, message, *links)
        return True
    except Exception:
        logger.exception(
            "VK notification failed for classified ad #%s during %s",
            ad.id,
            context,
        )
        return False


async def moderate_classified_ad(
    db: AsyncSession,
    ad_id: int,
    *,
    action: ModerationAction,
    actor: ClassifiedActorContext,
    notify_vk: bool = True,
) -> ModerationResult:
    """Approve or reject a pending classified ad."""
    result = await db.execute(select(ClassifiedAd).where(ClassifiedAd.id == ad_id))
    ad = result.scalar_one_or_none()
    if not ad:
        raise ClassifiedNotFoundError()

    if action == "approve":
        ad.is_active = True
        ad.payment_status = ClassifiedPaymentStatus.APPROVED
        cat_label = CLASSIFIED_LABELS.get(ad.category, ad.category)
        vk_msg = CLASSIFIED_APPROVED_VK.format(title=ad.title, category=cat_label)
        vk_notified = False
        if notify_vk:
            vk_notified = await safe_notify_vk(
                ad,
                vk_msg,
                context="approve",
                links=((LINK_CLASSIFIED, f"/classifieds/{ad.id}"),),
            )

        subscribers_notified = 0
        try:
            from app.services.vk.bot import notify_subscribers_new_ad

            subscribers_notified = await notify_subscribers_new_ad(db, ad)
        except Exception:
            logger.exception(
                "Subscriber notification failed for classified ad #%s on approve",
                ad.id,
            )

        audit_logged = await safe_classified_audit(
            db,
            "classified_approve",
            ad.id,
            actor,
            {"payment_status": ad.payment_status.value, "vk_notified": vk_notified},
        )
        return ModerationResult(
            ad=ad,
            message="Объявление опубликовано",
            subscribers_notified=subscribers_notified,
            vk_notified=vk_notified,
            audit_logged=audit_logged,
        )

    ad.is_active = False
    ad.payment_status = ClassifiedPaymentStatus.REJECTED
    vk_notified = await safe_notify_vk(
        ad,
        CLASSIFIED_REJECTED_VK.format(title=ad.title),
        context="reject",
        links=((LINK_SUBMIT_CLASSIFIED, "/classifieds?new=1"),),
    )
    audit_logged = await safe_classified_audit(
        db,
        "classified_reject",
        ad.id,
        actor,
        {"payment_status": ad.payment_status.value, "vk_notified": vk_notified},
    )
    return ModerationResult(
        ad=ad,
        message="Объявление отклонено",
        vk_notified=vk_notified,
        audit_logged=audit_logged,
    )
