"""VK bot command router — dispatches menu triggers to handlers."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.models.taxi import TaxiService
from app.services.vk import (
    get_ai_keyboard,
    get_welcome_keyboard,
    get_welcome_message,
    send_message,
)
from app.services.vk_ai_history import clear_ai_history
from app.services.vk_bot import format_ads_message, subscribe_peer, unsubscribe_peer
from app.services.vk_flows import (
    clear_flow,
    format_jobs_message,
    format_routes_message,
    start_classified_flow,
    start_map_report_flow,
    start_wish_flow,
)
from app.services.vk_messages import ai_enter_text, box, help_text

settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")

AI_EXAMPLES = (
    "• Напиши объявление про дрова\n"
    "• Что посмотреть в Пушкиногорье?\n"
    "• Идеи для дачи на лето\n"
    "• Как оформить жалобу в ЖКХ?"
)

CommandHandler = Callable[["VkRouteContext"], Awaitable[None]]


@dataclass
class VkRouteContext:
    db: AsyncSession
    peer_id: int
    from_id: int
    text: str
    text_lower: str
    ai_mode_peers: set[int]


# --- Handlers ---


async def handle_welcome(ctx: VkRouteContext) -> None:
    """Меню / главная / start."""
    ctx.ai_mode_peers.discard(ctx.peer_id)
    clear_flow(ctx.peer_id)
    await clear_ai_history(ctx.db, ctx.peer_id)
    await send_message(ctx.peer_id, get_welcome_message(), keyboard=get_welcome_keyboard())


async def handle_classifieds(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    msg = await format_ads_message(ctx.db)
    await send_message(ctx.peer_id, msg, keyboard=get_welcome_keyboard())


async def handle_services(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(
        ctx.peer_id,
        box(
            "Услуги посёлка",
            f"Огород, дрова, покос, мастера с записью:\n{_SITE}/services\n\n"
            f"📋 Объявления соседей:\n{_SITE}/classifieds\n\n"
            "✨ Всё бесплатно",
        ),
        keyboard=get_welcome_keyboard(),
    )


async def handle_subscribe_all(ctx: VkRouteContext) -> None:
    msg = await subscribe_peer(ctx.db, ctx.peer_id, "all")
    await send_message(ctx.peer_id, msg, keyboard=get_welcome_keyboard())


async def handle_subscribe_jobs(ctx: VkRouteContext) -> None:
    msg = await subscribe_peer(ctx.db, ctx.peer_id, "jobs")
    await send_message(ctx.peer_id, msg, keyboard=get_welcome_keyboard())


async def handle_subscribe_preset(ctx: VkRouteContext) -> None:
    preset = "firewood" if "дрова" in ctx.text_lower else "services"
    msg = await subscribe_peer(ctx.db, ctx.peer_id, preset)
    await send_message(ctx.peer_id, msg, keyboard=get_welcome_keyboard())


async def handle_unsubscribe(ctx: VkRouteContext) -> None:
    msg = await unsubscribe_peer(ctx.db, ctx.peer_id)
    await send_message(ctx.peer_id, msg, keyboard=get_welcome_keyboard())


async def handle_ai_enter(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.add(ctx.peer_id)
    await send_message(ctx.peer_id, ai_enter_text(), keyboard=get_ai_keyboard())


async def handle_ai_examples(ctx: VkRouteContext) -> None:
    await send_message(
        ctx.peer_id,
        box("Примеры для ИИ", AI_EXAMPLES),
        keyboard=get_ai_keyboard(),
    )


async def handle_ai_images(ctx: VkRouteContext) -> None:
    await send_message(
        ctx.peer_id,
        box(
            "Генерация картинок",
            f"На сайте: {_SITE}/ai → вкладка «Картинки»\n\n"
            "Модели: Flux, Turbo, Nano Banana.\n"
            "Пример: «Уютная изба в снегу» или «Усадьба на закате».\n"
            "Опишите сцену на русском — скачайте результат.",
        ),
        keyboard=get_ai_keyboard(),
    )


async def handle_ai_exit(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await clear_ai_history(ctx.db, ctx.peer_id)
    await send_message(ctx.peer_id, "Вернулись в меню 🪶", keyboard=get_welcome_keyboard())


async def handle_jobs(ctx: VkRouteContext) -> None:
    from app.api.v1 import vk_webhook as wh

    ctx.ai_mode_peers.discard(ctx.peer_id)
    msg = await format_jobs_message(ctx.db)
    await wh._send_with_site_links(ctx.peer_id, msg, ("💼 Вакансии", "/jobs"))


async def handle_routes(ctx: VkRouteContext) -> None:
    from app.api.v1 import vk_webhook as wh

    ctx.ai_mode_peers.discard(ctx.peer_id)
    await wh._send_with_site_links(ctx.peer_id, format_routes_message(0), ("🗺 На карте", "/map"))


async def handle_routes_page(ctx: VkRouteContext) -> None:
    from app.api.v1 import vk_webhook as wh

    page = int(ctx.text_lower.split()[-1]) - 1
    await wh._send_with_site_links(ctx.peer_id, format_routes_message(page), ("🗺 На карте", "/map"))


async def handle_map_report(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(ctx.peer_id, start_map_report_flow(ctx.peer_id), keyboard=get_welcome_keyboard())


async def handle_classified_add(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(ctx.peer_id, start_classified_flow(ctx.peer_id), keyboard=get_welcome_keyboard())


async def handle_classified_jobs(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(
        ctx.peer_id,
        start_classified_flow(ctx.peer_id, jobs=True),
        keyboard=get_welcome_keyboard(),
    )


async def handle_wish(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(ctx.peer_id, start_wish_flow(ctx.peer_id), keyboard=get_welcome_keyboard())


async def handle_taxi(ctx: VkRouteContext) -> None:
    result = await ctx.db.execute(
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
    await send_message(ctx.peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def handle_complaints_info(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(
        ctx.peer_id,
        box(
            "Жалобы жителей",
            f"Форма на сайте: {_SITE}/complaints\n\n"
            "Или опишите проблему прямо здесь — примем заявку.\n"
            "«Мои обращения» — статус ваших заявок.",
        ),
        keyboard=get_welcome_keyboard(),
    )


async def handle_register(ctx: VkRouteContext) -> None:
    ctx.ai_mode_peers.discard(ctx.peer_id)
    await send_message(
        ctx.peer_id,
        box(
            "Регистрация",
            f"{_SITE}/register\n\n"
            "🏠 Житель\n🏢 Организация\n"
            "🏛 Администрация / ЖКХ\n💇 Мастер услуг",
        ),
        keyboard=get_welcome_keyboard(),
    )


async def handle_site(ctx: VkRouteContext) -> None:
    await send_message(
        ctx.peer_id,
        box("Портал посёлка", f"{_SITE}\n\nГлавная · Карта · Объявления · Услуги · Жалобы · ИИ"),
        keyboard=get_welcome_keyboard(),
    )


async def handle_map(ctx: VkRouteContext) -> None:
    await send_message(
        ctx.peer_id,
        box(
            "Карта посёлка",
            f"{_SITE}/map\n\n"
            "Магазины, аптеки, кафе, АЗС, гостиницы, маршруты.\n"
            "Напишите: «аптека», «магазин», «заправка», «музей»",
        ),
        keyboard=get_welcome_keyboard(),
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
        await send_message(
            ctx.peer_id,
            "📋 Обращений пока нет. Опишите проблему — приму заявку!",
            keyboard=get_welcome_keyboard(),
        )
    else:
        status_emoji = {
            IssueStatus.NEW: "🆕",
            IssueStatus.UNDER_REVIEW: "🔍",
            IssueStatus.ASSIGNED: "👤",
            IssueStatus.IN_PROGRESS: "🔧",
            IssueStatus.RESOLVED: "✅",
            IssueStatus.REJECTED: "❌",
        }
        lines = ["📋 Ваши обращения:\n"]
        for issue in issues:
            emoji = status_emoji.get(issue.status, "📋")
            summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:50]
            lines.append(f"{emoji} #{issue.id} — {summary}")
        await send_message(ctx.peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def handle_help(ctx: VkRouteContext) -> None:
    await send_message(ctx.peer_id, help_text(), keyboard=get_welcome_keyboard())


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
    # welcome (also used by route_welcome)
    "начать": "welcome",
    "start": "welcome",
    "привет": "welcome",
    "здравствуйте": "welcome",
    "hello": "welcome",
    "меню": "welcome",
    "🏠 меню": "welcome",
    "главная": "welcome",
    "🏠 главная": "welcome",
    # classifieds
    "📋 объявления": "classifieds",
    "объявления": "classifieds",
    "объявление": "classifieds",
    "доска": "classifieds",
    # services
    "🛠 услуги": "services",
    "услуги": "services",
    "мастера": "services",
    "огород": "services",
    "дрова": "services",
    # subscribe
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
    # AI menu
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
    # jobs & routes
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
    # flows
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
    # info sections
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
    handler = COMMAND_HANDLERS[command_id]
    await handler(ctx)


async def route_welcome(ctx: VkRouteContext) -> bool:
    """Welcome/menu triggers — must run before voice transcription."""
    command_id = COMMAND_ALIASES.get(ctx.text_lower)
    if command_id != WELCOME_COMMAND:
        return False
    await _dispatch(ctx, WELCOME_COMMAND)
    return True


async def route_vk_message(ctx: VkRouteContext) -> bool:
    """Route menu commands and map keywords. Returns True if handled."""
    # Special matchers (order matters — routes_page before generic routes alias)
    if _matches_routes_page(ctx.text_lower):
        await handle_routes_page(ctx)
        return True

    if _matches_classified_jobs(ctx.text_lower):
        await handle_classified_jobs(ctx)
        return True

    command_id = COMMAND_ALIASES.get(ctx.text_lower)
    if command_id and command_id != WELCOME_COMMAND:
        await _dispatch(ctx, command_id)
        return True

    from app.api.v1 import vk_webhook as wh

    if await wh._try_map_keywords(ctx.db, ctx.peer_id, ctx.text_lower):
        return True

    return False
