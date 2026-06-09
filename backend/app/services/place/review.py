"""Place reviews and rating recalculation."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place, PlaceReview
from app.models.user import User
from app.schemas.place import PlaceReviewResponse
from app.services.place.crud import load_place
from app.services.place.schemas import PlaceReviewInput, PlaceReviewResult, resolve_author_name


async def recalculate_place_rating(db: AsyncSession, place: Place) -> None:
    """Update ``avg_rating`` and ``review_count`` from persisted reviews."""
    avg_result = await db.execute(
        select(func.avg(PlaceReview.rating), func.count(PlaceReview.id)).where(
            PlaceReview.place_id == place.id,
        ),
    )
    avg_row = avg_result.one()
    place.avg_rating = round(float(avg_row[0] or 0), 1)
    place.review_count = avg_row[1] or 0


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

    review = PlaceReview(
        place_id=place_id,
        rating=data.rating,
        text=data.text,
        author_name=author_name,
        user_id=user.id if user else None,
    )
    db.add(review)
    await db.flush()
    await recalculate_place_rating(db, place)
    return PlaceReviewResult(review=review)


def review_to_response(review: PlaceReview) -> PlaceReviewResponse:
    """Map review ORM row to API response."""
    return PlaceReviewResponse.model_validate(review)
