"""Anonymous visitor fingerprinting for visits and feedback."""

from __future__ import annotations

import hashlib


def visitor_key(ip: str, user_agent: str | None) -> str:
    """Return a stable short hash for deduplicating anonymous visitors."""
    raw = f"{ip}|{(user_agent or '')[:120]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
