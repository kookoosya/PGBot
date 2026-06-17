"""Subscription commands."""

from app.services.vk.bot import unsubscribe_peer
from app.services.vk.context import VkRouteContext
from app.services.vk.helpers import send_welcome, subscribe_and_reply


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
