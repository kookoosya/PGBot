"""Tests for VK Mini App API extensions (classifieds mine, issue comments)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.deps import get_current_user
from app.database import get_db
from app.main import app
from app.models.enums import ClassifiedPaymentStatus, UserRole


def _make_user(user_id: int = 7) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.role = MagicMock()
    user.role.name = UserRole.RESIDENT
    user.full_name = "Иван Житель"
    return user


@pytest.fixture
async def api_client():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    async def _mock_get_db():
        yield session

    app.dependency_overrides[get_db] = _mock_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
@patch("app.api.v1.classifieds.search_classifieds", new_callable=AsyncMock)
async def test_classifieds_mine_returns_user_ads(mock_search, api_client: AsyncClient):
    user = _make_user(5)
    app.dependency_overrides[get_current_user] = lambda: user

    ad = MagicMock()
    ad.id = 1
    ad.category = "firewood"
    ad.title = "Дрова"
    ad.description = "Сухие дрова"
    ad.price = 1000
    ad.price_unit = "₽"
    ad.phone = "+79990001122"
    ad.author_name = "Иван"
    ad.address = None
    ad.contact_telegram = None
    ad.views_count = 3
    ad.created_at = datetime.now(timezone.utc)
    ad.payment_status = ClassifiedPaymentStatus.PENDING
    ad.payment_reference = None
    ad.placement_fee = 150
    ad.contact_vk = None
    ad.is_active = False

    result = MagicMock()
    result.items = [ad]
    result.total = 1
    result.page = 1
    result.page_size = 20
    mock_search.return_value = result

    response = await api_client.get("/api/v1/classifieds/mine", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Дрова"
    assert data["items"][0]["payment_status"] == "pending"
    call_params = mock_search.await_args.args[1]
    assert call_params.user_id == 5
    assert call_params.payment_status is None


@pytest.mark.asyncio
@patch("app.api.v1.issues.list_comments_for_user", new_callable=AsyncMock)
async def test_issue_comments_list(mock_list, api_client: AsyncClient):
    user = _make_user(3)
    app.dependency_overrides[get_current_user] = lambda: user

    comment = MagicMock()
    comment.id = 10
    comment.text = "Уточнение от жителя"
    comment.is_internal = False
    comment.author_id = 3
    comment.created_at = datetime.now(timezone.utc)
    comment.author = MagicMock(full_name="Иван Житель")
    mock_list.return_value = [comment]

    response = await api_client.get("/api/v1/issues/42/comments", headers={"Authorization": "Bearer test"})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["text"] == "Уточнение от жителя"
    assert data["items"][0]["author_name"] == "Иван Житель"
