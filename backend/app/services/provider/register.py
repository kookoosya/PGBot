"""Provider registration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.models.enums import UserRole, VerificationStatus
from app.models.service import ProviderSchedule, ProviderService, ServiceProvider
from app.models.user import Role, User
from app.schemas.service import ProviderRegisterRequest
from app.services.notifications import notify_owner
from app.services.schedule import parse_time

from .schemas import ProviderValidationError


async def register_provider(db: AsyncSession, data: ProviderRegisterRequest) -> dict:
    """Register a new service provider pending approval."""
    ok, msg = validate_password(data.password)
    if not ok:
        raise ProviderValidationError(msg)

    existing = await db.execute(select(User).where(
        (User.username == data.username) | (User.email == data.email)
    ))
    if existing.scalar_one_or_none():
        raise ProviderValidationError("Логин или email уже заняты")

    role_result = await db.execute(select(Role).where(Role.name == UserRole.SERVICE_PROVIDER))
    role = role_result.scalar_one_or_none()
    if not role:
        role = Role(name=UserRole.SERVICE_PROVIDER, description="Мастер/специалист услуг")
        db.add(role)
        await db.flush()

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        phone=data.phone,
        role_id=role.id,
        verification_status=VerificationStatus.PENDING,
        is_active=False,
    )
    db.add(user)
    await db.flush()

    provider = ServiceProvider(
        user_id=user.id,
        full_name=data.full_name,
        phone=data.phone,
        email=data.email,
        bio=data.bio,
        address=data.address,
        verification_status=VerificationStatus.PENDING,
        is_active=False,
    )
    db.add(provider)
    await db.flush()

    for svc in data.services:
        db.add(ProviderService(
            provider_id=provider.id,
            service_type=svc.service_type,
            name=svc.name,
            description=svc.description,
            duration_minutes=svc.duration_minutes,
            price=svc.price,
        ))

    for sch in data.schedule:
        db.add(ProviderSchedule(
            provider_id=provider.id,
            day_of_week=sch.day_of_week,
            start_time=parse_time(sch.start_time),
            end_time=parse_time(sch.end_time),
            is_working=sch.is_working,
        ))

    svc_names = ", ".join(service.name for service in data.services)
    await notify_owner(
        "💇 Новая заявка мастера\n\n"
        f"#{provider.id} · {data.full_name}\n"
        f"📞 {data.phone}\n"
        f"Услуги: {svc_names}\n\n"
        "Одобрите в админ-панели."
    )
    return {"id": provider.id, "message": "Заявка отправлена на проверку. После одобрения вы появитесь в каталоге."}
