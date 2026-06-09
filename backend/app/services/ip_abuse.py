"""Простые проверки злоупотреблений по IP (дополнение к slowapi)."""

import re

SUSPICIOUS_URL_RE = re.compile(r"https?://|\.ru/|\.com/|t\.me/|telegram\.me", re.I)


def contains_suspicious_link(*values: str | None) -> bool:
    for val in values:
        if val and SUSPICIOUS_URL_RE.search(val):
            return True
    return False


def sanitize_public_text(text: str, *, max_len: int = 3000) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned
