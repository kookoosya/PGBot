"""Tests for KDC Pushgory HTML parsing."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.event_sources.fetchers.kdc_pushgory import _parse_homepage

MOSCOW = ZoneInfo("Europe/Moscow")


def _future_festival_text() -> tuple[str, int, int, int]:
    start = datetime.now(MOSCOW) + timedelta(days=21)
    end = start + timedelta(days=1)
    months = (
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )
    teaser = (
        f"Театральный фестиваль в Бугрово {start.day} и {end.day} "
        f"{months[start.month - 1]} {start.year}"
    )
    return teaser, start.day, end.day, start.year


def test_parse_homepage_extracts_future_event():
    teaser, day1, day2, year = _future_festival_text()
    sample_home = f"""
<div class="cms-block-news news-tile">
  <div class="row tile-news-body">
    <div class="col-md-6 news_item">
      <a class="content_block" href="/item/999001">
        <span class="bottom_block">{teaser}</span>
      </a>
      <h4 class="text-center"><a href="/item/999001">Бугровский гарнец</a></h4>
    </div>
  </div>
</div>
"""
    events = _parse_homepage(sample_home)
    assert len(events) == 1
    assert "гарнец" in events[0].title.lower()
    assert events[0].starts_at.day == day1
    assert events[0].ends_at is not None
    assert events[0].ends_at.day == day2
    assert events[0].starts_at.year == year
