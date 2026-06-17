"""Tests for VK classified ad creation via classified_service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassifiedCategory
from app.services.classified_service import ClassifiedValidationError, create_classified_ad_from_vk
from tests.conftest import postgres_available

pytestmark = pytest.mark.postgres


@pytest.fixture
async def db_session():
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_create_classified_ad_from_vk_success(db_session: AsyncSession):
    result = await create_classified_ad_from_vk(
        db_session,
        from_id=12345,
        category=ClassifiedCategory.OTHER,
        title="Продаю велосипед",
        description="Отличное состояние, самовывоз в посёлке",
        phone="+79001234567",
        author_name="Иван",
    )
    assert result.ad.id is not None
    assert result.ad.vk_id == 12345
    assert result.ad.payment_status.value == "pending"
    assert result.ad.is_active is False


@pytest.mark.asyncio
async def test_create_classified_ad_from_vk_rejects_scam(db_session: AsyncSession):
    with pytest.raises(ClassifiedValidationError, match="мошенническую"):
        await create_classified_ad_from_vk(
            db_session,
            from_id=12346,
            category=ClassifiedCategory.OTHER,
            title="Срочно",
            description="Нужна предоплата на карту",
            phone="+79001234568",
            author_name="Тест",
        )
