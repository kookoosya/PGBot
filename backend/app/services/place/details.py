"""Place detail loading."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.place import Place

from .responses import build_place_detail_response
from .schemas import COMPLAINTS_LIMIT, REVIEWS_LIMIT, PlaceDetailResult, PlaceNotFoundError

logger = logging.getLogger(__name__)

_PLACE_DETAIL_LOADS = (
    selectinload(Place.reviews),
    selectinload(Place.complaints),
)


async def load_place(db: AsyncSession, place_id: int) -> Place:
    """Load a place by id or raise ``PlaceNotFoundError``."""
    try:
        result = await db.execute(select(Place).where(Place.id == place_id))
        place = result.scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load place #%s", place_id)
        raise
    if place is None:
        raise PlaceNotFoundError()
    return place


async def get_place_details(db: AsyncSession, place_id: int) -> PlaceDetailResult:
    """Load a place with reviews and complaints; raise ``PlaceNotFoundError`` if missing."""
    try:
        result = await db.execute(
            select(Place)
            .options(*_PLACE_DETAIL_LOADS)
            .where(Place.id == place_id)
        )
        place = result.scalar_one_or_none()
    except Exception:
        logger.exception("Failed to load place #%s", place_id)
        raise

    if place is None:
        logger.debug("Place %s not found", place_id)
        raise PlaceNotFoundError()

    reviews = sorted(place.reviews, key=lambda review: review.created_at, reverse=True)[
        :REVIEWS_LIMIT
    ]
    recent_complaints = sorted(
        place.complaints,
        key=lambda complaint: complaint.created_at,
        reverse=True,
    )[:COMPLAINTS_LIMIT]

    response = build_place_detail_response(
        place,
        reviews=reviews,
        recent_complaints=recent_complaints,
    )
    return PlaceDetailResult(
        place=place,
        reviews=reviews,
        recent_complaints=recent_complaints,
        response=response,
    )
