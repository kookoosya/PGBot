from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IssueCategory, IssueStatus, Priority


class IssuePhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    created_at: datetime


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_valid: bool
    category: str | None
    priority: str | None
    summary: str | None
    duplicate_probability: float | None
    suggested_department: str | None


class IssueCommentCreate(BaseModel):
    text: str = Field(min_length=1)
    is_internal: bool = False


class IssueCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    is_internal: bool
    author_id: int
    created_at: datetime


class IssueCreate(BaseModel):
    description: str = Field(min_length=5)
    address: str | None = None
    category: IssueCategory | None = None


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    category: IssueCategory | None = None
    priority: Priority | None = None
    department_id: int | None = None
    assignee_id: int | None = None


class IssueStatusUpdate(BaseModel):
    status: IssueStatus
    resolution_text: str | None = None


class IssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    description: str
    status: IssueStatus
    category: IssueCategory | None
    priority: Priority
    address: str | None
    resident_id: int | None
    department_id: int | None
    assignee_id: int | None
    parent_issue_id: int | None
    confirmation_count: int
    is_spam: bool
    resolution_text: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    photos: list[IssuePhotoResponse] = []
    ai_analysis: AIAnalysisResponse | None = None


class IssueListResponse(BaseModel):
    items: list[IssueResponse]
    total: int
    page: int
    page_size: int
