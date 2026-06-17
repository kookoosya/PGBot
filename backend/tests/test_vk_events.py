"""Tests for VK events message formatting."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import EventRegion
from app.services.vk import digest as digest_mod
from app.services.vk.events import format_events_digest_lines, format_events_message
from tests.helpers.db_factories import create_event

pytestmark_postgres = pytest.mark.postgres


@pytest.mark.asyncio
@patch("app.services.vk.events.get_upcoming_events", new_callable=AsyncMock)
async def test_format_events_message_empty(mock_get):
    mock_get.return_value = []
    msg = await format_events_message(AsyncMock())
    assert "пуста" in msg.lower()
    assert "/events" in msg
    mock_get.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.vk.events.get_upcoming_events", new_callable=AsyncMock)
async def test_format_events_message_lists_items(mock_get):
    starts = datetime(2026, 7, 1, 18, 0, tzinfo=timezone.utc)
    mock_get.return_value = [
        SimpleNamespace(
            title="Концерт у музея",
            starts_at=starts,
            location="Пушкиногорье",
            category="culture",
            region="pushkin_gory",
        ),
    ]
    msg = await format_events_message(AsyncMock(), limit=4)
    assert "Концерт у музея" in msg
    assert "Культура" in msg
    assert "Пушкинские Горы" in msg
    assert "01.07.2026" in msg


@pytest.mark.asyncio
@patch("app.services.vk.events.get_upcoming_events", new_callable=AsyncMock)
async def test_format_events_digest_lines_empty(mock_get):
    mock_get.return_value = []
    assert await format_events_digest_lines(AsyncMock()) == []


@pytest.mark.asyncio
@patch("app.services.vk.events.get_upcoming_events", new_callable=AsyncMock)
async def test_format_events_digest_lines_preview(mock_get):
    starts = datetime(2026, 8, 15, 19, 30, tzinfo=timezone.utc)
    mock_get.return_value = [
        SimpleNamespace(title="Кино в Пскове", starts_at=starts),
    ]
    lines = await format_events_digest_lines(AsyncMock(), limit=2)
    assert lines[0] == "📅 Ближайшие события:"
    assert "Кино в Пскове" in lines[1]
    assert lines[-1].endswith("/events")


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_format_events_message_db(db_session):
    await create_event(
        db_session,
        title="Ярмарка на площади",
        region=EventRegion.PUSHKIN_GORY,
        starts_at=datetime.now(timezone.utc) + timedelta(days=2),
    )
    msg = await format_events_message(db_session)
    assert "Ярмарка на площади" in msg
    assert "/events" in msg


@pytest.mark.asyncio
@patch.object(digest_mod, "DIGEST_HOUR_UTC", 12)
@patch("app.services.vk.digest.format_events_digest_lines", new_callable=AsyncMock)
@patch("app.services.vk.digest.format_weather_digest_lines", return_value=[])
@patch("app.services.vk.digest.datetime")
@patch("app.services.vk.digest.send_message", new_callable=AsyncMock)
@patch("app.services.vk.digest.get_weather", new_callable=AsyncMock)
async def test_digest_includes_events_block(
    mock_weather, mock_send, mock_datetime, _fmt, mock_events
):
    fixed_now = datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = fixed_now
    mock_weather.return_value = object()
    mock_events.return_value = [
        "📅 Ближайшие события:",
        "• 10.06.2026 · 19:00 — Спектакль",
        "→ https://example.com/events",
    ]

    sub = SimpleNamespace(peer_id=100, categories="all", last_digest_at=None)

    db = AsyncMock()
    subs_result = MagicMock()
    subs_result.scalars.return_value.all.return_value = [sub]
    ads_result = MagicMock()
    ads_result.scalars.return_value.all.return_value = []
    count_result = MagicMock()
    count_result.scalar.return_value = 0
    db.execute = AsyncMock(side_effect=[subs_result, ads_result, count_result])
    db.flush = AsyncMock()

    sent = await digest_mod.send_daily_digest(db)
    assert sent == 1
    message = mock_send.await_args.args[1]
    assert "Ближайшие события" in message
    assert "Спектакль" in message
