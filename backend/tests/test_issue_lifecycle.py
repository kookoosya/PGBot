"""Unit tests for issue lifecycle business rules (no database)."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue
from app.services.issue.access import can_view_issue
from app.services.issue.schemas import IssueActorContext, IssueValidationError
from app.services.issue.status import change_issue_status, reopen_issue
from app.services.issue.validation import create_issue_from_web


def _user(role_name: UserRole, *, user_id: int = 1, department_id: int | None = None):
    role = SimpleNamespace(name=role_name)
    return SimpleNamespace(id=user_id, role=role, department_id=department_id)


def _issue(*, resident_id: int = 10, category: str = "roads", department_id: int | None = None):
    issue = Issue(
        description="Сломан фонарь на улице",
        status=IssueStatus.NEW,
        resident_id=resident_id,
        department_id=department_id,
    )
    issue.id = 42
    issue.category = category
    issue.created_at = datetime.now(timezone.utc)
    return issue


def test_resident_can_view_own_issue():
    user = _user(UserRole.RESIDENT, user_id=10)
    issue = _issue(resident_id=10)
    assert can_view_issue(user, issue) is True


def test_resident_cannot_view_others_issue():
    user = _user(UserRole.RESIDENT, user_id=1)
    issue = _issue(resident_id=99)
    assert can_view_issue(user, issue) is False


def test_super_admin_owner_can_view_any_issue():
    user = _user(UserRole.SUPER_ADMIN)
    issue = _issue(resident_id=99)
    with patch("app.services.issue.access.is_owner_user", return_value=True):
        assert can_view_issue(user, issue) is True


@pytest.mark.asyncio
async def test_reopen_rejects_invalid_target_status():
    db = AsyncMock()
    issue = _issue()
    issue.status = IssueStatus.RESOLVED
    actor = IssueActorContext(actor_id=1)

    with pytest.raises(IssueValidationError, match="target_status must be NEW or UNDER_REVIEW"):
        await reopen_issue(db, issue, actor=actor, target_status=IssueStatus.RESOLVED)


@pytest.mark.asyncio
@patch("app.services.issue.status.safe_notify_status", new_callable=AsyncMock, return_value=True)
@patch("app.services.issue.status.safe_audit", new_callable=AsyncMock, return_value=True)
async def test_status_change_skips_when_unchanged(mock_audit, mock_notify):
    db = AsyncMock()
    issue = _issue()
    issue.status = IssueStatus.UNDER_REVIEW
    actor = IssueActorContext(actor_id=1)

    result = await change_issue_status(
        db,
        issue,
        status=IssueStatus.UNDER_REVIEW,
        actor=actor,
        audit_action="status_change",
    )

    assert result is issue
    mock_audit.assert_not_awaited()
    mock_notify.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_issue_from_web_rejects_honeypot():
    db = AsyncMock()
    data = SimpleNamespace(
        website_url="http://spam.example",
        phone=None,
        full_name=None,
        description="Сломан фонарь на улице",
        category=None,
        address=None,
    )

    with pytest.raises(IssueValidationError, match="Обновите страницу"):
        await create_issue_from_web(db, data, user=None)


@pytest.mark.asyncio
async def test_create_issue_from_web_guest_requires_contact():
    db = AsyncMock()
    data = SimpleNamespace(
        website_url=None,
        phone=None,
        full_name=None,
        description="Сломан фонарь на улице",
        category=None,
        address=None,
    )

    with pytest.raises(IssueValidationError, match="имя и телефон"):
        await create_issue_from_web(db, data, user=None)


@pytest.mark.asyncio
@patch("app.services.issue_processor.process_web_complaint", new_callable=AsyncMock)
async def test_create_issue_from_web_rejects_spam(mock_process):
    db = AsyncMock()
    spam_issue = MagicMock()
    spam_issue.is_spam = True
    spam_issue.id = 7
    mock_process.return_value = spam_issue

    data = SimpleNamespace(
        website_url=None,
        phone="+79001234567",
        full_name="Иван",
        description="Сломан фонарь на улице",
        category=None,
        address=None,
    )

    with pytest.raises(IssueValidationError, match="не принято"):
        await create_issue_from_web(db, data, user=None)
