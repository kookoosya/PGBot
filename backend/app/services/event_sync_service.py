"""VK event sync — backward-compatible re-exports.

New code should use ``app.services.event_sources``.
"""

from app.services.event_sources.base import EventSyncResult
from app.services.event_sources.text_utils import (
    infer_category_from_text,
    parse_event_datetime,
)
from app.services.event_sources.vk_source import (
    sync_all_vk_event_sources,
    sync_events_from_vk,
)

__all__ = [
    "EventSyncResult",
    "infer_category_from_text",
    "parse_event_datetime",
    "sync_all_vk_event_sources",
    "sync_events_from_vk",
]
