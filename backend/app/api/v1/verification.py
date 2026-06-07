from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_client_ip, require_roles
from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.database import get_db
from app.models.enums import OFFICIAL_ROLES, UserRole, VerificationStatus
from app.models.user import Role, User
from app.schemas.verification import (
    OfficialRegisterRequest,
    VerificationAction,
    VerificationRequestResponse,
)
from app.services.audit import log_action
from app.services.telegram import send_telegram_message
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/register-official", response_model=VerificationRequestResponse, status_code=201)
async def register_official(data: OfficialRegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    if data.role not in OFFICIAL_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Регистрация доступна только для администрации, соцслужб и модераторов",
        )

    ok, msg = validate_password(data.password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    for field, value in [("username", data.username), ("email", data.email)]:
        result = await db.execute(select(User).where(getattr(User, field) == value))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"{'Логин' if field == 'username' else 'Email'} уже занят")

    role_result = await db.execute(select(Role).where(Role.name == data.role))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Некорректная роль")

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


@router.get("/pending", response_model=list[VerificationRequestResponse])
async def list_pending(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMINISTRATION))],
):
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.verification_status == VerificationStatus.PENDING)
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        VerificationRequestResponse(
            id=u.id, username=u.username, email=u.email, full_name=u.full_name,
            phone=u.phone, organization=u.organization, position=u.position,
            role=u.role.name, verification_status=u.verification_status,
            verification_note=u.verification_note, created_at=u.created_at,
        )
        for u in users
    ]


@router.post("/{user_id}/approve", response_model=VerificationRequestResponse)
async def approve_user(
    user_id: int,
    data: VerificationAction,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN))],
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.verification_status != VerificationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Заявка уже обработана")

    user.verification_status = VerificationStatus.APPROVED
    user.is_active = True
    user.verified_at = datetime.now(timezone.utc)
    user.verified_by_id = current_user.id
    if data.note:
        user.verification_note = data.note

    await log_action(
        db, "approve_verification", "user", user.id,
        user_id=current_user.id, details={"note": data.note},
        ip_address=get_client_ip(request),
    )

    return VerificationRequestResponse(
        id=user.id, username=user.username, email=user.email, full_name=user.full_name,
        phone=user.phone, organization=user.organization, position=user.position,
        role=user.role.name, verification_status=user.verification_status,
        verification_note=user.verification_note, created_at=user.created_at,
    )


@router.post("/{user_id}/reject", response_model=VerificationRequestResponse)
async def reject_user(
    user_id: int,
    data: VerificationAction,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN))],
):
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.verification_status != VerificationStatus.PENDING:
        raise HTTPException(status_code=400, detail="Заявка уже обработана")

    user.verification_status = VerificationStatus.REJECTED
    user.is_active = False
    if data.note:
        user.verification_note = data.note

    await log_action(
        db, "reject_verification", "user", user.id,
        user_id=current_user.id, details={"note": data.note},
        ip_address=get_client_ip(request),
    )

    return VerificationRequestResponse(
        id=user.id, username=user.username, email=user.email, full_name=user.full_name,
        phone=user.phone, organization=user.organization, position=user.position,
        role=user.role.name, verification_status=user.verification_status,
        verification_note=user.verification_note, created_at=user.created_at,
    )
