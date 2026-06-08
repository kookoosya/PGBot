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
from app.services.vk_messages import (
    ai_enter_text,
    ai_limit_text,
    ai_reply_footer,
    box,
    help_text,
    looks_like_ai_question,
    looks_like_complaint,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()

_ai_mode_peers: set[int] = set()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")

AI_EXAMPLES = (
    "• Напиши объявление про дрова\n"
    "• Что посмотреть в Пушкиногорье?\n"
    "• Идеи для дачи на лето\n"
    "• Как оформить жалобу в ЖКХ?"
)


async def _process_vk_ai(db: AsyncSession, peer_id: int, from_id: int, text: str) -> None:
    identifier = make_identifier(None, None, vk_id=from_id)
    used = await get_usage_today(db, identifier)
    limit = settings.AI_VK_DAILY_LIMIT

    if used >= limit:
        await send_message(peer_id, ai_limit_text(get_payment_info()), keyboard=get_ai_keyboard())
        return

    reply = await chat_with_ai(text)
    await increment_usage(db, identifier, "vk")
    remaining = limit - used - 1
    await send_message(
        peer_id,
        f"{reply}{ai_reply_footer(remaining)}",
        keyboard=get_ai_keyboard(),
    )


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

        menu_triggers = (
            "начать", "start", "привет", "здравствуйте", "hello", "меню",
            "🏠 меню", "главная", "🏠 главная",
        )
        if text_lower in menu_triggers:
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
                box(
                    "Услуги посёлка",
                    f"Огород, дрова, покос, мастера с записью:\n{_SITE}/services\n\n"
                    f"📋 Объявления соседей:\n{_SITE}/classifieds\n\n"
                    "✨ Всё бесплатно",
                ),
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
            await send_message(peer_id, ai_enter_text(), keyboard=get_ai_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("💡 примеры вопросов", "примеры"):
            await send_message(
                peer_id,
                box("Примеры для ИИ", AI_EXAMPLES),
                keyboard=get_ai_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🎨 картинки на сайте", "картинки", "нарисуй"):
            await send_message(
                peer_id,
                box(
                    "Генерация картинок",
                    f"На сайте: {_SITE}/ai → вкладка «Картинки»\n\n"
                    "Модели: Flux, Turbo, Nano Banana.\n"
                    "Пример: «Уютная изба в снегу» или «Усадьба на закате».\n"
                    "Опишите сцену на русском — скачайте результат.",
                ),
                keyboard=get_ai_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🚪 выйти из ии", "выйти из ии", "стоп"):
            _ai_mode_peers.discard(peer_id)
            await send_message(peer_id, "Вернулись в меню 🪶", keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("💡 пожелания", "пожелания", "предложения", "идея для сайта"):
            _ai_mode_peers.discard(peer_id)
            await send_message(
                peer_id,
                box(
                    "Пожелания жителей",
                    f"Предложите улучшение портала:\n{_SITE}/wishes\n\n"
                    "Идеи по дизайну, разделам, сервисам — всё сюда.",
                ),
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🚕 такси", "такси"):
            result = await db.execute(
                select(TaxiService).where(TaxiService.is_active.is_(True)).order_by(TaxiService.sort_order)
            )
            services = result.scalars().all()
            lines = ["🚕 Такси посёлка:\n"]
            if services:
                for t in services:
                    lines.append(f"• {t.name}: {t.phone}")
            else:
                lines.append("Справочник обновляется. Напишите «аптека» или откройте карту.")
            lines.append(f"\n{_SITE}/map")
            await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if text_lower in ("⚠️ жалобы", "жалобы", "обращения", "жалоба"):
            _ai_mode_peers.discard(peer_id)
            await send_message(
                peer_id,
                box(
                    "Жалобы жителей",
                    f"Форма на сайте: {_SITE}/complaints\n\n"
                    "Или опишите проблему прямо здесь — примем заявку.\n"
                    "«Мои обращения» — статус ваших заявок.",
                ),
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("📝 регистрация", "регистрация", "зарегистрироваться"):
            _ai_mode_peers.discard(peer_id)
            await send_message(
                peer_id,
                box(
                    "Регистрация",
                    f"{_SITE}/register\n\n"
                    "🏠 Житель\n🏢 Организация\n"
                    "🏛 Администрация / ЖКХ\n💇 Мастер услуг",
                ),
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🌐 сайт", "сайт"):
            await send_message(
                peer_id,
                box("Портал посёлка", f"{_SITE}\n\nГлавная · Карта · Объявления · Услуги · Жалобы · ИИ"),
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text_lower in ("🗺 карта", "карта"):
            await send_message(
                peer_id,
                box(
                    "Карта посёлка",
                    f"{_SITE}/map\n\n"
                    "Магазины, аптеки, кафе, АЗС, гостиницы.\n"
                    "Напишите: «аптека», «шиномонтаж», «заправка»",
                ),
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
            await send_message(peer_id, help_text(), keyboard=get_welcome_keyboard())
            return PlainTextResponse("ok")

        if peer_id in _ai_mode_peers or text_lower.startswith("ии:"):
            msg = text[3:].strip() if text_lower.startswith("ии:") else text
            if len(msg) < 2:
                await send_message(peer_id, "Напишите вопрос — отвечу в режиме ИИ.", keyboard=get_ai_keyboard())
            else:
                await _process_vk_ai(db, peer_id, from_id, msg)
            return PlainTextResponse("ok")

        if looks_like_ai_question(text) and not looks_like_complaint(text):
            _ai_mode_peers.add(peer_id)
            await _process_vk_ai(db, peer_id, from_id, text)
            return PlainTextResponse("ok")

        if looks_like_complaint(text) or parsed.get("photos"):
            try:
                await process_incoming_message(
                    db, text=text, vk_id=from_id, peer_id=peer_id,
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
