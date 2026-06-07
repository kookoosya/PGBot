from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: EmailStr | None = None
    password: str = Field(min_length=6)
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
    created_at: datetime
