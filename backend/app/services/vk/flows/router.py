"""Route VK messages through active multi-step flows."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.vk.flow_store import get_flow as get_flow_state

from .classified import handle_classified_flow
from .common import cancel_flow, is_cancel_message
from .map_report import handle_map_report_flow
from .wish import handle_wish_flow


async def handle_flow_message(
    db: AsyncSession,
    peer_id: int,
    from_id: int,
    text: str,
) -> str | None:
    """Обработать сообщение в активном сценарии. None — сценарий не активен."""
    flow = await get_flow_state(db, peer_id)
    if not flow:
        return None

    if is_cancel_message(text):
        return await cancel_flow(db, peer_id)

    kind = flow["kind"]
    if kind == "wish":
        return await handle_wish_flow(db, peer_id, from_id, text, flow)
    if kind == "classified":
        return await handle_classified_flow(db, peer_id, from_id, text, flow)
    if kind == "map_report":
        return await handle_map_report_flow(db, peer_id, text, flow)

    return None
