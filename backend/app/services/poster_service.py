"""Event image resolution — Kinopoisk posters, VK photos, category fallbacks."""

from __future__ import annotations

import logging
import re

import httpx

from app.config import get_settings
from app.constants.cinema_catalog import lookup_film
from app.models.enums import EventCategory

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

_STOCK_GALLERY_PREFIX = "/images/gallery/"

_CATEGORY_IMAGES: dict[str, str] = {
    EventCategory.CULTURE.value: "/images/gallery/monastery.jpg",
    EventCategory.HOLIDAY.value: "/images/gallery/nkc.jpg",
    EventCategory.TOURISM.value: "/images/gallery/mikhailovskoe.jpg",
    EventCategory.SPORT.value: "/images/gallery/petrovskoe.jpg",
    EventCategory.EDUCATION.value: "/images/gallery/trigorskoe.jpg",
    EventCategory.COMMUNITY.value: "/images/gallery/village.jpg",
    EventCategory.OTHER.value: "/images/gallery/monument.jpg",
}


def is_stock_gallery_poster(url: str | None) -> bool:
    """Site gallery placeholders — not real event posters."""
    return bool(url and url.strip().startswith(_STOCK_GALLERY_PREFIX))


def is_real_poster_url(url: str | None, *, category: str | None = None) -> bool:
    """True when URL is a real poster (Kinopoisk, VK, external), not a stock placeholder."""
    if not (url or "").strip():
        return False
    if is_stock_gallery_poster(url):
        return False
    if category == EventCategory.CINEMA.value and url.strip().startswith("/images/"):
        return False
    return True


def _clean_film_title(title: str) -> str:
    catalog = lookup_film(title)
    if catalog:
        return catalog.title
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
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -–—,.«»\"'")
    if cleaned.startswith('"') and '"' in cleaned[1:]:
        inner = cleaned.split('"', 2)[1].strip()
        if inner:
            return inner[:200]
    return cleaned[:200]


def _title_similarity(query: str, candidate: str) -> float:
    q = query.lower().strip()
    c = candidate.lower().strip()
    if not q or not c:
        return 0.0
    if q == c:
        return 1.0
    if q in c or c in q:
        return 0.85
    q_tokens = set(q.split())
    c_tokens = set(c.split())
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = len(q_tokens & c_tokens) / max(len(q_tokens), len(c_tokens))
    return overlap


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
    """Search Kinopoisk, pick best title match, return official ``posterUrl``."""
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
            best_id: int | None = None
            best_score = 0.0
            for item in films[:12]:
                fid = item.get("filmId") or item.get("kinopoiskId")
                if not fid:
                    continue
                names = [
                    item.get("nameRu") or "",
                    item.get("nameEn") or "",
                    item.get("nameOriginal") or "",
                ]
                score = max(_title_similarity(query, name) for name in names if name)
                if score > best_score:
                    best_score = score
                    best_id = int(fid)
            if not best_id or best_score < 0.35:
                _POSTER_CACHE[query] = None
                return None

            details = await client.get(
                f"{_KINOPOISK_BASE}/api/v2.2/films/{best_id}",
                headers=headers,
            )
            details.raise_for_status()
            data = details.json() or {}
            poster_url = data.get("posterUrl") or data.get("coverUrl")
            if not poster_url:
                images = await client.get(
                    f"{_KINOPOISK_BASE}/api/v2.2/films/{best_id}/images",
                    params={"type": "POSTER"},
                    headers=headers,
                )
                images.raise_for_status()
                items = (images.json() or {}).get("items") or []
                for item in items:
                    poster_url = item.get("imageUrl") or item.get("url")
                    if poster_url and "preview" not in poster_url.lower():
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
    """Prefer VK afisha photo; fall back to Kinopoisk official poster."""
    if vk_poster_url:
        return vk_poster_url
    return await fetch_kinopoisk_poster(title)


def category_fallback_image(category: str | None) -> str | None:
    if not category:
        return _CATEGORY_IMAGES.get(EventCategory.OTHER.value)
    return _CATEGORY_IMAGES.get(category)


async def resolve_event_poster(
    *,
    title: str,
    category: str,
    vk_poster_url: str | None = None,
) -> str | None:
    """Poster/image for any event type."""
    if vk_poster_url:
        return vk_poster_url
    if category == EventCategory.CINEMA.value:
        return await fetch_kinopoisk_poster(title)
    return category_fallback_image(category)


def strip_invalid_cinema_poster(poster_url: str | None, *, category: str) -> str | None:
    """Remove stock gallery images wrongly attached to cinema cards."""
    if category != EventCategory.CINEMA.value:
        return poster_url
    if is_real_poster_url(poster_url, category=category):
        return poster_url
    return None
