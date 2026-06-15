"""Unified event metadata enrichment for all categories."""

from __future__ import annotations

import re

from app.constants.pskov_cinemas import format_cinema_location, match_pskov_cinema
from app.models.enums import EventCategory, EventRegion
from app.services.text_cleaning import first_sentences, normalize_event_text
from app.services.cinema_enrichment import (
    build_cinema_description,
    enrich_cinema_title,
    extract_genre,
    resolve_cinema_from_catalog,
)

MIN_DESCRIPTION_LEN = 40
_MAX_TEASER_LEN = 240

_CATEGORY_FALLBACKS: dict[EventCategory, str] = {
    EventCategory.CULTURE: "Культурная программа для жителей и гостей региона.",
    EventCategory.HOLIDAY: "Праздничное мероприятие — отличный повод собраться всей семьёй.",
    EventCategory.TOURISM: "Экскурсионная программа: познакомьтесь с историей и природой региона.",
    EventCategory.SPORT: "Спортивное событие — приходите поддержать участников или принять участие.",
    EventCategory.EDUCATION: "Образовательная программа: лекция, мастер-класс или семинар.",
    EventCategory.COMMUNITY: "Местное мероприятие — полезно и жителям, и гостям.",
    EventCategory.OTHER: "Актуальное событие в афише региона.",
}

_LOCATION_SUFFIX_RE = re.compile(r"\s{2,}")


def enrich_event_fields(
    *,
    title: str,
    description: str | None,
    category: EventCategory,
    genre: str | None = None,
    location: str | None = None,
    region: EventRegion | None = None,
) -> tuple[str, str | None, str | None]:
    """Return enriched (title, genre, description)."""
    clean_title = (title or "").strip()
    clean_desc = normalize_event_text(description)

    if category == EventCategory.CINEMA:
        return _enrich_cinema(
            title=clean_title,
            description=clean_desc,
            genre=genre,
            location=location,
            region=region,
        )

    enriched_desc = _enrich_non_cinema_description(
        title=clean_title,
        description=clean_desc,
        category=category,
        location=location,
        region=region,
    )
    return clean_title, genre, enriched_desc


def _enrich_cinema(
    *,
    title: str,
    description: str | None,
    genre: str | None,
    location: str | None,
    region: EventRegion | None,
) -> tuple[str, str | None, str | None]:
    catalog = resolve_cinema_from_catalog(f"{title} {description or ''}")
    resolved_title = enrich_cinema_title(title, description, catalog=catalog)
    resolved_genre = genre or (catalog.genre if catalog else None) or extract_genre(
        f"{resolved_title} {description or ''}"
    )
    body = description
    if catalog and (not body or len(body) < MIN_DESCRIPTION_LEN):
        body = catalog.teaser
    resolved_location = format_cinema_location(location) if location else None
    if not resolved_location and region == EventRegion.PSKOV:
        resolved_location = _default_cinema_location(region)
    enriched = build_cinema_description(
        title=resolved_title,
        genre=resolved_genre,
        raw_description=body,
        location=resolved_location or location or _default_cinema_location(region),
    )
    if len(enriched) < MIN_DESCRIPTION_LEN:
        enriched = _pad_description(resolved_title, enriched, category=EventCategory.CINEMA)
    return resolved_title, resolved_genre, enriched


def _enrich_non_cinema_description(
    *,
    title: str,
    description: str | None,
    category: EventCategory,
    location: str | None,
    region: EventRegion | None,
) -> str | None:
    body = description
    if body and len(body) > _MAX_TEASER_LEN:
        body = first_sentences(body, max_sentences=3)

    if body and len(body) >= MIN_DESCRIPTION_LEN:
        if body.lower().startswith(title.lower().rstrip(".")):
            return _trim_teaser(body)
        return _trim_teaser(f"{title.rstrip('.')}. {body}")

    parts: list[str] = []
    if title:
        parts.append(title.rstrip(".") + ".")
    if body:
        parts.append(body.strip())

    fallback = _category_fallback(category, location=location, region=region)
    combined = " ".join(parts).strip()
    if len(combined) < MIN_DESCRIPTION_LEN:
        combined = f"{combined} {fallback}".strip() if combined else fallback
    return _trim_teaser(combined)


def _category_fallback(
    category: EventCategory,
    *,
    location: str | None,
    region: EventRegion | None,
) -> str:
    base = _CATEGORY_FALLBACKS.get(category, _CATEGORY_FALLBACKS[EventCategory.OTHER])
    place = location or _region_label(region)
    if place and category in (EventCategory.CULTURE, EventCategory.TOURISM, EventCategory.HOLIDAY):
        return f"{base.rstrip('.')}. Место: {place}."
    return base


def _region_label(region: EventRegion | None) -> str | None:
    if region == EventRegion.PSKOV:
        return "Псков"
    if region == EventRegion.PUSHKIN_GORY:
        return "Пушкинские Горы"
    return None


def _default_cinema_location(region: EventRegion | None) -> str:
    if region == EventRegion.PSKOV:
        return "кинотеатрах Пскова (Победа, Смена, Мираж, Silver Cinema)"
    return "кинотеатре"


def resolve_cinema_location_from_text(text: str, *, region: EventRegion | None) -> str | None:
    """Infer cinema venue from post title or body."""
    if region != EventRegion.PSKOV:
        return format_cinema_location(text)
    cinema = match_pskov_cinema(text)
    if cinema:
        return f"{cinema.name}, {cinema.address}"
    return format_cinema_location(text)


def _pad_description(title: str, description: str, *, category: EventCategory) -> str:
    if len(description) >= MIN_DESCRIPTION_LEN:
        return description
    extra = _CATEGORY_FALLBACKS.get(category, "")
    if title and title not in description:
        return f"{title}. {description} {extra}".strip()
    return f"{description} {extra}".strip()


def _trim_teaser(text: str) -> str:
    cleaned = _LOCATION_SUFFIX_RE.sub(" ", text.strip())
    if len(cleaned) <= _MAX_TEASER_LEN:
        return cleaned
    cut = cleaned[: _MAX_TEASER_LEN - 1].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"
