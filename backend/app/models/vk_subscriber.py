from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VkSubscriber(Base):
    """Подписчики VK-бота на новые объявления."""

    __tablename__ = "vk_subscribers"

    peer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    categories: Mapped[str] = mapped_column(String(80), default="all", server_default="all")
    last_digest_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
