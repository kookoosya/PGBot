"""Tests for VK group ID resolution (API 5.199+ response format)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.event_sources.vk_group_resolver import (
    extract_groups_from_response,
    normalize_group_identifier,
    resolve_vk_group_ids,
)


def test_normalize_club_prefix():
    assert normalize_group_identifier("club166260004") == "166260004"
    assert normalize_group_identifier("pushkinogorie") == "pushkinogorie"


def test_extract_groups_legacy_array():
    response = [{"id": 123, "screen_name": "test"}]
    assert extract_groups_from_response(response)[0]["id"] == 123


def test_extract_groups_api_5199_object():
    response = {
        "groups": [{"id": 456, "screen_name": "pushkinogorie"}],
        "profiles": [],
    }
    groups = extract_groups_from_response(response)
    assert len(groups) == 1
    assert groups[0]["id"] == 456


@pytest.mark.asyncio
async def test_resolve_vk_group_ids_batch():
    mock_response = {
        "groups": [
            {"id": 100, "screen_name": "pushkinogorie"},
            {"id": 166260004, "screen_name": "club166260004"},
        ],
        "profiles": [],
    }
    with patch(
        "app.services.event_sources.vk_group_resolver.vk_api_call",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        resolved = await resolve_vk_group_ids(["pushkinogorie", "club166260004"])

    assert resolved["pushkinogorie"] == 100
    assert resolved["club166260004"] == 166260004
