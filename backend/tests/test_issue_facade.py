"""Smoke tests for issue package public exports."""

import app.services.issue as pkg
from app.services.issue import access as access_mod
from app.services.issue import comment as comment_mod
from app.services.issue import crud as crud_mod
from app.services.issue import status as status_mod
from app.services.issue import validation as validation_mod


def test_package_exports_crud_functions():
    assert pkg.search_issues is crud_mod.search_issues
    assert pkg.require_issue_for_user is crud_mod.require_issue_for_user
    assert pkg.get_issue_details is crud_mod.get_issue_details


def test_package_exports_status_functions():
    assert pkg.apply_issue_status_update is status_mod.apply_issue_status_update
    assert pkg.reopen_issue is status_mod.reopen_issue
    assert pkg.archive_issue is status_mod.archive_issue


def test_package_exports_comment_and_validation():
    assert pkg.add_comment_for_user is comment_mod.add_comment_for_user
    assert pkg.create_issue_from_web is validation_mod.create_issue_from_web


def test_package_exports_access():
    assert pkg.can_view_issue is access_mod.can_view_issue


def test_package_schema_types():
    assert pkg.IssueValidationError is not None
    assert pkg.IssueActorContext is not None
    assert pkg.IssueSearchParams is not None
