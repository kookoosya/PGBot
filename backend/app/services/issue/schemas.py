"""Types, DTOs and errors for issue lifecycle service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.utils.errors import ServiceError

_REOPEN_TARGET_STATUSES = frozenset({IssueStatus.NEW, IssueStatus.UNDER_REVIEW})

_STATUS_AUDIT_ACTIONS = frozenset({"status_change", "reopen_issue", "archive_issue"})


@dataclass(frozen=True, slots=True)
class IssueStatusEvent:
    """Single status transition visible to the resident."""

    status: str
    label: str
    at: str
    previous_status: str | None = None
    resolution: str | None = None


@dataclass(frozen=True, slots=True)
class IssueActorContext:
    """Actor performing an issue action (used for audit logging)."""

    actor_id: int
    ip_address: Optional[str] = None


class IssueNotFoundError(ServiceError):
    """Business error when an issue cannot be loaded."""

    def __init__(self, detail: str = "Issue not found") -> None:
        super().__init__(detail, status_code=404)


class IssueValidationError(ServiceError):
    """Business validation failure for issue lifecycle actions."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class IssueAccessDeniedError(ServiceError):
    """Raised when a user cannot view or modify an issue."""

    def __init__(self, detail: str = "Access denied") -> None:
        super().__init__(detail, status_code=403)


@dataclass(frozen=True, slots=True)
class IssueSearchParams:
    """Filters for ``search_issues``."""

    status: Optional[IssueStatus] = None
    category: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class IssueSearchResult:
    """Paginated issue search result."""

    items: list[Issue]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
