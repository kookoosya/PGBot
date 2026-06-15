"""Shared event title normalization (no heavy imports)."""

from __future__ import annotations

import re

_TITLE_NORMALIZE_RE = re.compile(r"[^\w\s]+", re.UNICODE)


def normalize_event_title(title: str) -> str:
    """Lowercase alphanumeric title for duplicate checks."""
    cleaned = _TITLE_NORMALIZE_RE.sub(" ", title.lower())
    return " ".join(cleaned.split())
