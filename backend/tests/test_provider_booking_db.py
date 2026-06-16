"""Service provider registration, approval, and booking."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers.db_factories import auth_headers_for, create_owner_user, unique_username

pytestmark = pytest.mark.postgres

_PROVIDER_REGISTER = {
    "full_name": "Мария Стилист",
    "phone": "+79001234567",
    "password": "Testpass1234",
    "bio": "Стрижки и укладки",
    "address": "рп. Пушкинские Горы",
    "services": [
        {
            "service_type": "haircut",
            "name": "Женская стрижка",
            "duration_minutes": 60,
            "price": 1200,
        }
    ],
    "schedule": [
        {"day_of_week": day, "start_time": "09:00", "end_time": "18:00", "is_working": True}
        for day in range(7)
    ],
}


def _next_booking_date() -> date:
    """Pick a date within the next week that is not in the past."""
    return date.today() + timedelta(days=1)


@pytest.mark.asyncio
@patch("app.services.notifications.notify_owner", new_callable=AsyncMock)
async def test_provider_register_and_approve(
    _notify,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    owner = await create_owner_user(db_session)
    username = unique_username("master")
    payload = {**_PROVIDER_REGISTER, "username": username}

    reg = await api_client.post("/api/v1/services/register", json=payload)
    assert reg.status_code == 201
    provider_id = reg.json()["id"]

    pending = await api_client.get(
        "/api/v1/services/providers/pending/list",
        headers=auth_headers_for(owner),
    )
    assert pending.status_code == 200
    assert any(item["id"] == provider_id for item in pending.json())

    approve = await api_client.post(
        f"/api/v1/services/providers/{provider_id}/approve",
        headers=auth_headers_for(owner),
    )
    assert approve.status_code == 200

    catalog = await api_client.get("/api/v1/services/providers")
    assert catalog.status_code == 200
    assert any(item["id"] == provider_id for item in catalog.json())


@pytest.mark.asyncio
@patch("app.services.notifications.notify_owner", new_callable=AsyncMock)
@patch("app.services.notifications.notify_vk_user", new_callable=AsyncMock)
async def test_provider_booking_flow(
    _notify_vk,
    _notify_owner,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    owner = await create_owner_user(db_session)
    username = unique_username("book")
    reg = await api_client.post(
        "/api/v1/services/register",
        json={**_PROVIDER_REGISTER, "username": username},
    )
    provider_id = reg.json()["id"]
    await api_client.post(
        f"/api/v1/services/providers/{provider_id}/approve",
        headers=auth_headers_for(owner),
    )

    detail = await api_client.get(f"/api/v1/services/providers/{provider_id}")
    assert detail.status_code == 200
    service_id = detail.json()["services"][0]["id"]

    booking_date = _next_booking_date()
    slots_resp = await api_client.get(
        f"/api/v1/services/providers/{provider_id}/slots",
        params={"appointment_date": booking_date.isoformat(), "service_id": service_id},
    )
    assert slots_resp.status_code == 200
    slots = slots_resp.json()["slots"]
    available = next((s for s in slots if s["available"]), None)
    assert available is not None, "Expected at least one available slot"

    book = await api_client.post(
        f"/api/v1/services/providers/{provider_id}/book",
        json={
            "service_id": service_id,
            "appointment_date": booking_date.isoformat(),
            "start_time": available["time"],
            "client_name": "Анна Клиент",
            "client_phone": "+79009998877",
        },
    )
    assert book.status_code == 201
    body = book.json()
    assert body["client_name"] == "Анна Клиент"
    assert body["service_name"] == "Женская стрижка"
