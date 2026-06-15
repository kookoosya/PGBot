"""Контекст маршрутизации входящего VK-сообщения."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class VkRouteContext:
    """Данные одного входящего сообщения VK для обработчиков команд."""

    db: AsyncSession
    peer_id: int
    from_id: int
    text: str
    text_lower: str
    parsed: dict[str, Any] | None = None

    @classmethod
    def from_parsed(cls, db: AsyncSession, parsed: dict[str, Any]) -> VkRouteContext:
        text = parsed["text"]
        return cls(
            db=db,
            peer_id=parsed["peer_id"],
            from_id=parsed["from_id"],
            text=text,
            text_lower=text.lower(),
            parsed=parsed,
        )

    def update_text(self, text: str) -> None:
        self.text = text
        self.text_lower = text.lower()


CommandHandler = Callable[[VkRouteContext], Awaitable[None]]
