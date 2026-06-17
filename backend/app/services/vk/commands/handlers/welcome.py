"""Welcome / menu commands."""

from app.services.vk.ai_history import clear_ai_history
from app.services.vk.client import get_welcome_message
from app.services.vk.context import VkRouteContext
from app.services.vk.flows import clear_flow
from app.services.vk.helpers import send_welcome


async def handle_welcome(ctx: VkRouteContext) -> None:
    """Меню / главная / start."""
    await clear_flow(ctx.db, ctx.peer_id)
    await clear_ai_history(ctx.db, ctx.peer_id)
    await send_welcome(ctx, get_welcome_message())
