"""Paid AI access checks and owner grants."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_entitlement import AIEntitlement
from app.models.user import User
from app.services.ai_plans import build_ai_plans, plan_by_id, plan_to_dict


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_active(entitlement: AIEntitlement) -> bool:
    if not entitlement.is_active:
        return False
    if entitlement.expires_at and entitlement.expires_at <= _now():
        return False
    return True


async def find_active_entitlement(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    vk_id: int | None = None,
    web_identifier: str | None = None,
) -> AIEntitlement | None:
    conditions = [AIEntitlement.is_active.is_(True)]
    identity_filters = []
    if user_id is not None:
        identity_filters.append(AIEntitlement.user_id == user_id)
    if vk_id is not None:
        identity_filters.append(AIEntitlement.vk_id == vk_id)
    if web_identifier:
        identity_filters.append(AIEntitlement.web_identifier == web_identifier)
    if not identity_filters:
        return None

    result = await db.execute(
        select(AIEntitlement)
        .where(*conditions, or_(*identity_filters))
        .order_by(AIEntitlement.created_at.desc())
    )
    for entitlement in result.scalars().all():
        if _is_active(entitlement):
            return entitlement
    return None


async def maybe_grant_auto_trial(
    db: AsyncSession,
    user: User | None,
) -> AIEntitlement | None:
    """One-time trial for logged-in users — no paid API keys needed on their side."""
    if user is None:
        return None

    active = await find_active_entitlement(db, user_id=user.id)
    if active:
        return active

    prior = await db.execute(
        select(AIEntitlement).where(AIEntitlement.user_id == user.id).limit(1)
    )
    if prior.scalar_one_or_none():
        return None

    trial = plan_by_id("trial")
    if not trial:
        return None

    entitlement = AIEntitlement(
        user_id=user.id,
        plan_id=trial.id,
        expires_at=_now() + timedelta(days=trial.period_days),
        notes="Авто-пробный период после входа",
        is_active=True,
    )
    db.add(entitlement)
    await db.flush()
    return entitlement


async def resolve_ai_access(
    db: AsyncSession,
    *,
    user: User | None = None,
    web_identifier: str,
    vk_id: int | None = None,
    auto_trial: bool = True,
) -> dict:
    free_plan = plan_by_id("free")
    assert free_plan is not None

    if auto_trial and user is not None:
        await maybe_grant_auto_trial(db, user)

    entitlement = await find_active_entitlement(
        db,
        user_id=user.id if user else None,
        vk_id=vk_id,
        web_identifier=web_identifier,
    )
    if entitlement:
        paid_plan = plan_by_id(entitlement.plan_id) or plan_by_id("pro")
        assert paid_plan is not None
        return {
            "plan_id": paid_plan.id,
            "plan_name": paid_plan.name,
            "daily_limit": paid_plan.daily_limit,
            "chat_modes": list(paid_plan.chat_modes),
            "model_id": paid_plan.model_id,
            "is_paid": True,
            "expires_at": entitlement.expires_at.isoformat() if entitlement.expires_at else None,
            "payment_reference": entitlement.payment_reference,
        }

    return {
        "plan_id": free_plan.id,
        "plan_name": free_plan.name,
        "daily_limit": free_plan.daily_limit,
        "chat_modes": list(free_plan.chat_modes),
        "model_id": free_plan.model_id,
        "is_paid": False,
        "expires_at": None,
        "payment_reference": None,
    }


async def grant_entitlement(
    db: AsyncSession,
    *,
    plan_id: str,
    granted_by: User,
    user_id: int | None = None,
    vk_id: int | None = None,
    web_identifier: str | None = None,
    period_days: int | None = None,
    payment_reference: str | None = None,
    payment_amount: int | None = None,
    notes: str | None = None,
) -> AIEntitlement:
    plan = plan_by_id(plan_id)
    if not plan or plan.id == "free":
        raise ValueError("Неверный тариф")

    if not any([user_id, vk_id, web_identifier]):
        raise ValueError("Укажите user_id, vk_id или web_identifier")

    days = period_days or plan.period_days
    expires_at = _now() + timedelta(days=days) if days > 0 else None

    if user_id is not None:
        existing = await find_active_entitlement(db, user_id=user_id)
        if existing:
            existing.is_active = False
        if vk_id is not None:
            vk_existing = await find_active_entitlement(db, vk_id=vk_id)
            if vk_existing and vk_existing.id != (existing.id if existing else None):
                vk_existing.is_active = False

    entitlement = AIEntitlement(
        user_id=user_id,
        vk_id=vk_id,
        web_identifier=web_identifier,
        plan_id=plan.id,
        expires_at=expires_at,
        payment_reference=payment_reference,
        payment_amount=payment_amount,
        notes=notes,
        granted_by_id=granted_by.id,
        is_active=True,
    )
    db.add(entitlement)
    await db.flush()
    return entitlement


async def revoke_entitlement(db: AsyncSession, entitlement_id: int) -> AIEntitlement | None:
    result = await db.execute(select(AIEntitlement).where(AIEntitlement.id == entitlement_id))
    entitlement = result.scalar_one_or_none()
    if not entitlement:
        return None
    entitlement.is_active = False
    await db.flush()
    return entitlement


async def list_entitlements(db: AsyncSession, *, limit: int = 50) -> list[AIEntitlement]:
    result = await db.execute(
        select(AIEntitlement).order_by(AIEntitlement.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


def public_plans_payload() -> dict:
    plans = [plan_to_dict(plan) for plan in build_ai_plans()]
    return {
        "plans": plans,
        "notice": (
            "Бесплатно — 10 запросов в день. После входа — 7 дней пробного Pro через наш сервер "
            "(Gemini/Pollinations, прокси из РФ). Платная подписка — переводом, без зарубежных карт."
        ),
    }
