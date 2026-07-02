"""Tests for pushkinland.ru calendar parser."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.event_sources.fetchers.pushkinland import (
    _should_expand_with_program,
    parse_pushkinland_calendar,
    parse_pushkinland_program_page,
)

MOSCOW = ZoneInfo("Europe/Moscow")
MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


def _future_garnect() -> tuple[str, str, int, int, int]:
    start = datetime.now(MOSCOW) + timedelta(days=21)
    end = start + timedelta(days=1)
    year = start.year
    row = f"""
<div class="three wide column">
  <p class="ab"><b> {start.day} – {end.day} {MONTHS[start.month - 1]}</b></p>
  </div>
  <div class="thirteen wide column">
<p class="ab"><a href="/2018/news/news26/news57.php" target="_blank">Всероссийский театральный фестиваль <b>«Бугровский гарнец»</b></a>  </p>
</div>
"""
    program = f"""
<h3><b>{start.day} {MONTHS[start.month - 1]} </b></h3>
<p class="ab"><b>10.00	Открытие всероссийского театрального фестиваля «Бугровский гарнец»</b></p>
<p class="ab"><b>10.15	«Рассказы Девицы К. И. Т. »</b> по повестям – 70 мин</p>
<p class="ab"><i>Театр Пушкинского Заповедника</i></p>
<p class="ab"><b>13.00	Перерыв</b></p>
<h2><b>{end.day} {MONTHS[end.month - 1]} </b></h2>
<p class="ab"><b>10.15	Спектакль «Пиратские анекдоты»</b> – 45 мин</p>
<p class="ab"><i>Детская студия</i></p>
"""
    return row, program, year, start.day, end.day


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
    garnect_row, _, year, day1, day2 = _future_garnect()
    events = parse_pushkinland_calendar(garnect_row, year=year)
    assert len(events) == 1
    event = events[0]
    assert "гарнец" in event.title.lower()
    assert " . " not in event.title
    assert event.starts_at.day == day1
    assert event.ends_at is not None
    assert event.ends_at.day == day2
    assert event.starts_at.tzinfo == MOSCOW
    assert "pushkinland.ru" in event.source_url
    assert event.location.startswith("Бугрово")


def test_skips_long_exhibition_and_on_request():
    events = parse_pushkinland_calendar(EXHIBITION_ROW + ON_REQUEST_ROW, year=2026)
    assert events == []


def test_parse_garnect_program_into_performances():
    garnect_row, program, year, day1, day2 = _future_garnect()
    calendar = parse_pushkinland_calendar(garnect_row, year=year)
    assert len(calendar) == 1
    parent = calendar[0]

    performances = parse_pushkinland_program_page(
        program,
        year=year,
        source_url=parent.source_url,
        festival_title=parent.title,
        location=parent.location,
    )
    assert len(performances) == 3
    assert performances[0].starts_at.day == day1
    assert performances[-1].starts_at.day == day2
    assert all("гарнец" in item.title.lower() for item in performances)
    assert performances[1].description and "Коллектив" in performances[1].description


def test_should_expand_multi_day_festival_with_news_link():
    garnect_row, _, year, _, _ = _future_garnect()
    calendar = parse_pushkinland_calendar(garnect_row, year=year)
    assert _should_expand_with_program(calendar[0]) is True
