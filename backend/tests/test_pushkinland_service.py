"""Tests for pushkinland.ru calendar parser."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.pushkinland_service import parse_pushkinland_calendar

MOSCOW = ZoneInfo("Europe/Moscow")

GARNEC_ROW = """
<div class="three wide column">
  <p class="ab"><b> 19 – 20 июня</b></p>
  </div>
  <div class="thirteen wide column">
<p class="ab"><a href="/2018/news/news26/news57.php" target="_blank">Всероссийский театральный фестиваль <b>«Бугровский гарнец»</b></a>  </p>
</div>
"""

EXHIBITION_ROW = """
<div class="three wide column">
  <p class="ab"><b> 18 июня – 20 августа</b></p>
  </div>
  <div class="thirteen wide column">
<p class="ab"><a href="/2018/exh/exh26/exhf296.php"><b>«Собранье пестрых глав»</b>. Выставка</a></p>
</div>
"""

ON_REQUEST_ROW = """
<div class="three wide column">
  <p class="ab"><b> 2 января – 31 декабря (по заявкам)</b></p>
  </div>
  <div class="thirteen wide column">
<p class="ab"> <b>«Загадки русского языка»</b>. Просветительная программа  </p>
</div>
"""


def test_parse_garnect_festival():
    fallback = datetime(2026, 6, 10, 12, 0, tzinfo=MOSCOW)
    events = parse_pushkinland_calendar(GARNEC_ROW, year=2026)
    assert len(events) == 1
    event = events[0]
    assert "гарнец" in event.title.lower()
    assert " . " not in event.title
    assert event.starts_at.day == 19
    assert event.ends_at is not None
    assert event.ends_at.day == 20
    assert event.starts_at.tzinfo == MOSCOW
    assert "pushkinland.ru" in event.source_url
    assert event.location.startswith("Бугрово")


def test_skips_long_exhibition_and_on_request():
    events = parse_pushkinland_calendar(EXHIBITION_ROW + ON_REQUEST_ROW, year=2026)
    assert events == []
