from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ServiceType, VerificationStatus


class ServiceItemInput(BaseModel):
    service_type: ServiceType
    name: str = Field(min_length=2, max_length=255)
    duration_minutes: int = Field(ge=15, le=480, default=60)
    price: int | None = Field(None, ge=0)
    description: str | None = None


class ScheduleItemInput(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str  # "09:00"
    end_time: str    # "18:00"
    is_working: bool = True


class ProviderRegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=10, max_length=20)
    email: str | None = None
    password: str = Field(min_length=6)
    username: str = Field(min_length=3, max_length=100)
    bio: str | None = None
    address: str | None = None
    services: list[ServiceItemInput] = Field(min_length=1)
    schedule: list[ScheduleItemInput] = Field(min_length=1)


class ProviderServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_type: ServiceType
    service_label: str = ""
    name: str
    description: str | None
    duration_minutes: int
    price: int | None


class ScheduleResponse(BaseModel):
    day_of_week: int
    day_label: str
    start_time: str
    end_time: str
    is_working: bool


class ProviderListItem(BaseModel):
    id: int
    full_name: str
    phone: str
    bio: str | None
    address: str | None
    avg_rating: float
    review_count: int
    services: list[ProviderServiceResponse]
    status_today: str  # free, busy, off
    next_free_slot: str | None = None


class ProviderDetailResponse(ProviderListItem):
    schedule: list[ScheduleResponse]
    verification_status: VerificationStatus


class TimeSlot(BaseModel):
    time: str
    available: bool
    label: str


class SlotsResponse(BaseModel):
    date: date
    provider_id: int
    provider_name: str
    slots: list[TimeSlot]
    working_hours: str | None


class BookAppointmentRequest(BaseModel):
    service_id: int
    appointment_date: date
    start_time: str  # "14:00"
    client_name: str = Field(min_length=2, max_length=255)
    client_phone: str = Field(min_length=10, max_length=20)
    notes: str | None = None


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_name: str
    service_name: str
    appointment_date: date
    start_time: str
    end_time: str
    status: str
    client_name: str


class UpdateScheduleRequest(BaseModel):
    schedule: list[ScheduleItemInput]
