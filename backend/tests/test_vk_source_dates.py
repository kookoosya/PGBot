"""Tests for VK post import date selection."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.constants.event_config import VK_EVENT_GROUPS
from app.models.enums import EventRegion
from app.services.event_sources.vk_source import _post_to_fetched

MOSCOW = ZoneInfo("Europe/Moscow")
PRESET = next(g for g in VK_EVENT_GROUPS if g.screen_name == "pushkinogorie")


def test_vk_post_skipped_without_future_date():
    post = {
        "id": 1,
        "date": int(datetime(2026, 5, 1, 12, 0, tzinfo=MOSCOW).timestamp()),
        "text": "Приглашаем на концерт! Будет интересно.",
    }
    assert _post_to_fetched(post, preset=PRESET, group_id=958262) is None


def test_vk_post_imports_future_festival():
    start = datetime.now(MOSCOW) + timedelta(days=21)
    end = start + timedelta(days=1)
    months = (
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )
    post = {
        "id": 2,
        "date": int(datetime(2026, 6, 10, 12, 0, tzinfo=MOSCOW).timestamp()),
        "text": (
            "Приглашаем на «Бугровский гарнец»!\n"
            f"{start.day} и {end.day} {months[start.month - 1]} {start.year} — "
            "театральный фестиваль в Бугрово."
        ),
    }
    item = _post_to_fetched(post, preset=PRESET, group_id=958262)
    assert item is not None
    assert item.region == EventRegion.PUSHKIN_GORY
    assert item.starts_at.day == start.day
    assert item.ends_at is not None
    assert item.ends_at.day == end.day
