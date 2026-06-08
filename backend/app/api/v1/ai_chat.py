import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip
from app.core.rate_limit import limiter
from app.database import get_db
from app.schemas.ai import (
    AIStatusResponse,
    ChatRequest,
    ChatResponse,
    ImageRequest,
    ImageResponse,
    ModelsResponse,
    PaymentInfoResponse,
    UsageResponse,
)
from app.services.ai_status import get_ai_status
from app.services.ai_chat import (
    chat_with_ai,
    get_payment_info,
    get_usage_today,
    increment_usage,
    make_identifier,
)
from app.services.ai_image_store import image_media_type, image_path
from app.services.ai_media import CHAT_MODELS, IMAGE_MODELS, generate_image

router = APIRouter()
settings = get_settings()

AI_CAPABILITIES: list[str] = []


def _get_limit(source: str = "web") -> int:
    return settings.AI_VK_DAILY_LIMIT if source == "vk" else settings.AI_FREE_DAILY_LIMIT


@router.get("/status", response_model=AIStatusResponse)
async def ai_status():
    return AIStatusResponse(**get_ai_status())


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    return ModelsResponse(
        chat_models=CHAT_MODELS,
        image_models=IMAGE_MODELS,
        capabilities=AI_CAPABILITIES,
        status=get_ai_status(),
    )


@router.get("/payment-info", response_model=PaymentInfoResponse)
async def payment_info():
    return PaymentInfoResponse(**get_payment_info())


@router.get("/usage", response_model=UsageResponse)
async def get_usage(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    identifier = make_identifier(get_client_ip(request), request.headers.get("User-Agent"))
    used = await get_usage_today(db, identifier)
    limit = _get_limit()
    return UsageResponse(
        used=used,
        remaining=max(0, limit - used),
        daily_limit=limit,
        payment_info=get_payment_info(),
    )


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.AI_CHAT_RATE_LIMIT)
async def public_chat(
    data: ChatRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if len(data.message) > settings.AI_MAX_MESSAGE_LENGTH:
        raise HTTPException(status_code=400, detail="Сообщение слишком длинное")

    identifier = make_identifier(get_client_ip(request), request.headers.get("User-Agent"))
    used = await get_usage_today(db, identifier)
    limit = _get_limit()
    model_id = data.model or settings.GEMINI_MODEL

    if used >= limit:
        payment = get_payment_info()
        if payment["card_number"]:
            limit_reply = (
                f"🪶 Вы использовали {limit} бесплатных сообщений на сегодня.\n\n"
                f"ИИ-помощник работает за счёт добровольных пожертвований.\n\n"
                f"💳 Перевод: {payment['card_number']}\n"
                f"Получатель: {payment['card_holder']}\n"
                f"Сумма: от {payment['amount_suggested']} ₽\n\n"
                f"Завтра лимит обновится!"
            )
        else:
            limit_reply = (
                f"🪶 Вы использовали {limit} бесплатных сообщений на сегодня.\n\n"
                f"{payment['message']}\n\n"
                f"Завтра лимит обновится!"
            )
        return ChatResponse(
            reply=limit_reply,
            remaining=0,
            daily_limit=limit,
            limit_reached=True,
            payment_info=payment,
            model=model_id,
        )

    history = [{"role": m.role, "content": m.content} for m in data.history]
    reply = await chat_with_ai(data.message, history, model_id=model_id)
    new_count = await increment_usage(db, identifier, "web")

    return ChatResponse(
        reply=reply,
        remaining=max(0, limit - new_count),
        daily_limit=limit,
        limit_reached=False,
        model=model_id,
    )


@router.get("/images/{image_id}")
async def serve_generated_image(image_id: str):
    if not re.fullmatch(r"[a-f0-9]{32}", image_id):
        raise HTTPException(status_code=404, detail="Not found")
    path = image_path(image_id)
    if not path:
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type=image_media_type(path))


@router.post("/generate-image", response_model=ImageResponse)
@limiter.limit(settings.AI_IMAGE_RATE_LIMIT)
async def generate_image_endpoint(
    data: ImageRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    identifier = make_identifier(get_client_ip(request), request.headers.get("User-Agent"))
    used = await get_usage_today(db, identifier)
    limit = _get_limit()

    if used >= limit:
        raise HTTPException(status_code=429, detail="Дневной лимит ИИ исчерпан")

    result = await generate_image(data.prompt, data.model, data.width, data.height)
    if result.get("error"):
        return ImageResponse(
            url=None,
            model=data.model,
            prompt=data.prompt,
            error=result["error"],
        )

    await increment_usage(db, identifier, "web")
    return ImageResponse(**result)
