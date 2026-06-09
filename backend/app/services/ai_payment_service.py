"""YooKassa payments for AI subscriptions — auto-grant entitlements."""

from __future__ import annotations

import base64
import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_payment_order import AIPaymentOrder
from app.models.user import User
from app.services.ai_entitlement_service import grant_entitlement
from app.services.ai_plans import plan_by_id
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()

YOOKASSA_API = "https://api.yookassa.ru/v3"


class AIPaymentError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


def yookassa_enabled() -> bool:
    return bool(settings.YOOKASSA_SHOP_ID.strip() and settings.YOOKASSA_SECRET_KEY.strip())


def _auth_header() -> dict[str, str]:
    token = base64.b64encode(
        f"{settings.YOOKASSA_SHOP_ID}:{settings.YOOKASSA_SECRET_KEY}".encode()
    ).decode()
    return {"Authorization": f"Basic {token}"}


async def _get_owner_user(db: AsyncSession) -> User:
    for username in settings.owner_usernames:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if user:
            return user
    result = await db.execute(
        select(User).where(User.username == settings.SUPER_ADMIN_USERNAME)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AIPaymentError("Не найден пользователь-владелец для автовыдачи доступа", status_code=500)
    return user


async def create_subscription_payment(
    db: AsyncSession,
    *,
    user: User,
    plan_id: str,
) -> AIPaymentOrder:
    if not yookassa_enabled():
        raise AIPaymentError("Онлайн-оплата пока не настроена. Используйте перевод на карту.")

    plan = plan_by_id(plan_id)
    if not plan or not plan.requires_payment:
        raise AIPaymentError("Этот тариф нельзя оплатить онлайн")

    order = AIPaymentOrder(
        user_id=user.id,
        plan_id=plan.id,
        amount_rub=plan.price_rub,
        status="pending",
    )
    db.add(order)
    await db.flush()

    return_url = (
        settings.YOOKASSA_RETURN_URL.strip()
        or f"{settings.PUBLIC_SITE_URL.rstrip('/')}/ai?paid=1"
    )
    payload = {
        "amount": {"value": f"{plan.price_rub}.00", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": f"ИИ {plan.name} · {user.username}"[:128],
        "metadata": {
            "order_id": str(order.id),
            "user_id": str(user.id),
            "plan_id": plan.id,
        },
    }
    headers = {
        **_auth_header(),
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{YOOKASSA_API}/payments", json=payload, headers=headers)
    except httpx.HTTPError as exc:
        logger.exception("YooKassa create payment failed")
        raise AIPaymentError("Платёжный сервис временно недоступен") from exc

    if resp.status_code >= 400:
        logger.warning("YooKassa create error %s: %s", resp.status_code, resp.text[:500])
        raise AIPaymentError("Не удалось создать платёж. Попробуйте позже.")

    data = resp.json()
    order.external_id = data.get("id")
    confirmation = data.get("confirmation") or {}
    order.confirmation_url = confirmation.get("confirmation_url")
    await db.flush()
    return order


async def fetch_yookassa_payment(external_id: str) -> dict | None:
    if not yookassa_enabled():
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{YOOKASSA_API}/payments/{external_id}",
                headers=_auth_header(),
            )
        if resp.status_code >= 400:
            return None
        return resp.json()
    except httpx.HTTPError:
        logger.exception("YooKassa fetch payment failed")
        return None


async def _fulfill_order(db: AsyncSession, order: AIPaymentOrder, *, payment_id: str) -> AIPaymentOrder:
    if order.status == "succeeded" and order.entitlement_id:
        return order

    owner = await _get_owner_user(db)
    entitlement = await grant_entitlement(
        db,
        plan_id=order.plan_id,
        granted_by=owner,
        user_id=order.user_id,
        payment_reference=f"yookassa:{payment_id}",
        payment_amount=order.amount_rub,
        notes="Автоактивация после оплаты YooKassa",
    )
    order.status = "succeeded"
    order.paid_at = datetime.now(timezone.utc)
    order.entitlement_id = entitlement.id
    await db.flush()
    return order


async def process_yookassa_webhook(db: AsyncSession, payload: dict) -> bool:
    event = payload.get("event")
    obj = payload.get("object") or {}
    payment_id = obj.get("id")
    if not payment_id:
        return False

    payment = await fetch_yookassa_payment(payment_id)
    if not payment or payment.get("status") != "succeeded":
        return False

    metadata = payment.get("metadata") or {}
    order_id = metadata.get("order_id")
    order: AIPaymentOrder | None = None

    if order_id:
        result = await db.execute(select(AIPaymentOrder).where(AIPaymentOrder.id == int(order_id)))
        order = result.scalar_one_or_none()
    if order is None:
        result = await db.execute(
            select(AIPaymentOrder).where(AIPaymentOrder.external_id == payment_id)
        )
        order = result.scalar_one_or_none()
    if order is None:
        logger.warning("YooKassa webhook: order not found for payment %s", payment_id)
        return False

    await _fulfill_order(db, order, payment_id=payment_id)
    logger.info("AI subscription activated for user %s plan %s", order.user_id, order.plan_id)
    return True


async def sync_order_by_id(db: AsyncSession, order_id: int, *, user_id: int | None = None) -> AIPaymentOrder | None:
    result = await db.execute(select(AIPaymentOrder).where(AIPaymentOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        return None
    if user_id is not None and order.user_id != user_id:
        return None
    if order.status == "succeeded":
        return order
    if not order.external_id:
        return order

    payment = await fetch_yookassa_payment(order.external_id)
    if payment and payment.get("status") == "succeeded":
        await _fulfill_order(db, order, payment_id=order.external_id)
    elif payment and payment.get("status") == "canceled":
        order.status = "canceled"
        await db.flush()
    return order


async def get_latest_user_order(db: AsyncSession, user_id: int) -> AIPaymentOrder | None:
    result = await db.execute(
        select(AIPaymentOrder)
        .where(AIPaymentOrder.user_id == user_id)
        .order_by(AIPaymentOrder.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
