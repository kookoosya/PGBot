"""Состояние многошаговых VK-сценариев (объявления, пожелания, ошибки карты)."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VkFlowState(Base):
    __tablename__ = "vk_flow_states"

    peer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    step: Mapped[str] = mapped_column(String(32), nullable=False)
    data: Mapped[str] = mapped_column(Text, default="{}", server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
