from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PlaceCategory, ShopComplaintType


class Place(Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    category: Mapped[PlaceCategory] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    website: Mapped[str | None] = mapped_column(String(500))
    opening_hours: Mapped[str | None] = mapped_column(String(500))
    osm_id: Mapped[str | None] = mapped_column(String(50), unique=True, index=True)
    external_source: Mapped[str | None] = mapped_column(String(30))
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reviews: Mapped[list["PlaceReview"]] = relationship(back_populates="place", cascade="all, delete-orphan")
    complaints: Mapped[list["PlaceComplaint"]] = relationship(back_populates="place")


class PlaceReview(Base):
    __tablename__ = "place_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    author_name: Mapped[str | None] = mapped_column(String(255))
    vk_id: Mapped[int | None] = mapped_column(BigInteger)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    place: Mapped["Place"] = relationship(back_populates="reviews")


class PlaceComplaint(Base):
    __tablename__ = "place_complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_id: Mapped[int | None] = mapped_column(ForeignKey("issues.id", ondelete="SET NULL"))
    complaint_type: Mapped[ShopComplaintType] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_tagged: Mapped[str | None] = mapped_column(String(50))
    price_charged: Mapped[str | None] = mapped_column(String(50))
    receipt_info: Mapped[str | None] = mapped_column(Text)
    author_name: Mapped[str | None] = mapped_column(String(255))
    vk_id: Mapped[int | None] = mapped_column(BigInteger)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(30), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    place: Mapped["Place"] = relationship(back_populates="complaints")
