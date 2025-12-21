"""
Event Schema Definitions

Pydantic schemas for event-related API operations including querying,
filtering, and serialization. These schemas are used for request/response
validation in event-related endpoints.

Note: This is separate from event_types.py which defines the actual event
domain objects. These schemas are for API communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.events.event_types import EventType


# =============================================================================
# Event Query and Filter Schemas
# =============================================================================


class EventSortOrder(str, Enum):
    """Sort order for event queries."""

    ASC = "asc"
    DESC = "desc"


class EventSortField(str, Enum):
    """Fields available for sorting events."""

    TIMESTAMP = "timestamp"
    EVENT_TYPE = "event_type"
    AGGREGATE_ID = "aggregate_id"
    AGGREGATE_TYPE = "aggregate_type"


class EventFilterRequest(BaseModel):
    """
    Request schema for filtering events.

    Supports filtering by multiple criteria to query specific events
    from the event store.
    """

    aggregate_id: Optional[str] = Field(
        None, description="Filter by specific aggregate (entity) ID"
    )
    aggregate_type: Optional[str] = Field(
        None, description="Filter by aggregate type (e.g., 'Schedule', 'Assignment')"
    )
    event_types: Optional[list[EventType]] = Field(
        None, description="Filter by specific event types"
    )
    user_id: Optional[str] = Field(None, description="Filter by user who triggered event")
    correlation_id: Optional[str] = Field(
        None, description="Filter by correlation ID (related events)"
    )
    causation_id: Optional[str] = Field(
        None, description="Filter by causation ID (event that caused this)"
    )
    start_timestamp: Optional[datetime] = Field(
        None, description="Filter events after this timestamp"
    )
    end_timestamp: Optional[datetime] = Field(
        None, description="Filter events before this timestamp"
    )
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(50, ge=1, le=1000, description="Number of events per page")
    sort_by: EventSortField = Field(
        EventSortField.TIMESTAMP, description="Field to sort by"
    )
    sort_order: EventSortOrder = Field(EventSortOrder.DESC, description="Sort order")

    @model_validator(mode="after")
    def validate_timestamp_range(self) -> "EventFilterRequest":
        """Ensure start_timestamp is before end_timestamp."""
        if (
            self.start_timestamp
            and self.end_timestamp
            and self.start_timestamp > self.end_timestamp
        ):
            raise ValueError(
                "start_timestamp must be before or equal to end_timestamp"
            )
        return self


class EventStreamRequest(BaseModel):
    """
    Request schema for streaming events.

    Used for real-time event subscriptions and replay scenarios.
    """

    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None
    event_types: Optional[list[EventType]] = None
    from_sequence: int = Field(
        0, ge=0, description="Start streaming from this sequence number"
    )
    max_events: Optional[int] = Field(
        None, ge=1, le=10000, description="Maximum events to stream"
    )
    include_snapshots: bool = Field(
        False, description="Include snapshot events in stream"
    )


class EventReplayRequest(BaseModel):
    """
    Request schema for replaying events to rebuild state.

    Replays events in order to reconstruct aggregate state at a specific point in time.
    """

    aggregate_id: str = Field(..., description="ID of aggregate to replay")
    up_to_timestamp: Optional[datetime] = Field(
        None, description="Replay events up to this timestamp"
    )
    up_to_sequence: Optional[int] = Field(
        None, ge=0, description="Replay events up to this sequence number"
    )
    include_metadata: bool = Field(
        True, description="Include event metadata in response"
    )

    @model_validator(mode="after")
    def validate_replay_criteria(self) -> "EventReplayRequest":
        """Ensure at least one replay criterion is specified."""
        if not self.up_to_timestamp and self.up_to_sequence is None:
            raise ValueError(
                "Must specify either up_to_timestamp or up_to_sequence for replay"
            )
        return self


# =============================================================================
# Event Response Schemas
# =============================================================================


class EventMetadataResponse(BaseModel):
    """
    Response schema for event metadata.

    Provides context about when, where, and why an event occurred.
    """

    event_id: str
    event_type: str
    event_version: int
    timestamp: datetime
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


class EventResponse(BaseModel):
    """
    Generic event response schema.

    Used for returning event data from API endpoints.
    """

    aggregate_id: str
    aggregate_type: str
    metadata: EventMetadataResponse
    data: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )
    sequence_number: Optional[int] = Field(
        None, description="Sequence number in event stream"
    )

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


class EventListResponse(BaseModel):
    """
    Paginated list of events.

    Used for event query results with pagination support.
    """

    events: list[EventResponse]
    total: int = Field(..., description="Total number of events matching filter")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of events per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")

    @model_validator(mode="after")
    def calculate_pagination_flags(self) -> "EventListResponse":
        """Calculate has_next and has_previous flags."""
        if not hasattr(self, "has_next"):
            self.has_next = self.page < self.pages
        if not hasattr(self, "has_previous"):
            self.has_previous = self.page > 1
        return self


# =============================================================================
# Schedule Event Schemas
# =============================================================================


class ScheduleEventData(BaseModel):
    """Data schema for schedule events."""

    schedule_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    published_by: Optional[str] = None
    algorithm_version: Optional[str] = None
    constraint_set: Optional[dict[str, Any]] = None
    changes: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    notification_sent: bool = False


class ScheduleEventResponse(EventResponse):
    """Response schema for schedule events."""

    data: ScheduleEventData


# =============================================================================
# Assignment Event Schemas
# =============================================================================


class AssignmentEventData(BaseModel):
    """Data schema for assignment events."""

    assignment_id: str
    person_id: Optional[str] = None
    block_id: Optional[str] = None
    rotation_id: Optional[str] = None
    role: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_by: Optional[str] = None
    schedule_id: Optional[str] = None
    changes: Optional[dict[str, Any]] = None
    previous_values: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    soft_delete: bool = True


class AssignmentEventResponse(EventResponse):
    """Response schema for assignment events."""

    data: AssignmentEventData


# =============================================================================
# Swap Event Schemas
# =============================================================================


class SwapEventData(BaseModel):
    """Data schema for swap events."""

    swap_id: str
    requester_id: Optional[str] = None
    requester_assignment_id: Optional[str] = None
    target_assignment_id: Optional[str] = None
    swap_type: Optional[str] = None  # "one_to_one" or "absorb"
    reason: Optional[str] = None
    approved_by: Optional[str] = None
    executed_by: Optional[str] = None
    approval_notes: Optional[str] = None
    assignment_changes: Optional[list[dict[str, Any]]] = None
    acgme_validated: bool = True


class SwapEventResponse(EventResponse):
    """Response schema for swap events."""

    data: SwapEventData


# =============================================================================
# Conflict Event Schemas
# =============================================================================


class ConflictEventData(BaseModel):
    """Data schema for conflict/ACGME violation events."""

    violation_id: Optional[str] = None
    person_id: Optional[str] = None
    violation_type: Optional[str] = None  # "80_hour", "1_in_7", "supervision_ratio"
    severity: Optional[str] = None  # "warning", "critical"
    detected_at: Optional[datetime] = None
    details: Optional[dict[str, Any]] = None
    override_id: Optional[str] = None
    assignment_id: Optional[str] = None
    override_reason: Optional[str] = None
    applied_by: Optional[str] = None
    justification: Optional[str] = None
    approval_level: Optional[str] = None  # "coordinator", "program_director"


class ConflictEventResponse(EventResponse):
    """Response schema for conflict and ACGME compliance events."""

    data: ConflictEventData


# =============================================================================
# User Event Schemas
# =============================================================================


class UserEventData(BaseModel):
    """Data schema for user/person events."""

    person_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    changes: Optional[dict[str, Any]] = None
    activation_status: Optional[bool] = None


class UserEventResponse(EventResponse):
    """Response schema for user/person events."""

    data: UserEventData


# =============================================================================
# Event Aggregation and Analytics Schemas
# =============================================================================


class EventCountByType(BaseModel):
    """Count of events by type."""

    event_type: str
    count: int
    percentage: float = Field(..., ge=0.0, le=100.0)


class EventCountByAggregate(BaseModel):
    """Count of events by aggregate type."""

    aggregate_type: str
    count: int
    percentage: float = Field(..., ge=0.0, le=100.0)


class EventCountByUser(BaseModel):
    """Count of events by user."""

    user_id: str
    username: Optional[str] = None
    count: int
    percentage: float = Field(..., ge=0.0, le=100.0)


class EventStatisticsResponse(BaseModel):
    """
    Statistical summary of events.

    Provides aggregated analytics about events in the system.
    """

    total_events: int
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    by_event_type: list[EventCountByType] = Field(default_factory=list)
    by_aggregate_type: list[EventCountByAggregate] = Field(default_factory=list)
    by_user: list[EventCountByUser] = Field(default_factory=list)
    events_per_day_avg: float = Field(0.0, ge=0.0)
    most_active_aggregate: Optional[str] = None
    most_active_user: Optional[str] = None


# =============================================================================
# Schema Versioning Support
# =============================================================================


class SchemaVersionInfo(BaseModel):
    """
    Information about an event schema version.

    Tracks schema evolution over time for backward compatibility.
    """

    event_type: str
    version: int
    introduced_at: datetime
    deprecated_at: Optional[datetime] = None
    migration_available: bool = True
    breaking_changes: bool = False
    changes_description: str
    migration_notes: Optional[str] = None


class SchemaVersionListResponse(BaseModel):
    """List of schema versions for an event type."""

    event_type: str
    current_version: int
    versions: list[SchemaVersionInfo]
    total_versions: int


class SchemaMigrationRequest(BaseModel):
    """
    Request to migrate event data from one schema version to another.

    Used when replaying old events with updated schemas.
    """

    event_id: str
    from_version: int = Field(..., ge=1)
    to_version: int = Field(..., ge=1)
    validate_after_migration: bool = Field(
        True, description="Validate migrated data against target schema"
    )

    @field_validator("to_version")
    @classmethod
    def validate_version_upgrade(cls, v: int, info) -> int:
        """Ensure migration is to a newer version."""
        from_version = info.data.get("from_version")
        if from_version and v <= from_version:
            raise ValueError("to_version must be greater than from_version")
        return v


class SchemaMigrationResponse(BaseModel):
    """Response from schema migration."""

    success: bool
    event_id: str
    from_version: int
    to_version: int
    migrated_data: dict[str, Any]
    validation_errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# =============================================================================
# Event Validation Schemas
# =============================================================================


class EventValidationError(BaseModel):
    """Details about an event validation error."""

    field: str
    message: str
    error_code: str
    severity: str  # "error", "warning", "info"


class EventValidationResult(BaseModel):
    """
    Result of validating an event against its schema.

    Used to ensure event data integrity and compliance with schema requirements.
    """

    valid: bool
    event_id: str
    event_type: str
    version: int
    errors: list[EventValidationError] = Field(default_factory=list)
    warnings: list[EventValidationError] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class BulkEventValidationRequest(BaseModel):
    """Request to validate multiple events."""

    event_ids: list[str] = Field(..., min_length=1, max_length=1000)
    strict_mode: bool = Field(
        False, description="Fail on warnings, not just errors"
    )
    include_details: bool = Field(
        True, description="Include detailed error messages"
    )


class BulkEventValidationResponse(BaseModel):
    """Response from bulk event validation."""

    total_validated: int
    valid_count: int
    invalid_count: int
    warning_count: int
    results: list[EventValidationResult]


# =============================================================================
# Event Snapshot Schemas
# =============================================================================


class SnapshotCreateRequest(BaseModel):
    """
    Request to create a snapshot of current aggregate state.

    Snapshots optimize event replay by providing a baseline state.
    """

    aggregate_id: str
    aggregate_type: str
    snapshot_type: str = Field(
        "automatic", description="Type of snapshot (automatic, manual, scheduled)"
    )
    force: bool = Field(
        False,
        description="Force snapshot creation even if recent snapshot exists",
    )


class SnapshotResponse(BaseModel):
    """Response for snapshot operations."""

    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    snapshot_type: str
    event_count: int
    data_size_bytes: int
    created_at: datetime
    sequence_number: int = Field(..., description="Last event sequence in snapshot")


class SnapshotListResponse(BaseModel):
    """List of snapshots for an aggregate."""

    aggregate_id: str
    aggregate_type: str
    snapshots: list[SnapshotResponse]
    total: int
    latest_snapshot: Optional[SnapshotResponse] = None


# =============================================================================
# Event Projection Schemas
# =============================================================================


class ProjectionStatus(str, Enum):
    """Status of an event projection."""

    BUILDING = "building"
    ACTIVE = "active"
    REBUILDING = "rebuilding"
    ERROR = "error"
    STOPPED = "stopped"


class ProjectionInfo(BaseModel):
    """Information about an event projection (read model)."""

    projection_name: str
    description: str
    status: ProjectionStatus
    last_processed_event_id: Optional[str] = None
    last_processed_timestamp: Optional[datetime] = None
    events_processed: int = 0
    events_pending: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    rebuild_requested_at: Optional[datetime] = None


class ProjectionRebuildRequest(BaseModel):
    """Request to rebuild a projection from events."""

    projection_name: str
    from_beginning: bool = Field(
        True, description="Rebuild from first event (clear existing data)"
    )
    from_timestamp: Optional[datetime] = Field(
        None, description="Rebuild from specific timestamp"
    )


class ProjectionRebuildResponse(BaseModel):
    """Response from projection rebuild request."""

    projection_name: str
    rebuild_started: bool
    estimated_events: int
    started_at: datetime
    message: str


# =============================================================================
# Utility Functions for Schema Validation
# =============================================================================


def validate_event_data(
    event_type: EventType, data: dict[str, Any], version: int = 1
) -> EventValidationResult:
    """
    Validate event data against its schema.

    Args:
        event_type: Type of event to validate
        data: Event data dictionary
        version: Schema version to validate against

    Returns:
        EventValidationResult with validation details
    """
    from app.events.event_types import get_event_class

    errors: list[EventValidationError] = []
    warnings: list[EventValidationError] = []

    try:
        # Get the event class for this type
        event_class = get_event_class(event_type)

        # Attempt to create event instance (validates schema)
        event_class(**data)

        return EventValidationResult(
            valid=True,
            event_id=data.get("metadata", {}).get("event_id", "unknown"),
            event_type=event_type,
            version=version,
            errors=[],
            warnings=[],
        )

    except ValueError as e:
        # Schema validation failed
        errors.append(
            EventValidationError(
                field="unknown",
                message=str(e),
                error_code="SCHEMA_VALIDATION_ERROR",
                severity="error",
            )
        )

    except Exception as e:
        # Unexpected error
        errors.append(
            EventValidationError(
                field="unknown",
                message=f"Unexpected validation error: {str(e)}",
                error_code="VALIDATION_EXCEPTION",
                severity="error",
            )
        )

    return EventValidationResult(
        valid=False,
        event_id=data.get("metadata", {}).get("event_id", "unknown"),
        event_type=event_type,
        version=version,
        errors=errors,
        warnings=warnings,
    )


def serialize_event_for_api(event: Any) -> EventResponse:
    """
    Serialize an event object for API response.

    Args:
        event: Event object to serialize

    Returns:
        EventResponse schema
    """
    return EventResponse(
        aggregate_id=event.aggregate_id,
        aggregate_type=event.aggregate_type,
        metadata=EventMetadataResponse(**event.metadata.model_dump()),
        data=event.to_dict(),
    )
