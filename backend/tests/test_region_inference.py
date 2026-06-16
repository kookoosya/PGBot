"""Tests for shared region inference."""

from app.models.enums import EventRegion
from app.services.region_inference import infer_event_region_from_text


def test_infer_pushkin_gory_from_location():
    assert infer_event_region_from_text("Экскурсия в Михайловское") == EventRegion.PUSHKIN_GORY


def test_infer_pushkin_gory_from_bugrovo():
    assert infer_event_region_from_text("Бугровский гарнец, Пушкинские Горы") == EventRegion.PUSHKIN_GORY


def test_infer_pskov_default():
    assert infer_event_region_from_text("БКЗ Филармонии, Псков") == EventRegion.PSKOV


def test_infer_pskov_explicit_default():
    assert (
        infer_event_region_from_text("концерт", default=EventRegion.PUSHKIN_GORY)
        == EventRegion.PUSHKIN_GORY
    )
