from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_valid: Mapped[bool] = mapped_column(default=True)
    category: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[str | None] = mapped_column(String(20))
    summary: Mapped[str | None] = mapped_column(Text)
    duplicate_probability: Mapped[float | None] = mapped_column(Float)
    suggested_department: Mapped[str | None] = mapped_column(String(255))
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped["Issue"] = relationship(back_populates="ai_analysis")


from app.models.issue import Issue  # noqa: E402
