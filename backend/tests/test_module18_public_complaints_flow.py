"""Module 18: public complaints flow acceptance + regression."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus
from app.schemas.analysis_result import AnalysisResult
from app.schemas.issue import IssueCreate
from app.services.issue import create_issue_from_web
from app.services.map_routes import TYRE_ROUTE_NAME, get_map_routes, route_stop_names
from app.services.place import PlaceSearchParams, search_places
from app.services.place_inventory import load_place_inventory
from app.services.pushkin_places_seed import TAXI_SEED, _public_phone, seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DOC = REPO_ROOT / "docs" / "factual-integrity" / "module-18-public-complaints-flow.md"
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
EXPECTED_VERIFIED_PHONE_COUNT = 20


def _village_places() -> list[dict]:
    return [
        p
        for p in load_place_inventory()
        if p.get("decision") in {"KEEP", "RESTORE"}
        and p.get("active_status") != "CLOSED_CONFIRMED"
        and p.get("seed_as_reference", True)
        and p.get("scope") == "VILLAGE"
    ]


def test_module18_audit_doc_exists():
    assert AUDIT_DOC.is_file()
    text = AUDIT_DOC.read_text(encoding="utf-8")
    assert "268613b" in text
    assert "Complaints.tsx" in text or "complaints" in text


def test_module18_issue_create_schema_min_length():
    with pytest.raises(ValueError):
        IssueCreate(description="abc")


@pytest.mark.asyncio
async def test_module18_public_create_empty_description_422(client: AsyncClient):
    response = await client.post("/api/v1/issues", json={"description": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_module18_public_create_short_description_422(client: AsyncClient):
    response = await client.post("/api/v1/issues", json={"description": "abc"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_module18_public_create_requires_guest_contact(client: AsyncClient):
    response = await client.post(
        "/api/v1/issues",
        json={"description": MODULE18_TEST_TEXT},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_module18_public_create_rejects_honeypot(client: AsyncClient):
    response = await client.post(
        "/api/v1/issues",
        json={
            "description": MODULE18_TEST_TEXT,
            "full_name": "Module18 Test",
            "phone": "+79001300018",
            "website_url": "http://spam.example",
        },
    )
    assert response.status_code == 400


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_module18_valid_guest_complaint_returns_new_status(
    mock_gemini,
    _notify_owner,
    db_session: AsyncSession,
):
    mock_gemini.return_value = _VALID_ANALYSIS
    issue = await create_issue_from_web(
        db_session,
        IssueCreate(
            description=MODULE18_TEST_TEXT,
            full_name="Module18 Test",
            phone="+79001300018",
        ),
        user=None,
    )
    assert issue.id is not None
    assert issue.status == IssueStatus.NEW
    assert issue.is_spam is False


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_module18_api_create_returns_id_and_status(
    mock_gemini,
    _notify_owner,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    mock_gemini.return_value = _VALID_ANALYSIS
    response = await api_client.post(
        "/api/v1/issues",
        json={
            "description": MODULE18_TEST_TEXT,
            "full_name": "Module18 Test",
            "phone": "+79001300018",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] is not None
    assert body["status"] == IssueStatus.NEW.value


def test_module18_catalog_and_routes_unchanged():
    assert len(_village_places()) == EXPECTED_VILLAGE_COUNT
    assert len(get_map_routes()) == 11
    assert TYRE_ROUTE_NAME not in route_stop_names()


def test_module18_verified_phones_unchanged():
    verified = [p for p in _village_places() if _public_phone(p)]
    assert len(verified) == EXPECTED_VERIFIED_PHONE_COUNT


def test_module18_taxi_seed_still_empty():
    assert TAXI_SEED == []


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_module18_kdc_and_stolovaya_searchable(db_session: AsyncSession):
    await seed_village_places(db_session)
    kdc = await search_places(db_session, PlaceSearchParams(search="КДЦ", scope="VILLAGE"))
    stolovaya = await search_places(
        db_session, PlaceSearchParams(search="столовая", scope="VILLAGE")
    )
    assert kdc.total >= 1
    assert stolovaya.total >= 1
