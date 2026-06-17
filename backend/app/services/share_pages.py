"""Minimal HTML share landing pages with Open Graph tags for social crawlers."""

from __future__ import annotations

from html import escape

from sqlalchemy.ext.asyncio import AsyncSession

from app.canonical_site import CANONICAL_SITE_URL
from app.config import get_settings
from app.services.event.mappers import event_to_public_response
from app.services.event.public import get_public_event_by_id

GARNECT_SHARE_TITLE = "Бугровский гарнец — Пушкинские Горы"
GARNECT_SHARE_DESCRIPTION = (
    "Программа всероссийского театрального фестиваля в Пушкинских Горах. "
    "Спектакли, расписание и афиша на портале посёлка."
)


def _site_url() -> str:
    return (get_settings().PUBLIC_SITE_URL or CANONICAL_SITE_URL).rstrip("/")


def _event_app_path(event_id: int, *, source: str | None, title: str) -> str:
    path = f"/events/{event_id}"
    if source == "pushkinland" and "гарнец" in title.lower():
        return f"{path}?from=garnect"
    return path


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


async def build_event_share_html(db: AsyncSession, event_id: int) -> str | None:
    event = await get_public_event_by_id(db, event_id)
    if not event:
        return None

    payload = event_to_public_response(event)
    site = _site_url()
    share_url = f"{site}/share/events/{event_id}"
    app_path = _event_app_path(event_id, source=event.source, title=event.title or "")
    app_url = f"{site}{app_path}"
    title = escape(f"{payload['title']} — Пушкинские Горы")
    when = payload.get("starts_at_label") or ""
    where = payload.get("location") or ""
    bits = [bit for bit in (when, where, payload.get("region_label")) if bit]
    description_raw = (event.description or "").strip()
    if not description_raw:
        description_raw = f"{payload['title']}. " + " · ".join(bits)
    description = escape(description_raw[:300])

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
