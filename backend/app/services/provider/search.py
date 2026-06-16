"""Public provider catalog and details."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import ServiceType, VerificationStatus
from app.models.service import ServiceProvider
from app.schemas.service import ProviderDetailResponse, ProviderListItem
from app.services.schedule import get_provider_status_today

from .mappers import build_provider_detail_response, provider_service_to_response
from .schemas import ProviderNotFoundError


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
