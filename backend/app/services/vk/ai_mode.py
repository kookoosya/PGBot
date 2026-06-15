"""Персистентное хранилище AI-режима VK-бота."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vk_ai_mode import VkAiMode


async def _enter_ai_mode(db: AsyncSession, peer_id: int) -> None:
    """Включить AI-режим для peer_id (идемпотентно)."""
    result = await db.execute(select(VkAiMode).where(VkAiMode.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row is None:
        db.add(VkAiMode(peer_id=peer_id))
        await db.flush()


async def _exit_ai_mode(db: AsyncSession, peer_id: int) -> None:
    """Выключить AI-режим для peer_id."""
    result = await db.execute(select(VkAiMode).where(VkAiMode.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()


async def _is_ai_mode(db: AsyncSession, peer_id: int) -> bool:
    """Проверить, активен ли AI-режим для peer_id."""
    result = await db.execute(select(VkAiMode.peer_id).where(VkAiMode.peer_id == peer_id))
    return result.scalar_one_or_none() is not None


async def get_active_ai_peers(db: AsyncSession) -> list[int]:
    """Список peer_id в AI-режиме (для отладки и мониторинга)."""
    result = await db.execute(select(VkAiMode.peer_id))
    return [int(peer_id) for peer_id in result.scalars().all()]


async def enter_ai_mode(db: AsyncSession, peer_id: int) -> None:
    """Включить AI-режим для peer_id."""
    await _enter_ai_mode(db, peer_id)


async def exit_ai_mode(db: AsyncSession, peer_id: int) -> None:
    """Выключить AI-режим для peer_id."""
    await _exit_ai_mode(db, peer_id)


async def is_ai_mode(db: AsyncSession, peer_id: int) -> bool:
    """Проверить, активен ли AI-режим для peer_id."""
    return await _is_ai_mode(db, peer_id)
