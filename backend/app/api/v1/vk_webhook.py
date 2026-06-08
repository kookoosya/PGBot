import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.vk_command_router import (
    VkRouteContext,
    route_ai_message,
    route_complaint,
    route_vk_message,
    route_welcome,
    send_fallback_message,
)
from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.services.ai_mode import exit_ai_mode
from app.services.vk import get_welcome_keyboard, parse_vk_message, send_message
from app.services.vk_flows import handle_flow_message
from app.services.vk_voice import extract_audio_url, transcribe_audio_url

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/callback")
@limiter.limit(settings.VK_CALLBACK_RATE_LIMIT)
async def vk_callback(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    body: dict[str, Any] = await request.json()
    event_type = body.get("type")

    if event_type == "confirmation":
        return PlainTextResponse(settings.VK_CONFIRMATION_CODE)

    if event_type != "message_new":
        return PlainTextResponse("ok")

    if settings.VK_GROUP_TOKEN:
        if not settings.VK_SECRET_KEY or body.get("secret") != settings.VK_SECRET_KEY:
            logger.warning("VK webhook rejected: invalid or missing secret")
            return PlainTextResponse("ok")

    parsed = parse_vk_message(body)
    if not parsed:
        return PlainTextResponse("ok")

    ctx = VkRouteContext.from_parsed(db, parsed)

    # Welcome before voice — preserves original processing order
    if await route_welcome(ctx):
        return PlainTextResponse("ok")

    # Voice → text (may update ctx.text for downstream routing)
    audio_url = extract_audio_url(parsed.get("attachments") or [])
    if audio_url:
        transcribed = await transcribe_audio_url(audio_url)
        if transcribed:
            ctx.update_text(transcribed)
            await send_message(ctx.peer_id, f"🎤 Распознано: «{transcribed[:200]}»")
        elif not parsed["text"].strip():
            await send_message(
                ctx.peer_id,
                "Не удалось распознать голосовое. Напишите текстом или повторите.",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

    # Multi-step flows (classified, wish, map report, …)
    flow_reply = await handle_flow_message(db, ctx.peer_id, ctx.from_id, ctx.text)
    if flow_reply:
        exit_ai_mode(ctx.peer_id)
        await send_message(ctx.peer_id, flow_reply, keyboard=get_welcome_keyboard())
        return PlainTextResponse("ok")

    # Menu commands, map keywords
    if await route_vk_message(ctx):
        return PlainTextResponse("ok")

    # AI mode (active or auto-detected question)
    if await route_ai_message(ctx):
        return PlainTextResponse("ok")

    # Complaints with text or photo
    if await route_complaint(ctx):
        return PlainTextResponse("ok")

    await send_fallback_message(ctx)
    return PlainTextResponse("ok")
