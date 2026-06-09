"""Интеграционные тесты classifieds API."""

import pytest
from app.models.classified import ClassifiedAd
from app.models.enums import ClassifiedCategory, ClassifiedPaymentStatus
from httpx import AsyncClient

from tests.conftest import API_PREFIX

pytestmark = pytest.mark.asyncio


async def test_create_classified(client: AsyncClient):
    payload = {
        "category": ClassifiedCategory.OTHER.value,
        "title": "Продам дачный инвентарь",
        "description": "Лопаты, грабли, ведра — всё в хорошем состоянии",
        "phone": "+79007654321",
        "author_name": "Пётр",
        "agree_rules": True,
    }
    response = await client.post(f"{API_PREFIX}/classifieds", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["free"] is True


async def test_list_classifieds_includes_approved(client: AsyncClient, db_session):
    ad = ClassifiedAd(
        category=ClassifiedCategory.OTHER,
        title="Тестовое объявление для ленты",
        description="Описание тестового объявления для проверки API",
        phone="+79005556677",
        author_name="Тест",
        is_active=True,
        payment_status=ClassifiedPaymentStatus.APPROVED,
        placement_fee=0,
    )
    db_session.add(ad)
    await db_session.flush()

    response = await client.get(f"{API_PREFIX}/classifieds")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    titles = [item["title"] for item in body["items"]]
    assert ad.title in titles
