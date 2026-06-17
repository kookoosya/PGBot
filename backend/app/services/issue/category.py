"""Normalize issue category values from AI / forms."""

from __future__ import annotations

from app.models.enums import IssueCategory


def normalize_issue_category(raw: str | None) -> str | None:
    """Map Gemini slugs (``roads``) and enum names to ``IssueCategory`` values."""
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    for cat in IssueCategory:
        if text == cat.value or text.lower() == cat.name.lower():
            return cat.value
    return IssueCategory.OTHER.value
