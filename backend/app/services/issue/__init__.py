"""Issue lifecycle and ingest service package."""

from .access import can_view_issue
from .comment import add_comment_for_user, add_issue_comment
from .crud import (
    get_issue_details,
    get_issue_status_timeline,
    get_issues_for_user,
    get_status_timelines_for_issues,
    require_issue_for_user,
    search_issues,
    update_issue_fields,
)
from .dedup import find_similar_issues, handle_deduplication, should_link_duplicate_issue
from .gemini_analysis import analyze_issue_with_context, run_gemini_with_retry
from .ingest import process_incoming_message, process_web_complaint
from .residents import get_or_create_resident, get_or_create_web_resident
from .responses import (
    build_issue_actor,
    build_issue_list_response,
    build_my_issues_response,
    issue_to_my_response,
    issue_to_response,
)
from .schemas import (
    IssueAccessDeniedError,
    IssueActorContext,
    IssueNotFoundError,
    IssueSearchParams,
    IssueSearchResult,
    IssueStatusEvent,
    IssueValidationError,
)
from .status import (
    apply_issue_status_update,
    archive_issue,
    assign_issue,
    reopen_issue,
    resolve_issue,
    update_issue_status,
)
from .validation import create_issue_from_web

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
    "analyze_issue_with_context",
    "apply_issue_status_update",
    "archive_issue",
    "assign_issue",
    "build_issue_actor",
    "build_issue_list_response",
    "build_my_issues_response",
    "can_view_issue",
    "create_issue_from_web",
    "find_similar_issues",
    "get_issue_details",
    "get_issue_status_timeline",
    "get_issues_for_user",
    "get_or_create_resident",
    "get_or_create_web_resident",
    "get_status_timelines_for_issues",
    "handle_deduplication",
    "issue_to_my_response",
    "issue_to_response",
    "process_incoming_message",
    "process_web_complaint",
    "reopen_issue",
    "require_issue_for_user",
    "resolve_issue",
    "run_gemini_with_retry",
    "search_issues",
    "should_link_duplicate_issue",
    "update_issue_fields",
    "update_issue_status",
]
