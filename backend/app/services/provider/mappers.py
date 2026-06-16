"""Provider API response mappers."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SERVICE_TYPE_LABELS, ServiceType
from app.models.provider_busy import ProviderBusyBlock
from app.models.service import ProviderService, ServiceProvider
from app.schemas.service import (
    BusyBlockResponse,
    ProviderDetailResponse,
    ProviderServiceResponse,
    ScheduleResponse,
)
from app.services.schedule import DAY_LABELS, format_time, get_provider_status_today


def list_service_types() -> list[dict[str, str]]:
    """Return service type enum options."""
    return [
        {"value": service_type.value, "label": SERVICE_TYPE_LABELS[service_type]}
        for service_type in ServiceType
    ]


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
