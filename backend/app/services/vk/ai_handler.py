"""Обработка AI-режима VK-бота: лимиты, история, авто-детект вопросов."""

from app.config import get_settings
from app.services.ai_chat import (
    chat_with_ai,
    get_payment_info,
    get_usage_today,
    increment_usage,
    make_identifier,
)
from app.services.vk.ai_mode import enter_ai_mode, is_ai_mode
from app.services.vk.context import VkRouteContext
from app.services.vk.helpers import send_ai
from app.services.vk.ai_history import append_ai_turn, get_ai_history
from app.services.vk_messages import ai_limit_text, ai_reply_footer, looks_like_ai_question, looks_like_complaint

settings = get_settings()


async def process_vk_ai(ctx: VkRouteContext, text: str) -> None:
    """Отправить сообщение в ИИ с учётом лимита и истории диалога."""
    identifier = make_identifier(None, None, vk_id=ctx.from_id)
    used = await get_usage_today(ctx.db, identifier)
    limit = settings.AI_VK_DAILY_LIMIT

    if used >= limit:
        await send_ai(ctx, ai_limit_text(get_payment_info()))
        return

    history = await get_ai_history(ctx.db, ctx.peer_id)
    reply = await chat_with_ai(text, history=history)
    await increment_usage(ctx.db, identifier, "vk")
    await append_ai_turn(ctx.db, ctx.peer_id, text, reply)
    remaining = limit - used - 1
    await send_ai(ctx, f"{reply}{ai_reply_footer(remaining)}")


async def route_ai_message(ctx: VkRouteContext) -> bool:
    """Обработать активный AI-режим или авто-распознанный вопрос."""
    if await is_ai_mode(ctx.db, ctx.peer_id) or ctx.text_lower.startswith("ии:"):
        msg = ctx.text[3:].strip() if ctx.text_lower.startswith("ии:") else ctx.text
        if len(msg) < 2:
            await send_ai(ctx, "Напишите вопрос — отвечу в режиме ИИ.")
        else:
            await process_vk_ai(ctx, msg)
        return True

    if looks_like_ai_question(ctx.text) and not looks_like_complaint(ctx.text):
        await enter_ai_mode(ctx.db, ctx.peer_id)
        await process_vk_ai(ctx, ctx.text)
        return True

    return False


async def route_free_chat(ctx: VkRouteContext) -> bool:
    """Свободный диалог через ИИ, если сообщение не команда и не жалоба."""
    from app.services.vk.commands import COMMAND_ALIASES

    text = ctx.text.strip()
    if len(text) < 4:
        return False
    if ctx.text_lower in COMMAND_ALIASES:
        return False
    if looks_like_complaint(text):
        return False
    if len(text.split()) == 1 and len(text) < 12:
        return False

    await enter_ai_mode(ctx.db, ctx.peer_id)
    await process_vk_ai(
        ctx,
        "Ты — дружелюбный помощник портала Пушкинские Горы. "
        "Отвечай кратко и по делу о посёлке, туризме, услугах и событиях. "
        f"Вопрос пользователя: {text}",
    )
    return True
