"""Tests for drampush.ru afisha parser."""

from app.services.drampush_service import _parse_page

SAMPLE = """
<div class="afishalist" data-age="18+" data-place="большаясцена" data-date="20260619">
    <div class="news_date">
        <div>19 июня 2026 </div>
        <div>19:00</div>
    </div>
    <div class="af_head list-head"><h2><a href="/repertoire/revisor">«Ревизор»</a></h2>
    Большая сцена
    </div>
    <div class="list-button"><button onclick="listimWidget.openModal({event_id: 1232084});">Купить</button></div>
</div>
"""


def test_parse_drampush_afisha_block():
    events = _parse_page(SAMPLE)
    assert len(events) == 1
    assert "Ревизор" in events[0].title
    assert events[0].starts_at.day == 19
    assert events[0].starts_at.hour == 19
