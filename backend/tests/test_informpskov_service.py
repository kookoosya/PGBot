"""Tests for informpskov.ru RSS parser."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.event_sources.fetchers.informpskov import parse_informpskov_rss

MOSCOW = ZoneInfo("Europe/Moscow")

FUTURE_ITEM = """
<item>
    <title>Выставка архивных документов о Пушкине откроется в Пскове</title>
    <link>https://informpskov.ru/news/510374.html</link>
    <description><![CDATA[<p>Псковская библиотека приглашает на открытие выставки 20 июня 2026 в Пскове.</p>
    <img src="https://media.informpskov.ru/content/2026/06/pushkin.jpg" />]]></description>
    <category>Культура</category>
    <pubDate>Mon, 16 Jun 2026 18:00:00 +0300</pubDate>
</item>
"""

NOISE_ITEM = """
<item>
    <title>Более 1200 случаев ОРВИ зарегистрировали в Псковской области за неделю</title>
    <link>https://informpskov.ru/news/510382.html</link>
    <description><![CDATA[<p>С 8 по 14 июня в Псковской области зафиксировали 1 219 случаев ОРВИ.</p>]]></description>
    <category>Общество</category>
    <pubDate>Tue, 16 Jun 2026 21:40:33 +0300</pubDate>
</item>
"""

POLITICS_ITEM = """
<item>
    <title>Представитель Кремля назвал Псков оплотом русской государственности</title>
    <link>https://informpskov.ru/news/510421.html</link>
    <description><![CDATA[<p>Заместитель руководителя администрации президента РФ назвал Псков оплотом русской государственности на семинаре-совещании по вопросам реализации государственной национальной политики сегодня, 17 июня.</p>]]></description>
    <category>Общество</category>
    <pubDate>Wed, 17 Jun 2026 12:00:00 +0300</pubDate>
</item>
"""

PUSHKIN_ITEM = """
<item>
    <title>Опубликована программа фестиваля «Бугровский гарнец» в «Михайловском»</title>
    <link>https://informpskov.ru/news/510277.html</link>
    <description><![CDATA[<p>Фестиваль запланирован на 19 и 20 июня в Пушкинских Горах. Музей-заповедник приглашает гостей.</p>]]></description>
    <category>Культура</category>
    <pubDate>Sun, 15 Jun 2026 20:52:00 +0300</pubDate>
</item>
"""


def test_parse_future_culture_event_in_pskov():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=MOSCOW)
    events = parse_informpskov_rss(
        f"<rss><channel>{FUTURE_ITEM}</channel></rss>",
        now=now,
    )
    assert len(events) == 1
    assert events[0].region.value == "pskov"
    assert "Пушкин" in events[0].title
    assert events[0].location == "Псков"
    assert events[0].starts_at.day == 20
    assert events[0].poster_url is not None


def test_skips_health_noise():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=MOSCOW)
    events = parse_informpskov_rss(
        f"<rss><channel>{NOISE_ITEM}</channel></rss>",
        now=now,
    )
    assert events == []


def test_skips_political_news_without_invite():
    now = datetime(2026, 6, 17, 12, 0, tzinfo=MOSCOW)
    events = parse_informpskov_rss(
        f"<rss><channel>{POLITICS_ITEM}</channel></rss>",
        now=now,
    )
    assert events == []


def test_parse_pushkin_gory_festival_news():
    now = datetime(2026, 6, 16, 12, 0, tzinfo=MOSCOW)
    events = parse_informpskov_rss(
        f"<rss><channel>{PUSHKIN_ITEM}</channel></rss>",
        now=now,
    )
    assert len(events) == 1
    assert events[0].region.value == "pushkin_gory"
    assert "гарнец" in events[0].title.lower()
    assert events[0].starts_at.day == 19
