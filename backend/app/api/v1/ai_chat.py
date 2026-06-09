from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip, get_current_user, get_optional_user
from app.core.rate_limit import limiter
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.user import User
from app.schemas.ai import (
    AIAccessResponse,
    AIPlansResponse,
    AIPaymentStatusResponse,
    AIStatusResponse,
    AISubscribeRequest,
    AISubscribeResponse,
    ChatRequest,
    ChatResponse,
    ImageRequest,
    ImageResponse,
    ModelsResponse,
    PaymentInfoResponse,
    UsageResponse,
)
from app.services.ai_image_store import image_media_type, image_path
from app.services.ai_media import IMAGE_MODELS, get_chat_models
from app.services.ai_status import get_ai_status
from app.services.ai_entitlement_service import public_plans_payload, resolve_ai_access
from app.services.ai_chat import (
    AIValidationError,
    AILimitError,
    AI_CAPABILITIES,
    get_payment_info,
    get_usage_today,
    make_identifier,
    process_image_generation,
    process_public_chat,
)
from app.services.ai_payment_service import (
    AIPaymentError,
    create_subscription_payment,
    get_latest_user_order,
    process_yookassa_webhook,
    sync_order_by_id,
    yookassa_enabled,
)
from app.services.ai_plans import plan_by_id
import re

router = APIRouter()
settings = get_settings()


def _web_identifier(request: Request, user: User | None) -> str:
    return make_identifier(
        get_client_ip(request),
        request.headers.get("User-Agent"),
        user_id=user.id if user else None,
    )


@router.get("/status", response_model=AIStatusResponse)
async def ai_status():
    return AIStatusResponse(**get_ai_status())


@router.get("/plans", response_model=AIPlansResponse)
async def ai_plans():
    payload = public_plans_payload()
    return AIPlansResponse(**payload)


@router.get("/access", response_model=AIAccessResponse)
async def ai_access(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    identifier = _web_identifier(request, user)
    access = await resolve_ai_access(db, user=user, web_identifier=identifier)
    await db.commit()
    used = await get_usage_today(db, identifier)
    limit = access["daily_limit"]
    return AIAccessResponse(
        **access,
        used=used,
        remaining=max(0, limit - used),
    )


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    return ModelsResponse(
        chat_models=get_chat_models(),
        image_models=IMAGE_MODELS,
        capabilities=AI_CAPABILITIES,
        status=get_ai_status(),
    )


@router.get("/payment-info", response_model=PaymentInfoResponse)
async def payment_info():
    info = get_payment_info()
    info["auto_payment_available"] = yookassa_enabled()
    return PaymentInfoResponse(**info)


@router.post("/subscribe", response_model=AISubscribeResponse)
async def ai_subscribe(
    data: AISubscribeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        order = await create_subscription_payment(db, user=user, plan_id=data.plan_id)
        await db.commit()
    except AIPaymentError as exc:
        raise_http_for_service_error(exc)

    plan = plan_by_id(order.plan_id)
    if not order.confirmation_url:
        raise HTTPException(status_code=502, detail="Платёж создан без ссылки на оплату")

    return AISubscribeResponse(
        order_id=order.id,
        payment_url=order.confirmation_url,
        amount_rub=order.amount_rub,
        plan_id=order.plan_id,
        plan_name=plan.name if plan else order.plan_id,
    )


@router.post("/payment/webhook")
async def ai_payment_webhook(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ok = await process_yookassa_webhook(db, payload)
    if ok:
        await db.commit()
    return {"ok": ok}


@router.get("/payment/status/{order_id}", response_model=AIPaymentStatusResponse)
async def ai_payment_status(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    order = await sync_order_by_id(db, order_id, user_id=user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    await db.commit()
    return AIPaymentStatusResponse(
        order_id=order.id,
        status=order.status,
        plan_id=order.plan_id,
        entitlement_id=order.entitlement_id,
        activated=order.status == "succeeded",
    )


@router.get("/payment/latest", response_model=AIPaymentStatusResponse | None)
async def ai_payment_latest(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    order = await get_latest_user_order(db, user.id)
    if not order:
        return None
    order = await sync_order_by_id(db, order.id, user_id=user.id)
    await db.commit()
    assert order is not None
    return AIPaymentStatusResponse(
        order_id=order.id,
        status=order.status,
        plan_id=order.plan_id,
        entitlement_id=order.entitlement_id,
        activated=order.status == "succeeded",
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
):
    identifier = _web_identifier(request, user)
    access = await resolve_ai_access(db, user=user, web_identifier=identifier)
    used = await get_usage_today(db, identifier)
    limit = access["daily_limit"]
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
    user: Annotated[User | None, Depends(get_optional_user)],
):
    identifier = _web_identifier(request, user)
    try:
        result = await process_public_chat(
            db,
            message=data.message,
            history=[{"role": message.role, "content": message.content} for message in data.history],
            model_id=data.model,
            identifier=identifier,
            user=user,
            chat_mode=data.chat_mode,
        )
        await db.commit()
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
    user: Annotated[User | None, Depends(get_optional_user)],
):
    identifier = _web_identifier(request, user)
    try:
        result = await process_image_generation(
            db,
            prompt=data.prompt,
            model=data.model,
            width=data.width,
            height=data.height,
            identifier=identifier,
            user=user,
        )
        await db.commit()
    except AILimitError as exc:
        raise_http_for_service_error(exc)
    return ImageResponse(**result)
