"""VK community chat moderation state and violation log."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VkUserModeration(Base):
    """Per-user warning count and ban window for VK bot chat."""

    __tablename__ = "vk_user_moderation"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    peer_id: Mapped[int] = mapped_column(Integer, index=True)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    banned_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_violation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class VkModerationLog(Base):
    """Audit trail of moderation actions in VK bot."""

    __tablename__ = "vk_moderation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_user_id: Mapped[int] = mapped_column(Integer, index=True)
    peer_id: Mapped[int] = mapped_column(Integer, index=True)
    message_excerpt: Mapped[str] = mapped_column(String(500))
    reason: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(20))
    warning_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
