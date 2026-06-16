"""Gemini analysis with retry for complaint ingest."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.issue import Issue
from app.schemas.analysis_result import AnalysisResult
from app.services.gemini import GeminiAnalysisError, request_gemini_analysis
from app.services.issue_utils import issue_display_summary

from .dedup import find_similar_issues

logger = logging.getLogger(__name__)
settings = get_settings()

_GEMINI_MAX_ATTEMPTS = 2
_GEMINI_RETRY_DELAY_SEC = 0.75
_GEMINI_FAILURE_SUMMARY = (
    "Не удалось проанализировать обращение автоматически. Попробуйте позже."
)


def _is_transient_gemini_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    return type(exc).__name__ in {
        "ServiceUnavailable",
        "DeadlineExceeded",
        "InternalServerError",
        "TooManyRequests",
        "ResourceExhausted",
        "GoogleAPIError",
        "RetryError",
    }


def _gemini_failure_result(exc: Exception) -> AnalysisResult:
    return AnalysisResult(
        is_valid=False,
        summary=_GEMINI_FAILURE_SUMMARY,
        raw_response={"error": str(exc)},
    )


async def run_gemini_with_retry(text: str, context: str) -> AnalysisResult:
    """Call Gemini with one retry on transient failures."""
    last_exc: Exception | None = None
    for attempt in range(1, _GEMINI_MAX_ATTEMPTS + 1):
        try:
            raw = await request_gemini_analysis(text, context)
            return AnalysisResult.from_gemini(raw)
        except GeminiAnalysisError as exc:
            last_exc = exc
            if attempt < _GEMINI_MAX_ATTEMPTS and _is_transient_gemini_error(exc):
                logger.warning(
                    "Gemini analysis attempt %s/%s failed (%s), retrying",
                    attempt,
                    _GEMINI_MAX_ATTEMPTS,
                    exc,
                )
                await asyncio.sleep(_GEMINI_RETRY_DELAY_SEC * attempt)
                continue
            logger.warning("Gemini analysis failed after %s attempt(s): %s", attempt, exc)
            return _gemini_failure_result(exc)
        except Exception as exc:
            logger.warning("Unexpected error during Gemini analysis: %s", exc)
            return _gemini_failure_result(exc)
    return _gemini_failure_result(last_exc or GeminiAnalysisError("unknown"))


async def analyze_issue_with_context(
    db: AsyncSession,
    text: str,
    category: str | None = None,
) -> tuple[AnalysisResult, list[Issue]]:
    """Find similar issues, build context and run Gemini analysis."""
    existing = await find_similar_issues(db, text, category)
    context_lines = [
        f"#{issue.id}: {issue_display_summary(issue)}"
        for issue in existing[:5]
    ]
    analysis = await run_gemini_with_retry(text, "\n".join(context_lines))
    return analysis, existing
