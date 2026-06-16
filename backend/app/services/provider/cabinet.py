"""Provider cabinet: schedule, services, busy blocks, appointments."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.provider_busy import ProviderBusyBlock
from app.models.service import ProviderSchedule, ProviderService, ServiceAppointment
from app.models.user import User
from app.schemas.service import (
    AppointmentResponse,
    BusyBlockCreate,
    BusyBlockResponse,
    ProviderServiceResponse,
    ServiceItemInput,
    UpdateScheduleRequest,
)
from app.services.schedule import format_time, parse_time

from .crud import get_provider_for_user
from .mappers import busy_block_to_response, provider_service_to_response
from .schemas import ProviderNotFoundError


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
