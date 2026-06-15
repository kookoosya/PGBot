"""Обработчики команд меню VK-бота и таблицы алиасов."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.constants.portal_copy import (
    COMPLAINTS_INFO_VK,
    LINK_CABINET,
    LINK_CLASSIFIEDS,
    LINK_COMPLAINTS,
    LINK_EVENTS,
    LINK_MAP,
    LINK_SUBMIT_CLASSIFIED,
    LINK_SUBMIT_COMPLAINT,
)
from app.models.issue import Issue
from app.services.issue_utils import issue_display_summary
from app.services.notifications import issue_status_hint
from app.services.site_urls import public_site_url
from app.services.vk.client import get_welcome_keyboard, get_welcome_message, send_message
from app.services.vk.context import CommandHandler, VkRouteContext
from app.services.vk.flows import (
    clear_flow,
    format_jobs_message,
    format_routes_message,
    start_classified_flow,
    start_map_report_flow,
    start_wish_flow,
)
from app.services.vk.helpers import (
    AI_EXAMPLES,
    ISSUE_STATUS_EMOJI,
    reply_taxi,
    send_ai,
    send_welcome,
    send_with_site_links,
    start_flow_message,
    subscribe_and_reply,
)
from app.services.vk.ai_mode import enter_ai_mode
from app.services.vk_ai_history import clear_ai_history
from app.services.vk.bot import format_ads_message, unsubscribe_peer
from app.services.vk_messages import ai_enter_text, box, help_text
from app.services.weather_service import (
    WeatherFetchError,
    format_weather_vk_current,
    format_weather_vk_hourly,
    get_weather,
    looks_like_hourly_weather,
)

# Команды, при которых AI-режим не сбрасывается.
AI_PRESERVE_MODE = frozenset({"ai_enter", "ai_examples", "ai_images"})

WELCOME_COMMAND = "welcome"


async def handle_welcome(ctx: VkRouteContext) -> None:
    """Меню / главная / start."""
    await clear_flow(ctx.db, ctx.peer_id)
    await clear_ai_history(ctx.db, ctx.peer_id)
    await send_welcome(ctx, get_welcome_message())


async def handle_classifieds(ctx: VkRouteContext) -> None:
    msg = await format_ads_message(ctx.db)
    await send_with_site_links(
        ctx.peer_id,
        msg,
        (LINK_CLASSIFIEDS, "/classifieds"),
        (LINK_SUBMIT_CLASSIFIED, "/classifieds?new=1"),
        ("💼 Вакансии", "/jobs"),
    )


async def handle_services(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box(
            "Услуги посёлка",
            "Огород, дрова, покос, мастера с записью.\n"
            "Объявления соседей — на доске.\n\n"
            "✨ Всё бесплатно",
        ),
        ("🛠 Услуги", "/services"),
        (LINK_CLASSIFIEDS, "/classifieds"),
    )


async def handle_subscribe_all(ctx: VkRouteContext) -> None:
    await subscribe_and_reply(ctx, "all")


async def handle_subscribe_jobs(ctx: VkRouteContext) -> None:
    await subscribe_and_reply(ctx, "jobs")


async def handle_subscribe_preset(ctx: VkRouteContext) -> None:
    text = ctx.text_lower
    if "дрова" in text:
        preset = "firewood"
    elif "огород" in text:
        preset = "garden"
    elif "сосед" in text or "помощ" in text:
        preset = "neighbor"
    elif "услуг" in text or "мастер" in text:
        preset = "services"
    else:
        preset = "services"
    await subscribe_and_reply(ctx, preset)


async def handle_subscribe_custom(ctx: VkRouteContext) -> None:
    raw = ctx.text_lower.removeprefix("подписка").strip()
    await subscribe_and_reply(ctx, raw or "all")


async def handle_unsubscribe(ctx: VkRouteContext) -> None:
    msg = await unsubscribe_peer(ctx.db, ctx.peer_id)
    await send_welcome(ctx, msg)


async def handle_ai_enter(ctx: VkRouteContext) -> None:
    await enter_ai_mode(ctx.db, ctx.peer_id)
    await send_ai(ctx, ai_enter_text())


async def handle_ai_examples(ctx: VkRouteContext) -> None:
    await send_ai(ctx, box("Примеры для ИИ", AI_EXAMPLES))


async def handle_ai_images(ctx: VkRouteContext) -> None:
    await send_ai(
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
    await send_welcome(ctx, "Вернулись в меню 🪶")


async def handle_jobs(ctx: VkRouteContext) -> None:
    msg = await format_jobs_message(ctx.db)
    await send_with_site_links(ctx.peer_id, msg, ("💼 Вакансии", "/jobs"))


async def handle_routes(ctx: VkRouteContext) -> None:
    await send_with_site_links(ctx.peer_id, format_routes_message(0), ("🗺 На карте", "/map"))


async def handle_routes_page(ctx: VkRouteContext) -> None:
    page = int(ctx.text_lower.split()[-1]) - 1
    await send_with_site_links(ctx.peer_id, format_routes_message(page), ("🗺 На карте", "/map"))


async def handle_map_report(ctx: VkRouteContext) -> None:
    await start_flow_message(ctx, await start_map_report_flow(ctx.db, ctx.peer_id))


async def handle_classified_add(ctx: VkRouteContext) -> None:
    msg = await start_classified_flow(ctx.db, ctx.peer_id)
    await send_message(
        ctx.peer_id,
        f"{msg}\n\n🌐 Форма на сайте: {public_site_url()}/classifieds?new=1",
        keyboard=get_welcome_keyboard(),
    )


async def handle_classified_jobs(ctx: VkRouteContext) -> None:
    await start_flow_message(ctx, await start_classified_flow(ctx.db, ctx.peer_id, jobs=True))


async def handle_wish(ctx: VkRouteContext) -> None:
    await start_flow_message(ctx, await start_wish_flow(ctx.db, ctx.peer_id))


async def handle_taxi(ctx: VkRouteContext) -> None:
    await reply_taxi(
        ctx.db,
        ctx.peer_id,
        header="🚕 Такси посёлка:\n",
        empty_line="Справочник обновляется. Напишите «аптека» или откройте карту.",
    )


async def handle_complaints_info(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box("Обращения жителей", COMPLAINTS_INFO_VK),
        (LINK_SUBMIT_COMPLAINT, "/complaints"),
        (LINK_COMPLAINTS, "/complaints"),
    )


async def handle_events(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box(
            "Афиша Пушкиногорья",
            "Концерты в посёлке, праздники и кино в Пскове — на одной странице.",
        ),
        (LINK_EVENTS, "/events"),
    )


async def handle_register(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box(
            "Регистрация",
            "🏠 Житель · 🏢 Организация\n"
            "🏛 Администрация / ЖКХ · 💇 Мастер услуг",
        ),
        ("✍️ Регистрация", "/register"),
    )


async def handle_site(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box("Портал посёлка", f"{public_site_url()}\n\nАфиша · Карта · Объявления · Обращения · ИИ"),
        (LINK_EVENTS, "/events"),
        (LINK_MAP, "/map"),
        (LINK_CLASSIFIEDS, "/classifieds"),
    )


async def handle_map(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box(
            "Карта посёлка",
            "Магазины, аптеки, кафе, АЗС, гостиницы, маршруты.\n"
            "Напишите: «аптека», «магазин», «заправка», «музей»",
        ),
        (LINK_MAP, "/map"),
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
        await send_with_site_links(
            ctx.peer_id,
            "📋 Обращений пока нет.\n\nОпишите проблему — примем заявку!",
            (LINK_COMPLAINTS, "/complaints"),
        )
        return

    lines = ["📋 Ваши обращения:\n"]
    for issue in issues:
        emoji = ISSUE_STATUS_EMOJI.get(issue.status, "📋")
        status_val = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
        hint = issue_status_hint(status_val)
        lines.append(f"{emoji} #{issue.id} — {issue_display_summary(issue, max_len=50)}")
        if hint:
            lines.append(f"   {hint}")
    latest = issues[0]
    await send_with_site_links(
        ctx.peer_id,
        "\n".join(lines),
        (LINK_COMPLAINTS, f"/complaints?issue={latest.id}"),
    )


async def handle_cabinet(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        box(
            "Личный кабинет",
            "На сайте — ваши обращения, профиль и быстрые ссылки.\n"
            "Войдите по логину, который указали при регистрации.",
        ),
        (LINK_CABINET, "/cabinet/login"),
        (LINK_COMPLAINTS, "/complaints"),
    )


async def handle_help(ctx: VkRouteContext) -> None:
    await send_with_site_links(
        ctx.peer_id,
        help_text(),
        (LINK_SUBMIT_CLASSIFIED, "/classifieds?new=1"),
        (LINK_SUBMIT_COMPLAINT, "/complaints"),
        (LINK_EVENTS, "/events"),
    )


async def handle_weather(ctx: VkRouteContext) -> None:
    try:
        snapshot = await get_weather()
    except WeatherFetchError:
        await send_welcome(
            ctx,
            "🌤 Прогноз временно недоступен. Попробуйте позже или откройте сайт.",
        )
        return

    if looks_like_hourly_weather(ctx.text_lower):
        message = format_weather_vk_hourly(snapshot)
    else:
        message = format_weather_vk_current(snapshot)

    await send_with_site_links(
        ctx.peer_id,
        box("Погода", message),
        (LINK_EVENTS, "/events"),
    )


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "welcome": handle_welcome,
    "classifieds": handle_classifieds,
    "services": handle_services,
    "subscribe_all": handle_subscribe_all,
    "subscribe_jobs": handle_subscribe_jobs,
    "subscribe_preset": handle_subscribe_preset,
    "subscribe_custom": handle_subscribe_custom,
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
    "cabinet": handle_cabinet,
    "events": handle_events,
    "weather": handle_weather,
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
    "подписка огород": "subscribe_preset",
    "подписка сосед": "subscribe_preset",
    "подписка neighbor": "subscribe_preset",
    "подписка garden": "subscribe_preset",
    "подписка firewood": "subscribe_preset",
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
    "🌤 погода": "weather",
    "погода": "weather",
    "прогноз": "weather",
    "погода на завтра": "weather",
    "почасовая погода": "weather",
    "почасовой прогноз": "weather",
    "📋 мои обращения": "my_issues",
    "мои обращения": "my_issues",
    "статус обращения": "my_issues",
    "статус заявки": "my_issues",
    "🪶 кабинет": "cabinet",
    "кабинет": "cabinet",
    "личный кабинет": "cabinet",
    "мой кабинет": "cabinet",
    "📅 афиша": "events",
    "афиша": "events",
    "события": "events",
    "событие": "events",
    "кино": "events",
    "мероприятия": "events",
    "ℹ️ помощь": "help",
    "помощь": "help",
}
