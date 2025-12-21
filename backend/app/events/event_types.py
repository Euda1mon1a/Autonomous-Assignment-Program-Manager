"""
Event Type Definitions

Defines all event types in the system with versioning support.
Events are immutable records of things that have happened.

Event Naming Convention:
- Use past tense (e.g., "ScheduleCreated", not "CreateSchedule")
- Be specific (e.g., "AssignmentUpdated", not "Updated")
- Include domain context (e.g., "ScheduleCreatedEvent")

Event Versioning:
- All events have a version field
- When event structure changes, increment version
- Old versions remain supported for replay
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Enumeration of all event types in the system."""

    # Schedule events
    SCHEDULE_CREATED = "ScheduleCreated"
    SCHEDULE_UPDATED = "ScheduleUpdated"
    SCHEDULE_DELETED = "ScheduleDeleted"
    SCHEDULE_PUBLISHED = "SchedulePublished"
    SCHEDULE_ARCHIVED = "ScheduleArchived"

    # Assignment events
    ASSIGNMENT_CREATED = "AssignmentCreated"
    ASSIGNMENT_UPDATED = "AssignmentUpdated"
    ASSIGNMENT_DELETED = "AssignmentDeleted"
    ASSIGNMENT_CONFIRMED = "AssignmentConfirmed"

    # Swap events
    SWAP_REQUESTED = "SwapRequested"
    SWAP_APPROVED = "SwapApproved"
    SWAP_REJECTED = "SwapRejected"
    SWAP_EXECUTED = "SwapExecuted"
    SWAP_CANCELLED = "SwapCancelled"
    SWAP_ROLLED_BACK = "SwapRolledBack"

    # Absence events
    ABSENCE_CREATED = "AbsenceCreated"
    ABSENCE_UPDATED = "AbsenceUpdated"
    ABSENCE_APPROVED = "AbsenceApproved"
    ABSENCE_REJECTED = "AbsenceRejected"
    ABSENCE_DELETED = "AbsenceDeleted"

    # ACGME compliance events
    ACGME_VIOLATION_DETECTED = "ACGMEViolationDetected"
    ACGME_OVERRIDE_APPLIED = "ACGMEOverrideApplied"
    ACGME_COMPLIANCE_RESTORED = "ACGMEComplianceRestored"

    # Person events
    PERSON_CREATED = "PersonCreated"
    PERSON_UPDATED = "PersonUpdated"
    PERSON_ACTIVATED = "PersonActivated"
    PERSON_DEACTIVATED = "PersonDeactivated"

    # Resilience events
    RESILIENCE_LEVEL_CHANGED = "ResilienceLevelChanged"
    CONTINGENCY_ACTIVATED = "ContingencyActivated"
    LOAD_SHED_INITIATED = "LoadShedInitiated"

    # System events
    SNAPSHOT_CREATED = "SnapshotCreated"
    MIGRATION_STARTED = "MigrationStarted"
    MIGRATION_COMPLETED = "MigrationCompleted"


class EventMetadata(BaseModel):
    """
    Metadata attached to every event.

    This provides context about when, where, and why the event occurred.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    event_version: int = Field(default=1, ge=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # Links related events
    causation_id: Optional[str] = None  # ID of event that caused this one
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


class BaseEvent(BaseModel):
    """
    Base class for all events.

    All events must:
    1. Be immutable (no updates after creation)
    2. Include an aggregate_id (entity the event relates to)
    3. Include metadata
    4. Be serializable to JSON
    """

    aggregate_id: str  # ID of the entity this event relates to
    aggregate_type: str  # Type of entity (e.g., "Schedule", "Assignment")
    metadata: EventMetadata

    class Config:
        frozen = True  # Make events immutable
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEvent":
        """Reconstruct event from dictionary."""
        return cls(**data)


# =============================================================================
# Schedule Events
# =============================================================================


class ScheduleCreatedEvent(BaseEvent):
    """Event emitted when a new schedule is created."""

    aggregate_type: str = "Schedule"
    schedule_id: str
    start_date: datetime
    end_date: datetime
    created_by: str
    algorithm_version: Optional[str] = None
    constraint_set: Optional[dict[str, Any]] = None

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SCHEDULE_CREATED)
        super().__init__(**data)


class ScheduleUpdatedEvent(BaseEvent):
    """Event emitted when a schedule is updated."""

    aggregate_type: str = "Schedule"
    schedule_id: str
    updated_by: str
    changes: dict[str, Any]
    reason: Optional[str] = None

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SCHEDULE_UPDATED)
        super().__init__(**data)


class SchedulePublishedEvent(BaseEvent):
    """Event emitted when a schedule is published."""

    aggregate_type: str = "Schedule"
    schedule_id: str
    published_by: str
    notification_sent: bool = False

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SCHEDULE_PUBLISHED)
        super().__init__(**data)


# =============================================================================
# Assignment Events
# =============================================================================


class AssignmentCreatedEvent(BaseEvent):
    """Event emitted when an assignment is created."""

    aggregate_type: str = "Assignment"
    assignment_id: str
    person_id: str
    block_id: str
    rotation_id: Optional[str] = None
    role: str
    created_by: str
    schedule_id: Optional[str] = None

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ASSIGNMENT_CREATED)
        super().__init__(**data)


class AssignmentUpdatedEvent(BaseEvent):
    """Event emitted when an assignment is updated."""

    aggregate_type: str = "Assignment"
    assignment_id: str
    updated_by: str
    changes: dict[str, Any]
    previous_values: dict[str, Any]
    reason: Optional[str] = None

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ASSIGNMENT_UPDATED)
        super().__init__(**data)


class AssignmentDeletedEvent(BaseEvent):
    """Event emitted when an assignment is deleted."""

    aggregate_type: str = "Assignment"
    assignment_id: str
    deleted_by: str
    reason: Optional[str] = None
    soft_delete: bool = True

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ASSIGNMENT_DELETED)
        super().__init__(**data)


# =============================================================================
# Swap Events
# =============================================================================


class SwapRequestedEvent(BaseEvent):
    """Event emitted when a swap is requested."""

    aggregate_type: str = "Swap"
    swap_id: str
    requester_id: str
    requester_assignment_id: str
    target_assignment_id: Optional[str] = None
    swap_type: str  # "one_to_one" or "absorb"
    reason: Optional[str] = None

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SWAP_REQUESTED)
        super().__init__(**data)


class SwapApprovedEvent(BaseEvent):
    """Event emitted when a swap is approved."""

    aggregate_type: str = "Swap"
    swap_id: str
    approved_by: str
    approval_notes: Optional[str] = None

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SWAP_APPROVED)
        super().__init__(**data)


class SwapExecutedEvent(BaseEvent):
    """Event emitted when a swap is executed."""

    aggregate_type: str = "Swap"
    swap_id: str
    executed_by: str
    assignment_changes: list[dict[str, Any]]
    acgme_validated: bool = True

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SWAP_EXECUTED)
        super().__init__(**data)


# =============================================================================
# Absence Events
# =============================================================================


class AbsenceCreatedEvent(BaseEvent):
    """Event emitted when an absence is created."""

    aggregate_type: str = "Absence"
    absence_id: str
    person_id: str
    start_date: datetime
    end_date: datetime
    absence_type: str
    reason: Optional[str] = None
    created_by: str

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ABSENCE_CREATED)
        super().__init__(**data)


class AbsenceApprovedEvent(BaseEvent):
    """Event emitted when an absence is approved."""

    aggregate_type: str = "Absence"
    absence_id: str
    approved_by: str
    approval_notes: Optional[str] = None
    coverage_assigned: bool = False

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ABSENCE_APPROVED)
        super().__init__(**data)


# =============================================================================
# ACGME Compliance Events
# =============================================================================


class ACGMEViolationDetectedEvent(BaseEvent):
    """Event emitted when an ACGME violation is detected."""

    aggregate_type: str = "ACGMECompliance"
    violation_id: str
    person_id: str
    violation_type: str  # "80_hour", "1_in_7", "supervision_ratio"
    severity: str  # "warning", "critical"
    detected_at: datetime
    details: dict[str, Any]

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ACGME_VIOLATION_DETECTED)
        if "detected_at" not in data:
            data["detected_at"] = datetime.utcnow()
        super().__init__(**data)


class ACGMEOverrideAppliedEvent(BaseEvent):
    """Event emitted when an ACGME override is applied."""

    aggregate_type: str = "ACGMECompliance"
    override_id: str
    assignment_id: str
    override_reason: str
    applied_by: str
    justification: str
    approval_level: str  # "coordinator", "program_director"

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.ACGME_OVERRIDE_APPLIED)
        super().__init__(**data)


# =============================================================================
# Person Events
# =============================================================================


class PersonCreatedEvent(BaseEvent):
    """Event emitted when a person is created."""

    aggregate_type: str = "Person"
    person_id: str
    name: str
    email: str
    role: str
    created_by: str

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.PERSON_CREATED)
        super().__init__(**data)


class PersonUpdatedEvent(BaseEvent):
    """Event emitted when a person is updated."""

    aggregate_type: str = "Person"
    person_id: str
    updated_by: str
    changes: dict[str, Any]

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.PERSON_UPDATED)
        super().__init__(**data)


# =============================================================================
# Resilience Events
# =============================================================================


class ResilienceLevelChangedEvent(BaseEvent):
    """Event emitted when resilience defense level changes."""

    aggregate_type: str = "Resilience"
    previous_level: str
    new_level: str
    utilization: float
    trigger_reason: str

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.RESILIENCE_LEVEL_CHANGED)
        super().__init__(**data)


# =============================================================================
# Snapshot Events
# =============================================================================


class SnapshotCreatedEvent(BaseEvent):
    """Event emitted when a snapshot is created."""

    aggregate_type: str = "Snapshot"
    snapshot_id: str
    snapshot_type: str
    event_count: int
    data_size_bytes: int

    def __init__(self, **data):
        if "metadata" not in data:
            data["metadata"] = EventMetadata(event_type=EventType.SNAPSHOT_CREATED)
        super().__init__(**data)


# =============================================================================
# Event Version Migration Support
# =============================================================================


class EventVersionMigrator:
    """
    Handles migration between event versions.

    When event schemas evolve, this class ensures old events
    can be read and converted to the latest version.
    """

    @staticmethod
    def migrate(event_data: dict[str, Any]) -> dict[str, Any]:
        """
        Migrate event to latest version.

        Args:
            event_data: Raw event data from storage

        Returns:
            Migrated event data compatible with current version
        """
        event_type = event_data.get("metadata", {}).get("event_type")
        event_version = event_data.get("metadata", {}).get("event_version", 1)

        # Add version-specific migrations here
        # Example:
        # if event_type == "ScheduleCreated" and event_version == 1:
        #     event_data = migrate_schedule_created_v1_to_v2(event_data)

        return event_data


def get_event_class(event_type: str) -> type[BaseEvent]:
    """
    Get event class by type name.

    Args:
        event_type: Event type string

    Returns:
        Event class

    Raises:
        ValueError: If event type is unknown
    """
    event_map = {
        EventType.SCHEDULE_CREATED: ScheduleCreatedEvent,
        EventType.SCHEDULE_UPDATED: ScheduleUpdatedEvent,
        EventType.SCHEDULE_PUBLISHED: SchedulePublishedEvent,
        EventType.ASSIGNMENT_CREATED: AssignmentCreatedEvent,
        EventType.ASSIGNMENT_UPDATED: AssignmentUpdatedEvent,
        EventType.ASSIGNMENT_DELETED: AssignmentDeletedEvent,
        EventType.SWAP_REQUESTED: SwapRequestedEvent,
        EventType.SWAP_APPROVED: SwapApprovedEvent,
        EventType.SWAP_EXECUTED: SwapExecutedEvent,
        EventType.ABSENCE_CREATED: AbsenceCreatedEvent,
        EventType.ABSENCE_APPROVED: AbsenceApprovedEvent,
        EventType.ACGME_VIOLATION_DETECTED: ACGMEViolationDetectedEvent,
        EventType.ACGME_OVERRIDE_APPLIED: ACGMEOverrideAppliedEvent,
        EventType.PERSON_CREATED: PersonCreatedEvent,
        EventType.PERSON_UPDATED: PersonUpdatedEvent,
        EventType.RESILIENCE_LEVEL_CHANGED: ResilienceLevelChangedEvent,
        EventType.SNAPSHOT_CREATED: SnapshotCreatedEvent,
    }

    if event_type not in event_map:
        raise ValueError(f"Unknown event type: {event_type}")

    return event_map[event_type]
