import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.vk_command_router import VkRouteContext, route_vk_message, route_welcome
from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.enums import PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService
from app.services.ai_chat import (
    chat_with_ai,
    get_payment_info,
    get_usage_today,
    increment_usage,
    make_identifier,
)
from app.services.issue_processor import process_incoming_message
from app.services.vk import (
    get_ai_keyboard,
    get_inline_links_keyboard,
    get_welcome_keyboard,
    parse_vk_message,
    send_message,
)
from app.services.vk_ai_history import append_ai_turn, get_ai_history
from app.services.vk_voice import extract_audio_url, transcribe_audio_url
from app.services.vk_flows import clear_flow, handle_flow_message
from app.services.vk_messages import (
    ai_limit_text,
    ai_reply_footer,
    box,
    looks_like_ai_question,
    looks_like_complaint,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

_ai_mode_peers: set[int] = set()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def _process_vk_ai(db: AsyncSession, peer_id: int, from_id: int, text: str) -> None:
    identifier = make_identifier(None, None, vk_id=from_id)
    used = await get_usage_today(db, identifier)
    limit = settings.AI_VK_DAILY_LIMIT

    if used >= limit:
        await send_message(peer_id, ai_limit_text(get_payment_info()), keyboard=get_ai_keyboard())
        return

    history = await get_ai_history(db, peer_id)
    reply = await chat_with_ai(text, history=history)
    await increment_usage(db, identifier, "vk")
    await append_ai_turn(db, peer_id, text, reply)
    remaining = limit - used - 1
    await send_message(
        peer_id,
        f"{reply}{ai_reply_footer(remaining)}",
        keyboard=get_ai_keyboard(),
    )


async def _send_with_site_links(peer_id: int, message: str, *paths: str) -> None:
    links = [(label, f"{_SITE}{path}") for label, path in paths]
    kb = get_inline_links_keyboard(links) if links else get_welcome_keyboard()
    await send_message(peer_id, message, keyboard=kb)


async def _reply_places(
    db: AsyncSession,
    peer_id: int,
    *,
    category: PlaceCategory | None = None,
    categories: tuple[PlaceCategory, ...] | None = None,
    search: str | None = None,
) -> None:
    query = select(Place).where(Place.is_active.is_(True))
    if categories:
        query = query.where(Place.category.in_(categories))
    elif category:
        query = query.where(Place.category == category)
    if search:
        query = query.where(Place.name.ilike(f"%{search}%") | Place.address.ilike(f"%{search}%"))
    result = await db.execute(query.order_by(Place.name).limit(6))
    places = result.scalars().all()
    if not places:
        await send_message(
            peer_id,
            f"Пока не нашёл в справочнике. Откройте карту:\n{_SITE}/map",
            keyboard=get_welcome_keyboard(),
        )
        return
    lines = ["🗺 На карте посёлка:\n"]
    for p in places:
        lines.append(f"• {p.name}")
        if p.address:
            lines.append(f"  📍 {p.address}")
        if p.phone:
            lines.append(f"  📞 {p.phone}")
    lines.append(f"\nВся карта: {_SITE}/map")
    await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def _try_map_keywords(db: AsyncSession, peer_id: int, text_lower: str) -> bool:
    """Справочник карты важнее ИИ для запросов «где аптека»."""
    if any(k in text_lower for k in ("гостиниц", "отель", "ночлег", "где жить", "проживан")):
        await _reply_places(db, peer_id, category=PlaceCategory.HOTEL)
        return True
    if "аптек" in text_lower:
        await _reply_places(db, peer_id, category=PlaceCategory.PHARMACY)
        return True
    if any(k in text_lower for k in ("магазин", "продукт", "пятёроч", "магнит", "супермаркет")):
        await _reply_places(
            db, peer_id,
            categories=(PlaceCategory.SHOP, PlaceCategory.SUPERMARKET),
        )
        return True
    if any(k in text_lower for k in ("кафе", "ресторан", "поесть")):
        await _reply_places(
            db, peer_id,
            categories=(PlaceCategory.CAFE, PlaceCategory.RESTAURANT),
        )
        return True
    if any(k in text_lower for k in ("банк", "банкомат", "сбер")):
        await _reply_places(db, peer_id, category=PlaceCategory.BANK)
        return True
    if any(k in text_lower for k in ("больниц", "поликлин", "врач", "медиц")):
        await _reply_places(db, peer_id, category=PlaceCategory.HOSPITAL)
        return True
    if any(k in text_lower for k in ("музей", "михайловск", "пушкин", "лавр", "монаст")):
        await _reply_places(db, peer_id, category=PlaceCategory.CULTURE)
        return True
    if any(k in text_lower for k in ("такси", "извоз")):
        result = await db.execute(
            select(TaxiService).where(TaxiService.is_active.is_(True)).order_by(TaxiService.sort_order)
        )
        services = result.scalars().all()
        lines = ["🚕 Такси:\n"]
        for t in services:
            lines.append(f"• {t.name}: {t.phone}")
        lines.append(f"\n{_SITE}/map")
        await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
        return True
    if any(k in text_lower for k in ("шиномонтаж", "шины", "колеса", "колёса")):
        await _reply_places(db, peer_id, category=PlaceCategory.TYRE)
        return True
    if any(k in text_lower for k in ("азс", "заправка", "бензин")):
        await _reply_places(db, peer_id, category=PlaceCategory.GAS)
        return True
    return False


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

        text = parsed["text"]
        from_id = parsed["from_id"]
        peer_id = parsed["peer_id"]
        text_lower = text.lower()

        ctx = VkRouteContext(
            db=db,
            peer_id=peer_id,
            from_id=from_id,
            text=text,
            text_lower=text_lower,
            ai_mode_peers=_ai_mode_peers,
        )

        if await route_welcome(ctx):
            return PlainTextResponse("ok")

        # Голосовое → текст
        audio_url = extract_audio_url(parsed.get("attachments") or [])
        if audio_url:
            transcribed = await transcribe_audio_url(audio_url)
            if transcribed:
                ctx.text = transcribed
                ctx.text_lower = transcribed.lower()
                await send_message(peer_id, f"🎤 Распознано: «{transcribed[:200]}»")
            elif not text.strip():
                await send_message(
                    peer_id,
                    "Не удалось распознать голосовое. Напишите текстом или повторите.",
                    keyboard=get_welcome_keyboard(),
                )
                return PlainTextResponse("ok")

        flow_reply = await handle_flow_message(db, peer_id, from_id, ctx.text)
        if flow_reply:
            _ai_mode_peers.discard(peer_id)
            await send_message(peer_id, flow_reply, keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if await route_vk_message(ctx):
            return PlainTextResponse("ok")

        if peer_id in _ai_mode_peers or ctx.text_lower.startswith("ии:"):
            msg = ctx.text[3:].strip() if ctx.text_lower.startswith("ии:") else ctx.text
            if len(msg) < 2:
                await send_message(peer_id, "Напишите вопрос — отвечу в режиме ИИ.", keyboard=get_ai_keyboard())
            else:
                await _process_vk_ai(db, peer_id, from_id, msg)
            return PlainTextResponse("ok")

        if looks_like_ai_question(ctx.text) and not looks_like_complaint(ctx.text):
            _ai_mode_peers.add(peer_id)
            await _process_vk_ai(db, peer_id, from_id, ctx.text)
            return PlainTextResponse("ok")

        complaint_text = ctx.text.strip()
        if parsed.get("photos") and len(complaint_text) < 5:
            complaint_text = "Фото проблемы (VK)"

        if looks_like_complaint(complaint_text) or parsed.get("photos"):
            try:
                await process_incoming_message(
                    db, text=complaint_text, vk_id=from_id, peer_id=peer_id,
                    message_id=parsed.get("message_id"), photos=parsed.get("photos"),
                )
            except Exception as e:
                logger.exception("Error processing VK message: %s", e)
                await send_message(peer_id, "Ошибка. Напишите «помощь».", keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        await send_message(
            peer_id,
            box(
                "Не понял сообщение",
                "Выберите кнопку меню или:\n"
                "🤖 ИИ-помощник — любые вопросы\n"
                "⚠️ Жалобы — опишите проблему подробно\n\n"
                "«Меню» — вернуться к разделам",
            ),
            keyboard=get_welcome_keyboard(),
        )

    return PlainTextResponse("ok")
