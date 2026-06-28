"""Canonical public site URL — no app imports (avoids circular deps)."""

import os

CANONICAL_SITE_HOST = os.environ.get("CANONICAL_SITE_HOST", "pushkinskie-gory.xyz")
CANONICAL_SITE_URL = f"https://{CANONICAL_SITE_HOST}"
SITE_HOSTS = (
    "pushkinskie-gory.ru",
    "www.pushkinskie-gory.ru",
    "pushkinskie-gory.xyz",
    "www.pushkinskie-gory.xyz",
)