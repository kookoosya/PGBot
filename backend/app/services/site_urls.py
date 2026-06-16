from app.config import get_settings
from app.canonical_site import CANONICAL_SITE_URL


def public_site_url() -> str:
    """Canonical public site base URL without trailing slash."""
    url = get_settings().PUBLIC_SITE_URL.rstrip("/")
    if not url:
        return CANONICAL_SITE_URL
    return url
