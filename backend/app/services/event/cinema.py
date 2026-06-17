"""Cinema metadata — genre, title resolution, filter for real film shows."""

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

CULTURE_LIKE_TITLE_RE = re.compile(
    r"культурно-просветительн|мероприяти[ея]|петрушкин|спектакл|концерт|выставк|"
    r"праздник|фестиваль|экскурс|лекци|ярмарк|театр|музе[йя]|мастер[- ]класс|"
    r"постановк|игра\s*«",
    re.IGNORECASE,
)

_CINEMA_AFISHA_SOURCES = frozenset({
    "orbilet", "kinopskov", "mirage", "silver", "kudago", "timepad",
})


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


def is_real_cinema_event(
    *,
    title: str,
    description: str | None = None,
    category: str,
    genre: str | None = None,
    source: str | None = None,
    location: str | None = None,
) -> bool:
    """True when a cinema-category row is an actual film show, not a miscategorized event."""
    if category != EventCategory.CINEMA.value:
        return False

    from app.services.poster_service import _is_planetarium_event

    if _is_planetarium_event(title, location):
        return False

    combined = f"{title} {description or ''}"
    if CULTURE_LIKE_TITLE_RE.search(title):
        return False

    catalog = lookup_film(combined)
    if is_generic_cinema_title(title) and not catalog:
        return False

    src = (source or "").strip().lower()
    if src in _CINEMA_AFISHA_SOURCES:
        return True
    if genre or catalog:
        return True
    if re.search(r'[«»"]', title):
        return True

    return False
