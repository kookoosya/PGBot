"""PostgreSQL integration tests for issue lifecycle."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus, UserRole
from app.services.issue import (
    IssueActorContext,
    add_issue_comment,
    apply_issue_status_update,
    archive_issue,
    reopen_issue,
    require_issue_for_user,
)
from tests.helpers.db_factories import create_issue, create_user

pytestmark = pytest.mark.postgres


@pytest.fixture
async def issue_context(db_session: AsyncSession):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    official = await create_user(
        db_session,
        role_name=UserRole.ADMINISTRATION,
        full_name="Администратор",
    )
    issue = await create_issue(db_session, resident=resident)
    actor = IssueActorContext(actor_id=official.id, ip_address="127.0.0.1")
    return {"resident": resident, "official": official, "issue": issue, "actor": actor}


@pytest.mark.asyncio
@patch("app.services.issue.status.safe_notify_status", new_callable=AsyncMock, return_value=True)
async def test_issue_full_lifecycle(mock_notify, db_session: AsyncSession, issue_context):
    """Create → review → resolve → comment → reopen → archive."""
    issue = issue_context["issue"]
    actor = issue_context["actor"]
    resident = issue_context["resident"]

    await apply_issue_status_update(
        db_session,
        issue,
        status=IssueStatus.UNDER_REVIEW,
        resolution_text=None,
        actor=actor,
    )
    assert issue.status == IssueStatus.UNDER_REVIEW

    await apply_issue_status_update(
        db_session,
        issue,
        status=IssueStatus.RESOLVED,
        resolution_text="Фонарь заменён",
        actor=actor,
    )
    assert issue.status == IssueStatus.RESOLVED
    assert issue.resolution_text == "Фонарь заменён"
    assert issue.resolved_at is not None

    comment = await add_issue_comment(
        db_session,
        issue,
        author=resident,
        text="Спасибо, стало светлее",
        is_internal=False,
    )
    assert comment.text == "Спасибо, стало светлее"

    await reopen_issue(
        db_session,
        issue,
        actor=actor,
        target_status=IssueStatus.UNDER_REVIEW,
    )
    assert issue.status == IssueStatus.UNDER_REVIEW
    assert issue.resolved_at is None

    await archive_issue(db_session, issue, actor=actor)
    assert issue.status == IssueStatus.ARCHIVED
    mock_notify.assert_awaited()


@pytest.mark.asyncio
async def test_resident_can_read_own_issue(db_session: AsyncSession, issue_context):
    loaded = await require_issue_for_user(
        db_session,
        issue_context["issue"].id,
        issue_context["resident"],
    )
    assert loaded.id == issue_context["issue"].id


@pytest.mark.asyncio
async def test_other_resident_cannot_read_issue(db_session: AsyncSession, issue_context):
    from app.services.issue import IssueAccessDeniedError

    stranger = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Чужой")
    with pytest.raises(IssueAccessDeniedError):
        await require_issue_for_user(
            db_session,
            issue_context["issue"].id,
            stranger,
        )
