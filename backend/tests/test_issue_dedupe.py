"""Unit tests for issue duplicate linking business rules."""

from app.config import get_settings
from app.services.issue import should_link_duplicate_issue


def test_should_link_at_threshold():
    threshold = get_settings().DUPLICATE_THRESHOLD
    assert should_link_duplicate_issue(threshold, has_existing=True) is True


def test_should_not_link_below_threshold():
    threshold = get_settings().DUPLICATE_THRESHOLD
    assert should_link_duplicate_issue(threshold - 0.01, has_existing=True) is False


def test_should_not_link_without_existing_issues():
    assert should_link_duplicate_issue(0.99, has_existing=False) is False


def test_duplicate_threshold_default():
    assert get_settings().DUPLICATE_THRESHOLD == 0.80
