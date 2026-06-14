"""Cinema metadata extraction — genre and teaser descriptions."""

from __future__ import annotations

import re
from typing import Optional

from app.models.enums import EventCategory

_GENRE_RE = re.compile(
    r"(?:жанр[:\s]+|genre[:\s]+)([а-яёa-z0-9 ,/\-]+)",
    re.IGNORECASE,
)

_KNOWN_GENRES = (
    "фантастика", "драма", "комедия", "триллер", "боевик", "мелодрама",
    "ужасы", "детектив", "приключения", "семейный", "документальный",
    "биография", "история", "мультфильм", "аниме", "военный", "криминал",
    "фэнтези", "музыкальный",
)

_INLINE_GENRE_RE = re.compile(
    r"\b(" + "|".join(re.escape(g) for g in _KNOWN_GENRES) + r")\b",
    re.IGNORECASE,
)


def extract_genre(text: str) -> str | None:
    """Parse genre from description or title."""
    if not text:
        return None
    match = _GENRE_RE.search(text)
    if match:
        return _normalize_genre(match.group(1))
    inline = _INLINE_GENRE_RE.search(text.lower())
    if inline:
        return _normalize_genre(inline.group(1))
    return None


def _normalize_genre(raw: str) -> str:
    cleaned = raw.strip().strip(".,;")
    if not cleaned:
        return raw.strip()
    return cleaned[0].upper() + cleaned[1:].lower()


def build_cinema_description(
    *,
    title: str,
    genre: str | None,
    raw_description: str | None,
    location: str | None = None,
) -> str:
    """Build a short cinema teaser: genre + plot hint."""
    parts: list[str] = []
    if genre:
        parts.append(f"Жанр: {genre}.")
    body = (raw_description or "").strip()
    if body and not body.lower().startswith("жанр:"):
        teaser = body.split("\n")[0].strip()
        if len(teaser) > 220:
            teaser = teaser[:217].rstrip() + "…"
        parts.append(teaser)
    elif not parts:
        parts.append(f"Сеанс в {location or 'кинотеатре Пскова'}. Удобно совместить с поездкой из Пушкинских Гор.")
    return " ".join(parts)


def enrich_cinema_fields(
    *,
    title: str,
    description: str | None,
    category: EventCategory,
    genre: str | None = None,
    location: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (genre, enriched_description) for cinema events."""
    if category != EventCategory.CINEMA:
        if description and len(description.strip()) < 24 and title:
            return genre, f"{title}. {description}".strip()[:2000]
        return genre, description

    resolved_genre = genre or extract_genre(f"{title} {description or ''}")
    enriched = build_cinema_description(
        title=title,
        genre=resolved_genre,
        raw_description=description,
        location=location,
    )
    return resolved_genre, enriched
