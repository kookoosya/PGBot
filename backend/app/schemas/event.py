"""Village event schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import EventCategory


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    location: str | None = Field(None, max_length=500)
    category: EventCategory = EventCategory.OTHER
    source: str | None = Field(None, max_length=100)
    source_url: str | None = Field(None, max_length=1000)
    is_published: bool = True


class EventUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location: str | None = Field(None, max_length=500)
    category: EventCategory | None = None
    source: str | None = Field(None, max_length=100)
    source_url: str | None = Field(None, max_length=1000)
    is_published: bool | None = None


class EventResponse(BaseModel):
    id: int
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    starts_at_label: str
    ends_at_label: str | None = None
    location: str | None
    category: str
    category_label: str
    source: str | None
    source_url: str | None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
