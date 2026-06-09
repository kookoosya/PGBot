"""Taxi services listed on the map."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxi import TaxiService


async def list_active_taxi(db: AsyncSession) -> list[TaxiService]:
    """Return active taxi services sorted by ``sort_order`` and rating."""
    result = await db.execute(
        select(TaxiService)
        .where(TaxiService.is_active.is_(True))
        .order_by(TaxiService.sort_order, TaxiService.rating.desc()),
    )
    return list(result.scalars().all())
