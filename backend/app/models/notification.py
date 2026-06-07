from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import NotificationPriority, NotificationStatus


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int | None] = mapped_column(ForeignKey("issues.id", ondelete="SET NULL"))
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    channel: Mapped[str] = mapped_column(String(50), default="telegram")
    priority: Mapped[NotificationPriority] = mapped_column(String(20), default=NotificationPriority.NORMAL)
    status: Mapped[NotificationStatus] = mapped_column(String(20), default=NotificationStatus.PENDING, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issue: Mapped["Issue | None"] = relationship()
    recipient: Mapped["User | None"] = relationship()


from app.models.issue import Issue  # noqa: E402
from app.models.user import User  # noqa: E402
