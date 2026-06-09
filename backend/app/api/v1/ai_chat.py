import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip
from app.core.rate_limit import limiter
from app.core.service_http import raise_http_for_service_error
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
from app.services.ai_image_store import image_media_type, image_path
from app.services.ai_media import CHAT_MODELS, IMAGE_MODELS
from app.services.ai_status import get_ai_status
from app.services.ai_chat import (
    AIValidationError,
    AILimitError,
    get_daily_limit,
    get_payment_info,
    get_usage_today,
    make_identifier,
    process_image_generation,
    process_public_chat,
    AI_CAPABILITIES,
)

router = APIRouter()
settings = get_settings()


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
    limit = get_daily_limit()
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
    identifier = make_identifier(get_client_ip(request), request.headers.get("User-Agent"))
    try:
        result = await process_public_chat(
            db,
            message=data.message,
            history=[{"role": message.role, "content": message.content} for message in data.history],
            model_id=data.model,
            identifier=identifier,
        )
    except AIValidationError as exc:
        raise_http_for_service_error(exc)
    return ChatResponse(**result)


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
    try:
        result = await process_image_generation(
            db,
            prompt=data.prompt,
            model=data.model,
            width=data.width,
            height=data.height,
            identifier=identifier,
        )
    except AILimitError as exc:
        raise_http_for_service_error(exc)
    return ImageResponse(**result)
