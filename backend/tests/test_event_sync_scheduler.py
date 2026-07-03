"""Module 6: event sync interval and scheduler behavior."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings, get_settings
from app.core import background_tasks as bg
from app.core.background_tasks import run_periodic, start_background_tasks, stop_background_tasks
from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.event_sources.base import FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_CONSTANTS = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "constants.ts"
MAP_ATTRIBUTION = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "mapAttribution.ts"
EVENTS_RIBBON = REPO_ROOT / "frontend" / "src" / "pages" / "events" / "EventsStatsRibbon.tsx"
MAP_RIBBON = REPO_ROOT / "frontend" / "src" / "pages" / "map" / "MapStatsRibbon.tsx"
NATIONAL_FLAG_EMOJI = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")


async def _spawn_background_tasks(settings: Settings) -> list[asyncio.Task]:
    return start_background_tasks(settings)


@pytest.fixture(autouse=True)
def reset_background_task_state():
    bg._background_tasks_started = False
    yield
    bg._background_tasks_started = False


@pytest.fixture
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_default_event_sync_interval_hours_is_four(clear_settings_cache, monkeypatch):
    monkeypatch.delenv("EVENT_SYNC_INTERVAL_HOURS", raising=False)
    settings = Settings()
    assert settings.EVENT_SYNC_INTERVAL_HOURS == 4


def test_env_override_event_sync_interval_hours(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "8")
    settings = Settings()
    assert settings.EVENT_SYNC_INTERVAL_HOURS == 8
    assert settings.event_sync_interval_seconds == 8 * 3600


def test_event_sync_interval_converts_to_seconds(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    settings = Settings()
    assert settings.event_sync_interval_seconds == 14400


def test_zero_event_sync_interval_disables_scheduler_task(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "0")
    settings = Settings()
    tasks = asyncio.run(_spawn_background_tasks(settings))
    event_tasks = [t for t in tasks if t.get_name() == "periodic:Event sync"]
    assert event_tasks == []
    for task in tasks:
        task.cancel()


def test_negative_event_sync_interval_disables_scheduler_task(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "-1")
    settings = Settings()
    tasks = asyncio.run(_spawn_background_tasks(settings))
    event_tasks = [t for t in tasks if t.get_name() == "periodic:Event sync"]
    assert event_tasks == []
    for task in tasks:
        task.cancel()


def test_scheduler_uses_event_interval_not_map_interval(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    monkeypatch.setenv("MAP_AUTO_SYNC_HOURS", "6")
    settings = Settings()
    tasks = asyncio.run(_spawn_background_tasks(settings))
    event_tasks = [t for t in tasks if t.get_name() == "periodic:Event sync"]
    map_tasks = [t for t in tasks if t.get_name() == "periodic:Map auto-sync"]
    assert len(event_tasks) == 1
    assert len(map_tasks) == 1
    for task in tasks:
        task.cancel()


@pytest.mark.asyncio
async def test_run_periodic_runs_work_before_sleep():
    calls: list[str] = []

    async def work():
        calls.append("work")
        raise asyncio.CancelledError()

    with patch("app.core.background_tasks.asyncio.sleep", new_callable=AsyncMock) as sleep:
        with pytest.raises(asyncio.CancelledError):
            await run_periodic("test", 14400, work)
    assert calls == ["work"]
    sleep.assert_not_called()


@pytest.mark.asyncio
async def test_run_periodic_sleeps_four_hours_after_sync(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    settings = Settings()
    sleeps: list[float] = []

    async def work():
        if len(sleeps) >= 1:
            raise asyncio.CancelledError()

    async def fake_sleep(seconds: float):
        sleeps.append(seconds)
        raise asyncio.CancelledError()

    with patch("app.core.background_tasks.asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await run_periodic("Event sync", settings.event_sync_interval_seconds, work)
    assert sleeps == [14400.0]


@pytest.mark.asyncio
async def test_run_periodic_continues_after_exception(caplog):
    attempts: list[int] = []

    async def work():
        attempts.append(len(attempts) + 1)
        if len(attempts) == 1:
            raise RuntimeError("sync failed")

    async def fake_sleep(_seconds: float):
        if len(attempts) >= 2:
            raise asyncio.CancelledError()

    with patch("app.core.background_tasks.asyncio.sleep", fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await run_periodic("Event sync", 14400, work)
    assert len(attempts) == 2
    assert "sync failed" in caplog.text


def test_start_background_tasks_creates_single_event_sync_task(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    monkeypatch.setenv("MAP_AUTO_SYNC_HOURS", "0")
    settings = Settings()
    tasks = asyncio.run(_spawn_background_tasks(settings))
    event_tasks = [t for t in tasks if t.get_name() == "periodic:Event sync"]
    assert len(event_tasks) == 1
    for task in tasks:
        task.cancel()


def test_duplicate_start_background_tasks_registration_skipped(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    monkeypatch.setenv("MAP_AUTO_SYNC_HOURS", "0")
    settings = Settings()

    async def _spawn_twice():
        first = start_background_tasks(settings)
        second = start_background_tasks(settings)
        return first, second

    first, second = asyncio.run(_spawn_twice())
    assert len(first) >= 1
    assert second == []
    for task in first:
        task.cancel()


@pytest.mark.asyncio
async def test_stop_background_tasks_cancels_scheduler(clear_settings_cache, monkeypatch):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    monkeypatch.setenv("MAP_AUTO_SYNC_HOURS", "0")
    settings = Settings()
    tasks = start_background_tasks(settings)
    await stop_background_tasks(tasks)
    assert all(task.cancelled() or task.done() for task in tasks)
    assert bg._background_tasks_started is False


@pytest.mark.asyncio
async def test_upsert_same_event_twice_updates_without_duplicate_create(monkeypatch):
    existing = Event(
        id=9,
        title="Концерт",
        starts_at=datetime(2026, 7, 10, 18, 0, tzinfo=timezone.utc),
        ends_at=None,
        region=EventRegion.PSKOV.value,
        category=EventCategory.CULTURE.value,
        is_published=True,
        source="vk",
        source_url="https://vk.com/wall-1_99",
    )
    create_mock = AsyncMock()
    update_mock = AsyncMock()

    monkeypatch.setattr(
        "app.services.event_sources.upsert.find_existing_event",
        AsyncMock(return_value=existing),
    )
    monkeypatch.setattr("app.services.event_sources.upsert.create_event", create_mock)
    monkeypatch.setattr("app.services.event_sources.upsert.update_event", update_mock)

    item = FetchedEvent(
        title="Концерт",
        description="Описание",
        starts_at=datetime(2026, 7, 10, 18, 0, tzinfo=timezone.utc),
        ends_at=None,
        location="Псков",
        region=EventRegion.PSKOV,
        category=EventCategory.CULTURE,
        source="vk",
        source_url="https://vk.com/wall-1_99",
    )
    db = MagicMock()
    first = await upsert_fetched_event(db, item)
    second = await upsert_fetched_event(db, item)
    assert first == "updated"
    assert second == "updated"
    create_mock.assert_not_called()
    assert update_mock.await_count == 2


def test_map_auto_sync_hours_default_unchanged(clear_settings_cache, monkeypatch):
    monkeypatch.delenv("MAP_AUTO_SYNC_HOURS", raising=False)
    settings = Settings()
    assert settings.MAP_AUTO_SYNC_HOURS == 6


def test_map_stats_ribbon_still_uses_map_interval_text():
    text = MAP_RIBBON.read_text(encoding="utf-8")
    assert "auto_sync_hours" in text
    assert "каждые" in text


def test_events_ribbon_uses_event_sync_hours_not_map_interval():
    text = EVENTS_RIBBON.read_text(encoding="utf-8")
    assert "event_sync_hours" in text
    assert "auto_sync_hours" not in text
    assert "каждые ${stats.event_sync_hours} ч" in text


@pytest.mark.asyncio
async def test_public_events_stats_exposes_event_sync_hours(
    clear_settings_cache, monkeypatch, db_session, api_client
):
    monkeypatch.setenv("EVENT_SYNC_INTERVAL_HOURS", "4")
    get_settings.cache_clear()
    response = await api_client.get("/api/v1/public/events/stats")
    assert response.status_code == 200
    assert response.json()["event_sync_hours"] == 4


def test_compose_prod_sets_event_sync_interval_four():
    compose = (REPO_ROOT / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert 'EVENT_SYNC_INTERVAL_HOURS: "4"' in compose
    assert 'MAP_AUTO_SYNC_HOURS: "0"' in compose


def test_module5_inventory_tests_still_present():
    assert (REPO_ROOT / "backend" / "tests" / "test_core_conflicts_inventory.py").is_file()


def test_category_emojis_preserved():
    text = FRONTEND_CONSTANTS.read_text(encoding="utf-8")
    for cat in ("gas", "school", "hospital"):
        assert f"{cat}:" in text


def test_leaflet_attribution_no_ukrainian_flag():
    text = MAP_ATTRIBUTION.read_text(encoding="utf-8")
    prefix_block = text.split("LEAFLET_ATTRIBUTION_PREFIX", 1)[1].split(";", 1)[0]
    assert "🇺🇦" not in prefix_block
    assert not NATIONAL_FLAG_EMOJI.search(prefix_block)
