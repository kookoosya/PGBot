"""Shared VK flow helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.vk.flow_store import clear_flow as clear_flow_state
from app.services.vk.flow_store import get_flow as get_flow_state

CANCEL_WORDS = frozenset({"отмена", "стоп", "меню", "🏠 меню"})


async def clear_flow(db: AsyncSession, peer_id: int) -> None:
    """Завершить активный сценарий для peer_id."""
    await clear_flow_state(db, peer_id)


async def get_flow(db: AsyncSession, peer_id: int) -> dict[str, Any] | None:
    """Получить активный сценарий для peer_id."""
    return await get_flow_state(db, peer_id)


def is_cancel_message(text: str) -> bool:
    return text.lower().strip() in CANCEL_WORDS


async def cancel_flow(db: AsyncSession, peer_id: int) -> str:
    await clear_flow_state(db, peer_id)
    return "Отменено. Напишите «меню»."
