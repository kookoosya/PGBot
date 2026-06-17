"""Owner-only statistics and admin API tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers.db_factories import auth_headers_for, create_issue, create_owner_user, create_user

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_statistics_requires_owner(api_client: AsyncClient, db_session: AsyncSession):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    response = await api_client.get("/api/v1/statistics", headers=auth_headers_for(resident))
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_statistics_owner_sees_issues(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    await create_issue(db_session, resident=resident)

    response = await api_client.get("/api/v1/statistics", headers=auth_headers_for(owner))
    assert response.status_code == 200
    data = response.json()
    assert data["total_issues"] >= 1
    assert "top_categories" in data


@pytest.mark.asyncio
async def test_admin_audit_logs_owner_only(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)

    denied = await api_client.get("/api/v1/admin/audit-logs", headers=auth_headers_for(resident))
    assert denied.status_code == 403

    allowed = await api_client.get("/api/v1/admin/audit-logs", headers=auth_headers_for(owner))
    assert allowed.status_code == 200
    assert isinstance(allowed.json(), list)


@pytest.mark.asyncio
async def test_admin_notifications_list(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    response = await api_client.get("/api/v1/admin/notifications", headers=auth_headers_for(owner))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_event_sources_overview_owner_only(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)

    denied = await api_client.get("/api/v1/admin/events/sources", headers=auth_headers_for(resident))
    assert denied.status_code == 403

    allowed = await api_client.get("/api/v1/admin/events/sources", headers=auth_headers_for(owner))
    assert allowed.status_code == 200
    data = allowed.json()
    assert "sources" in data
    assert "total_published" in data
    ids = {item["id"] for item in data["sources"]}
    assert "pushkinland" in ids
