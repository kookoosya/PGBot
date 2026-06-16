"""PostgreSQL integration tests for public API with seeded data."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassifiedCategory, EventRegion
from app.services.classified.schemas import ClassifiedActorContext, ClassifiedCreateInput
from app.services.classified_service import create_classified_ad, moderate_classified_ad
from tests.helpers.db_factories import create_event, create_owner_user

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_public_today_includes_seeded_event(db_session: AsyncSession, api_client: AsyncClient):
    event = await create_event(
        db_session,
        title="Ярмарка у музея",
        region=EventRegion.PUSHKIN_GORY,
    )

    response = await api_client.get("/api/v1/public/today", params={"region": "pushkin_gory"})
    assert response.status_code == 200
    data = response.json()
    titles = {item["title"] for item in data["upcoming_events"]}
    assert event.title in titles


@pytest.mark.asyncio
async def test_public_events_dedupes_same_title(db_session: AsyncSession, api_client: AsyncClient):
    starts = datetime.now(timezone.utc) + timedelta(days=5)
    await create_event(
        db_session,
        title="«Майкл»",
        region=EventRegion.PSKOV,
        source="vk",
        starts_at=starts,
    )
    richer = await create_event(
        db_session,
        title="майкл",
        region=EventRegion.PSKOV,
        source="orbilet",
        starts_at=starts,
        poster_url="https://example.com/poster.jpg",
    )

    response = await api_client.get("/api/v1/public/events", params={"region": "pskov", "limit": 50})
    assert response.status_code == 200
    data = response.json()
    michael_items = [item for item in data["items"] if "майкл" in item["title"].lower()]
    assert len(michael_items) == 1
    assert michael_items[0]["id"] == richer.id


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_public_classifieds_category_filter(
    _notify_subs,
    _notify_owner,
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    owner = await create_owner_user(db_session)
    created = await create_classified_ad(
        db_session,
        ClassifiedCreateInput(
            category=ClassifiedCategory.FIREWOOD,
            title="Дрова ольховые сухие",
            description="Колотые дрова, доставка по посёлку",
            phone="+79005554433",
            author_name="Сосед",
            agree_rules=True,
        ),
    )
    await moderate_classified_ad(
        db_session,
        created.ad.id,
        action="approve",
        actor=ClassifiedActorContext(actor_id=owner.id),
    )

    response = await api_client.get(
        "/api/v1/classifieds",
        params={"category": "firewood", "ads_only": "true", "page_size": 50},
    )
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert created.ad.id in ids

    other = await api_client.get(
        "/api/v1/classifieds",
        params={"category": "rent", "ads_only": "true", "page_size": 50},
    )
    assert created.ad.id not in {item["id"] for item in other.json()["items"]}


@pytest.mark.asyncio
async def test_public_classifieds_search_filter(db_session: AsyncSession, api_client: AsyncClient):
    owner = await create_owner_user(db_session)
    with patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True):
        created = await create_classified_ad(
            db_session,
            ClassifiedCreateInput(
                category=ClassifiedCategory.SALE,
                title="Велосипед горный",
                description="Продаю велосипед в отличном состоянии",
                phone="+79001112233",
                author_name="Продавец",
                agree_rules=True,
            ),
        )
    await moderate_classified_ad(
        db_session,
        created.ad.id,
        action="approve",
        actor=ClassifiedActorContext(actor_id=owner.id),
    )

    found = await api_client.get("/api/v1/classifieds", params={"search": "велосипед", "page_size": 50})
    assert found.status_code == 200
    assert any(item["id"] == created.ad.id for item in found.json()["items"])

    missing = await api_client.get("/api/v1/classifieds", params={"search": "самокат", "page_size": 50})
    assert created.ad.id not in {item["id"] for item in missing.json()["items"]}


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_classified_mine_lists_user_ads(
    _notify_subs,
    _notify_owner,
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    from app.models.enums import UserRole
    from tests.helpers.db_factories import auth_headers_for, create_user

    user = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Продавец")
    created = await create_classified_ad(
        db_session,
        ClassifiedCreateInput(
            category=ClassifiedCategory.FIREWOOD,
            title="Дрова для бани",
            description="Сухие берёзовые дрова, самовывоз",
            phone="+79006665544",
            author_name="Продавец",
            agree_rules=True,
        ),
        user=user,
    )

    response = await api_client.get("/api/v1/classifieds/mine", headers=auth_headers_for(user))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["id"] == created.ad.id for item in data["items"])
    assert data["items"][0]["payment_status"] == "pending"


@pytest.mark.asyncio
async def test_public_info_has_contact_links(api_client: AsyncClient):
    response = await api_client.get("/api/v1/public/info")
    assert response.status_code == 200
    data = response.json()
    for key in ("site_url", "vk_url", "map_url", "vk_bot_ready", "vk_bot_hint", "portal_links"):
        assert key in data
    assert "complaints" in data["portal_links"]
