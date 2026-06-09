"""User verification — organization/official registration and approval.

Public API: ``register_organization``, ``register_official``, ``list_pending_verifications``,
``approve_verification``, ``reject_verification``, ``verification_to_response``.
Errors: ``VerificationNotFoundError``, ``VerificationValidationError``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.models.enums import OFFICIAL_ROLES, UserRole, VerificationStatus
from app.models.user import Role, User
from app.schemas.verification import (
    OfficialRegisterRequest,
    OrganizationRegisterRequest,
    VerificationAction,
    VerificationRequestResponse,
)
from app.services.audit import log_action
from app.services.notifications import notify_owner
from app.services.telegram import send_telegram_message
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


class VerificationNotFoundError(ServiceError):
    def __init__(self, detail: str = "Пользователь не найден") -> None:
        super().__init__(detail, status_code=404)


class VerificationValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


def verification_to_response(user: User) -> VerificationRequestResponse:
    """Map a pending user to verification API response."""
    return VerificationRequestResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        organization=user.organization,
        position=user.position,
        role=user.role.name,
        verification_status=user.verification_status,
        verification_note=user.verification_note,
        created_at=user.created_at,
    )


async def _ensure_unique_credentials(db: AsyncSession, username: str, email: str | None) -> None:
    for field, value, label in [
        ("username", username, "Логин"),
        ("email", email, "Email"),
    ]:
        if not value:
            continue
        result = await db.execute(select(User).where(getattr(User, field) == value))
        if result.scalar_one_or_none():
            raise VerificationValidationError(f"{label} уже занят")


async def register_organization(
    db: AsyncSession,
    data: OrganizationRegisterRequest,
) -> VerificationRequestResponse:
    """Register an organization pending owner approval."""
    ok, msg = validate_password(data.password)
    if not ok:
        raise VerificationValidationError(msg)

    await _ensure_unique_credentials(db, data.username, data.email)

    role_result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    role = role_result.scalar_one_or_none()
    if not role:
        raise VerificationValidationError("Роль не найдена")

    note_parts = [
        "[ОРГАНИЗАЦИЯ]",
        f"Адрес: {data.org_address}",
        f"Ответственный: {data.responsible_full_name}, {data.responsible_position}",
    ]
    if data.inn:
        note_parts.append(f"ИНН: {data.inn}")
    if data.website:
        note_parts.append(f"Сайт: {data.website}")
    note_parts.append(f"Описание: {data.description}")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.responsible_full_name,
        phone=data.phone,
        organization=data.organization_name,
        position=data.responsible_position,
        role_id=role.id,
        verification_status=VerificationStatus.PENDING,
        verification_note="\n".join(note_parts),
        is_active=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["role"])

    await notify_owner(
        "🏢 Новая организация на проверку\n\n"
        f"«{data.organization_name}»\n"
        f"Ответственный: {data.responsible_full_name}\n"
        f"📞 {data.phone} · {data.org_address}\n\n"
        "Одобрите в админ-панели → Верификация."
    )
    return verification_to_response(user)


async def register_official(
    db: AsyncSession,
    data: OfficialRegisterRequest,
) -> VerificationRequestResponse:
    """Register an official/moderator pending owner approval."""
    if data.role not in OFFICIAL_ROLES:
        raise VerificationValidationError(
            "Регистрация доступна только для администрации, соцслужб и модераторов",
        )

    ok, msg = validate_password(data.password)
    if not ok:
        raise VerificationValidationError(msg)

    await _ensure_unique_credentials(db, data.username, data.email)

    role_result = await db.execute(select(Role).where(Role.name == data.role))
    role = role_result.scalar_one_or_none()
    if not role:
        raise VerificationValidationError("Некорректная роль")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        organization=data.organization,
        position=data.position,
        role_id=role.id,
        verification_status=VerificationStatus.PENDING,
        verification_note=data.verification_note,
        is_active=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["role"])

    if settings.TELEGRAM_ADMIN_CHAT_ID:
        await send_telegram_message(
            settings.TELEGRAM_ADMIN_CHAT_ID,
            f"📝 <b>Новая заявка на верификацию</b>\n"
            f"👤 {user.full_name}\n"
            f"🏛 {user.organization} — {user.position}\n"
            f"📋 Роль: {user.role.name.value}\n"
            f"📧 {user.email}\n"
            f"📞 {user.phone}",
        )

    await notify_owner(
        "🏛 Заявка службы/администрации\n\n"
        f"{user.full_name} — {user.organization}\n"
        f"Роль: {user.role.name.value}\n"
        f"📞 {user.phone}\n\n"
        "Одобрите в админке → Верификация."
    )
    return verification_to_response(user)


async def list_pending_verifications(db: AsyncSession) -> list[VerificationRequestResponse]:
    """Return users awaiting verification approval."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.verification_status == VerificationStatus.PENDING)
        .order_by(User.created_at.desc())
    )
    return [verification_to_response(user) for user in result.scalars().all()]


async def _get_pending_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise VerificationNotFoundError()
    if user.verification_status != VerificationStatus.PENDING:
        raise VerificationValidationError("Заявка уже обработана")
    return user


async def approve_verification(
    db: AsyncSession,
    user_id: int,
    data: VerificationAction,
    *,
    actor_id: int,
    ip_address: str | None = None,
) -> VerificationRequestResponse:
    """Approve a pending verification request."""
    user = await _get_pending_user(db, user_id)
    user.verification_status = VerificationStatus.APPROVED
    user.is_active = True
    user.verified_at = datetime.now(timezone.utc)
    user.verified_by_id = actor_id
    if data.note:
        user.verification_note = data.note

    await log_action(
        db, "approve_verification", "user", user.id,
        user_id=actor_id, details={"note": data.note},
        ip_address=ip_address,
    )
    return verification_to_response(user)


async def reject_verification(
    db: AsyncSession,
    user_id: int,
    data: VerificationAction,
    *,
    actor_id: int,
    ip_address: str | None = None,
) -> VerificationRequestResponse:
    """Reject a pending verification request."""
    user = await _get_pending_user(db, user_id)
    user.verification_status = VerificationStatus.REJECTED
    user.is_active = False
    if data.note:
        user.verification_note = data.note

    await log_action(
        db, "reject_verification", "user", user.id,
        user_id=actor_id, details={"note": data.note},
        ip_address=ip_address,
    )
    return verification_to_response(user)
