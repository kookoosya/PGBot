"""VK moderation admin schemas."""

from datetime import datetime

from pydantic import BaseModel


class VkModerationStateResponse(BaseModel):
    vk_user_id: int
    peer_id: int
    warning_count: int
    banned_until: datetime | None
    last_violation_at: datetime | None
    updated_at: datetime


class VkModerationLogResponse(BaseModel):
    id: int
    vk_user_id: int
    peer_id: int
    message_excerpt: str
    reason: str
    action: str
    warning_number: int
    created_at: datetime


class VkModerationOverviewResponse(BaseModel):
    states: list[VkModerationStateResponse]
    recent_logs: list[VkModerationLogResponse]
