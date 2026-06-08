import logging
from dataclasses import dataclass, field
from typing import Any

from app.models.enums import Priority

logger = logging.getLogger(__name__)


def _coerce_bool(value: Any, *, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "1", "yes", "да"):
            return True
        if normalized in ("false", "0", "no", "нет"):
            return False
    return default


def _coerce_probability(value: Any) -> float:
    try:
        prob = float(value if value is not None else 0.0)
    except (TypeError, ValueError):
        logger.warning("Invalid duplicate_probability from Gemini: %r", value)
        return 0.0
    return max(0.0, min(1.0, prob))


def _coerce_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value).strip() or None


@dataclass(slots=True, frozen=True)
class AnalysisResult:
    """Structured result of Gemini issue analysis."""

    is_valid: bool = True
    category: str | None = None
    priority: str | None = None
    summary: str | None = None
    duplicate_probability: float = 0.0
    suggested_department: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_gemini(cls, data: Any) -> "AnalysisResult":
        """Parse Gemini JSON into a normalized, typed result."""
        if not isinstance(data, dict):
            logger.warning("Gemini analysis is not a dict: %r", type(data))
            return cls(is_valid=False, raw_response={})

        try:
            return cls(
                is_valid=_coerce_bool(data.get("is_valid"), default=True),
                category=_coerce_optional_str(data.get("category")),
                priority=_coerce_optional_str(data.get("priority")),
                summary=_coerce_optional_str(data.get("summary")),
                duplicate_probability=_coerce_probability(data.get("duplicate_probability")),
                suggested_department=_coerce_optional_str(data.get("suggested_department")),
                raw_response=data,
            )
        except Exception as exc:
            logger.warning("Failed to parse Gemini analysis: %s", exc)
            return cls(is_valid=False, raw_response=data)

    @property
    def resolved_priority(self) -> str:
        return self.priority or Priority.MEDIUM.value

    def summary_or(self, fallback: str) -> str:
        return self.summary or fallback
