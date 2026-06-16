"""Incoming complaint processing — thin facade over ``app.services.issue`` ingest modules.

Lifecycle updates on existing issues live in ``issue_service``.
"""

from app.services.issue.dedup import find_similar_issues, should_link_duplicate_issue
from app.services.issue.gemini_analysis import run_gemini_with_retry
from app.services.issue.ingest import (
    find_department_by_name,
    process_incoming_message,
    process_web_complaint,
)
from app.services.issue.residents import get_or_create_resident, get_or_create_web_resident
from app.services.notifications import notify_owner

# Backward-compatible alias for tests that patch the old private name.
_run_gemini_with_retry = run_gemini_with_retry

__all__ = [
    "_run_gemini_with_retry",
    "find_department_by_name",
    "find_similar_issues",
    "get_or_create_resident",
    "get_or_create_web_resident",
    "notify_owner",
    "process_incoming_message",
    "process_web_complaint",
    "run_gemini_with_retry",
    "should_link_duplicate_issue",
]
