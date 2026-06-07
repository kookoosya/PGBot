from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.deps import get_client_ip
from app.database import get_db
from app.schemas.ai import ChatRequest, ChatResponse, PaymentInfoResponse, UsageResponse
from app.services.ai_chat import (
    chat_with_ai,
    get_payment_info,
    get_usage_today,
    increment_usage,
    make_identifier,
)

router = APIRouter()
settings = get_settings()


def _get_limit(source: str = "web") -> int:
    return settings.AI_VK_DAILY_LIMIT if source == "vk" else settings.AI_FREE_DAILY_LIMIT


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

    if used >= limit:
        payment = get_payment_info()
        return ChatResponse(
            reply=(
                f"🪶 Вы использовали {limit} бесплатных сообщений на сегодня.\n\n"
                f"ИИ-помощник работает за счёт добровольных пожертвований — "
                f"серверы и API стоят денег.\n\n"
                f"💳 Перевод: {payment['card_number']}\n"
                f"Получатель: {payment['card_holder']}\n"
                f"Банк: {payment['bank_name']}\n"
                f"Сумма: от {payment['amount_suggested']} ₽\n"
                f"Комментарий: «{payment['description']}»\n\n"
                f"После перевода напишите на {payment['contact_email']} — "
                f"мы расширим ваш лимит. Завтра бесплатные сообщения обновятся!"
            ),
            remaining=0,
            daily_limit=limit,
            limit_reached=True,
            payment_info=payment,
        )

    history = [{"role": m.role, "content": m.content} for m in data.history]
    reply = await chat_with_ai(data.message, history)
    new_count = await increment_usage(db, identifier, "web")

    return ChatResponse(
        reply=reply,
        remaining=max(0, limit - new_count),
        daily_limit=limit,
        limit_reached=False,
    )
