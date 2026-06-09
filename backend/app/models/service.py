from datetime import date, datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import ServiceType, VerificationStatus


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    bio: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(String(500))
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id", ondelete="SET NULL"))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        String(30), default=VerificationStatus.PENDING
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    avg_rating: Mapped[float] = mapped_column(default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    services: Mapped[list["ProviderService"]] = relationship(back_populates="provider", cascade="all, delete-orphan")
    schedule: Mapped[list["ProviderSchedule"]] = relationship(back_populates="provider", cascade="all, delete-orphan")
    appointments: Mapped[list["ServiceAppointment"]] = relationship(back_populates="provider")


class ProviderService(Base):
    __tablename__ = "provider_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    price: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    provider: Mapped["ServiceProvider"] = relationship(back_populates="services")
    appointments: Mapped[list["ServiceAppointment"]] = relationship(back_populates="service")


class ProviderSchedule(Base):
    __tablename__ = "provider_schedule"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon, 6=Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, default=True)

    provider: Mapped["ServiceProvider"] = relationship(back_populates="schedule")


class ServiceAppointment(Base):
    __tablename__ = "service_appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("service_providers.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("provider_services.id", ondelete="CASCADE"), nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    client_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="booked")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    provider: Mapped["ServiceProvider"] = relationship(back_populates="appointments")
    service: Mapped["ProviderService"] = relationship(back_populates="appointments")
