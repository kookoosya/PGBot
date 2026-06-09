"""VK Callback API — тонкий HTTP-слой (логика в app.services.vk_webhook)."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.services.vk import parse_vk_message
from app.services.vk_webhook import handle_message_new

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

    if event_type == "message_new":
        if settings.VK_GROUP_TOKEN:
            if not settings.VK_SECRET_KEY or body.get("secret") != settings.VK_SECRET_KEY:
                logger.warning("VK webhook rejected: invalid or missing secret")
                return PlainTextResponse("ok")

        parsed = parse_vk_message(body)
        if not parsed:
            return PlainTextResponse("ok")

        await handle_message_new(db, parsed)

    return PlainTextResponse("ok")
