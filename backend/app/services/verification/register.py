"""Organization and official registration pending verification."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.models.enums import OFFICIAL_ROLES, UserRole, VerificationStatus
from app.models.user import Role, User
from app.schemas.verification import OfficialRegisterRequest, OrganizationRegisterRequest, VerificationRequestResponse
from app.services.notifications import notify_owner
from app.services.telegram import send_telegram_message
from app.services.verification.credentials import ensure_unique_credentials
from app.services.verification.responses import verification_to_response
from app.services.verification.schemas import VerificationValidationError

settings = get_settings()


async def register_organization(
    db: AsyncSession,
    data: OrganizationRegisterRequest,
) -> VerificationRequestResponse:
    """Register an organization pending owner approval."""
    ok, msg = validate_password(data.password)
    if not ok:
        raise VerificationValidationError(msg)

    await ensure_unique_credentials(db, data.username, data.email)

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

    await ensure_unique_credentials(db, data.username, data.email)

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
