"""PLN Pskov (pln-pskov.ru) RSS — regional culture news."""

from __future__ import annotations

from app.services.news_rss_service import NewsRssEvent, fetch_news_rss_events, parse_news_rss

PLN_RSS_URL = "https://pln-pskov.ru/rss.php"

PlnEvent = NewsRssEvent


def parse_pln_rss(xml_text: str, *, now=None) -> list[NewsRssEvent]:
    return parse_news_rss(xml_text, fallback_url=PLN_RSS_URL, now=now)


async def fetch_pln_events(*, item_limit: int = 40) -> list[NewsRssEvent]:
    return await fetch_news_rss_events(PLN_RSS_URL, item_limit=item_limit)
