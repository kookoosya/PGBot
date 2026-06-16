"""Tests for upsert ends_at sync on update."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import EventCategory, EventRegion
from app.models.event import Event
from app.services.event.admin import update_event
from app.services.event.schemas import EventUpdateInput
from app.services.event_sources.base import FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event


@pytest.mark.asyncio
async def test_update_event_clears_invalid_ends_at_with_sync_flag():
    event = Event(
        id=1,
        title="Test",
        starts_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 19, 20, 0, tzinfo=timezone.utc),
        region=EventRegion.PSKOV.value,
        category=EventCategory.CULTURE.value,
        is_published=True,
    )
    db = MagicMock()
    db.flush = AsyncMock()
    await update_event(
        db,
        event,
        EventUpdateInput(
            starts_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
            ends_at=None,
            sync_ends_at=True,
        ),
    )
    assert event.ends_at is None


@pytest.mark.asyncio
async def test_upsert_update_passes_sync_ends_at(monkeypatch):
    existing = Event(
        id=5,
        title="VK event",
        starts_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 19, 20, 0, tzinfo=timezone.utc),
        region=EventRegion.PUSHKIN_GORY.value,
        category=EventCategory.CULTURE.value,
        is_published=True,
    )
    captured: dict = {}

    async def fake_update(db, event, data, *, actor_id=None):
        captured["sync_ends_at"] = data.sync_ends_at
        captured["ends_at"] = data.ends_at

    monkeypatch.setattr(
        "app.services.event_sources.upsert.find_existing_event",
        AsyncMock(return_value=existing),
    )
    monkeypatch.setattr("app.services.event_sources.upsert.update_event", fake_update)

    item = FetchedEvent(
        title="VK event",
        description=None,
        starts_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 19, 20, 0, tzinfo=timezone.utc),
        location="Пушкинские Горы",
        region=EventRegion.PUSHKIN_GORY,
        category=EventCategory.CULTURE,
        source="vk",
        source_url="https://vk.com/wall-1_2",
    )
    await upsert_fetched_event(MagicMock(), item)
    assert captured["sync_ends_at"] is True
    assert captured["ends_at"] is None
