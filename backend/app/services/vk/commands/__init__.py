"""VK bot command handlers registry."""

from app.services.vk.context import CommandHandler

from . import handlers
from .aliases import COMMAND_ALIASES

AI_PRESERVE_MODE = handlers.AI_PRESERVE_MODE
WELCOME_COMMAND = handlers.WELCOME_COMMAND

COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "welcome": handlers.handle_welcome,
    "classifieds": handlers.handle_classifieds,
    "services": handlers.handle_services,
    "subscribe_all": handlers.handle_subscribe_all,
    "subscribe_jobs": handlers.handle_subscribe_jobs,
    "subscribe_preset": handlers.handle_subscribe_preset,
    "subscribe_custom": handlers.handle_subscribe_custom,
    "unsubscribe": handlers.handle_unsubscribe,
    "ai_enter": handlers.handle_ai_enter,
    "ai_examples": handlers.handle_ai_examples,
    "ai_images": handlers.handle_ai_images,
    "ai_exit": handlers.handle_ai_exit,
    "jobs": handlers.handle_jobs,
    "routes": handlers.handle_routes,
    "map_report": handlers.handle_map_report,
    "classified_add": handlers.handle_classified_add,
    "classified_jobs": handlers.handle_classified_jobs,
    "wish": handlers.handle_wish,
    "taxi": handlers.handle_taxi,
    "complaints_info": handlers.handle_complaints_info,
    "register": handlers.handle_register,
    "site": handlers.handle_site,
    "map": handlers.handle_map,
    "my_issues": handlers.handle_my_issues,
    "cabinet": handlers.handle_cabinet,
    "events": handlers.handle_events,
    "cinema": handlers.handle_cinema,
    "weather": handlers.handle_weather,
    "help": handlers.handle_help,
}

__all__ = [
    "AI_PRESERVE_MODE",
    "COMMAND_ALIASES",
    "COMMAND_HANDLERS",
    "WELCOME_COMMAND",
    "handle_classified_jobs",
    "handle_routes_page",
    "handle_subscribe_custom",
]

# Re-export handlers used by message_router keyword fallbacks.
handle_classified_jobs = handlers.handle_classified_jobs
handle_routes_page = handlers.handle_routes_page
handle_subscribe_custom = handlers.handle_subscribe_custom
