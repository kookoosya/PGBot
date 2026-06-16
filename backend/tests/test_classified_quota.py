"""Unit tests for classified placement quota."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.classified.quota import get_classified_quota


@pytest.mark.asyncio
async def test_quota_without_phone_returns_free_placement():
    db = AsyncMock()
    quota = await get_classified_quota(db, phone=None)
    assert quota["requires_payment"] is False
    assert quota["free_used"] == 0


@pytest.mark.asyncio
async def test_quota_counts_existing_ads(monkeypatch):
    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar.return_value = 2
    db.execute = AsyncMock(return_value=execute_result)

    quota = await get_classified_quota(db, phone="+79001112233")
    assert quota["free_used"] == 2
    assert quota["requires_payment"] is False
