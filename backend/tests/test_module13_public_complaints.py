"""Module 13: public web complaints flow."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus, UserRole
from app.schemas.analysis_result import AnalysisResult
from app.schemas.issue import IssueCreate
from app.services.issue import create_issue_from_web, process_web_complaint
from app.services.issue.gemini_analysis import analyze_issue_with_context, run_gemini_with_retry
from app.services.gemini import GeminiAnalysisError
from tests.helpers.db_factories import auth_headers_for, create_user

REPO_ROOT = Path(__file__).resolve().parents[2]

_VALID_TEXT = "Не работает уличное освещение на перекрёстке улиц Ленина и Новоржевской."
_VALID_ANALYSIS = AnalysisResult(
    is_valid=True,
    category="Освещение",
    summary="Не работает освещение",
    duplicate_probability=0.0,
)


def test_module13_audit_exists():
    audit = REPO_ROOT / "docs" / "factual-integrity" / "module-13-public-complaints-flow.md"
    assert audit.is_file()
    text = audit.read_text(encoding="utf-8")
    assert "e856efd" in text
    assert "KEEP_VERIFIED" in text or "FIX_" in text or "CONFIRMED" in text


def test_issue_create_schema_rejects_short_description():
    with pytest.raises(ValueError):
        IssueCreate(description="abc")


@pytest.mark.asyncio
async def test_public_create_issue_validation_returns_422(client: AsyncClient):
    response = await client.post("/api/v1/issues", json={"description": "abc"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_public_create_issue_requires_contact_without_auth(client: AsyncClient):
    response = await client.post(
        "/api/v1/issues",
        json={"description": "Сломан фонарь на улице Ленина возле дома 5"},
    )
    assert response.status_code == 400
    assert "телефон" in response.json()["detail"].lower() or "кабинет" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_public_create_issue_rejects_honeypot(client: AsyncClient):
    response = await client.post(
        "/api/v1/issues",
        json={
            "description": _VALID_TEXT,
            "full_name": "Тест",
            "phone": "+79001112233",
            "website_url": "http://spam.example",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("app.services.issue.gemini_analysis.request_gemini_analysis", new_callable=AsyncMock)
async def test_gemini_failure_uses_rule_fallback(mock_gemini):
    mock_gemini.side_effect = GeminiAnalysisError("service unavailable")
    result = await run_gemini_with_retry(_VALID_TEXT, "")
    assert result.is_valid is True
    assert result.category == "Освещение"


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.gemini_analysis.request_gemini_analysis", new_callable=AsyncMock)
async def test_gemini_false_negative_overridden_by_rule_fallback(
    mock_gemini,
    db_session: AsyncSession,
):
    mock_gemini.return_value = {
        "is_valid": False,
        "category": "other",
        "priority": "medium",
        "summary": "reject",
        "duplicate_probability": 0.0,
    }
    analysis, _ = await analyze_issue_with_context(db_session, _VALID_TEXT)
    assert analysis.is_valid is True
    assert analysis.category == "Освещение"


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.request_gemini_analysis", new_callable=AsyncMock)
async def test_web_complaint_creates_issue_when_gemini_fails(
    mock_gemini,
    _notify_owner,
    db_session: AsyncSession,
):
    mock_gemini.side_effect = GeminiAnalysisError("quota exceeded")
    issue = await process_web_complaint(
        db_session,
        _VALID_TEXT,
        phone="+79001300013",
        full_name="MODULE13 Test",
    )
    assert issue.is_spam is False
    assert issue.status == IssueStatus.NEW
    assert issue.id is not None


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_create_issue_from_web_returns_loaded_issue(
    mock_gemini,
    _notify_owner,
    db_session: AsyncSession,
):
    mock_gemini.return_value = _VALID_ANALYSIS
    issue = await create_issue_from_web(
        db_session,
        IssueCreate(description=_VALID_TEXT, full_name="Житель", phone="+79001112233"),
        user=None,
    )
    assert issue.id is not None
    assert issue.status == IssueStatus.NEW


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_authenticated_issue_visible_in_my_list(
    mock_gemini,
    _notify_owner,
    api_client: AsyncClient,
    db_session: AsyncSession,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель API")
    mock_gemini.return_value = _VALID_ANALYSIS

    response = await api_client.post(
        "/api/v1/issues",
        headers=auth_headers_for(resident),
        json={"description": _VALID_TEXT},
    )
    assert response.status_code == 201
    issue_id = response.json()["id"]
    assert response.json()["status"] == IssueStatus.NEW.value

    mine = await api_client.get("/api/v1/issues/my", headers=auth_headers_for(resident))
    assert mine.status_code == 200
    assert any(item["id"] == issue_id for item in mine.json()["items"])


@pytest.mark.postgres
@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_duplicate_submit_links_when_probability_high(
    mock_gemini,
    _notify_owner,
    db_session: AsyncSession,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    mock_gemini.side_effect = [
        AnalysisResult(is_valid=True, category="Освещение", summary="Фонарь", duplicate_probability=0.0),
        AnalysisResult(is_valid=True, category="Освещение", summary="Фонарь", duplicate_probability=0.95),
    ]
    first = await process_web_complaint(db_session, _VALID_TEXT, user=resident)
    second = await process_web_complaint(
        db_session,
        "Снова не горит фонарь на перекрёстке Ленина и Новоржевской",
        user=resident,
    )
    assert second.id == first.id
    assert first.confirmation_count >= 1
