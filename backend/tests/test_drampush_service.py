"""Tests for drampush.ru afisha parser."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.event_sources.fetchers.drampush import _parse_page

MOSCOW = ZoneInfo("Europe/Moscow")


def _future_sample() -> tuple[str, int, int]:
    start = datetime.now(MOSCOW) + timedelta(days=21)
    date_attr = start.strftime("%Y%m%d")
    months = (
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )
    label = f"{start.day} {months[start.month - 1]} {start.year}"
    return date_attr, start.day, label


def test_parse_drampush_afisha_block():
    date_attr, day, label = _future_sample()
    sample = f"""
<div class="afishalist" data-age="18+" data-place="большаясцена" data-date="{date_attr}">
    <div class="news_date">
        <div>{label} </div>
        <div>19:00</div>
    </div>
    <div class="af_head list-head"><h2><a href="/repertoire/revisor">«Ревизор»</a></h2>
    Большая сцена
    </div>
    <div class="list-button"><button onclick="listimWidget.openModal({{event_id: 1232084}});">Купить</button></div>
</div>
"""
    events = _parse_page(sample)
    assert len(events) == 1
    assert "Ревизор" in events[0].title
    assert events[0].starts_at.day == day
    assert events[0].starts_at.hour == 19
