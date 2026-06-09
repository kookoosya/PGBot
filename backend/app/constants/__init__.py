"""Domain configuration constants shared across services."""

from app.constants.event_config import (
    EVENT_CATEGORY_KEYWORDS,
    EVENT_REGION_LABELS,
    KUDAGO_CATEGORY_MAP,
    KUDAGO_LOCATION_PRESETS,
    VK_EVENT_SOURCE_PRESETS,
)
from app.constants.issue_config import JKH_CATEGORIES
from app.constants.map_config import MAP_FILTER_MODES, MapFilterMode, get_map_filter_modes
from app.constants.visit_config import PAGE_LABELS
from app.constants.vk_config import SUBSCRIPTION_ALIASES, SUBSCRIPTION_PRESETS

__all__ = [
    "EVENT_CATEGORY_KEYWORDS",
    "EVENT_REGION_LABELS",
    "KUDAGO_CATEGORY_MAP",
    "KUDAGO_LOCATION_PRESETS",
    "JKH_CATEGORIES",
    "MAP_FILTER_MODES",
    "MapFilterMode",
    "PAGE_LABELS",
    "SUBSCRIPTION_ALIASES",
    "SUBSCRIPTION_PRESETS",
    "VK_EVENT_SOURCE_PRESETS",
    "get_map_filter_modes",
]
