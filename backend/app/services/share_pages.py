"""Minimal HTML share landing pages with Open Graph tags for social crawlers."""

from __future__ import annotations

from html import escape

from app.canonical_site import CANONICAL_SITE_URL
from app.config import get_settings

GARNECT_SHARE_TITLE = "Бугровский гарнец — Пушкинские Горы"
GARNECT_SHARE_DESCRIPTION = (
    "Программа всероссийского театрального фестиваля в Пушкинских Горах. "
    "Спектакли, расписание и афиша на портале посёлка."
)


def _site_url() -> str:
    return (get_settings().PUBLIC_SITE_URL or CANONICAL_SITE_URL).rstrip("/")


def garnect_share_html() -> str:
    site = _site_url()
    share_url = f"{site}/share/festival/garnect"
    app_url = f"{site}/events?festival=garnect"
    title = escape(GARNECT_SHARE_TITLE)
    description = escape(GARNECT_SHARE_DESCRIPTION)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{escape(share_url)}" />
  <meta property="og:locale" content="ru_RU" />
  <link rel="canonical" href="{escape(app_url)}" />
  <meta http-equiv="refresh" content="0;url={escape(app_url)}" />
</head>
<body>
  <p><a href="{escape(app_url)}">{title}</a></p>
</body>
</html>
"""
