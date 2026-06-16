"""Tests for VK event import token policy."""

from app.services.event_sources.vk_token_policy import vk_wall_access_token


def test_wall_token_prefers_events_token(monkeypatch):
    from app.services.event_sources import vk_token_policy

    monkeypatch.setattr(vk_token_policy.settings, "VK_EVENTS_TOKEN", "user-token")
    monkeypatch.setattr(vk_token_policy.settings, "VK_GROUP_TOKEN", "group-token")
    monkeypatch.setattr(vk_token_policy.settings, "VK_GROUP_ID", 1)
    assert vk_wall_access_token(group_id=999) == "user-token"


def test_wall_token_group_fallback_for_own_group(monkeypatch):
    from app.services.event_sources import vk_token_policy

    monkeypatch.setattr(vk_token_policy.settings, "VK_EVENTS_TOKEN", "")
    monkeypatch.setattr(vk_token_policy.settings, "VK_GROUP_TOKEN", "group-token")
    monkeypatch.setattr(vk_token_policy.settings, "VK_GROUP_ID", 42)
    assert vk_wall_access_token(group_id=42) == "group-token"
    assert vk_wall_access_token(group_id=99) is None
