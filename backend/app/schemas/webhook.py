"""Webhook schemas for API request/response validation."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ============================================================================
# Webhook Schemas
# ============================================================================


class WebhookCreate(BaseModel):
    """Schema for creating a webhook."""

    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    name: str = Field(..., min_length=1, max_length=255, description="Webhook name")
    description: str | None = Field(None, description="Optional description")
    event_types: list[str] = Field(..., min_length=1, description="Event types to subscribe to")
    secret: str | None = Field(None, min_length=32, description="Shared secret (auto-generated if not provided)")
    custom_headers: dict[str, str] | None = Field(None, description="Custom headers for requests")
    timeout_seconds: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(5, ge=0, le=10, description="Maximum retry attempts")
    metadata: dict[str, Any] | None = Field(None, description="Optional metadata")

    @field_validator('event_types')
    @classmethod
    def validate_event_types(cls, v: list[str]) -> list[str]:
        """Ensure event types are unique."""
        return list(set(v))


class WebhookUpdate(BaseModel):
    """Schema for updating a webhook."""

    url: HttpUrl | None = None
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    event_types: list[str] | None = Field(None, min_length=1)
    secret: str | None = Field(None, min_length=32)
    custom_headers: dict[str, str] | None = None
    timeout_seconds: int | None = Field(None, ge=1, le=300)
    max_retries: int | None = Field(None, ge=0, le=10)
    metadata: dict[str, Any] | None = None

    @field_validator('event_types')
    @classmethod
    def validate_event_types(cls, v: list[str] | None) -> list[str] | None:
        """Ensure event types are unique."""
        if v is not None:
            return list(set(v))
        return v


class WebhookResponse(BaseModel):
    """Schema for webhook response."""

    id: UUID
    url: str
    name: str
    description: str | None
    event_types: list[str]
    status: str
    retry_enabled: bool
    max_retries: int
    timeout_seconds: int
    custom_headers: dict[str, str]
    metadata: dict[str, Any]
    owner_id: UUID | None
    created_at: datetime
    updated_at: datetime
    last_triggered_at: datetime | None

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Schema for webhook list response."""

    webhooks: list[WebhookResponse]
    total: int
    skip: int
    limit: int


# ============================================================================
# Webhook Delivery Schemas
# ============================================================================


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response."""

    id: UUID
    webhook_id: UUID
    event_type: str
    event_id: str | None
    payload: dict[str, Any]
    status: str
    attempt_count: int
    max_attempts: int
    next_retry_at: datetime | None
    http_status_code: int | None
    response_body: str | None
    response_time_ms: int | None
    error_message: str | None
    created_at: datetime
    first_attempted_at: datetime | None
    last_attempted_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class WebhookDeliveryListResponse(BaseModel):
    """Schema for delivery list response."""

    deliveries: list[WebhookDeliveryResponse]
    total: int
    skip: int
    limit: int


class WebhookDeliveryRetryRequest(BaseModel):
    """Schema for retry request."""

    delivery_id: UUID = Field(..., description="Delivery ID to retry")


# ============================================================================
# Event Trigger Schemas
# ============================================================================


class WebhookEventTrigger(BaseModel):
    """Schema for manually triggering a webhook event."""

    event_type: str = Field(..., description="Event type to trigger")
    payload: dict[str, Any] = Field(..., description="Event payload")
    event_id: str | None = Field(None, description="Optional event identifier")
    immediate: bool = Field(False, description="Attempt immediate delivery")


class WebhookEventTriggerResponse(BaseModel):
    """Schema for event trigger response."""

    event_type: str
    webhooks_triggered: int
    message: str


# ============================================================================
# Dead Letter Schemas
# ============================================================================


class WebhookDeadLetterResponse(BaseModel):
    """Schema for dead letter response."""

    id: UUID
    delivery_id: UUID
    webhook_id: UUID
    event_type: str
    payload: dict[str, Any]
    total_attempts: int
    last_error_message: str | None
    last_http_status: int | None
    resolved: bool
    resolved_at: datetime | None
    resolved_by: UUID | None
    resolution_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeadLetterListResponse(BaseModel):
    """Schema for dead letter list response."""

    dead_letters: list[WebhookDeadLetterResponse]
    total: int
    skip: int
    limit: int


class WebhookDeadLetterResolveRequest(BaseModel):
    """Schema for resolving a dead letter."""

    notes: str | None = Field(None, description="Resolution notes")
    retry: bool = Field(False, description="Retry the delivery after resolving")


# ============================================================================
# Statistics Schemas
# ============================================================================


class WebhookStatistics(BaseModel):
    """Schema for webhook statistics."""

    webhook_id: UUID
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    pending_deliveries: int
    dead_letter_count: int
    success_rate: float
    average_response_time_ms: float | None


class WebhookStatisticsResponse(BaseModel):
    """Schema for webhook statistics response."""

    statistics: WebhookStatistics
