"""Shared pagination helpers for search services."""

from __future__ import annotations


def normalize_pagination(
    *,
    page: int,
    page_size: int,
    total: int,
    offset: int | None = None,
    max_page_size: int = 100,
) -> tuple[int, int, int, int, bool, bool]:
    """Return clamped page, offset, page_size, total_pages, has_prev, has_next."""
    safe_page_size = max(1, min(page_size, max_page_size))
    total_pages = max(1, (total + safe_page_size - 1) // safe_page_size) if total else 1
    if offset is not None:
        safe_offset = max(0, offset)
        safe_page = safe_offset // safe_page_size + 1
    else:
        safe_page = max(1, min(page, total_pages))
        safe_offset = (safe_page - 1) * safe_page_size
    has_prev = safe_offset > 0
    has_next = safe_offset + safe_page_size < total
    return safe_page, safe_offset, safe_page_size, total_pages, has_prev, has_next
