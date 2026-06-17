"""Tests for optional event source health labels."""

from app.services.event_source_health import (
    build_event_sources_health,
    proculture_health_status,
    timepad_health_status,
)


def test_timepad_needs_token_by_default(monkeypatch):
    monkeypatch.setenv("TIMEPAD_API_TOKEN", "")
    from app.config import get_settings

    get_settings.cache_clear()
    assert timepad_health_status() == "needs_token"


def test_timepad_ready_with_token(monkeypatch):
    monkeypatch.setenv("TIMEPAD_API_TOKEN", "secret-token")
    from app.config import get_settings

    get_settings.cache_clear()
    assert timepad_health_status() == "ready"


def test_proculture_needs_token_by_default(monkeypatch):
    monkeypatch.setenv("PROCULTURE_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    assert proculture_health_status() == "needs_token"


def test_build_event_sources_health_shape(monkeypatch):
    monkeypatch.setenv("TIMEPAD_API_TOKEN", "")
    monkeypatch.setenv("PROCULTURE_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    health = build_event_sources_health()
    assert set(health) == {"vk_wall", "timepad", "proculture"}
