from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VkAiMode(Base):
    """Peer_id, находящийся в режиме ИИ-помощника VK-бота."""

    __tablename__ = "vk_ai_modes"

    peer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
