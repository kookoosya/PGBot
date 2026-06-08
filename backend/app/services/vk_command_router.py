"""VK bot command router — dispatches menu triggers, map keywords, AI and complaints."""

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.enums import IssueStatus, PlaceCategory
from app.models.issue import Issue
from app.models.place import Place
from app.models.taxi import TaxiService
from app.services.ai_mode import enter_ai_mode, exit_ai_mode, is_ai_mode
from app.services.ai_chat import (
    chat_with_ai,
    get_payment_info,
    get_usage_today,
    increment_usage,
    make_identifier,
)
from app.services.issue_processor import process_incoming_message
from app.services.issue_utils import issue_display_summary
from app.services.site_urls import public_site_url
from app.services.vk import (
    get_ai_keyboard,
    get_inline_links_keyboard,
    get_welcome_keyboard,
    get_welcome_message,
    send_message,
)
from app.services.vk_ai_history import append_ai_turn, clear_ai_history, get_ai_history
from app.services.vk_bot import format_ads_message, subscribe_peer, unsubscribe_peer
from app.services.vk_flows import (
    clear_flow,
    format_jobs_message,
    format_routes_message,
    start_classified_flow,
    start_map_report_flow,
    start_wish_flow,
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

AI_EXAMPLES = (
    "• Напиши объявление про дрова\n"
    "• Что посмотреть в Пушкиногорье?\n"
    "• Идеи для дачи на лето\n"
    "• Как оформить жалобу в ЖКХ?"
)

CommandHandler = Callable[["VkRouteContext"], Awaitable[None]]

# Commands that keep AI chat mode active (do not call exit_ai_mode in _dispatch).
AI_PRESERVE_MODE = frozenset({"ai_enter", "ai_examples", "ai_images"})

ISSUE_STATUS_EMOJI = {
    IssueStatus.NEW: "🆕",
    IssueStatus.UNDER_REVIEW: "🔍",
    IssueStatus.ASSIGNED: "👤",
    IssueStatus.IN_PROGRESS: "🔧",
    IssueStatus.RESOLVED: "✅",
    IssueStatus.REJECTED: "❌",
}


@dataclass(slots=True)
class VkRouteContext:
    db: AsyncSession
    peer_id: int
    from_id: int
    text: str
    text_lower: str
    parsed: dict[str, Any] | None = None

    @classmethod
    def from_parsed(
        cls,
        db: AsyncSession,
        parsed: dict[str, Any],
    ) -> "VkRouteContext":
        text = parsed["text"]
        return cls(
            db=db,
            peer_id=parsed["peer_id"],
            from_id=parsed["from_id"],
            text=text,
            text_lower=text.lower(),
            parsed=parsed,
        )

    def update_text(self, text: str) -> None:
        self.text = text
        self.text_lower = text.lower()


# --- Shared reply helpers ---


async def _send_welcome(ctx: VkRouteContext, message: str) -> None:
    await send_message(ctx.peer_id, message, keyboard=get_welcome_keyboard())


async def _send_ai(ctx: VkRouteContext, message: str) -> None:
    await send_message(ctx.peer_id, message, keyboard=get_ai_keyboard())


async def _send_with_site_links(peer_id: int, message: str, *paths: str) -> None:
    site = public_site_url()
    links = [(label, f"{site}{path}") for label, path in paths]
    kb = get_inline_links_keyboard(links) if links else get_welcome_keyboard()
    await send_message(peer_id, message, keyboard=kb)


async def _subscribe_and_reply(ctx: VkRouteContext, preset: str) -> None:
    msg = await subscribe_peer(ctx.db, ctx.peer_id, preset)
    await _send_welcome(ctx, msg)


async def _start_flow_message(ctx: VkRouteContext, message: str) -> None:
    await _send_welcome(ctx, message)


def _format_taxi_lines(services: list[TaxiService], *, header: str, empty_line: str | None) -> str:
    lines = [header]
    if services:
        for taxi in services:
            lines.append(f"• {taxi.name}: {taxi.phone}")
    elif empty_line:
        lines.append(empty_line)
    lines.append(f"\n{public_site_url()}/map")
    return "\n".join(lines)


async def _reply_taxi(db: AsyncSession, peer_id: int, *, header: str, empty_line: str | None = None) -> None:
    result = await db.execute(
        select(TaxiService).where(TaxiService.is_active.is_(True)).order_by(TaxiService.sort_order)
    )
    services = result.scalars().all()
    message = _format_taxi_lines(services, header=header, empty_line=empty_line)
    await send_message(peer_id, message, keyboard=get_welcome_keyboard())


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
            f"Пока не нашёл в справочнике. Откройте карту:\n{public_site_url()}/map",
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
    lines.append(f"\nВся карта: {public_site_url()}/map")
    await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def _try_map_keywords(ctx: VkRouteContext) -> bool:
    """Справочник карты важнее ИИ для запросов «где аптека»."""
    text_lower = ctx.text_lower
    db = ctx.db
    peer_id = ctx.peer_id

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
        await _reply_taxi(db, peer_id, header="🚕 Такси:\n")
        return True
    if any(k in text_lower for k in ("шиномонтаж", "шины", "колеса", "колёса")):
        await _reply_places(db, peer_id, category=PlaceCategory.TYRE)
        return True
    if any(k in text_lower for k in ("азс", "заправка", "бензин")):
        await _reply_places(db, peer_id, category=PlaceCategory.GAS)
        return True
    return False


async def _process_vk_ai(ctx: VkRouteContext, text: str) -> None:
    identifier = make_identifier(None, None, vk_id=ctx.from_id)
    used = await get_usage_today(ctx.db, identifier)
    limit = settings.AI_VK_DAILY_LIMIT

    if used >= limit:
        await _send_ai(ctx, ai_limit_text(get_payment_info()))
        return

    history = await get_ai_history(ctx.db, ctx.peer_id)
    reply = await chat_with_ai(text, history=history)
    await increment_usage(ctx.db, identifier, "vk")
    await append_ai_turn(ctx.db, ctx.peer_id, text, reply)
    remaining = limit - used - 1
    await _send_ai(ctx, f"{reply}{ai_reply_footer(remaining)}")


# --- Command handlers ---


async def handle_welcome(ctx: VkRouteContext) -> None:
    """Меню / главная / start."""
    clear_flow(ctx.peer_id)
    await clear_ai_history(ctx.db, ctx.peer_id)
    await _send_welcome(ctx, get_welcome_message())


async def handle_classifieds(ctx: VkRouteContext) -> None:
    msg = await format_ads_message(ctx.db)
    await _send_welcome(ctx, msg)


async def handle_services(ctx: VkRouteContext) -> None:
    site = public_site_url()
    await _send_welcome(
        ctx,
        box(
            "Услуги посёлка",
            f"Огород, дрова, покос, мастера с записью:\n{site}/services\n\n"
            f"📋 Объявления соседей:\n{site}/classifieds\n\n"
            "✨ Всё бесплатно",
        ),
    )


async def handle_subscribe_all(ctx: VkRouteContext) -> None:
    await _subscribe_and_reply(ctx, "all")


async def handle_subscribe_jobs(ctx: VkRouteContext) -> None:
    await _subscribe_and_reply(ctx, "jobs")


async def handle_subscribe_preset(ctx: VkRouteContext) -> None:
    preset = "firewood" if "дрова" in ctx.text_lower else "services"
    await _subscribe_and_reply(ctx, preset)


async def handle_unsubscribe(ctx: VkRouteContext) -> None:
    msg = await unsubscribe_peer(ctx.db, ctx.peer_id)
    await _send_welcome(ctx, msg)


async def handle_ai_enter(ctx: VkRouteContext) -> None:
    enter_ai_mode(ctx.peer_id)
    await _send_ai(ctx, ai_enter_text())


async def handle_ai_examples(ctx: VkRouteContext) -> None:
    await _send_ai(ctx, box("Примеры для ИИ", AI_EXAMPLES))


async def handle_ai_images(ctx: VkRouteContext) -> None:
    await _send_ai(
        ctx,
        box(
            "Генерация картинок",
            f"На сайте: {public_site_url()}/ai → вкладка «Картинки»\n\n"
            "Модели: Flux, Turbo, Nano Banana.\n"
            "Пример: «Уютная изба в снегу» или «Усадьба на закате».\n"
            "Опишите сцену на русском — скачайте результат.",
        ),
    )


async def handle_ai_exit(ctx: VkRouteContext) -> None:
    await clear_ai_history(ctx.db, ctx.peer_id)
    await _send_welcome(ctx, "Вернулись в меню 🪶")


async def handle_jobs(ctx: VkRouteContext) -> None:
    msg = await format_jobs_message(ctx.db)
    await _send_with_site_links(ctx.peer_id, msg, ("💼 Вакансии", "/jobs"))


async def handle_routes(ctx: VkRouteContext) -> None:
    await _send_with_site_links(ctx.peer_id, format_routes_message(0), ("🗺 На карте", "/map"))


async def handle_routes_page(ctx: VkRouteContext) -> None:
    page = int(ctx.text_lower.split()[-1]) - 1
    await _send_with_site_links(ctx.peer_id, format_routes_message(page), ("🗺 На карте", "/map"))


async def handle_map_report(ctx: VkRouteContext) -> None:
    await _start_flow_message(ctx, start_map_report_flow(ctx.peer_id))


async def handle_classified_add(ctx: VkRouteContext) -> None:
    await _start_flow_message(ctx, start_classified_flow(ctx.peer_id))


async def handle_classified_jobs(ctx: VkRouteContext) -> None:
    await _start_flow_message(ctx, start_classified_flow(ctx.peer_id, jobs=True))


async def handle_wish(ctx: VkRouteContext) -> None:
    await _start_flow_message(ctx, start_wish_flow(ctx.peer_id))


async def handle_taxi(ctx: VkRouteContext) -> None:
    await _reply_taxi(
        ctx.db,
        ctx.peer_id,
        header="🚕 Такси посёлка:\n",
        empty_line="Справочник обновляется. Напишите «аптека» или откройте карту.",
    )


async def handle_complaints_info(ctx: VkRouteContext) -> None:
    await _send_welcome(
        ctx,
        box(
            "Жалобы жителей",
            f"Форма на сайте: {public_site_url()}/complaints\n\n"
            "Или опишите проблему прямо здесь — примем заявку.\n"
            "«Мои обращения» — статус ваших заявок.",
        ),
    )


async def handle_register(ctx: VkRouteContext) -> None:
    await _send_welcome(
        ctx,
        box(
            "Регистрация",
            f"{public_site_url()}/register\n\n"
            "🏠 Житель\n🏢 Организация\n"
            "🏛 Администрация / ЖКХ\n💇 Мастер услуг",
        ),
    )


async def handle_site(ctx: VkRouteContext) -> None:
    site = public_site_url()
    await _send_welcome(
        ctx,
        box("Портал посёлка", f"{site}\n\nГлавная · Карта · Объявления · Услуги · Жалобы · ИИ"),
    )


async def handle_map(ctx: VkRouteContext) -> None:
    await _send_welcome(
        ctx,
        box(
            "Карта посёлка",
            f"{public_site_url()}/map\n\n"
            "Магазины, аптеки, кафе, АЗС, гостиницы, маршруты.\n"
            "Напишите: «аптека», «магазин», «заправка», «музей»",
        ),
    )


async def handle_my_issues(ctx: VkRouteContext) -> None:
    result = await ctx.db.execute(
        select(Issue)
        .options(selectinload(Issue.ai_analysis))
        .where(Issue.vk_peer_id == ctx.peer_id, Issue.parent_issue_id.is_(None))
        .order_by(Issue.created_at.desc())
        .limit(10)
    )
    issues = result.scalars().all()
    if not issues:
        await _send_welcome(ctx, "📋 Обращений пока нет. Опишите проблему — приму заявку!")
        return

    lines = ["📋 Ваши обращения:\n"]
    for issue in issues:
        emoji = ISSUE_STATUS_EMOJI.get(issue.status, "📋")
        lines.append(f"{emoji} #{issue.id} — {issue_display_summary(issue, max_len=50)}")
    await _send_welcome(ctx, "\n".join(lines))


async def handle_help(ctx: VkRouteContext) -> None:
    await _send_welcome(ctx, help_text())


# --- Routing tables ---

COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "welcome": handle_welcome,
    "classifieds": handle_classifieds,
    "services": handle_services,
    "subscribe_all": handle_subscribe_all,
    "subscribe_jobs": handle_subscribe_jobs,
    "subscribe_preset": handle_subscribe_preset,
    "unsubscribe": handle_unsubscribe,
    "ai_enter": handle_ai_enter,
    "ai_examples": handle_ai_examples,
    "ai_images": handle_ai_images,
    "ai_exit": handle_ai_exit,
    "jobs": handle_jobs,
    "routes": handle_routes,
    "map_report": handle_map_report,
    "classified_add": handle_classified_add,
    "classified_jobs": handle_classified_jobs,
    "wish": handle_wish,
    "taxi": handle_taxi,
    "complaints_info": handle_complaints_info,
    "register": handle_register,
    "site": handle_site,
    "map": handle_map,
    "my_issues": handle_my_issues,
    "help": handle_help,
}

COMMAND_ALIASES: dict[str, str] = {
    "начать": "welcome",
    "start": "welcome",
    "привет": "welcome",
    "здравствуйте": "welcome",
    "hello": "welcome",
    "меню": "welcome",
    "🏠 меню": "welcome",
    "главная": "welcome",
    "🏠 главная": "welcome",
    "📋 объявления": "classifieds",
    "объявления": "classifieds",
    "объявление": "classifieds",
    "доска": "classifieds",
    "🛠 услуги": "services",
    "услуги": "services",
    "мастера": "services",
    "огород": "services",
    "дрова": "services",
    "🔔 подписаться": "subscribe_all",
    "подписаться": "subscribe_all",
    "подписка": "subscribe_all",
    "подписка все": "subscribe_all",
    "подписка работа": "subscribe_jobs",
    "подписка вакансии": "subscribe_jobs",
    "🔔 работа": "subscribe_jobs",
    "подписка дрова": "subscribe_preset",
    "подписка услуги": "subscribe_preset",
    "🔕 отписаться": "unsubscribe",
    "отписаться": "unsubscribe",
    "🤖 ии-помощник": "ai_enter",
    "ии-помощник": "ai_enter",
    "ии": "ai_enter",
    "ai": "ai_enter",
    "помощник": "ai_enter",
    "💡 примеры вопросов": "ai_examples",
    "примеры": "ai_examples",
    "🎨 картинки на сайте": "ai_images",
    "картинки": "ai_images",
    "нарисуй": "ai_images",
    "🚪 выйти из ии": "ai_exit",
    "выйти из ии": "ai_exit",
    "стоп": "ai_exit",
    "💼 работа": "jobs",
    "работа": "jobs",
    "вакансии": "jobs",
    "вакансия": "jobs",
    "подработка": "jobs",
    "🛤 маршруты": "routes",
    "маршруты": "routes",
    "маршрут": "routes",
    "куда сходить": "routes",
    "экскурсия": "routes",
    "🗺 ошибка карты": "map_report",
    "ошибка карты": "map_report",
    "ошибка на карте": "map_report",
    "карта ошибка": "map_report",
    "➕ объявление": "classified_add",
    "подать объявление": "classified_add",
    "добавить объявление": "classified_add",
    "разместить объявление": "classified_add",
    "💡 пожелания": "wish",
    "пожелания": "wish",
    "предложения": "wish",
    "идея для сайта": "wish",
    "🚕 такси": "taxi",
    "такси": "taxi",
    "⚠️ жалобы": "complaints_info",
    "жалобы": "complaints_info",
    "обращения": "complaints_info",
    "жалоба": "complaints_info",
    "📝 регистрация": "register",
    "регистрация": "register",
    "зарегистрироваться": "register",
    "🌐 сайт": "site",
    "сайт": "site",
    "🗺 карта": "map",
    "карта": "map",
    "📋 мои обращения": "my_issues",
    "мои обращения": "my_issues",
    "ℹ️ помощь": "help",
    "помощь": "help",
}

WELCOME_COMMAND = "welcome"


def _matches_routes_page(text_lower: str) -> bool:
    return text_lower.startswith("маршруты ") and text_lower.split()[-1].isdigit()


def _matches_classified_jobs(text_lower: str) -> bool:
    return text_lower in ("вакансия работа",) or text_lower == "вакансию"


async def _dispatch(ctx: VkRouteContext, command_id: str) -> None:
    if command_id not in AI_PRESERVE_MODE:
        exit_ai_mode(ctx.peer_id)
    await COMMAND_HANDLERS[command_id](ctx)


async def route_welcome(ctx: VkRouteContext) -> bool:
    """Welcome/menu triggers — must run before voice transcription."""
    command_id = COMMAND_ALIASES.get(ctx.text_lower)
    if command_id != WELCOME_COMMAND:
        return False
    await _dispatch(ctx, WELCOME_COMMAND)
    return True


async def route_vk_message(ctx: VkRouteContext) -> bool:
    """Route menu commands and map keywords. Returns True if handled."""
    # Special matchers first (order matters — routes_page before generic routes alias)
    if _matches_routes_page(ctx.text_lower):
        await handle_routes_page(ctx)
        return True

    if _matches_classified_jobs(ctx.text_lower):
        exit_ai_mode(ctx.peer_id)
        await handle_classified_jobs(ctx)
        return True

    command_id = COMMAND_ALIASES.get(ctx.text_lower)
    if command_id and command_id != WELCOME_COMMAND:
        await _dispatch(ctx, command_id)
        return True

    # Free-text map queries («аптека», «магазин», …) before AI
    if await _try_map_keywords(ctx):
        return True

    return False


async def route_ai_message(ctx: VkRouteContext) -> bool:
    """Handle active AI mode or auto-detected AI questions."""
    if is_ai_mode(ctx.peer_id) or ctx.text_lower.startswith("ии:"):
        msg = ctx.text[3:].strip() if ctx.text_lower.startswith("ии:") else ctx.text
        if len(msg) < 2:
            await _send_ai(ctx, "Напишите вопрос — отвечу в режиме ИИ.")
        else:
            await _process_vk_ai(ctx, msg)
        return True

    if looks_like_ai_question(ctx.text) and not looks_like_complaint(ctx.text):
        enter_ai_mode(ctx.peer_id)
        await _process_vk_ai(ctx, ctx.text)
        return True

    return False


async def route_complaint(ctx: VkRouteContext) -> bool:
    """Process complaint text or photo attachments."""
    if ctx.parsed is None:
        return False

    complaint_text = ctx.text.strip()
    if ctx.parsed.get("photos") and len(complaint_text) < 5:
        complaint_text = "Фото проблемы (VK)"

    if not looks_like_complaint(complaint_text) and not ctx.parsed.get("photos"):
        return False

    try:
        await process_incoming_message(
            ctx.db,
            text=complaint_text,
            vk_id=ctx.from_id,
            peer_id=ctx.peer_id,
            message_id=ctx.parsed.get("message_id"),
            photos=ctx.parsed.get("photos"),
        )
    except Exception as e:
        logger.exception("Error processing VK message: %s", e)
        await _send_welcome(ctx, "Ошибка. Напишите «помощь».")
    return True


async def send_fallback_message(ctx: VkRouteContext) -> None:
    """Default reply when nothing else matched."""
    await _send_welcome(
        ctx,
        box(
            "Не понял сообщение",
            "Выберите кнопку меню или:\n"
            "🤖 ИИ-помощник — любые вопросы\n"
            "⚠️ Жалобы — опишите проблему подробно\n\n"
            "«Меню» — вернуться к разделам",
        ),
    )
