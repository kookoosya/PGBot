from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PageVisit(Base):
    __tablename__ = "page_visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    visitor_key: Mapped[str | None] = mapped_column(String(64), index=True)
    user_agent: Mapped[str | None] = mapped_column(String(300))
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
