"""Shared text normalization for event import pipelines."""

from __future__ import annotations

import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = _HTML_TAG_RE.sub(" ", value)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
    return _WS_RE.sub(" ", text).strip()


def normalize_event_text(value: str | None) -> str | None:
    cleaned = strip_html(value)
    return cleaned or None


def first_sentences(text: str, *, max_sentences: int = 2, max_len: int = 240) -> str:
    """Take first N sentences for teaser."""
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    teaser = " ".join(parts[:max_sentences]).strip()
    if len(teaser) > max_len:
        teaser = teaser[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return teaser
