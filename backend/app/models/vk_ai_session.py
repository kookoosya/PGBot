from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VkAiSession(Base):
    __tablename__ = "vk_ai_sessions"

    peer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    messages: Mapped[str] = mapped_column(Text, default="[]", server_default="[]")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
