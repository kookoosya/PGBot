"""Issue-related domain constants."""

from app.models.enums import IssueCategory

JKH_CATEGORIES = frozenset(
    {IssueCategory.UTILITIES, IssueCategory.WATER, IssueCategory.SEWERAGE}
)
