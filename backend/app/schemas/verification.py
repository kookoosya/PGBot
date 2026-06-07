from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole, VerificationStatus


class OfficialRegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=10, max_length=20)
    organization: str = Field(min_length=2, max_length=255)
    position: str = Field(min_length=2, max_length=255)
    role: UserRole = Field(description="administration, social_service или moderator")
    verification_note: str | None = Field(
        None,
        max_length=500,
        description="Комментарий: должность, контакты для проверки",
    )


class VerificationRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    full_name: str | None
    phone: str | None
    organization: str | None
    position: str | None
    role: UserRole
    verification_status: VerificationStatus
    verification_note: str | None
    created_at: datetime


class VerificationAction(BaseModel):
    note: str | None = None
