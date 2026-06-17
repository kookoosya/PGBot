"""Informpskov.ru RSS — regional culture and event news."""

from __future__ import annotations

from app.services.event_sources.fetchers.news_rss import NewsRssEvent, fetch_news_rss_events, parse_news_rss

INFORMPSKOV_RSS_URL = "https://informpskov.ru/rss.xml"

InformpskovEvent = NewsRssEvent


def parse_informpskov_rss(xml_text: str, *, now=None) -> list[NewsRssEvent]:
    return parse_news_rss(xml_text, fallback_url=INFORMPSKOV_RSS_URL, now=now)


async def fetch_informpskov_events(*, item_limit: int = 40) -> list[NewsRssEvent]:
    return await fetch_news_rss_events(INFORMPSKOV_RSS_URL, item_limit=item_limit)
