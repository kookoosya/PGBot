"""Issue lifecycle and ingest service package."""

from .dedup import find_similar_issues, handle_deduplication, should_link_duplicate_issue
from .gemini_analysis import analyze_issue_with_context, run_gemini_with_retry
from .ingest import process_incoming_message, process_web_complaint
from .residents import get_or_create_resident, get_or_create_web_resident

__all__ = [
    "analyze_issue_with_context",
    "find_similar_issues",
    "get_or_create_resident",
    "get_or_create_web_resident",
    "handle_deduplication",
    "process_incoming_message",
    "process_web_complaint",
    "run_gemini_with_retry",
    "should_link_duplicate_issue",
]
