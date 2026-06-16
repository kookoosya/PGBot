"""Smoke tests for split ``app.models.enums`` package."""

from app.models.enums import (
    CLASSIFIED_LABELS,
    EVENT_REGION_LABELS,
    JOB_CLASSIFIED_CATEGORIES,
    OFFICIAL_ROLES,
    ClassifiedCategory,
    EventRegion,
    IssueStatus,
    UserRole,
)


def test_user_roles_and_official_set():
    assert UserRole.RESIDENT.value == "resident"
    assert UserRole.MODERATOR in OFFICIAL_ROLES
    assert UserRole.RESIDENT not in OFFICIAL_ROLES


def test_classified_job_categories_subset():
    assert ClassifiedCategory.JOB_TOURISM in JOB_CLASSIFIED_CATEGORIES
    assert ClassifiedCategory.FIREWOOD not in JOB_CLASSIFIED_CATEGORIES
    assert CLASSIFIED_LABELS[ClassifiedCategory.JOB_TOURISM]


def test_issue_and_event_enums():
    assert IssueStatus.NEW.value == "NEW"
    assert EVENT_REGION_LABELS[EventRegion.PUSHKIN_GORY]
