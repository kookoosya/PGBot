from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ClassifiedCategory, ClassifiedPaymentStatus


class ClassifiedAd(Base):
    __tablename__ = "classified_ads"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[ClassifiedCategory] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[int | None] = mapped_column(Integer)
    price_unit: Mapped[str | None] = mapped_column(String(50))
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    vk_id: Mapped[int | None] = mapped_column(BigInteger)
    contact_telegram: Mapped[str | None] = mapped_column(String(100))
    contact_vk: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=False)
    payment_status: Mapped[ClassifiedPaymentStatus] = mapped_column(String(20), default=ClassifiedPaymentStatus.PENDING)
    payment_reference: Mapped[str | None] = mapped_column(String(200))
    placement_fee: Mapped[int] = mapped_column(Integer, default=150)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
