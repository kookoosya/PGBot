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

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

_ai_mode_peers: set[int] = set()

_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def _reply_places(db: AsyncSession, peer_id: int, *, category: PlaceCategory | None = None, search: str | None = None) -> None:
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
            f"Пока не нашёл в справочнике. Откройте карту на сайте:\n{_SITE}/map",
            keyboard=get_welcome_keyboard(),
        )
        return
    lines = ["🗺 Нашёл на карте посёлка:\n"]
    for p in places:
        cat = PLACE_CATEGORY_LABELS.get(p.category, "")
        lines.append(f"• {p.name} — {p.address or 'Пушкинские Горы'}")
        if p.phone:
            lines.append(f"  📞 {p.phone}")
        if p.website:
            lines.append(f"  🔗 {p.website}")
        if p.yandex_url:
            lines.append(f"  🧭 {p.yandex_url}")
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

        if text_lower in ("начать", "start", "привет", "здравствуйте", "hello"):
            _ai_mode_peers.discard(peer_id)
            await send_message(peer_id, get_welcome_message(), keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("🤖 ии-помощник", "ии-помощник", "ии", "ai", "помощник"):
            _ai_mode_peers.add(peer_id)
            await send_message(
                peer_id,
                PUSHKIN_AI_HINT.format(limit=settings.AI_VK_DAILY_LIMIT),
                keyboard=get_ai_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🚪 выйти из ии", "выйти из ии", "выйти", "стоп"):
            _ai_mode_peers.discard(peer_id)
            await send_message(
                peer_id,
                "Вернулись в режим обращений. Опишите проблему — я приму заявку! 🪶",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🌐 сайт", "сайт"):
            await send_message(
                peer_id,
                f"🌐 Портал посёлка Пушкинские Горы:\n{_SITE}\n\n"
                "Карта, объявления, услуги, ИИ-помощник и регистрация.",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🗺 карта", "карта"):
            await send_message(
                peer_id,
                f"🗺 Карта посёлка — магазины, аптеки, АЗС, гостиницы:\n{_SITE}/map\n\n"
                "Напишите «шиномонтаж», «заправка» или «гостиница».",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if any(k in text_lower for k in (
            "гостиниц", "отель", "отдых", "ночлег", "гостевой", "остановиться",
            "где жить", "проживан", "турбаз", "усадьб",
        )):
            await _reply_places(db, peer_id, category=PlaceCategory.HOTEL)
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("такси", "извоз", "машин")):
            result = await db.execute(
                select(TaxiService)
                .where(TaxiService.is_active.is_(True))
                .order_by(TaxiService.sort_order)
            )
            services = result.scalars().all()
            if services:
                lines = ["🚕 Местное такси — звоните с мобильного:\n"]
                for t in services:
                    lines.append(f"• {t.name}: {t.phone}")
                    if t.phones_extra:
                        lines.append(f"  ещё: {t.phones_extra}")
                lines.append(f"\nКарта: {_SITE}/map")
                await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
            else:
                await send_message(
                    peer_id,
                    "🚕 Наше такси: +7 (921) 000-28-28\nТакси Комфорт: +7 (931) 905-50-50",
                    keyboard=get_welcome_keyboard(),
                )
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("шиномонтаж", "шины", "колеса", "колёса")):
            await _reply_places(db, peer_id, category=PlaceCategory.TYRE)
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("азс", "заправка", "бензин", "лукойл")):
            await _reply_places(db, peer_id, category=PlaceCategory.GAS)
            return PlainTextResponse("ok")

        if any(k in text_lower for k in ("аэродромная", "аэродром")):
            await _reply_places(db, peer_id, search="аэродром")
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
                await send_message(peer_id, "📋 У вас пока нет обращений. Опишите проблему — я приму!")
            else:
                lines = ["📋 Ваши обращения:\n"]
                status_emoji = {
                    IssueStatus.NEW: "🆕", IssueStatus.UNDER_REVIEW: "🔍",
                    IssueStatus.ASSIGNED: "👤", IssueStatus.IN_PROGRESS: "🔧",
                    IssueStatus.RESOLVED: "✅", IssueStatus.REJECTED: "❌",
                    IssueStatus.ARCHIVED: "📦",
                }
                for issue in issues:
                    emoji = status_emoji.get(issue.status, "📋")
                    summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:50]
                    lines.append(f"{emoji} #{issue.id} — {summary}")
                await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("ℹ️ помощь", "помощь", "ℹ️ как отправить обращение", "как отправить обращение"):
            await send_message(
                peer_id,
                "ℹ️ Как пользоваться ботом:\n\n"
                "📝 Обращение — просто напишите проблему:\n"
                "«Не работает фонарь на ул. Ленина, 15»\n\n"
                "🤖 ИИ-помощник — нажмите кнопку, задайте вопрос\n\n"
                "📋 Мои обращения — статус ваших заявок\n"
                f"🗺 Карта — {_SITE}/map\n"
                "«шиномонтаж», «заправка», «гостиница», «посуточно»\n\n"
                "🪶 «Я памятник себе воздвиг нерукотворный...»\n"
                "А мы воздвигаем порядок в поселке — вместе!",
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
                    f"🪶 Лимит ИИ на сегодня исчерпан ({limit} сообщений).\n\n"
                    f"💳 Поддержать проект: {payment['card_number']}\n"
                    f"{payment['card_holder']} — от {payment['amount_suggested']} ₽\n\n"
                    f"Завтра лимит обновится!",
                    keyboard=get_ai_keyboard(),
                )
            else:
                reply = await chat_with_ai(msg)
                await increment_usage(db, identifier, "vk")
                remaining = limit - used - 1
                await send_message(
                    peer_id,
                    f"{reply}\n\n—\n💬 Осталось сегодня: {max(0, remaining)}",
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
            await send_message(
                peer_id,
                "Произошла ошибка. Попробуйте позже или напишите «помощь».",
                keyboard=get_welcome_keyboard(),
            )

    return PlainTextResponse("ok")
