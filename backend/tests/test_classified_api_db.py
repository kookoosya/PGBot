"""Classified ads: create via API and moderation lifecycle."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers.db_factories import auth_headers_for, create_owner_user, create_user, unique_phone, unique_username

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_create_classified_via_api(
    _notify_subs,
    _notify_owner,
    api_client: AsyncClient,
):
    payload = {
        "category": "firewood",
        "title": "Дрова берёзовые колотые",
        "description": "Сухие дрова, самовывоз с участка у НКЦ",
        "phone": unique_phone(),
        "author_name": "Сосед",
        "agree_rules": True,
    }
    response = await api_client.post("/api/v1/classifieds", json=payload)
    assert response.status_code == 201
    ad_id = response.json()["id"]
    assert ad_id > 0

    pending = await api_client.get("/api/v1/classifieds", params={"ads_only": "true", "page_size": 50})
    assert pending.status_code == 200
    pending_ids = {item["id"] for item in pending.json()["items"]}
    assert ad_id in pending_ids


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_moderate_classified_approve_via_api(
    _notify_subs,
    _notify_create,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    owner = await create_owner_user(db_session)
    phone = unique_phone()
    create_resp = await api_client.post(
        "/api/v1/classifieds",
        json={
            "category": "handyman",
            "title": f"Покос травы {unique_username('svc')}",
            "description": "Покошу участок, вывезу траву по договорённости",
            "phone": phone,
            "author_name": "Мастер",
            "agree_rules": True,
        },
    )
    assert create_resp.status_code == 201
    ad_id = create_resp.json()["id"]

    approve = await api_client.post(
        f"/api/v1/classifieds/{ad_id}/approve",
        headers=auth_headers_for(owner),
    )
    assert approve.status_code == 200

    listed = await api_client.get(
        "/api/v1/classifieds",
        params={"category": "handyman", "ads_only": "true", "page_size": 50},
    )
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert ad_id in ids


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_moderate_classified_reject_via_api(
    _notify_subs,
    _notify_create,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    owner = await create_owner_user(db_session)
    create_resp = await api_client.post(
        "/api/v1/classifieds",
        json={
            "category": "firewood",
            "title": "Дрова сомнительные",
            "description": "Описание для отклонения модератором",
            "phone": unique_phone(),
            "author_name": "Автор",
            "agree_rules": True,
        },
    )
    ad_id = create_resp.json()["id"]

    reject = await api_client.post(
        f"/api/v1/classifieds/{ad_id}/reject",
        headers=auth_headers_for(owner),
    )
    assert reject.status_code == 200

    listed = await api_client.get(
        "/api/v1/classifieds",
        params={"ads_only": "true", "page_size": 50},
    )
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert ad_id not in ids


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_moderate_classified_requires_owner(
    _notify_subs,
    _notify_create,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    create_resp = await api_client.post(
        "/api/v1/classifieds",
        json={
            "category": "handyman",
            "title": f"Услуга для модерации {unique_username('mod')}",
            "description": "Только владелец может одобрить",
            "phone": unique_phone(),
            "author_name": "Мастер",
            "agree_rules": True,
        },
    )
    assert create_resp.status_code == 201
    ad_id = create_resp.json()["id"]

    forbidden = await api_client.post(
        f"/api/v1/classifieds/{ad_id}/approve",
        headers=auth_headers_for(resident),
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_create_classified_rejects_short_description(api_client: AsyncClient):
    response = await api_client.post(
        "/api/v1/classifieds",
        json={
            "category": "firewood",
            "title": "Дрова",
            "description": "Сухие",
            "phone": unique_phone(),
            "author_name": "Сосед",
            "agree_rules": True,
        },
    )
    assert response.status_code == 400
    assert "коротк" in response.json()["detail"].lower()
