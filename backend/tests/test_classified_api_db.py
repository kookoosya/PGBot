"""Classified ads: create via API and moderation lifecycle."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.db_factories import auth_headers_for, create_owner_user

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
        "phone": "+79005556677",
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
    assert ad_id not in pending_ids


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
    create_resp = await api_client.post(
        "/api/v1/classifieds",
        json={
            "category": "services",
            "title": "Покос травы аккуратно",
            "description": "Покошу участок, вывезу траву по договорённости",
            "phone": "+79007778899",
            "author_name": "Мастер",
            "agree_rules": True,
        },
    )
    ad_id = create_resp.json()["id"]

    approve = await api_client.post(
        f"/api/v1/classifieds/{ad_id}/approve",
        headers=auth_headers_for(owner),
    )
    assert approve.status_code == 200

    listed = await api_client.get(
        "/api/v1/classifieds",
        params={"category": "services", "ads_only": "true", "page_size": 50},
    )
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert ad_id in ids
