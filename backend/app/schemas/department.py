from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    telegram_chat_id: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    telegram_chat_id: str | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    contact_email: str | None
    contact_phone: str | None
    telegram_chat_id: str | None
    is_active: bool
    created_at: datetime
