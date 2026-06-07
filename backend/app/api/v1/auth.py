from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.deps import get_client_ip, get_current_user, require_owner
from app.core.password_policy import validate_password
from app.core.security import create_access_token, get_password_hash, verify_password
from app.database import get_db
from app.models.enums import UserRole, VerificationStatus
from app.models.user import Role, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, Token, UserCreate, UserResponse
from app.services.audit import log_action

router = APIRouter()
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


def _check_lockout(user: User) -> None:
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Аккаунт заблокирован. Попробуйте через {remaining} мин.",
        )


async def _record_failed_login(user: User, db: AsyncSession) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.LOGIN_MAX_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
        user.failed_login_attempts = 0


@router.post("/login", response_model=Token)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(request: Request, data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.username == data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")

    _check_lockout(user)

    if not verify_password(data.password, user.hashed_password):
        await _record_failed_login(user, db)
        await log_action(
            db, "login_failed", "user", user.id,
            details={"ip": get_client_ip(request)}, ip_address=get_client_ip(request),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")

    if user.verification_status == VerificationStatus.PENDING:
        raise HTTPException(status_code=403, detail="Аккаунт ожидает верификации")
    if user.verification_status == VerificationStatus.REJECTED:
        raise HTTPException(status_code=403, detail="Заявка отклонена")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт отключён")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)

    pwd_ts = int((user.password_changed_at or user.created_at).timestamp())
    token = create_access_token({"sub": str(user.id), "role": user.role.name.value, "pwd": pwd_ts})
    await log_action(db, "login_success", "user", user.id, user_id=user.id, ip_address=get_client_ip(request))
    return Token(access_token=token)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.hashed_password or not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    ok, msg = validate_password(data.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    current_user.hashed_password = get_password_hash(data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    current_user.failed_login_attempts = 0
    current_user.locked_until = None

    await log_action(
        db, "password_change", "user", current_user.id,
        user_id=current_user.id, ip_address=get_client_ip(request),
    )
    return {"message": "Пароль изменён"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(request: Request, data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    if data.role != UserRole.RESIDENT:
        raise HTTPException(
            status_code=403,
            detail="Публичная регистрация только для жителей. Службы — через /register",
        )

    ok, msg = validate_password(data.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Логин уже занят")

    role_result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Роль не найдена")

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
    return UserResponse(
        id=user.id, username=user.username, email=user.email, full_name=user.full_name,
        phone=user.phone, vk_id=user.vk_id, role=user.role.name,
        department_id=user.department_id, is_active=user.is_active, created_at=user.created_at,
    )


@router.get("/owner-check")
async def owner_check(current_user: Annotated[User, Depends(require_owner())]):
    return {"ok": True, "username": current_user.username}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return UserResponse(
        id=current_user.id, username=current_user.username, email=current_user.email,
        full_name=current_user.full_name, phone=current_user.phone, vk_id=current_user.vk_id,
        role=current_user.role.name, department_id=current_user.department_id,
        is_active=current_user.is_active, organization=current_user.organization,
        position=current_user.position, verification_status=current_user.verification_status,
        created_at=current_user.created_at,
    )
