"""Маршрутизация входящих VK-сообщений: команды, жалобы, fallback."""

import logging

from app.services.issue.ingest import process_incoming_message
from app.services.vk.ai_mode import exit_ai_mode
from app.services.vk.commands import (
    AI_PRESERVE_MODE,
    COMMAND_ALIASES,
    COMMAND_HANDLERS,
    WELCOME_COMMAND,
    handle_classified_jobs,
    handle_routes_page,
    handle_subscribe_custom,
)
from app.services.vk.context import VkRouteContext
from app.services.vk.helpers import send_welcome, try_map_keywords
from app.services.vk.messages import box, looks_like_complaint

logger = logging.getLogger(__name__)


def _matches_routes_page(text_lower: str) -> bool:
    return text_lower.startswith("маршруты ") and text_lower.split()[-1].isdigit()


def _matches_classified_jobs(text_lower: str) -> bool:
    return text_lower in ("вакансия работа",) or text_lower == "вакансию"


def _matches_weather_query(text_lower: str) -> bool:
    if text_lower in COMMAND_ALIASES and COMMAND_ALIASES[text_lower] == "weather":
        return True
    if text_lower.startswith("погода"):
        return True
    return text_lower.startswith("прогноз")


def _matches_subscription_custom(text_lower: str) -> bool:
    return text_lower.startswith("подписка ") and text_lower.count(",") > 0


async def dispatch_command(ctx: VkRouteContext, command_id: str) -> None:
    """Вызвать обработчик команды; при необходимости выйти из AI-режима."""
    if command_id not in AI_PRESERVE_MODE:
        await exit_ai_mode(ctx.db, ctx.peer_id)
    await COMMAND_HANDLERS[command_id](ctx)


async def route_welcome(ctx: VkRouteContext) -> bool:
    """Welcome/menu triggers — must run before voice transcription."""
    command_id = COMMAND_ALIASES.get(ctx.text_lower)
    if command_id != WELCOME_COMMAND:
        return False
    await dispatch_command(ctx, WELCOME_COMMAND)
    return True


async def route_vk_message(ctx: VkRouteContext) -> bool:
    """Route menu commands and map keywords. Returns True if handled."""
    if _matches_routes_page(ctx.text_lower):
        await handle_routes_page(ctx)
        return True

    if _matches_classified_jobs(ctx.text_lower):
        await exit_ai_mode(ctx.db, ctx.peer_id)
        await handle_classified_jobs(ctx)
        return True

    if _matches_weather_query(ctx.text_lower):
        await dispatch_command(ctx, "weather")
        return True

    if _matches_subscription_custom(ctx.text_lower):
        await handle_subscribe_custom(ctx)
        return True

    command_id = COMMAND_ALIASES.get(ctx.text_lower)
    if command_id and command_id != WELCOME_COMMAND:
        await dispatch_command(ctx, command_id)
        return True

    if await try_map_keywords(ctx):
        return True

    return False


async def route_complaint(ctx: VkRouteContext) -> bool:
    """Process complaint text or photo attachments."""
    if ctx.parsed is None:
        return False

    complaint_text = ctx.text.strip()
    if ctx.parsed.get("photos") and len(complaint_text) < 5:
        complaint_text = "Фото проблемы (VK)"

    if not looks_like_complaint(complaint_text) and not ctx.parsed.get("photos"):
        return False

    try:
        await process_incoming_message(
            ctx.db,
            text=complaint_text,
            vk_id=ctx.from_id,
            peer_id=ctx.peer_id,
            message_id=ctx.parsed.get("message_id"),
            photos=ctx.parsed.get("photos"),
        )
    except Exception as e:
        logger.exception("Error processing VK message: %s", e)
        await send_welcome(ctx, "Ошибка. Напишите «помощь».")
    return True


async def send_fallback_message(ctx: VkRouteContext) -> None:
    """Default reply when nothing else matched."""
    await send_welcome(
        ctx,
        box(
            "Не понял сообщение",
            "Напишите свободно — отвечу как помощник.\n"
            "Или выберите кнопку меню:\n"
            "🤖 ИИ · ⚠️ Жалобы · 🗺 Карта\n\n"
            "«Меню» — разделы портала",
        ),
    )
