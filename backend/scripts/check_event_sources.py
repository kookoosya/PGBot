#!/usr/bin/env python3
"""Print event source readiness (VK tokens, group count, wall probe)."""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.constants.event_config import VK_EVENT_GROUPS
from app.models.enums import EventRegion
from app.services.event_sources.vk_group_resolver import resolve_vk_group_ids
from app.services.event_sources.vk_source import _fetch_wall_posts
from app.services.event_sources.vk_token_policy import (
    vk_events_access_token,
    vk_wall_access_token,
    vk_wall_health_status,
)


async def main() -> None:
    health = vk_wall_health_status()
    events_token = vk_events_access_token()
    resolved = await resolve_vk_group_ids([g.screen_name for g in VK_EVENT_GROUPS])
    wall_ready = sum(
        1 for gid in resolved.values() if vk_wall_access_token(group_id=gid)
    )

    probe_group = None
    probe_posts = 0
    pushkin_presets = [g for g in VK_EVENT_GROUPS if g.region == EventRegion.PUSHKIN_GORY]
    if pushkin_presets:
        preset = pushkin_presets[0]
        group_id = resolved.get(preset.screen_name) or preset.group_id
        if group_id and vk_wall_access_token(group_id=group_id):
            probe_group = preset.screen_name
            probe_posts = len(await _fetch_wall_posts(group_id, count=3))

    payload = {
        "vk_groups_configured": len(VK_EVENT_GROUPS),
        "vk_groups_resolved": len(resolved),
        "vk_wall_readable_groups": wall_ready,
        "vk_events_token": bool(events_token),
        "vk_wall_health": health,
        "vk_wall_probe_group": probe_group,
        "vk_wall_probe_posts": probe_posts,
        "status": health if health != "group_token_only" else "needs_vk_events_token",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
