"""Tests for admin event sources overview."""

import pytest

from app.services.event_sources.admin_overview import (
    SOURCE_LABELS,
    _source_health,
    _token_hint,
    build_event_sources_overview,
)


def test_source_health_mapping():
    health = {"vk_wall": "group_token_only", "timepad": "needs_token", "proculture": "ready"}
    assert _source_health("vk", health) == "group_token_only"
    assert _source_health("timepad", health) == "needs_token"
    assert _source_health("pushkinland", health) == "ready"


def test_token_hint_for_vk_group_token():
    hint = _token_hint("vk", "group_token_only")
    assert hint is not None
    assert "VK_EVENTS_TOKEN" in hint


def test_token_hint_ready_is_none():
    assert _token_hint("timepad", "ready") is None


def test_source_labels_cover_core_sources():
    for name in ("vk", "pushkinland", "timepad", "proculture", "orbilet"):
        assert name in SOURCE_LABELS


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_build_event_sources_overview(db_session):
    payload = await build_event_sources_overview(db_session)
    assert payload["total_published"] >= 0
    assert len(payload["sources"]) >= 10
    ids = {item["id"] for item in payload["sources"]}
    assert "vk" in ids
    assert "pushkinland" in ids
    assert "event_sources_health" in payload
