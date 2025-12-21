"""WebSocket event types and schemas for real-time updates."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """WebSocket event types."""

    SCHEDULE_UPDATED = "schedule_updated"
    ASSIGNMENT_CHANGED = "assignment_changed"
    SWAP_REQUESTED = "swap_requested"
    SWAP_APPROVED = "swap_approved"
    CONFLICT_DETECTED = "conflict_detected"
    RESILIENCE_ALERT = "resilience_alert"
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"


class WebSocketEvent(BaseModel):
    """Base class for all WebSocket events."""

    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ScheduleUpdatedEvent(BaseModel):
    """Event for schedule updates."""

    event_type: EventType = EventType.SCHEDULE_UPDATED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    schedule_id: Optional[UUID] = None
    academic_year_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    update_type: str  # "generated", "modified", "regenerated"
    affected_blocks_count: int = 0
    message: str = ""

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class AssignmentChangedEvent(BaseModel):
    """Event for assignment changes."""

    event_type: EventType = EventType.ASSIGNMENT_CHANGED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    assignment_id: UUID
    person_id: UUID
    block_id: UUID
    rotation_template_id: Optional[UUID] = None
    change_type: str  # "created", "updated", "deleted"
    changed_by: Optional[UUID] = None
    message: str = ""

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class SwapRequestedEvent(BaseModel):
    """Event for swap requests."""

    event_type: EventType = EventType.SWAP_REQUESTED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    swap_id: UUID
    requester_id: UUID
    target_person_id: Optional[UUID] = None
    swap_type: str  # "one_to_one", "absorb"
    affected_assignments: list[UUID] = Field(default_factory=list)
    message: str = ""

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class SwapApprovedEvent(BaseModel):
    """Event for swap approvals."""

    event_type: EventType = EventType.SWAP_APPROVED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    swap_id: UUID
    requester_id: UUID
    target_person_id: Optional[UUID] = None
    approved_by: UUID
    affected_assignments: list[UUID] = Field(default_factory=list)
    message: str = ""

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ConflictDetectedEvent(BaseModel):
    """Event for conflict detection."""

    event_type: EventType = EventType.CONFLICT_DETECTED
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    conflict_id: Optional[UUID] = None
    person_id: UUID
    conflict_type: str  # "double_booking", "acgme_violation", "absence_overlap"
    severity: str  # "low", "medium", "high", "critical"
    affected_blocks: list[UUID] = Field(default_factory=list)
    message: str = ""

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ResilienceAlertEvent(BaseModel):
    """Event for resilience system alerts."""

    event_type: EventType = EventType.RESILIENCE_ALERT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    alert_type: str  # "utilization_high", "n1_failure", "n2_failure", "defense_level_change"
    severity: str  # "green", "yellow", "orange", "red", "black"
    current_utilization: Optional[float] = None
    defense_level: Optional[str] = None
    affected_persons: list[UUID] = Field(default_factory=list)
    message: str = ""
    recommendations: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class ConnectionAckEvent(BaseModel):
    """Event acknowledging successful connection."""

    event_type: EventType = EventType.CONNECTION_ACK
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: UUID
    message: str = "Connection established"

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class PingEvent(BaseModel):
    """Ping event for keepalive."""

    event_type: EventType = EventType.PING
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class PongEvent(BaseModel):
    """Pong event response to ping."""

    event_type: EventType = EventType.PONG
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
