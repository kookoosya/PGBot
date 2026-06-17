"""Classified ads, jobs and wishes."""

from app.constants.portal_copy import LINK_CLASSIFIEDS, LINK_SUBMIT_CLASSIFIED
from app.services.site_urls import public_site_url
from app.services.vk.bot import format_ads_message
from app.services.vk.client import get_welcome_keyboard, send_message
from app.services.vk.context import VkRouteContext
from app.services.vk.flows import (
    format_jobs_message,
    start_classified_flow,
    start_wish_flow,
)
from app.services.vk.helpers import send_with_site_links, start_flow_message


async def handle_classifieds(ctx: VkRouteContext) -> None:
    msg = await format_ads_message(ctx.db)
    await send_with_site_links(
        ctx.peer_id,
        msg,
        (LINK_CLASSIFIEDS, "/classifieds"),
        (LINK_SUBMIT_CLASSIFIED, "/classifieds?new=1"),
        ("💼 Вакансии", "/jobs"),
    )


async def handle_jobs(ctx: VkRouteContext) -> None:
    msg = await format_jobs_message(ctx.db)
    await send_with_site_links(ctx.peer_id, msg, ("💼 Вакансии", "/jobs"))


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
