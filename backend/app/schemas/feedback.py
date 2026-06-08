from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    message: str = Field(min_length=5, max_length=4000)
    contact: str | None = Field(default=None, max_length=200)
    page: str | None = Field(default=None, max_length=120)


class FeedbackItem(BaseModel):
    id: int
    message: str
    contact: str | None
    page: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackListResponse(BaseModel):
    items: list[FeedbackItem]
    total: int
