"""Orbilet source region assignment."""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models.enums import EventCategory, EventRegion
from app.services.event_sources.orbilet_source import _to_fetched
from app.services.orbilet_service import OrbiletEvent

MOSCOW = ZoneInfo("Europe/Moscow")


def _sample(**kwargs) -> OrbiletEvent:
    defaults = dict(
        title="Концерт",
        description="Описание",
        starts_at=datetime(2026, 7, 1, 19, 0, tzinfo=MOSCOW),
        location="Псков",
        category=EventCategory.CULTURE,
        source_url="https://www.orbilet.ru/session/1",
    )
    defaults.update(kwargs)
    return OrbiletEvent(**defaults)


def test_orbilet_pskov_venue():
    fetched = _to_fetched(_sample(location="БКЗ Филармонии"))
    assert fetched.region == EventRegion.PSKOV


def test_orbilet_pushkin_excursion():
    fetched = _to_fetched(
        _sample(
            title="Экскурсия в Пушкинский заповедник",
            location="Михайловское",
            category=EventCategory.OTHER,
        )
    )
    assert fetched.region == EventRegion.PUSHKIN_GORY
