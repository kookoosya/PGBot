"""Bank transfer payments for AI Pro — auto-grant via email notifications."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_payment_order import AIPaymentOrder
from app.models.user import User
from app.services.ai_entitlement_service import find_active_entitlement
from app.services.ai_payment_service import AIPaymentError, fulfill_payment_order
from app.services.ai_plans import plan_by_id

logger = logging.getLogger(__name__)
settings = get_settings()


def payment_destination_configured() -> bool:
    return bool(settings.PAYMENT_CARD_NUMBER.strip() or settings.PAYMENT_PHONE.strip())


def bank_auto_enabled() -> bool:
    return bool(
        payment_destination_configured()
        and settings.BANK_IMAP_HOST.strip()
        and settings.BANK_IMAP_USER.strip()
        and settings.BANK_IMAP_PASSWORD.strip()
    )


def _payment_code(order_id: int) -> str:
    return f"PG{order_id:04d}"


async def create_bank_payment_order(
    db: AsyncSession,
    *,
    user: User,
    plan_id: str = "pro",
) -> AIPaymentOrder:
    if not payment_destination_configured():
        raise AIPaymentError("Реквизиты для оплаты ещё не настроены")

    plan = plan_by_id(plan_id)
    if not plan or not plan.requires_payment:
        raise AIPaymentError("Этот тариф нельзя оплатить переводом")

    active = await find_active_entitlement(db, user_id=user.id)
    if active and active.plan_id == "pro":
        raise AIPaymentError("У вас уже активна подписка ИИ Pro")

    pending = await db.execute(
        select(AIPaymentOrder)
        .where(
            AIPaymentOrder.user_id == user.id,
            AIPaymentOrder.status == "pending",
            AIPaymentOrder.plan_id == plan.id,
            AIPaymentOrder.provider == "bank_transfer",
        )
        .order_by(AIPaymentOrder.created_at.desc())
        .limit(1)
    )
    existing = pending.scalar_one_or_none()
    if existing:
        return existing

    order = AIPaymentOrder(
        user_id=user.id,
        plan_id=plan.id,
        amount_rub=plan.price_rub,
        status="pending",
        provider="bank_transfer",
    )
    db.add(order)
    await db.flush()
    order.payment_code = _payment_code(order.id)
    await db.flush()
    return order


async def fulfill_bank_order(
    db: AsyncSession,
    order: AIPaymentOrder,
    *,
    reference: str,
) -> AIPaymentOrder:
    if order.status == "succeeded" and order.entitlement_id:
        return order

    await fulfill_payment_order(db, order, reference=reference, source="bank")
    order.matched_reference = reference[:500]
    await db.flush()
    logger.info("AI Pro activated for user %s via bank transfer (%s)", order.user_id, order.payment_code)
    return order


def bank_payment_payload(order: AIPaymentOrder, *, username: str) -> dict:
    return {
        "order_id": order.id,
        "plan_id": order.plan_id,
        "amount_rub": order.amount_rub,
        "payment_code": order.payment_code or _payment_code(order.id),
        "status": order.status,
        "card_number": settings.PAYMENT_CARD_NUMBER.strip(),
        "phone": settings.PAYMENT_PHONE.strip(),
        "card_holder": settings.PAYMENT_CARD_HOLDER,
        "bank_name": settings.PAYMENT_BANK_NAME,
        "comment": f"{order.payment_code} · ИИ Pro · {username}",
        "instructions": (
            f"Переведите ровно {order.amount_rub} ₽ на карту или по СБП на телефон. "
            f"В комментарии обязательно укажите код: {order.payment_code}"
        ),
        "auto_enabled": bank_auto_enabled(),
        "activated": order.status == "succeeded",
    }
