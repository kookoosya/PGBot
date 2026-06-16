"""Appointment booking."""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import ProviderService, ServiceAppointment
from app.schemas.service import AppointmentResponse, BookAppointmentRequest, SlotsResponse, TimeSlot
from app.services.notifications import notify_owner, notify_vk_user
from app.services.schedule import format_time, get_provider_slots, parse_time

from app.models.user import User

from .crud import get_active_provider
from .schemas import ProviderNotFoundError, ProviderValidationError


async def get_provider_slots_response(
    db: AsyncSession,
    provider_id: int,
    *,
    appointment_date,
    service_id: int,
) -> SlotsResponse:
    """Return available time slots for booking."""
    svc_result = await db.execute(select(ProviderService).where(ProviderService.id == service_id))
    service = svc_result.scalar_one_or_none()
    if not service:
        raise ProviderNotFoundError("Услуга не найдена")

    provider = await get_active_provider(db, provider_id)
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

    provider = await get_active_provider(db, provider_id)

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
