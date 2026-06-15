"""Issue lifecycle operations — thin facade over ``app.services.issue`` package.

Creation and AI analysis live in ``issue_processor``.

Public API is unchanged; implementation lives in submodules.
"""

from app.services.issue.access import can_view_issue
from app.services.issue.comment import add_comment_for_user, add_issue_comment
from app.services.issue.crud import (
    get_issue_details,
    get_issue_status_timeline,
    get_issues_for_user,
    get_status_timelines_for_issues,
    require_issue_for_user,
    search_issues,
    update_issue_fields,
)
from app.services.issue.responses import (
    build_issue_actor,
    build_issue_list_response,
    build_my_issues_response,
    issue_to_my_response,
    issue_to_response,
)
from app.services.issue.schemas import (
    IssueAccessDeniedError,
    IssueActorContext,
    IssueNotFoundError,
    IssueSearchParams,
    IssueSearchResult,
    IssueStatusEvent,
    IssueValidationError,
)
from app.services.issue.status import (
    apply_issue_status_update,
    archive_issue,
    assign_issue,
    reopen_issue,
    resolve_issue,
    update_issue_status,
)
from app.services.issue.validation import create_issue_from_web

__all__ = [
    "IssueAccessDeniedError",
    "IssueActorContext",
    "IssueNotFoundError",
    "IssueSearchParams",
    "IssueSearchResult",
    "IssueStatusEvent",
    "IssueValidationError",
    "add_comment_for_user",
    "add_issue_comment",
    "apply_issue_status_update",
    "archive_issue",
    "assign_issue",
    "build_issue_actor",
    "build_issue_list_response",
    "build_my_issues_response",
    "can_view_issue",
    "create_issue_from_web",
    "get_issue_details",
    "get_issue_status_timeline",
    "get_issues_for_user",
    "get_status_timelines_for_issues",
    "issue_to_my_response",
    "issue_to_response",
    "reopen_issue",
    "require_issue_for_user",
    "resolve_issue",
    "search_issues",
    "update_issue_fields",
    "update_issue_status",
]
