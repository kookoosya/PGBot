"""Service providers seed — intentionally empty. Masters register themselves."""

from sqlalchemy.ext.asyncio import AsyncSession


async def seed_service_providers(db: AsyncSession) -> int:
    """No demo masters — catalog starts empty until real registration."""
    return 0
