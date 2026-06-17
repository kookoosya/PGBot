"""Unit tests for mixed public events feed."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.models.enums import EventRegion
from app.models.event import Event
from app.services.event.public import load_mixed_public_events


def _event(event_id: int, *, region: str, title: str) -> Event:
    return Event(
        id=event_id,
        title=title,
        starts_at=datetime(2026, 6, 20, 12, 0, tzinfo=timezone.utc),
        region=region,
        category="culture",
        source="manual",
        is_published=True,
    )


@pytest.mark.asyncio
@patch("app.services.event.public._load_upcoming_grouped", new_callable=AsyncMock)
@patch("app.services.event.public.collapse_festival_program_feed", side_effect=lambda events: events)
async def test_load_mixed_public_events_pushkin_first(mock_collapse, mock_load):
    pushkin = [_event(1, region=EventRegion.PUSHKIN_GORY.value, title="Ярмарка")]
    pskov = [_event(2, region=EventRegion.PSKOV.value, title="Лекция")]
    cinema = [_event(3, region=EventRegion.PSKOV.value, title="«Фильм»")]

    async def _side_effect(db, *, now, limit, region=None, category=None, exclude_category=None):
        if region == EventRegion.PUSHKIN_GORY:
            return pushkin
        if category is not None:
            return cinema
        return pskov

    mock_load.side_effect = _side_effect

    result = await load_mixed_public_events(AsyncMock(), limit=10)
    assert [event.id for event in result] == [1, 2, 3]
