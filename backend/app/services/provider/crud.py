"""Provider ORM lookups."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import UserRole, VerificationStatus
from app.models.service import ServiceProvider
from app.models.user import User

from .schemas import ProviderAccessDeniedError, ProviderNotFoundError


async def get_provider_by_id(db: AsyncSession, provider_id: int) -> ServiceProvider:
    result = await db.execute(select(ServiceProvider).where(ServiceProvider.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise ProviderNotFoundError()
    return provider


async def get_active_provider(db: AsyncSession, provider_id: int) -> ServiceProvider:
    result = await db.execute(
        select(ServiceProvider).where(
            ServiceProvider.id == provider_id,
            ServiceProvider.is_active.is_(True),
            ServiceProvider.verification_status == VerificationStatus.APPROVED,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise ProviderNotFoundError()
    return provider


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
