"""Module 19: admin/official complaint moderation flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus, UserRole
from app.schemas.analysis_result import AnalysisResult
from app.schemas.issue import IssueCreate
from app.services.issue import create_issue_from_web
from app.services.map_routes import TYRE_ROUTE_NAME, get_map_routes, route_stop_names
from app.services.place import PlaceSearchParams, search_places
from app.services.place_inventory import load_place_inventory
from app.services.pushkin_places_seed import TAXI_SEED, _public_phone, seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DOC = REPO_ROOT / "docs" / "factual-integrity" / "module-19-admin-complaints-flow.md"
MODULE18_TEST_TEXT = (
    "MODULE 18 TEST — просьба не обрабатывать, проверка формы обращения."
)
_VALID_ANALYSIS = AnalysisResult(
    is_valid=True,
    category="other",
    summary="MODULE 18 test",
    duplicate_probability=0.0,
)
EXPECTED_VILLAGE_COUNT = 45


def _village_places() -> list[dict]:
    return [
        p
        for p in load_place_inventory()
        if p.get("decision") in {"KEEP", "RESTORE"}
        and p.get("active_status") != "CLOSED_CONFIRMED"
        and p.get("seed_as_reference", True)
        and p.get("scope") == "VILLAGE"
    ]


def test_module19_audit_doc_exists():
    assert AUDIT_DOC.is_file()
    text = AUDIT_DOC.read_text(encoding="utf-8")
    assert "48384d9" in text
    assert "IssuesWorkbench" in text or "admin" in text


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_module19_guest_issue_visible_to_official_list(
    mock_gemini,
    _notify_owner,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    from tests.helpers.db_factories import auth_headers_for, create_user

    mock_gemini.return_value = _VALID_ANALYSIS
    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION, full_name="Служба")
    created = await api_client.post(
        "/api/v1/issues",
        json={
            "description": MODULE18_TEST_TEXT,
            "full_name": "Module18 Test",
            "phone": "+79001300018",
        },
    )
    assert created.status_code == 201
    issue_id = created.json()["id"]

    listing = await api_client.get(
        "/api/v1/issues",
        headers=auth_headers_for(official),
        params={"search": "MODULE 18"},
    )
    assert listing.status_code == 200
    ids = [item["id"] for item in listing.json()["items"]]
    assert issue_id in ids


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_module19_official_detail_and_status_update(
    mock_gemini,
    _notify_owner,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    from tests.helpers.db_factories import auth_headers_for, create_user

    mock_gemini.return_value = _VALID_ANALYSIS
    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION, full_name="Служба")
    created = await create_issue_from_web(
        db_session,
        IssueCreate(
            description=MODULE18_TEST_TEXT,
            full_name="Module18 Test",
            phone="+79001300018",
        ),
        user=None,
    )

    detail = await api_client.get(
        f"/api/v1/issues/{created.id}",
        headers=auth_headers_for(official),
    )
    assert detail.status_code == 200
    assert detail.json()["description"] == MODULE18_TEST_TEXT
    assert detail.json()["status"] == IssueStatus.NEW.value

    updated = await api_client.patch(
        f"/api/v1/issues/{created.id}/status",
        headers=auth_headers_for(official),
        json={
            "status": "RESOLVED",
            "resolution_text": "MODULE 19: тестовое обращение закрыто.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == IssueStatus.RESOLVED.value
    assert "MODULE 19" in (updated.json()["resolution_text"] or "")


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.status.safe_notify_status", new_callable=AsyncMock, return_value=True)
async def test_module19_archive_guest_issue(
    _notify,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    from tests.helpers.db_factories import auth_headers_for, create_issue, create_user

    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION)
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    issue = await create_issue(
        db_session,
        resident=resident,
        description=MODULE18_TEST_TEXT,
    )

    resolved = await api_client.patch(
        f"/api/v1/issues/{issue.id}/status",
        headers=auth_headers_for(official),
        json={"status": "RESOLVED", "resolution_text": "MODULE 19 archive test"},
    )
    assert resolved.status_code == 200

    archived = await api_client.patch(
        f"/api/v1/issues/{issue.id}/archive",
        headers=auth_headers_for(official),
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == IssueStatus.ARCHIVED.value


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module19_missing_issue_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    from tests.helpers.db_factories import auth_headers_for, create_user

    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION)
    response = await api_client.get(
        "/api/v1/issues/999999",
        headers=auth_headers_for(official),
    )
    assert response.status_code == 404


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module19_resident_cannot_update_status(
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    from tests.helpers.db_factories import auth_headers_for, create_issue, create_user

    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    issue = await create_issue(db_session, resident=resident)
    response = await api_client.patch(
        f"/api/v1/issues/{issue.id}/status",
        headers=auth_headers_for(resident),
        json={"status": "RESOLVED", "resolution_text": "Сам"},
    )
    assert response.status_code == 403


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_module19_public_create_still_works_after_admin_flow(
    mock_gemini,
    _notify_owner,
    api_client: AsyncClient,
):
    mock_gemini.return_value = _VALID_ANALYSIS
    response = await api_client.post(
        "/api/v1/issues",
        json={
            "description": "MODULE 19 TEST — проверка public flow после admin.",
            "full_name": "Module19 Test",
            "phone": "+79001300019",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == IssueStatus.NEW.value


def test_module19_regression_catalog_routes_taxi():
    assert len(_village_places()) == EXPECTED_VILLAGE_COUNT
    assert len(get_map_routes()) == 11
    assert TYRE_ROUTE_NAME not in route_stop_names()
    assert TAXI_SEED == []


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module19_kdc_and_stolovaya_searchable(db_session: AsyncSession):
    await seed_village_places(db_session)
    kdc = await search_places(db_session, PlaceSearchParams(search="КДЦ", scope="VILLAGE"))
    stolovaya = await search_places(
        db_session, PlaceSearchParams(search="столовая", scope="VILLAGE")
    )
    assert kdc.total >= 1
    assert stolovaya.total >= 1
