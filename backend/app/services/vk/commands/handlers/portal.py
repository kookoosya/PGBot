"""Portal navigation, services, weather and help."""

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
from app.services.site_urls import public_site_url
from app.services.vk.context import VkRouteContext
from app.services.vk.helpers import send_welcome, send_with_site_links
from app.services.vk.messages import box, help_text
from app.services.weather import (
    WeatherFetchError,
    format_weather_vk_current,
    format_weather_vk_hourly,
    get_weather,
    looks_like_hourly_weather,
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
