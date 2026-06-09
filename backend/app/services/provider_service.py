"""Service providers — registration, booking, schedule and cabinet.

Public API
----------
- ``list_service_types``, ``register_provider``, ``search_providers``, ``get_provider_details``
- ``get_provider_slots``, ``book_appointment``, ``list_pending_providers``
- ``approve_provider``, ``reject_provider``
- ``get_provider_for_user``, busy blocks, services, schedule, appointments
- Response mappers: ``provider_service_to_response``, ``build_provider_detail_response``

Errors: ``ProviderNotFoundError``, ``ProviderValidationError``, ``ProviderAccessDeniedError``.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.password_policy import validate_password
from app.core.security import get_password_hash
from app.models.enums import SERVICE_TYPE_LABELS, ServiceType, UserRole, VerificationStatus
from app.models.provider_busy import ProviderBusyBlock
from app.models.service import ProviderSchedule, ProviderService, ServiceAppointment, ServiceProvider
from app.models.user import Role, User
from app.schemas.service import (
    AppointmentResponse,
    BookAppointmentRequest,
    BusyBlockCreate,
    BusyBlockResponse,
    ProviderDetailResponse,
    ProviderListItem,
    ProviderRegisterRequest,
    ProviderServiceResponse,
    ScheduleResponse,
    ServiceItemInput,
    SlotsResponse,
    TimeSlot,
    UpdateScheduleRequest,
)
from app.services.notifications import notify_owner, notify_vk_user
from app.services.schedule import (
    DAY_LABELS,
    format_time,
    get_provider_slots,
    get_provider_status_today,
    parse_time,
)
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)


class ProviderNotFoundError(ServiceError):
    def __init__(self, detail: str = "Мастер не найден") -> None:
        super().__init__(detail, status_code=404)


class ProviderValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class ProviderAccessDeniedError(ServiceError):
    def __init__(self, detail: str = "Доступ только для мастеров") -> None:
        super().__init__(detail, status_code=403)


def list_service_types() -> list[dict[str, str]]:
    """Return service type enum options."""
    return [{"value": service_type.value, "label": SERVICE_TYPE_LABELS[service_type]} for service_type in ServiceType]


def provider_service_to_response(service: ProviderService) -> ProviderServiceResponse:
    """Map provider service ORM row to API response."""
    return ProviderServiceResponse(
        id=service.id,
        service_type=service.service_type,
        service_label=SERVICE_TYPE_LABELS.get(service.service_type, service.service_type),
        name=service.name,
        description=service.description,
        duration_minutes=service.duration_minutes,
        price=service.price,
    )


def busy_block_to_response(block: ProviderBusyBlock) -> BusyBlockResponse:
    """Map busy block ORM row to API response."""
    return BusyBlockResponse(
        id=block.id,
        block_date=block.block_date,
        start_time=format_time(block.start_time),
        end_time=format_time(block.end_time),
        reason=block.reason,
        note=block.note,
    )


async def build_provider_detail_response(
    db: AsyncSession,
    provider: ServiceProvider,
) -> ProviderDetailResponse:
    """Build full provider detail including schedule and today's status."""
    status, next_slot = await get_provider_status_today(db, provider)
    schedule = [
        ScheduleResponse(
            day_of_week=entry.day_of_week,
            day_label=DAY_LABELS[entry.day_of_week],
            start_time=format_time(entry.start_time),
            end_time=format_time(entry.end_time),
            is_working=entry.is_working,
        )
        for entry in sorted(provider.schedule, key=lambda item: item.day_of_week)
    ]
    return ProviderDetailResponse(
        id=provider.id,
        full_name=provider.full_name,
        phone=provider.phone,
        bio=provider.bio,
        address=provider.address,
        avg_rating=provider.avg_rating,
        review_count=provider.review_count,
        services=[provider_service_to_response(service) for service in provider.services if service.is_active],
        status_today=status,
        next_free_slot=next_slot,
        schedule=schedule,
        verification_status=provider.verification_status,
    )


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


async def search_providers(
    db: AsyncSession,
    *,
    service_type: Optional[ServiceType] = None,
) -> list[ProviderListItem]:
    """Return active approved providers for the public catalog."""
    query = (
        select(ServiceProvider)
        .options(selectinload(ServiceProvider.services))
        .where(
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    result = await db.execute(query.order_by(ServiceProvider.full_name))
    items: list[ProviderListItem] = []
    for provider in result.scalars().all():
        services = [provider_service_to_response(service) for service in provider.services if service.is_active]
        if service_type and not any(service.service_type == service_type for service in provider.services):
            continue
        status, next_slot = await get_provider_status_today(db, provider)
        items.append(ProviderListItem(
            id=provider.id,
            full_name=provider.full_name,
            phone=provider.phone,
            bio=provider.bio,
            address=provider.address,
            avg_rating=provider.avg_rating,
            review_count=provider.review_count,
            services=services,
            status_today=status,
            next_free_slot=next_slot,
        ))
    return items


async def list_pending_providers(db: AsyncSession) -> list[dict]:
    """Return providers awaiting approval."""
    result = await db.execute(
        select(ServiceProvider)
        .options(selectinload(ServiceProvider.services))
        .where(ServiceProvider.verification_status == VerificationStatus.PENDING)
    )
    return [
        {
            "id": provider.id,
            "full_name": provider.full_name,
            "phone": provider.phone,
            "address": provider.address,
            "services": [service.name for service in provider.services],
        }
        for provider in result.scalars().all()
    ]


async def _get_provider(db: AsyncSession, provider_id: int) -> ServiceProvider:
    result = await db.execute(select(ServiceProvider).where(ServiceProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise ProviderNotFoundError()
    return provider


async def approve_provider(db: AsyncSession, provider_id: int) -> dict:
    """Approve a pending provider and notify them."""
    provider = await _get_provider(db, provider_id)
    provider.verification_status = VerificationStatus.APPROVED
    provider.is_active = True
    if provider.user_id:
        user_result = await db.execute(select(User).where(User.id == provider.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.verification_status = VerificationStatus.APPROVED
            user.is_active = True
            if user.vk_id:
                await notify_vk_user(
                    user.vk_id,
                    f"✅ Ваш профиль мастера одобрен!\n\n{provider.full_name} — теперь в каталоге услуг посёлка.",
                )
    await notify_owner(f"✅ Мастер #{provider_id} «{provider.full_name}» одобрен и опубликован.")
    return {"status": "approved"}


async def reject_provider(
    db: AsyncSession,
    provider_id: int,
    *,
    reason: str = "Не подтверждены данные",
) -> dict:
    """Reject a pending provider."""
    provider = await _get_provider(db, provider_id)
    provider.verification_status = VerificationStatus.REJECTED
    provider.is_active = False
    if provider.user_id:
        user_result = await db.execute(select(User).where(User.id == provider.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.verification_status = VerificationStatus.REJECTED
            user.is_active = False
            if user.vk_id:
                await notify_vk_user(user.vk_id, f"❌ Заявка мастера отклонена.\n{reason}")
    await notify_owner(f"❌ Мастер #{provider_id} «{provider.full_name}» отклонён: {reason}")
    return {"status": "rejected"}


async def get_provider_details(db: AsyncSession, provider_id: int) -> ProviderDetailResponse:
    """Load an active approved provider with schedule."""
    result = await db.execute(
        select(ServiceProvider)
        .options(selectinload(ServiceProvider.services), selectinload(ServiceProvider.schedule))
        .where(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise ProviderNotFoundError()
    return await build_provider_detail_response(db, provider)


async def get_provider_slots_response(
    db: AsyncSession,
    provider_id: int,
    *,
    appointment_date: date,
    service_id: int,
) -> SlotsResponse:
    """Return available time slots for booking."""
    svc_result = await db.execute(select(ProviderService).where(ProviderService.id == service_id))
    service = svc_result.scalar_one_or_none()
    if not service:
        raise ProviderNotFoundError("Услуга не найдена")

    prov_result = await db.execute(select(ServiceProvider).where(
        ServiceProvider.id == provider_id,
        ServiceProvider.is_active.is_(True),
        ServiceProvider.verification_status == VerificationStatus.APPROVED,
    ))
    provider = prov_result.scalar_one_or_none()
    if not provider:
        raise ProviderNotFoundError()

    slots, hours = await get_provider_slots(db, provider_id, appointment_date, service.duration_minutes)
    return SlotsResponse(
        date=appointment_date,
        provider_id=provider_id,
        provider_name=provider.full_name,
        working_hours=hours,
        slots=[TimeSlot(**slot) for slot in slots],
    )


async def book_appointment(
    db: AsyncSession,
    provider_id: int,
    data: BookAppointmentRequest,
) -> AppointmentResponse:
    """Book an appointment with an active provider."""
    svc_result = await db.execute(
        select(ProviderService).where(
            ProviderService.id == data.service_id,
            ProviderService.provider_id == provider_id,
        )
    )
    service = svc_result.scalar_one_or_none()
    if not service:
        raise ProviderNotFoundError("Услуга не найдена")

    prov_result = await db.execute(select(ServiceProvider).where(
        ServiceProvider.id == provider_id,
        ServiceProvider.is_active.is_(True),
        ServiceProvider.verification_status == VerificationStatus.APPROVED,
    ))
    provider = prov_result.scalar_one_or_none()
    if not provider:
        raise ProviderValidationError("Мастер недоступен для записи", status_code=404)

    start = parse_time(data.start_time)
    end_dt = datetime.combine(data.appointment_date, start) + timedelta(minutes=service.duration_minutes)
    end = end_dt.time()

    slots, _ = await get_provider_slots(db, provider_id, data.appointment_date, service.duration_minutes)
    slot = next((item for item in slots if item["time"] == data.start_time), None)
    if not slot or not slot["available"]:
        raise ProviderValidationError("Это время уже занято или недоступно")

    appointment = ServiceAppointment(
        provider_id=provider_id,
        service_id=service.id,
        client_name=data.client_name,
        client_phone=data.client_phone,
        appointment_date=data.appointment_date,
        start_time=start,
        end_time=end,
        notes=data.notes,
        status="booked",
    )
    db.add(appointment)
    await db.flush()

    date_str = appointment.appointment_date.isoformat()
    time_str = format_time(appointment.start_time)
    await notify_owner(
        "📅 Новая запись к мастеру!\n\n"
        f"Мастер: {provider.full_name}\n"
        f"Услуга: {service.name}\n"
        f"📆 {date_str} в {time_str}\n"
        f"👤 {appointment.client_name} · 📞 {appointment.client_phone}"
    )

    if provider.user_id:
        user_result = await db.execute(select(User).where(User.id == provider.user_id))
        provider_user = user_result.scalar_one_or_none()
        if provider_user and provider_user.vk_id:
            await notify_vk_user(
                provider_user.vk_id,
                f"📅 Новая запись!\n\n"
                f"{service.name} · {date_str} в {time_str}\n"
                f"Клиент: {appointment.client_name}, {appointment.client_phone}",
            )

    return AppointmentResponse(
        id=appointment.id,
        provider_name=provider.full_name,
        service_name=service.name,
        appointment_date=appointment.appointment_date,
        start_time=format_time(appointment.start_time),
        end_time=format_time(appointment.end_time),
        status=appointment.status,
        client_name=appointment.client_name,
    )


async def get_provider_for_user(db: AsyncSession, user: User) -> ServiceProvider:
    """Load the service provider profile linked to the current user."""
    role_name = user.role.name if hasattr(user.role, "name") else user.role
    if role_name != UserRole.SERVICE_PROVIDER:
        raise ProviderAccessDeniedError()
    result = await db.execute(
        select(ServiceProvider)
        .options(
            selectinload(ServiceProvider.services),
            selectinload(ServiceProvider.schedule),
        )
        .where(ServiceProvider.user_id == user.id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise ProviderNotFoundError("Профиль мастера не найден")
    return provider


async def add_busy_block(
    db: AsyncSession,
    user: User,
    data: BusyBlockCreate,
) -> BusyBlockResponse:
    """Add a busy block to the provider's schedule."""
    provider = await get_provider_for_user(db, user)
    block = ProviderBusyBlock(
        provider_id=provider.id,
        block_date=data.block_date,
        start_time=parse_time(data.start_time),
        end_time=parse_time(data.end_time),
        reason=data.reason,
        note=data.note,
    )
    db.add(block)
    await db.flush()
    return busy_block_to_response(block)


async def list_busy_blocks(db: AsyncSession, user: User) -> list[BusyBlockResponse]:
    """List busy blocks for the current provider."""
    provider = await get_provider_for_user(db, user)
    result = await db.execute(
        select(ProviderBusyBlock)
        .where(ProviderBusyBlock.provider_id == provider.id)
        .order_by(ProviderBusyBlock.block_date.desc())
        .limit(100)
    )
    return [busy_block_to_response(block) for block in result.scalars().all()]


async def delete_busy_block(db: AsyncSession, user: User, block_id: int) -> dict:
    """Delete a busy block owned by the current provider."""
    provider = await get_provider_for_user(db, user)
    result = await db.execute(
        select(ProviderBusyBlock).where(
            ProviderBusyBlock.id == block_id,
            ProviderBusyBlock.provider_id == provider.id,
        )
    )
    block = result.scalar_one_or_none()
    if not block:
        raise ProviderNotFoundError()
    await db.delete(block)
    return {"status": "deleted"}


async def add_provider_service(
    db: AsyncSession,
    user: User,
    data: ServiceItemInput,
) -> ProviderServiceResponse:
    """Add a service offering for the current provider."""
    provider = await get_provider_for_user(db, user)
    service = ProviderService(
        provider_id=provider.id,
        service_type=data.service_type,
        name=data.name,
        description=data.description,
        duration_minutes=data.duration_minutes,
        price=data.price,
    )
    db.add(service)
    await db.flush()
    return provider_service_to_response(service)


async def update_provider_schedule(
    db: AsyncSession,
    user: User,
    data: UpdateScheduleRequest,
) -> dict:
    """Replace the provider's weekly schedule."""
    provider = await get_provider_for_user(db, user)
    await db.execute(delete(ProviderSchedule).where(ProviderSchedule.provider_id == provider.id))
    await db.flush()

    for entry in data.schedule:
        db.add(ProviderSchedule(
            provider_id=provider.id,
            day_of_week=entry.day_of_week,
            start_time=parse_time(entry.start_time),
            end_time=parse_time(entry.end_time),
            is_working=entry.is_working,
        ))
    return {"status": "ok"}


async def list_provider_appointments(db: AsyncSession, user: User) -> list[AppointmentResponse]:
    """Return recent appointments for the current provider."""
    provider = await get_provider_for_user(db, user)
    result = await db.execute(
        select(ServiceAppointment)
        .options(selectinload(ServiceAppointment.service))
        .where(ServiceAppointment.provider_id == provider.id)
        .order_by(ServiceAppointment.appointment_date.desc())
        .limit(50)
    )
    return [
        AppointmentResponse(
            id=appointment.id,
            provider_name=provider.full_name,
            service_name=appointment.service.name if appointment.service else "—",
            appointment_date=appointment.appointment_date,
            start_time=format_time(appointment.start_time),
            end_time=format_time(appointment.end_time),
            status=appointment.status,
            client_name=appointment.client_name,
        )
        for appointment in result.scalars().all()
    ]
