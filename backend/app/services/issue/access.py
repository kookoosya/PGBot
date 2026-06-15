"""Issue visibility and query access filters."""

from __future__ import annotations

from sqlalchemy import or_

from app.constants.issue_config import JKH_CATEGORIES
from app.core.deps import is_official_user, is_owner_user
from app.models.enums import OFFICIAL_ROLES, UserRole
from app.models.issue import Issue
from app.models.user import User

from .schemas import IssueValidationError


def _official_category_filter(user: User):
    if user.role.name == UserRole.SOCIAL_SERVICE:
        conditions = [Issue.category.in_(JKH_CATEGORIES)]
        if user.department_id:
            conditions.append(Issue.department_id == user.department_id)
        return or_(*conditions)
    return None


def can_view_issue(user: User, issue: Issue) -> bool:
    """Return whether ``user`` may read or comment on ``issue``."""
    if user.role.name == UserRole.RESIDENT:
        return issue.resident_id == user.id
    if is_owner_user(user):
        return True
    if is_official_user(user):
        if user.role.name == UserRole.SOCIAL_SERVICE:
            return (
                issue.category in JKH_CATEGORIES
                or (user.department_id and issue.department_id == user.department_id)
            )
        return True
    return False


def apply_issue_access_filter(query, user: User):
    """Restrict an issue query to rows visible to ``user``."""
    if user.role.name == UserRole.RESIDENT:
        return query.where(Issue.resident_id == user.id)
    if user.role.name in OFFICIAL_ROLES or user.role.name == UserRole.MODERATOR:
        cat_filter = _official_category_filter(user)
        if cat_filter is not None:
            return query.where(cat_filter)
        return query
    raise IssueValidationError("Недостаточно прав", status_code=403)
