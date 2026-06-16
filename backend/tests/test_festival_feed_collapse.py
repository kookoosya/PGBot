"""Tests for festival program collapse in compact feeds."""

from datetime import datetime, timezone

from app.models.event import Event
from app.services.event.public import collapse_festival_program_feed

PROGRAM_URL = "https://pushkinland.ru/2018/news/news26/news57.php"


def _event(
    event_id: int,
    *,
    title: str,
    starts_at: datetime,
    source: str = "pushkinland",
    source_url: str = PROGRAM_URL,
) -> Event:
    return Event(
        id=event_id,
        title=title,
        starts_at=starts_at,
        source=source,
        source_url=source_url,
        region="pushkin_gory",
        category="culture",
        is_published=True,
    )


def test_collapse_garnect_program_to_one_card():
    events = [
        _event(1, title="«Снежная королева» — Бугровский гарнец", starts_at=datetime(2026, 6, 19, 11, 45, tzinfo=timezone.utc)),
        _event(2, title="«Пиратские анекдоты» — Бугровский гарнец", starts_at=datetime(2026, 6, 20, 10, 15, tzinfo=timezone.utc)),
        _event(3, title="День языков народов России", starts_at=datetime(2026, 6, 18, 12, 0, tzinfo=timezone.utc), source_url="https://pushkinland.ru/cal"),
    ]
    collapsed = collapse_festival_program_feed(events)
    assert len(collapsed) == 2
    assert collapsed[0].id == 3
    assert collapsed[1].id == 1
