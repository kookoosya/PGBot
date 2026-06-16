"""Informpskov.ru RSS — regional culture and event news."""

from __future__ import annotations

import html
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import httpx

from app.models.enums import EventCategory, EventRegion

logger = logging.getLogger(__name__)
MOSCOW_TZ = ZoneInfo("Europe/Moscow")
INFORMPSKOV_RSS_URL = "https://informpskov.ru/rss.xml"

_PUSHKIN_KEYWORDS = (
    "пушкиногор", "пушкинские гор", "михайловск", "бугров", "пушкинский заповедник",
    "пушкинск", "святогор", "тригорск", "петровск",
)
_PSKOV_KEYWORDS = ("псков", "великие лук", "печор", "изборск", "остров", "порхов")
_EVENT_SIGNAL_RE = re.compile(
    r"фестиваль|концерт|выставк|спектакл|праздник|афиш|мероприят|театр|кинофестиваль|ярмарк|форум",
    re.IGNORECASE,
)
_INVITE_SIGNAL_RE = re.compile(
    r"приглашает|приглашаем|пройд[её]т|откроется|состоится|начн[её]тся|пройд[её]т",
    re.IGNORECASE,
)
_PAST_RE = re.compile(
    r"\b(прошёл|прошла|прошло|состоялся|состоялась|состоялось|завершился|завершилась)\b",
    re.IGNORECASE,
)
_SKIP_RE = re.compile(
    r"орви|погиб|пожар|ремонт школ|ваканси|уголов|задержан|тариф|бюджет|налог|дтп|авария"
    r"|вручили диплом|участникам программы «герои|\bсво\b",
    re.IGNORECASE,
)
_IN_PSKOV_RE = re.compile(r"\bв пскове\b|\bг\.?\s*псков\b", re.IGNORECASE)
_IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)
_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)
_ALLOWED_CATEGORIES = frozenset({"культура", "спорт", "общество", "туризм"})


@dataclass(frozen=True, slots=True)
class InformpskovEvent:
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    location: str
    region: EventRegion
    category: EventCategory
    source_url: str
    poster_url: str | None = None


def _strip_html(value: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", text).strip()


def _extract_poster(description: str) -> str | None:
    match = _IMG_RE.search(description)
    if not match:
        return None
    url = match.group(1).strip()
    return url if url.startswith("http") else None


def _infer_region(text: str) -> EventRegion | None:
    lower = text.lower()
    if _IN_PSKOV_RE.search(lower):
        return EventRegion.PSKOV
    if any(keyword in lower for keyword in _PUSHKIN_KEYWORDS):
        return EventRegion.PUSHKIN_GORY
    if any(keyword in lower for keyword in _PSKOV_KEYWORDS):
        return EventRegion.PSKOV
    return None


def _default_location(region: EventRegion) -> str:
    if region == EventRegion.PUSHKIN_GORY:
        return "Пушкинские Горы"
    return "Псков"


def _parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=MOSCOW_TZ)
        return parsed.astimezone(MOSCOW_TZ)
    except (TypeError, ValueError, IndexError):
        return None


def _is_relevant_item(*, title: str, description: str, category: str) -> bool:
    combined = f"{title}. {description}"
    if _SKIP_RE.search(combined):
        return False
    if _PAST_RE.search(title) and not _INVITE_SIGNAL_RE.search(combined):
        return False
    if "открылась" in title.lower() and "сегодня" not in combined.lower():
        return False
    category_lower = category.lower()
    has_category = any(cat in category_lower for cat in _ALLOWED_CATEGORIES)
    has_event_signal = _EVENT_SIGNAL_RE.search(combined) is not None
    has_invite = _INVITE_SIGNAL_RE.search(combined) is not None
    return has_category and has_event_signal and (has_invite or "сегодня" in combined.lower())


def _parse_rss_items(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []
    items: list[dict[str, str]] = []
    for item in channel.findall("item"):
        description = item.findtext("description") or ""
        cdata = _CDATA_RE.search(description)
        if cdata:
            description = cdata.group(1)
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "description": description,
            "category": (item.findtext("category") or "").strip(),
            "pub_date": item.findtext("pubDate") or "",
        })
    return items


def parse_informpskov_rss(xml_text: str, *, now: datetime | None = None) -> list[InformpskovEvent]:
    """Parse Informpskov RSS feed into normalized events."""
    from app.services.event_sources.text_utils import infer_category_from_text, parse_event_date_range

    now = now or datetime.now(MOSCOW_TZ)
    events: list[InformpskovEvent] = []
    seen: set[str] = set()

    for item in _parse_rss_items(xml_text):
        title = _strip_html(item["title"])
        if len(title) < 10:
            continue
        description_html = item["description"]
        description = _strip_html(description_html)
        if not _is_relevant_item(title=title, description=description, category=item["category"]):
            continue

        combined = f"{title}. {description}"
        region = _infer_region(combined)
        if region is None:
            continue

        pub_date = _parse_pub_date(item["pub_date"])
        fallback = pub_date or now
        try:
            starts_at, ends_at = parse_event_date_range(combined, fallback=fallback)
        except ValueError:
            continue
        if not starts_at and pub_date:
            starts_at = pub_date.replace(hour=12, minute=0, second=0, microsecond=0)
        if not starts_at:
            continue
        if starts_at < now - timedelta(days=1):
            continue
        if starts_at > now + timedelta(days=120):
            continue

        link = item["link"] or INFORMPSKOV_RSS_URL
        if link in seen:
            continue
        seen.add(link)

        events.append(
            InformpskovEvent(
                title=title[:300],
                description=description[:2000] or None,
                starts_at=starts_at,
                ends_at=ends_at,
                location=_default_location(region),
                region=region,
                category=infer_category_from_text(combined),
                source_url=link,
                poster_url=_extract_poster(description_html),
            )
        )

    events.sort(key=lambda event: event.starts_at)
    return events


async def fetch_informpskov_events(*, item_limit: int = 40) -> list[InformpskovEvent]:
    headers = {"User-Agent": "PGBot-Events/1.0 (+https://192-210-213-135.sslip.io/events)"}
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers=headers) as client:
            response = await client.get(INFORMPSKOV_RSS_URL)
            response.raise_for_status()
            events = parse_informpskov_rss(response.text)
            return events[:item_limit]
    except Exception:
        logger.exception("Informpskov RSS fetch failed")
        return []
