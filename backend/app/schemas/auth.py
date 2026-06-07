from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole, VerificationStatus


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr | None = None
    password: str = Field(min_length=10, max_length=128)
    full_name: str | None = None
    phone: str | None = None
    role: UserRole = UserRole.RESIDENT
    department_id: int | None = None


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    role: UserRole | None = None
    department_id: int | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str | None
    full_name: str | None
    phone: str | None
    vk_id: int | None
    role: UserRole
    department_id: int | None
    is_active: bool
    organization: str | None = None
    position: str | None = None
    verification_status: VerificationStatus | None = None
    created_at: datetime
