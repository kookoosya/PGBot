"""Unit and PostgreSQL tests for place reviews and complaints."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlaceCategory, ShopComplaintType
from app.services.place_service import (
    PlaceComplaintInput,
    PlaceReviewInput,
    PlaceValidationError,
    add_place_review,
    create_place_complaint,
    place_rating_meta,
)
from tests.helpers.db_factories import create_place

pytestmark = pytest.mark.postgres


def test_place_rating_meta_prefers_external_yandex():
    from types import SimpleNamespace

    place = SimpleNamespace(
        external_rating=4.5,
        external_review_count=120,
        external_source="yandex",
        avg_rating=3.0,
        review_count=2,
    )
    meta = place_rating_meta(place)
    assert meta["display_rating"] == 4.5
    assert meta["rating_source"] == "yandex"


@pytest.mark.asyncio
async def test_add_place_review_updates_rating(db_session: AsyncSession):
    place = await create_place(db_session, name="Магазин у дома")

    result = await add_place_review(
        db_session,
        place.id,
        PlaceReviewInput(rating=4, text="Хороший выбор", author_name="Анна"),
    )
    assert result.review.rating == 4
    assert result.place.avg_rating == 4.0
    assert result.place.review_count == 1


@pytest.mark.asyncio
async def test_duplicate_review_rejected(db_session: AsyncSession):
    place = await create_place(db_session, name="Аптека центральная")

    await add_place_review(
        db_session,
        place.id,
        PlaceReviewInput(rating=5, text="Отлично", author_name="Пётр"),
    )

    with pytest.raises(PlaceValidationError, match="уже отправляли"):
        await add_place_review(
            db_session,
            place.id,
            PlaceReviewInput(rating=3, text="Повтор", author_name="Пётр"),
        )


@pytest.mark.asyncio
@patch("app.services.place.complaint.safe_notify_owner", new_callable=AsyncMock, return_value=True)
async def test_create_place_complaint_links_issue(mock_notify, db_session: AsyncSession):
    place = await create_place(db_session, category=PlaceCategory.SHOP)

    result = await create_place_complaint(
        db_session,
        place.id,
        PlaceComplaintInput(
            complaint_type=ShopComplaintType.PRICE_TAG_FRAUD,
            description="На ценнике 100 рублей, на кассе сняли 150",
            price_tagged="100",
            price_charged="150",
            author_name="Покупатель",
        ),
    )

    assert result.complaint.id is not None
    assert result.issue.id is not None
    assert result.complaint.issue_id == result.issue.id
    assert place.complaint_count == 1
    mock_notify.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.place.complaint.safe_notify_owner", new_callable=AsyncMock, return_value=True)
async def test_duplicate_complaint_within_cooldown(mock_notify, db_session: AsyncSession):
    place = await create_place(db_session)

    payload = PlaceComplaintInput(
        complaint_type=ShopComplaintType.OTHER,
        description="Первичная жалоба на обслуживание в магазине",
        author_name="Клиент",
    )
    await create_place_complaint(db_session, place.id, payload)

    with pytest.raises(PlaceValidationError, match="уже отправляли"):
        await create_place_complaint(db_session, place.id, payload)
