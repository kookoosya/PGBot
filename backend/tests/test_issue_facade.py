"""Smoke tests for issue_service facade after package split."""

import app.services.issue_service as facade
from app.services.issue import access as access_mod
from app.services.issue import comment as comment_mod
from app.services.issue import crud as crud_mod
from app.services.issue import status as status_mod
from app.services.issue import validation as validation_mod


def test_facade_exports_crud_functions():
    assert facade.search_issues is crud_mod.search_issues
    assert facade.require_issue_for_user is crud_mod.require_issue_for_user
    assert facade.get_issue_details is crud_mod.get_issue_details


def test_facade_exports_status_functions():
    assert facade.apply_issue_status_update is status_mod.apply_issue_status_update
    assert facade.reopen_issue is status_mod.reopen_issue
    assert facade.archive_issue is status_mod.archive_issue


def test_facade_exports_comment_and_validation():
    assert facade.add_comment_for_user is comment_mod.add_comment_for_user
    assert facade.create_issue_from_web is validation_mod.create_issue_from_web


def test_facade_exports_access():
    assert facade.can_view_issue is access_mod.can_view_issue


def test_facade_schema_types():
    assert facade.IssueValidationError is not None
    assert facade.IssueActorContext is not None
    assert facade.IssueSearchParams is not None
