import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import limiter
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.schemas.vk_mini_app import VkMiniAppAuthRequest, VkMiniAppAuthResponse
from app.services.vk.mini_app_auth import VkMiniAppAuthError, authenticate_vk_mini_app
from app.services.vk import get_welcome_keyboard, parse_vk_message, send_message
from app.services.vk.ai_mode import exit_ai_mode
from app.services.vk.command_router import (
    VkRouteContext,
    route_ai_message,
    route_complaint,
    route_free_chat,
    route_vk_message,
    route_welcome,
    send_fallback_message,
)
from app.services.vk.flows import handle_flow_message
from app.services.vk.moderation import process_incoming_moderation
from app.services.vk.voice import extract_audio_url, transcribe_audio_url

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/auth", response_model=VkMiniAppAuthResponse)
@limiter.limit("30/minute")
async def vk_mini_app_auth(
    request: Request,
    data: VkMiniAppAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange VK Mini App launch params for a portal JWT."""
    try:
        token, user = await authenticate_vk_mini_app(db, launch_params=data.launch_params)
        await db.commit()
        return VkMiniAppAuthResponse(access_token=token.access_token, user=user.model_dump())
    except VkMiniAppAuthError as exc:
        raise_http_for_service_error(exc)


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

    # Moderation: ban check + profanity/spam warnings
    if ctx.text.strip():
        mod = await process_incoming_moderation(db, ctx.from_id, ctx.peer_id, ctx.text)
        await db.commit()
        if not mod.allowed:
            if mod.message:
                await send_message(ctx.peer_id, mod.message)
            return PlainTextResponse("ok")

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
        await exit_ai_mode(db, ctx.peer_id)
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

    if await route_free_chat(ctx):
        return PlainTextResponse("ok")

    await send_fallback_message(ctx)
    return PlainTextResponse("ok")
