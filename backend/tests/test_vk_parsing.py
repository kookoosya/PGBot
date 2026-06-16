"""Tests for VK wall post parsing and relevance."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.enums import EventCategory
from app.services.event_sources.vk_parsing import is_relevant_vk_event_post, parse_vk_post

MOSCOW = ZoneInfo("Europe/Moscow")


def test_garnets_post_is_relevant():
    text = (
        "Приглашаем на «Бугровский гарнец»!\n"
        "19 и 20 июня 2026 — театральный фестиваль в Бугрово.\n"
        "Программа: спектакли, фольклор, мастер-классы."
    )
    parsed_date = datetime(2026, 6, 19, 12, 0, tzinfo=MOSCOW)
    assert is_relevant_vk_event_post(text, parsed_date=parsed_date) is True


def test_plnpsk_requires_region_keyword():
    text = "Концерт 20 июня в 19:00. Билеты в кассе."
    parsed_date = datetime(2026, 6, 20, 19, 0, tzinfo=MOSCOW)
    assert is_relevant_vk_event_post(text, parsed_date=parsed_date, region_keywords=("псков",)) is False
    assert is_relevant_vk_event_post(
        text + " Псков, НКЦ.",
        parsed_date=parsed_date,
        region_keywords=("псков",),
    ) is True


def test_parse_vk_post_extracts_quoted_festival_title():
    text = (
        "Анонс!\n"
        "«Бугровский гарнец» пройдёт 19 и 20 июня в Бугрово.\n"
        "Театральный фестиваль Пушкиногорья."
    )
    parsed = parse_vk_post(text)
    assert "гарнец" in parsed.title.lower()
    assert parsed.category in (EventCategory.HOLIDAY, EventCategory.CULTURE)
