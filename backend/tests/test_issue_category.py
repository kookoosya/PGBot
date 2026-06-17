"""Issue category normalization from AI slugs."""

from app.models.enums import IssueCategory
from app.services.issue.category import normalize_issue_category


def test_normalize_issue_category_from_slug():
    assert normalize_issue_category("roads") == IssueCategory.ROADS.value


def test_normalize_issue_category_from_russian_value():
    assert normalize_issue_category("Дороги") == IssueCategory.ROADS.value


def test_normalize_issue_category_unknown():
    assert normalize_issue_category("totally_unknown") == IssueCategory.OTHER.value
