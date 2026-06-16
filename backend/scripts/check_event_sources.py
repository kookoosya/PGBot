#!/usr/bin/env python3
"""Print event source readiness (VK tokens, group count)."""

from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.constants.event_config import VK_EVENT_GROUPS
from app.services.event_sources.vk_group_resolver import resolve_vk_group_ids
from app.services.event_sources.vk_token_policy import vk_events_access_token, vk_wall_access_token


async def main() -> None:
    events_token = vk_events_access_token()
    resolved = await resolve_vk_group_ids([g.screen_name for g in VK_EVENT_GROUPS])
    wall_ready = sum(
        1 for gid in resolved.values() if vk_wall_access_token(group_id=gid)
    )
    payload = {
        "vk_groups_configured": len(VK_EVENT_GROUPS),
        "vk_groups_resolved": len(resolved),
        "vk_wall_readable_groups": wall_ready,
        "vk_events_token": bool(events_token),
        "status": "ready" if events_token else "needs_vk_events_token",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
