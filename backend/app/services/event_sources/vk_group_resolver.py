"""Resolve VK community screen names to numeric IDs (API 5.199+)."""

from __future__ import annotations

import logging
from typing import Any

from app.constants.event_config import VK_EVENT_GROUPS
from app.services.event_sources.vk_token_policy import vk_events_access_token
from app.services.vk import vk_api_call

logger = logging.getLogger(__name__)

_BATCH_SIZE = 400


def normalize_group_identifier(screen_name: str) -> str:
    """Prepare identifier for groups.getById (club123 → 123)."""
    name = screen_name.strip()
    if name.startswith("club") and name[4:].isdigit():
        return name[4:]
    return name


def extract_groups_from_response(response: Any) -> list[dict]:
    """Parse groups.getById response (array legacy or {groups, profiles} in 5.199+)."""
    if isinstance(response, list):
        return [item for item in response if isinstance(item, dict)]
    if isinstance(response, dict):
        groups = response.get("groups")
        if isinstance(groups, list):
            return [item for item in groups if isinstance(item, dict)]
        if "id" in response:
            return [response]
    return []


def _index_groups(groups: list[dict]) -> dict[str, int]:
    """Map screen_name / string id → numeric group id."""
    index: dict[str, int] = {}
    for group in groups:
        gid = group.get("id")
        if gid is None:
            continue
        numeric = int(gid)
        index[str(numeric)] = numeric
        screen = group.get("screen_name")
        if screen:
            index[str(screen).lower()] = numeric
    return index


async def resolve_vk_group_ids(screen_names: list[str]) -> dict[str, int]:
    """Resolve many VK groups in batched groups.getById calls."""
    if not screen_names:
        return {}

    identifiers: dict[str, str] = {
        screen_name: normalize_group_identifier(screen_name)
        for screen_name in screen_names
    }
    unique_identifiers = list(dict.fromkeys(identifiers.values()))
    index: dict[str, int] = {}

    for offset in range(0, len(unique_identifiers), _BATCH_SIZE):
        chunk = unique_identifiers[offset : offset + _BATCH_SIZE]
        token = vk_events_access_token()
        if not token:
            logger.warning("VK events token not configured")
            break
        try:
            response = await vk_api_call(
                "groups.getById",
                {"group_ids": ",".join(chunk)},
                token=vk_events_access_token(),
            )
        except Exception:
            logger.warning("VK groups.getById failed for chunk", exc_info=True)
            continue
        index.update(_index_groups(extract_groups_from_response(response)))

    resolved: dict[str, int] = {}
    fallbacks = {g.screen_name: g.group_id for g in VK_EVENT_GROUPS if g.group_id > 0}
    for screen_name, identifier in identifiers.items():
        gid = index.get(identifier) or index.get(identifier.lower())
        if not gid and screen_name in fallbacks:
            gid = fallbacks[screen_name]
        if gid:
            resolved[screen_name] = gid
        else:
            logger.warning("VK group not resolved: %s (identifier=%s)", screen_name, identifier)

    return resolved
