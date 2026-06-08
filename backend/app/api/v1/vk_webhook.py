import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.enums import IssueStatus, PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.issue import Issue
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
    PUSHKIN_AI_HINT,
    get_ai_keyboard,
    get_welcome_keyboard,
    get_welcome_message,
    parse_vk_message,
    send_message,
)
from app.services.vk_bot import (
    format_ads_message,
    subscribe_peer,
    unsubscribe_peer,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

_ai_mode_peers: set[int] = set()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def _reply_places(
    db: AsyncSession, peer_id: int, *, category: PlaceCategory | None = None, search: str | None = None,
) -> None:
    query = select(Place).where(Place.is_active.is_(True))
    if category:
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


@router.post("/callback")
async def vk_callback(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    body: dict[str, Any] = await request.json()
    event_type = body.get("type")

    if event_type == "confirmation":
        return PlainTextResponse(settings.VK_CONFIRMATION_CODE)

    if event_type == "message_new":
        if settings.VK_SECRET_KEY and body.get("secret") != settings.VK_SECRET_KEY:
            return PlainTextResponse("ok")

        parsed = parse_vk_message(body)
        if not parsed:
            return PlainTextResponse("ok")

        text = parsed["text"]
        from_id = parsed["from_id"]
        peer_id = parsed["peer_id"]
        text_lower = text.lower()

        if text_lower in ("начать", "start", "привет", "здравствуйте", "hello", "меню"):
            _ai_mode_peers.discard(peer_id)
            await send_message(peer_id, get_welcome_message(), keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("📋 объявления", "объявления", "объявление", "доска"):
            _ai_mode_peers.discard(peer_id)
            msg = await format_ads_message(db)
            await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("🛠 услуги", "услуги", "мастера", "огород", "дрова"):
            _ai_mode_peers.discard(peer_id)
            await send_message(
                peer_id,
                f"🛠 Услуги посёлка — огород, дрова, покос, мастера:\n{_SITE}/services\n\n"
                f"Объявления соседей: {_SITE}/classifieds\n"
                f"Первые {settings.CLASSIFIED_FREE_LIMIT} объявления — бесплатно!",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🔔 подписаться", "подписаться", "подписка"):
            msg = await subscribe_peer(db, peer_id)
            await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("🔕 отписаться", "отписаться"):
            msg = await unsubscribe_peer(db, peer_id)
            await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("🤖 ии-помощник", "ии-помощник", "ии", "ai", "помощник"):
            _ai_mode_peers.add(peer_id)
            await send_message(
                peer_id,
                PUSHKIN_AI_HINT.format(limit=settings.AI_VK_DAILY_LIMIT),
                keyboard=get_ai_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🎨 картинки на сайте", "картинки", "нарисуй"):
            await send_message(
                peer_id,
                f"🎨 Генерация картинок на сайте:\n{_SITE}/ai\n\n"
                "Модели: Nano Banana, Flux, Turbo, Gemini Imagen.\n"
                "Опишите что нарисовать — и скачайте!",
                keyboard=get_ai_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🚪 выйти из ии", "выйти из ии", "выйти", "стоп"):
            _ai_mode_peers.discard(peer_id)
            await send_message(peer_id, "Вернулись в меню 🪶", keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("🌐 сайт", "сайт"):
            await send_message(
                peer_id,
                f"🌐 Портал посёлка:\n{_SITE}\n\n"
                "Карта · Объявления · Услуги · ИИ · Регистрация",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🗺 карта", "карта"):
            await send_message(
                peer_id,
                f"🗺 Карта — магазины, аптеки, кафе, АЗС, гостиницы:\n{_SITE}/map\n\n"
                "Напишите: «аптека», «шиномонтаж», «заправка», «гостиница»",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("гостиниц", "отель", "ночлег", "где жить", "проживан")):
            await _reply_places(db, peer_id, category=PlaceCategory.HOTEL)
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("аптек", "магазин", "продукт")):
            await _reply_places(db, peer_id, category=PlaceCategory.PHARMACY if "аптек" in text_lower else PlaceCategory.SHOP)
            return PlainTextResponse("ok")

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
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("шиномонтаж", "шины", "колеса", "колёса")):
            await _reply_places(db, peer_id, category=PlaceCategory.TYRE)
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("азс", "заправка", "бензин")):
            await _reply_places(db, peer_id, category=PlaceCategory.GAS)
            return PlainTextResponse("ok")

        if text_lower in ("📋 мои обращения", "мои обращения"):
            result = await db.execute(
                select(Issue)
                .options(selectinload(Issue.ai_analysis))
                .where(Issue.vk_peer_id == peer_id, Issue.parent_issue_id.is_(None))
                .order_by(Issue.created_at.desc())
                .limit(10)
            )
            issues = result.scalars().all()
            if not issues:
                await send_message(peer_id, "📋 Обращений пока нет. Опишите проблему — приму заявку!")
            else:
                status_emoji = {
                    IssueStatus.NEW: "🆕", IssueStatus.UNDER_REVIEW: "🔍",
                    IssueStatus.ASSIGNED: "👤", IssueStatus.IN_PROGRESS: "🔧",
                    IssueStatus.RESOLVED: "✅", IssueStatus.REJECTED: "❌",
                }
                lines = ["📋 Ваши обращения:\n"]
                for issue in issues:
                    emoji = status_emoji.get(issue.status, "📋")
                    summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:50]
                    lines.append(f"{emoji} #{issue.id} — {summary}")
                await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("ℹ️ помощь", "помощь"):
            await send_message(
                peer_id,
                "ℹ️ Бот = сайт в VK\n\n"
                "📋 Объявления — доска (3 бесплатно)\n"
                "🗺 Карта — магазины, аптеки, кафе\n"
                "🛠 Услуги — мастера, огород, дрова\n"
                "🤖 ИИ — любые вопросы + картинки на сайте\n"
                "🔔 Подписаться — уведомления о новых объявлениях\n"
                "📝 Обращение — просто напишите проблему\n\n"
                f"🌐 {_SITE}",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if peer_id in _ai_mode_peers or text_lower.startswith("ии:"):
            msg = text[3:].strip() if text_lower.startswith("ии:") else text
            identifier = make_identifier(None, None, vk_id=from_id)
            used = await get_usage_today(db, identifier)
            limit = settings.AI_VK_DAILY_LIMIT

            if used >= limit:
                payment = get_payment_info()
                await send_message(
                    peer_id,
                    f"🪶 Лимит ИИ на сегодня ({limit}).\n"
                    f"💳 Поддержка: {payment['card_number']}\n"
                    f"Завтра лимит обновится!\n"
                    f"Картинки: {_SITE}/ai",
                    keyboard=get_ai_keyboard(),
                )
            else:
                reply = await chat_with_ai(msg)
                await increment_usage(db, identifier, "vk")
                remaining = limit - used - 1
                await send_message(
                    peer_id,
                    f"{reply}\n\n—\n💬 Осталось: {max(0, remaining)} · 🎨 Картинки: {_SITE}/ai",
                    keyboard=get_ai_keyboard(),
                )
            return PlainTextResponse("ok")

        try:
            await process_incoming_message(
                db, text=text, vk_id=from_id, peer_id=peer_id,
                message_id=parsed.get("message_id"), photos=parsed.get("photos"),
            )
        except Exception as e:
            logger.exception("Error processing VK message: %s", e)
            await send_message(peer_id, "Ошибка. Напишите «помощь».", keyboard=get_welcome_keyboard())

    return PlainTextResponse("ok")
