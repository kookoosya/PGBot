from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Event(Base):
    """Village events shown on the landing page (concerts, holidays, etc.)."""

    __tablename__ = "village_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(50), default="other", server_default="other", index=True)
    source: Mapped[str | None] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
