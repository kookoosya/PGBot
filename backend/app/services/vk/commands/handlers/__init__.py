"""VK bot command handlers."""

from .ai import handle_ai_enter, handle_ai_examples, handle_ai_exit, handle_ai_images
from .classifieds import (
    handle_classified_add,
    handle_classified_jobs,
    handle_classifieds,
    handle_jobs,
    handle_wish,
)
from .common import AI_PRESERVE_MODE, WELCOME_COMMAND
from .issues import handle_my_issues
from .map_nav import handle_map_report, handle_routes, handle_routes_page, handle_taxi
from .portal import (
    handle_cabinet,
    handle_complaints_info,
    handle_events,
    handle_help,
    handle_map,
    handle_register,
    handle_services,
    handle_site,
    handle_weather,
)
from .subscriptions import (
    handle_subscribe_all,
    handle_subscribe_custom,
    handle_subscribe_jobs,
    handle_subscribe_preset,
    handle_unsubscribe,
)
from .welcome import handle_welcome

__all__ = [
    "AI_PRESERVE_MODE",
    "WELCOME_COMMAND",
    "handle_ai_enter",
    "handle_ai_examples",
    "handle_ai_exit",
    "handle_ai_images",
    "handle_cabinet",
    "handle_classified_add",
    "handle_classified_jobs",
    "handle_classifieds",
    "handle_complaints_info",
    "handle_events",
    "handle_help",
    "handle_jobs",
    "handle_map",
    "handle_map_report",
    "handle_my_issues",
    "handle_register",
    "handle_routes",
    "handle_routes_page",
    "handle_services",
    "handle_site",
    "handle_subscribe_all",
    "handle_subscribe_custom",
    "handle_subscribe_jobs",
    "handle_subscribe_preset",
    "handle_unsubscribe",
    "handle_taxi",
    "handle_weather",
    "handle_welcome",
    "handle_wish",
]
