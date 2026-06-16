"""Feedback and visits API tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers.db_factories import auth_headers_for, create_owner_user, create_user

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_submit_feedback(client: AsyncClient):
    response = await client.post(
        "/api/v1/feedback",
        json={
            "message": "Предложение: добавить расписание автобуса на главную",
            "contact": "resident@example.com",
            "page": "/wishes",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "new"
    assert "автобуса" in data["message"]


@pytest.mark.asyncio
async def test_list_feedback_owner_only(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)

    denied = await api_client.get("/api/v1/feedback", headers=auth_headers_for(resident))
    assert denied.status_code == 403

    allowed = await api_client.get("/api/v1/feedback", headers=auth_headers_for(owner))
    assert allowed.status_code == 200
    body = allowed.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_track_visit(client: AsyncClient):
    response = await client.post("/api/v1/visits/track", json={"path": "/map"})
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_visit_stats_owner(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    await api_client.post("/api/v1/visits/track", json={"path": "/events"})

    response = await api_client.get("/api/v1/visits/stats", headers=auth_headers_for(owner))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0
    assert "top_pages" in data
