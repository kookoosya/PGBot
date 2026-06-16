"""Place reviews — create, deduplication and rating recalculation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place, PlaceReview
from app.models.user import User

from .details import load_place
from .schemas import (
    REVIEW_DUPLICATE_HOURS,
    PlaceReviewInput,
    PlaceReviewResult,
    PlaceValidationError,
    resolve_author_name,
)

logger = logging.getLogger(__name__)


async def check_duplicate_review(
    db: AsyncSession,
    place_id: int,
    *,
    user_id: int | None,
    author_name: str,
) -> None:
    """Reject duplicate reviews from the same user or anonymous author."""
    try:
        if user_id is not None:
            existing = await db.execute(
                select(PlaceReview.id)
                .where(PlaceReview.place_id == place_id, PlaceReview.user_id == user_id)
                .limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                raise PlaceValidationError(
                    "Вы уже оставляли отзыв об этом месте",
                    status_code=409,
                )
            return

        since = datetime.now(timezone.utc) - timedelta(hours=REVIEW_DUPLICATE_HOURS)
        recent = await db.execute(
            select(PlaceReview.id)
            .where(
                PlaceReview.place_id == place_id,
                PlaceReview.user_id.is_(None),
                PlaceReview.author_name == author_name,
                PlaceReview.created_at >= since,
            )
            .limit(1)
        )
        if recent.scalar_one_or_none() is not None:
            raise PlaceValidationError(
                "Отзыв с этим именем уже отправляли недавно — попробуйте позже",
                status_code=429,
            )
    except PlaceValidationError:
        raise
    except Exception:
        logger.exception(
            "Duplicate review check failed for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise


async def recalculate_place_rating(db: AsyncSession, place: Place) -> None:
    """Update ``avg_rating`` and ``review_count`` from persisted reviews."""
    try:
        avg_result = await db.execute(
            select(func.avg(PlaceReview.rating), func.count(PlaceReview.id)).where(
                PlaceReview.place_id == place.id
            )
        )
        avg_row = avg_result.one()
        place.avg_rating = round(float(avg_row[0] or 0), 1)
        place.review_count = avg_row[1] or 0
    except Exception:
        logger.exception("Failed to recalculate rating for place #%s", place.id)
        raise


async def add_place_review(
    db: AsyncSession,
    place_id: int,
    data: PlaceReviewInput,
    *,
    user: User | None = None,
) -> PlaceReviewResult:
    """Add a review to a place and recalculate its average rating."""
    place = await load_place(db, place_id)
    author_name = resolve_author_name(data.author_name, user)
    user_id = user.id if user else None

    await check_duplicate_review(
        db,
        place_id,
        user_id=user_id,
        author_name=author_name,
    )

    review = PlaceReview(
        place_id=place_id,
        rating=data.rating,
        text=data.text,
        author_name=author_name,
        user_id=user_id,
    )

    try:
        db.add(review)
        await db.flush()
        await recalculate_place_rating(db, place)
    except PlaceValidationError:
        raise
    except Exception:
        logger.exception(
            "Failed to persist review for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise

    logger.info(
        "Place review #%s added to place #%s (rating=%s, user_id=%s)",
        review.id,
        place_id,
        data.rating,
        user_id,
    )
    return PlaceReviewResult(review=review, place=place)
