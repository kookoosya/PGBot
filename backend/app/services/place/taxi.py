"""Active taxi services for the map."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxi import TaxiService

logger = logging.getLogger(__name__)


async def list_active_taxi(db: AsyncSession) -> list[TaxiService]:
    """Return active taxi services sorted by ``sort_order`` and rating."""
    try:
        result = await db.execute(
            select(TaxiService)
            .where(TaxiService.is_active.is_(True))
            .order_by(TaxiService.sort_order, TaxiService.rating.desc())
        )
        items = list(result.scalars().all())
    except Exception:
        logger.exception("Failed to load active taxi services")
        raise

    logger.debug("Loaded %s active taxi service(s)", len(items))
    return items
