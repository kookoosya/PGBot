"""Cinema metadata extraction — genre, title resolution and teaser descriptions."""

from __future__ import annotations

import re

from app.constants.cinema_catalog import FilmMetadata, is_generic_cinema_title, lookup_film
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


def resolve_cinema_from_catalog(text: str) -> FilmMetadata | None:
    return lookup_film(text)


def enrich_cinema_title(
    title: str,
    description: str | None,
    *,
    catalog: FilmMetadata | None = None,
) -> str:
    """Replace generic cinema titles with catalog or quoted film names."""
    catalog = catalog or lookup_film(f"{title} {description or ''}")
    if catalog and is_generic_cinema_title(title):
        return catalog.title
    if catalog and catalog.title.lower() in f"{title} {description or ''}".lower():
        return catalog.title
    if not is_generic_cinema_title(title):
        return title.strip()
    if catalog:
        return catalog.title
    return title.strip()


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
    if genre:
        body = re.sub(r"(?i)жанр[:\s]+[^.!\n]+[.!\n]?", "", body).strip()
    if body and not body.lower().startswith("жанр:"):
        teaser = body.split("\n")[0].strip()
        if len(teaser) > 220:
            teaser = teaser[:217].rstrip() + "…"
        if teaser.lower() != title.lower():
            parts.append(teaser)
    elif not parts:
        parts.append(
            f"Сеанс «{title}» в {location or 'кинотеатре Пскова'}. "
            "Удобно совместить с поездкой из Пушкинских Гор."
        )
    return " ".join(parts)


def enrich_cinema_fields(
    *,
    title: str,
    description: str | None,
    category: EventCategory,
    genre: str | None = None,
    location: str | None = None,
) -> tuple[str | None, str | None]:
    """Return (genre, enriched_description) for cinema events.

    Deprecated: prefer ``event_enrichment_service.enrich_event_fields``.
    """
    if category != EventCategory.CINEMA:
        if description and len(description.strip()) < 24 and title:
            return genre, f"{title}. {description}".strip()[:2000]
        return genre, description

    catalog = resolve_cinema_from_catalog(f"{title} {description or ''}")
    resolved_title = enrich_cinema_title(title, description, catalog=catalog)
    resolved_genre = genre or (catalog.genre if catalog else None) or extract_genre(
        f"{resolved_title} {description or ''}"
    )
    body = description
    if catalog and (not body or len(body) < 40):
        body = catalog.teaser
    enriched = build_cinema_description(
        title=resolved_title,
        genre=resolved_genre,
        raw_description=body,
        location=location,
    )
    return resolved_genre, enriched
