"""Film poster resolution — Kinopoisk Unofficial API and VK attachments."""

from __future__ import annotations

import logging
import re

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_KINOPOISK_BASE = "https://kinopoiskapiunofficial.tech"
_POSTER_CACHE: dict[str, str | None] = {}
_TITLE_CLEAN_RE = re.compile(
    r"\s*(?:\d{1,2}[:.]\d{2}|3d|2d|imax|4dx|сеанс|билет).*$",
    re.IGNORECASE,
)
_QUOTED_TITLE_RE = re.compile(r"[«\"“]([^»\"”]+)[»\"”]")
_PREFIXES = (
    "полнокупольная программа",
    "полнокупольный фильм",
    "полнокупольный",
    "киносеанс",
    "кинопоказ",
    "премьера",
    "фильм",
)


def _clean_film_title(title: str) -> str:
    cleaned = (title or "").strip()
    quoted = _QUOTED_TITLE_RE.search(cleaned)
    if quoted:
        return quoted.group(1).strip()[:200]
    lower = cleaned.lower()
    for prefix in _PREFIXES:
        if lower.startswith(prefix):
            cleaned = cleaned[len(prefix) :].lstrip(" :«\"—-")
            lower = cleaned.lower()
    cleaned = _TITLE_CLEAN_RE.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -–—,.«»\"")
    return cleaned[:200]


def extract_vk_poster_url(post: dict) -> str | None:
    """Pick the largest photo attachment from a VK wall post."""
    best_url: str | None = None
    best_area = 0
    for attachment in post.get("attachments") or []:
        if attachment.get("type") != "photo":
            continue
        photo = attachment.get("photo") or {}
        for size in photo.get("sizes") or []:
            width = int(size.get("width") or 0)
            height = int(size.get("height") or 0)
            area = width * height
            url = size.get("url")
            if url and area > best_area:
                best_area = area
                best_url = url
    return best_url


async def fetch_kinopoisk_poster(film_title: str) -> str | None:
    """Search Kinopoisk and return the first POSTER image URL."""
    token = (get_settings().KINOPOISK_API_TOKEN or "").strip()
    if not token or token.startswith("your-"):
        return None

    query = _clean_film_title(film_title)
    if len(query) < 2:
        return None
    if query in _POSTER_CACHE:
        return _POSTER_CACHE[query]

    headers = {"X-API-KEY": token}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            search = await client.get(
                f"{_KINOPOISK_BASE}/api/v2.1/films/search-by-keyword",
                params={"keyword": query},
                headers=headers,
            )
            search.raise_for_status()
            films = (search.json() or {}).get("films") or []
            film_id = None
            for item in films:
                fid = item.get("filmId") or item.get("kinopoiskId")
                if fid:
                    film_id = int(fid)
                    break
            if not film_id:
                _POSTER_CACHE[query] = None
                return None

            images = await client.get(
                f"{_KINOPOISK_BASE}/api/v2.2/films/{film_id}/images",
                params={"type": "POSTER"},
                headers=headers,
            )
            images.raise_for_status()
            items = (images.json() or {}).get("items") or []
            poster_url = None
            for item in items:
                poster_url = item.get("imageUrl") or item.get("url")
                if poster_url:
                    break
            _POSTER_CACHE[query] = poster_url
            return poster_url
    except Exception as exc:
        logger.debug("Kinopoisk poster lookup failed for %r: %s", query, exc)
        _POSTER_CACHE[query] = None
        return None


async def resolve_cinema_poster(
    title: str,
    *,
    vk_poster_url: str | None = None,
) -> str | None:
    """Prefer VK afisha photo; fall back to Kinopoisk."""
    if vk_poster_url:
        return vk_poster_url
    return await fetch_kinopoisk_poster(title)
