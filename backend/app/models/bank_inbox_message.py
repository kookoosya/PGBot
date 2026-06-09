from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BankInboxMessage(Base):
    __tablename__ = "bank_inbox_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
