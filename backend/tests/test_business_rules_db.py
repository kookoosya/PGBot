"""PostgreSQL tests for cross-cutting business rules (dedupe, validation)."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus, UserRole
from app.schemas.analysis_result import AnalysisResult
from app.services.issue import process_web_complaint
from tests.helpers.db_factories import create_issue, create_user

pytestmark = pytest.mark.postgres

_VALID_ANALYSIS = AnalysisResult(
    is_valid=True,
    category="roads",
    summary="Сломан фонарь на улице Ленина",
    duplicate_probability=0.0,
)


@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_issue_dedupe_links_to_existing_open_issue(
    mock_gemini,
    _notify_owner,
    db_session: AsyncSession,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    existing = await create_issue(
        db_session,
        resident=resident,
        description="Не работает фонарь на улице Ленина",
        status=IssueStatus.UNDER_REVIEW,
    )

    mock_gemini.return_value = AnalysisResult(
        is_valid=True,
        category="roads",
        summary="Тот же фонарь на Ленина",
        duplicate_probability=0.92,
    )

    linked = await process_web_complaint(
        db_session,
        "Снова не горит фонарь на улице Ленина возле дома 5",
        user=resident,
    )

    assert linked.id == existing.id
    assert existing.confirmation_count >= 1


@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_issue_dedupe_creates_new_when_probability_low(
    mock_gemini,
    _notify_owner,
    db_session: AsyncSession,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    await create_issue(
        db_session,
        resident=resident,
        description="Не работает фонарь на улице Ленина",
    )

    mock_gemini.return_value = _VALID_ANALYSIS

    created = await process_web_complaint(
        db_session,
        "Сломанная скамейка у школы номер три",
        user=resident,
    )

    assert created.id is not None
    assert "скамейка" in created.description.lower()
