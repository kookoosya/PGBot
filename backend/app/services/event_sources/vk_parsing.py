"""VK wall post parsing — titles, teasers, spam filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.constants.cinema_catalog import lookup_film
from app.models.enums import EventCategory
from app.services.cinema_enrichment import extract_genre
from app.services.event_sources.text_utils import (
    VK_AD_KEYWORDS,
    infer_category_from_text,
    parse_event_datetime,
)

_QUOTED_TITLE_RE = re.compile(
    r"[«\"']([^»\"'\n]{3,120})[»\"']",
)
_CINEMA_LINE_RE = re.compile(
    r"(?:фильм|кино|сеанс|премьера|показ)\s*[:\-—]?\s*[«\"']?([^»\"'\n.!]{3,100})",
    re.IGNORECASE,
)
_HASHTAG_RE = re.compile(r"#\w+")
_URL_RE = re.compile(r"https?://\S+|vk\.com/\S+")
_MENTION_RE = re.compile(r"@\w+|\[id\d+\|[^\]]+\]")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

_SPAM_KEYWORDS = (
    "розыгрыш", "выиграй", "выиграть", "приз", "призы", "промокод", "промо-код",
    "скидк", "акци", "распродаж", "cashback", "кэшбэк", "кешбэк",
    "подписывайт", "подпишись", "репостни", "репост", "лайкни", "конкурс репост",
    "реклама", "#реклама", "erid", "инн ", "огрн",
    "ваканси", "требуется сотрудник", "набор персонала", "зарплат",
    "продам", "продаю", "сдам", "сдаётся", "аренда квартир",
    "тариф", "абонемент", "подключ", "интернет", "мобильн",
    "опрос", "голосован", "анкет",
)

_EVENT_SIGNALS = (
    "приглаша", "ждём", "ждем", "вход", "начало в", "начало:", "сбор в",
    "билет", "бесплатн", "участие", "программа", "экскурс", "концерт",
    "спектакл", "выставк", "фестиваль", "ярмарк", "праздник", "кино", "фильм",
    "сеанс", "лекци", "мастер-класс", "турнир", "марафон",
)


@dataclass(frozen=True, slots=True)
class VkParsedPost:
    title: str
    body: str
    category: EventCategory
    genre: str | None = None


def clean_post_text(text: str) -> str:
    """Strip URLs, mentions and excessive whitespace."""
    cleaned = _URL_RE.sub("", text)
    cleaned = _MENTION_RE.sub("", cleaned)
    cleaned = _HASHTAG_RE.sub("", cleaned)
    cleaned = _MULTI_NEWLINE_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def is_likely_spam_post(text: str) -> bool:
    lower = text.lower()
    if any(keyword in lower for keyword in VK_AD_KEYWORDS):
        return True
    if any(keyword in lower for keyword in _SPAM_KEYWORDS):
        return True
    # Mostly links / hashtags with little substance
    alpha = sum(1 for ch in lower if ch.isalpha())
    if alpha < 25 and ("http" in lower or "#" in text):
        return True
    return False


def is_relevant_vk_event_post(text: str, *, parsed_date) -> bool:
    """Stricter relevance check for VK wall posts."""
    cleaned = clean_post_text(text)
    lower = cleaned.lower()
    if len(lower) < 20:
        return False
    if is_likely_spam_post(cleaned):
        return False

    has_signal = any(signal in lower for signal in _EVENT_SIGNALS)
    has_date = parsed_date is not None

    if has_date and has_signal:
        return True
    if has_date and len(lower) >= 40:
        return True

    category = infer_category_from_text(cleaned)
    if category != EventCategory.OTHER and (has_signal or has_date):
        return True

    if lookup_film(cleaned):
        return True

    return False


def extract_quoted_titles(text: str) -> list[str]:
    return [m.group(1).strip() for m in _QUOTED_TITLE_RE.finditer(text) if len(m.group(1).strip()) >= 3]


def extract_cinema_title(text: str) -> str | None:
    """Best-effort film title from VK post."""
    catalog = lookup_film(text)
    if catalog:
        return catalog.title

    for quoted in extract_quoted_titles(text):
        film = lookup_film(quoted)
        if film:
            return film.title
        if _looks_like_film_title(quoted):
            return _normalize_title(quoted)

    match = _CINEMA_LINE_RE.search(text)
    if match:
        candidate = match.group(1).strip(" «»\"'.,!")
        film = lookup_film(candidate)
        if film:
            return film.title
        if _looks_like_film_title(candidate):
            return _normalize_title(candidate)

    return None


def _looks_like_film_title(value: str) -> bool:
    lower = value.lower().strip()
    if len(lower) < 3 or len(lower) > 100:
        return False
    blocked = (
        "псков", "кинотеатр", "сеанс", "билет", "премьера недели",
        "афиша", "расписание", "пушкин", "музей",
    )
    return not any(word in lower for word in blocked)


def _normalize_title(value: str) -> str:
    value = value.strip().strip("«»\"'")
    if not value:
        return value
    if value.isupper() or value.islower():
        return value[0].upper() + value[1:]
    return value


def extract_teaser_body(text: str, *, title: str, max_len: int = 220) -> str:
    """First meaningful paragraph(s), skipping title line and metadata."""
    lines: list[str] = []
    title_lower = title.lower()
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if lower == title_lower or title_lower in lower and len(line) < len(title) + 10:
            continue
        if lower.startswith(("📅", "📍", "🕐", "🎬", "когда:", "где:", "дата:", "время:")):
            continue
        if _URL_RE.search(line) or line.startswith("#"):
            continue
        lines.append(line)
    body = " ".join(lines).strip()
    if len(body) > max_len:
        body = body[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return body


def parse_vk_post(text: str) -> VkParsedPost:
    """Parse VK wall text into structured event fields."""
    cleaned = clean_post_text(text)
    category = infer_category_from_text(cleaned)

    if category == EventCategory.CINEMA or any(
        word in cleaned.lower() for word in ("кино", "фильм", "сеанс", "кинотеатр")
    ):
        category = EventCategory.CINEMA
        title = extract_cinema_title(cleaned)
        if not title:
            first_line = next((ln.strip() for ln in cleaned.split("\n") if ln.strip()), "Кино")
            title = _normalize_title(first_line[:120])
        genre = extract_genre(cleaned)
        catalog = lookup_film(f"{title} {cleaned}")
        if catalog:
            title = catalog.title
            genre = genre or catalog.genre
        body = extract_teaser_body(cleaned, title=title)
        if catalog and len(body) < 30:
            body = catalog.teaser
        return VkParsedPost(title=title[:300], body=body, category=category, genre=genre)

    first_line = next((ln.strip() for ln in cleaned.split("\n") if ln.strip()), "Событие")
    title = _normalize_title(first_line[:300])
    body = extract_teaser_body(cleaned, title=title) or cleaned[:500]
    return VkParsedPost(title=title, body=body, category=category, genre=None)
