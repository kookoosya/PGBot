"""Issue status lifecycle via HTTP API."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from tests.helpers.db_factories import auth_headers_for, create_issue, create_user

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
@patch("app.services.issue.status.safe_notify_status", new_callable=AsyncMock, return_value=True)
async def test_issue_reopen_and_archive_via_http(
    _notify,
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION, full_name="Служба")
    issue = await create_issue(db_session, resident=resident)

    resolved = await api_client.patch(
        f"/api/v1/issues/{issue.id}/status",
        headers=auth_headers_for(official),
        json={"status": "resolved", "resolution_text": "Проблема устранена"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    reopened = await api_client.patch(
        f"/api/v1/issues/{issue.id}/reopen",
        headers=auth_headers_for(official),
        json={"target_status": "under_review"},
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "under_review"
    assert reopened.json()["resolved_at"] is None

    archived = await api_client.patch(
        f"/api/v1/issues/{issue.id}/archive",
        headers=auth_headers_for(official),
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_resident_cannot_update_issue_status(
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    issue = await create_issue(db_session, resident=resident)

    response = await api_client.patch(
        f"/api/v1/issues/{issue.id}/status",
        headers=auth_headers_for(resident),
        json={"status": "resolved", "resolution_text": "Сам решил"},
    )
    assert response.status_code == 403
