"""AI mode state for VK bot peers — persisted in PostgreSQL."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.vk_ai_mode_store import enter_ai_mode as _enter_ai_mode
from app.services.vk_ai_mode_store import exit_ai_mode as _exit_ai_mode
from app.services.vk_ai_mode_store import is_ai_mode as _is_ai_mode


async def enter_ai_mode(db: AsyncSession, peer_id: int) -> None:
    """Включить AI-режим для peer_id."""
    await _enter_ai_mode(db, peer_id)


async def exit_ai_mode(db: AsyncSession, peer_id: int) -> None:
    """Выключить AI-режим для peer_id."""
    await _exit_ai_mode(db, peer_id)


async def is_ai_mode(db: AsyncSession, peer_id: int) -> bool:
    """Проверить, активен ли AI-режим для peer_id."""
    return await _is_ai_mode(db, peer_id)
