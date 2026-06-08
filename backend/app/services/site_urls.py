from app.config import get_settings


def public_site_url() -> str:
    """Canonical public site base URL without trailing slash."""
    return get_settings().PUBLIC_SITE_URL.rstrip("/")
