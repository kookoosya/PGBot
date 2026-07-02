"""Verified Pushkin quotes — academic sources only."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
QUOTES_PATH = REPO_ROOT / "shared" / "pushkin_quotes.json"

QUOTE_REQUEST_RE = re.compile(
    r"(цитат|пушкин|стих|пословиц)",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def load_verified_quotes() -> list[dict]:
    with QUOTES_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return list(payload.get("quotes", []))


def format_quote(quote: dict) -> str:
    return (
        f"«{quote['text']}»\n"
        f"— {quote['author']}, «{quote['work']}», {quote['year']}"
    )


def maybe_append_verified_quote(message: str, reply: str) -> str:
    """Append a verified quote only when the user explicitly asks about Pushkin/poetry."""
    if not QUOTE_REQUEST_RE.search(message):
        return reply
    import random

    quote = random.choice(load_verified_quotes())
    return f"{reply}\n\n🪶 {format_quote(quote)}"
