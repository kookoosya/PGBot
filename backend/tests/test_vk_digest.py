"""Unit tests for VK daily digest category matching."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import ClassifiedCategory
from app.services.vk import digest as digest_mod


@pytest.mark.asyncio
@patch.object(digest_mod, "DIGEST_HOUR_UTC", 12)
@patch("app.services.vk.digest.format_weather_digest_lines", return_value=[])
@patch("app.services.vk.digest.datetime")
@patch("app.services.vk.digest.send_message", new_callable=AsyncMock)
@patch("app.services.vk.digest.get_weather", new_callable=AsyncMock)
async def test_digest_sends_zero_matching_ads_message(
    mock_weather, mock_send, mock_datetime, _fmt
):
    fixed_now = datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = fixed_now
    mock_weather.return_value = object()

    jobs_ad = SimpleNamespace(
        category=ClassifiedCategory.JOB_TOURISM,
        title="Гид",
        description="Работа",
        created_at=fixed_now,
    )
    sub = SimpleNamespace(
        peer_id=100,
        categories="firewood",
        last_digest_at=None,
    )

    db = AsyncMock()
    subs_result = MagicMock()
    subs_result.scalars.return_value.all.return_value = [sub]
    ads_result = MagicMock()
    ads_result.scalars.return_value.all.return_value = [jobs_ad]
    count_result = MagicMock()
    count_result.scalar.return_value = 1
    db.execute = AsyncMock(side_effect=[subs_result, ads_result, count_result])
    db.flush = AsyncMock()

    sent = await digest_mod.send_daily_digest(db)
    assert sent == 1
    mock_send.assert_awaited_once()
    message = mock_send.await_args.args[1]
    assert "0 по вашей подписке" in message
