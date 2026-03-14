"""Pydantic schemas for notification API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """Response schema for a single notification."""

    id: UUID
    recipient_id: UUID
    notification_type: str
    subject: str
    body: str
    data: dict | None = None
    priority: str = "normal"
    channels_delivered: str | None = None
    is_read: bool = False
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    pages: int


class NotificationMarkReadResponse(BaseModel):
    """Response for marking notifications as read."""

    success: bool
    message: str
    count: int = 1
