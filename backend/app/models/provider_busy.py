from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProviderBusyBlock(Base):
    """Мастер сам отмечает занятое время."""

    __tablename__ = "provider_busy_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False)
    block_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
