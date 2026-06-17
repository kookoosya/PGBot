"""Tests for PLN RSS parser."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.event_sources.fetchers.pln import parse_pln_rss

MOSCOW = ZoneInfo("Europe/Moscow")

PLN_ITEM = """
<item>
    <title><![CDATA[Выставка архивных документов о предках Александра Пушкина откроется в Пскове]]></title>
    <link>http://pln-pskov.ru/culture/590600.html</link>
    <description><![CDATA[<p>Библиотека приглашает на открытие выставки 18 июня 2026 в Пскове.</p>]]></description>
    <category><![CDATA[Культура]]></category>
    <pubDate>Mon, 16 Jun 2026 12:00:00 +0000</pubDate>
</item>
"""


def test_parse_pln_culture_event():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=MOSCOW)
    events = parse_pln_rss(f"<rss><channel>{PLN_ITEM}</channel></rss>", now=now)
    assert len(events) == 1
    assert events[0].region.value == "pskov"
    assert "Пушкин" in events[0].title
    assert events[0].starts_at.day == 18
