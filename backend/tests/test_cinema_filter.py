"""Unit tests for cinema event filtering (real films vs miscategorized events)."""

import pytest

from app.models.enums import EventCategory
from app.services.cinema_enrichment import is_real_cinema_event


@pytest.mark.parametrize(
    ("title", "source", "genre", "expected"),
    [
        ("Майкл", "kinopskov", "биография", True),
        ("Петрушкины забавы", "vk", None, False),
        ("Концерт в НКЦ", "vk", None, False),
        ("«Дюна: часть вторая»", "orbilet", None, True),
        ("кино", "vk", None, False),
        ("Выставка в музее", "kudago", None, False),
    ],
)
def test_is_real_cinema_event(title: str, source: str, genre: str | None, expected: bool):
    assert is_real_cinema_event(
        title=title,
        category=EventCategory.CINEMA.value,
        source=source,
        genre=genre,
    ) is expected


def test_non_cinema_category_rejected():
    assert is_real_cinema_event(
        title="Майкл",
        category=EventCategory.CULTURE.value,
        source="kinopskov",
        genre="биография",
    ) is False


def test_planetarium_filtered():
    assert is_real_cinema_event(
        title="Звёздное небо",
        category=EventCategory.CINEMA.value,
        source="vk",
        location="Планетарий Пскова",
    ) is False
