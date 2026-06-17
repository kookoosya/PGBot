"""Map, routes and taxi commands."""

from app.services.vk.context import VkRouteContext
from app.services.vk.flows import format_routes_message, start_map_report_flow
from app.services.vk.helpers import reply_taxi, send_with_site_links, start_flow_message


async def handle_routes(ctx: VkRouteContext) -> None:
    await send_with_site_links(ctx.peer_id, format_routes_message(0), ("🗺 На карте", "/map"))


async def handle_routes_page(ctx: VkRouteContext) -> None:
    page = int(ctx.text_lower.split()[-1]) - 1
    await send_with_site_links(ctx.peer_id, format_routes_message(page), ("🗺 На карте", "/map"))


async def handle_map_report(ctx: VkRouteContext) -> None:
    await start_flow_message(ctx, await start_map_report_flow(ctx.db, ctx.peer_id))


async def handle_taxi(ctx: VkRouteContext) -> None:
    await reply_taxi(
        ctx.db,
        ctx.peer_id,
        header="🚕 Такси посёлка:\n",
        empty_line="Справочник обновляется. Напишите «аптека» или откройте карту.",
    )
