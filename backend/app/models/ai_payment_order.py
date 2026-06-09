from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIPaymentOrder(Base):
    __tablename__ = "ai_payment_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_code: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    provider: Mapped[str] = mapped_column(String(32), default="yookassa")
    external_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    confirmation_url: Mapped[str | None] = mapped_column(Text)
    entitlement_id: Mapped[int | None] = mapped_column(
        ForeignKey("ai_entitlements.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    matched_reference: Mapped[str | None] = mapped_column(Text)
