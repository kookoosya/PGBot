"""Authentication and resident self-registration.

Public API: ``authenticate``, ``change_password``, ``register_resident``, ``user_to_response``.
Errors: ``AuthValidationError``, ``AuthFailedError``, ``AccountLockedError``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.password_policy import validate_password
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.enums import UserRole, VerificationStatus
from app.models.user import Role, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, Token, UserCreate
from app.services.audit import log_action
from app.services.user_service import UserValidationError, user_to_response
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthFailedError(ServiceError):
    def __init__(self, detail: str = "Неверный логин или пароль") -> None:
        super().__init__(detail, status_code=401)


class AuthValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class AccountLockedError(ServiceError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=423)


def _check_lockout(user: User) -> None:
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise AccountLockedError(f"Аккаунт заблокирован. Попробуйте через {remaining} мин.")


async def _record_failed_login(user: User, db: AsyncSession) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        user.failed_login_attempts = 0


async def authenticate(
    db: AsyncSession,
    data: LoginRequest,
    *,
    ip_address: str | None = None,
) -> Token:
    """Validate credentials and return a JWT access token."""
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise AuthFailedError()

    _check_lockout(user)

    if not verify_password(data.password, user.hashed_password):
        await _record_failed_login(user, db)
        await log_action(
            db, "login_failed", "user", user.id,
            details={"ip": ip_address}, ip_address=ip_address,
        )
        raise AuthFailedError()

    if user.verification_status == VerificationStatus.PENDING:
        raise AuthValidationError("Аккаунт ожидает верификации", status_code=403)
    if user.verification_status == VerificationStatus.REJECTED:
        raise AuthValidationError("Заявка отклонена", status_code=403)
    if not user.is_active:
        raise AuthValidationError("Аккаунт отключён", status_code=403)

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    pwd_ts = int((user.password_changed_at or user.created_at).timestamp())
    role_name = user.role.name.value if hasattr(user.role.name, "value") else user.role.name
    token = create_access_token({"sub": str(user.id), "role": role_name, "pwd": pwd_ts})
    await log_action(db, "login_success", "user", user.id, user_id=user.id, ip_address=ip_address)
    return Token(access_token=token)


async def change_password(
    db: AsyncSession,
    user: User,
    data: ChangePasswordRequest,
    *,
    ip_address: str | None = None,
) -> dict[str, str]:
    """Change password for the current user."""
    if not user.hashed_password or not verify_password(data.current_password, user.hashed_password):
        raise AuthValidationError("Неверный текущий пароль")

    ok, msg = validate_password(data.new_password)
    if not ok:
        raise AuthValidationError(msg)

    user.hashed_password = get_password_hash(data.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    user.failed_login_attempts = 0
    user.locked_until = None

    await log_action(
        db, "password_change", "user", user.id,
        user_id=user.id, ip_address=ip_address,
    )
    return {"message": "Пароль изменён"}


async def register_resident(db: AsyncSession, data: UserCreate):
    """Public resident registration."""
    if data.role != UserRole.RESIDENT:
        raise AuthValidationError(
            "Публичная регистрация только для жителей. Службы — через /register",
            status_code=403,
        )

    ok, msg = validate_password(data.password)
    if not ok:
        raise AuthValidationError(msg)

    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise UserValidationError("Логин уже занят")

    if data.email:
        email_taken = await db.execute(select(User).where(User.email == data.email))
        if email_taken.scalar_one_or_none():
            raise UserValidationError("Email уже занят")

    role_result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    role = role_result.scalar_one_or_none()
    if not role:
        raise UserValidationError("Роль не найдена")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role_id=role.id,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, ["role"])
    return user_to_response(user)
