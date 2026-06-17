"""VK flow: site feedback / wishes."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_feedback import SiteFeedback
from app.services.site_urls import public_site_url
from app.services.vk.flow_store import clear_flow as clear_flow_state
from app.services.vk.flow_store import save_flow
from app.services.vk.messages import box


async def start_wish_flow(db: AsyncSession, peer_id: int) -> str:
    await save_flow(db, peer_id, {"kind": "wish", "step": "message", "data": {}})
    return box(
        "Пожелание",
        "Напишите идею или пожелание для портала — что улучшить, что добавить.\n\n"
        "«Отмена» — выйти.",
    )


async def handle_wish_flow(
    db: AsyncSession,
    peer_id: int,
    from_id: int,
    text: str,
    flow: dict[str, Any],
) -> str:
    msg = text.strip()
    if len(msg) < 5:
        return "Слишком коротко. Опишите пожелание подробнее или «отмена»."
    row = SiteFeedback(
        message=msg,
        contact=f"vk:{from_id}",
        page="vk-bot",
        visitor_key=f"vk_{from_id}",
    )
    db.add(row)
    await db.flush()
    await clear_flow_state(db, peer_id)
    return box(
        "Спасибо!",
        "Пожелание принято. Учтём при развитии портала.\n\n"
        f"Ещё идеи — кнопка «💡 Пожелания» или {public_site_url()}/wishes",
    )
