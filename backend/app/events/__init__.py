"""
Event Sourcing Package

This package provides a comprehensive event sourcing system for maintaining
an immutable audit trail of all system events.

Key Features:
- Immutable event log
- Event versioning and evolution
- Event replay for rebuilding state
- Snapshot support for performance
- Temporal queries (state at any point in time)
- Event aggregation and analytics
- Pub/sub for real-time updates

Components:
- event_store: Persistent storage for events
- event_types: Type definitions and schemas
- event_bus: Pub/sub message bus
- projections: Read models from event streams
- handlers: Event handlers for different domains

Usage:
    from app.events import EventBus, EventStore
    from app.events.event_types import ScheduleCreatedEvent

    # Publish event
    event = ScheduleCreatedEvent(
        aggregate_id="schedule-123",
        schedule_id="schedule-123",
        created_by="user-456"
    )
    await event_bus.publish(event)

    # Query events
    events = await event_store.get_events(
        aggregate_id="schedule-123",
        event_type="ScheduleCreated"
    )

    # Replay events to rebuild state
    state = await event_store.replay_events(
        aggregate_id="schedule-123",
        up_to_timestamp=datetime(2025, 1, 1)
    )
"""

from app.events.event_bus import EventBus, get_event_bus
from app.events.event_store import EventStore, get_event_store
from app.events.event_types import (
    BaseEvent,
    EventMetadata,
    EventType,
    ScheduleCreatedEvent,
    ScheduleUpdatedEvent,
    AssignmentCreatedEvent,
    AssignmentUpdatedEvent,
    AssignmentDeletedEvent,
    SwapRequestedEvent,
    SwapApprovedEvent,
    SwapExecutedEvent,
    AbsenceCreatedEvent,
    AbsenceApprovedEvent,
    ACGMEViolationDetectedEvent,
    ACGMEOverrideAppliedEvent,
)
from app.events.projections import (
    EventProjection,
    ScheduleProjection,
    AssignmentProjection,
    AuditProjection,
)
from app.events.replay_service import (
    EventReplayService,
    ReplayConfig,
    ReplayFilterConfig,
    ReplayProgress,
    ReplayStatus,
    ReplaySpeed,
    ReplayTargetConfig,
    ReplayTarget,
    ReplayVerificationResult,
    create_replay_from_timestamp,
    replay_aggregate_history,
)
from app.events.snapshot_store import (
    SnapshotStore,
    SnapshotConfig,
    SnapshotMetadata,
    SnapshotValidationResult,
    get_snapshot_store,
    auto_snapshot_aggregate,
    cleanup_all_old_snapshots,
)

__all__ = [
    # Core components
    "EventBus",
    "EventStore",
    "get_event_bus",
    "get_event_store",
    # Snapshot store
    "SnapshotStore",
    "SnapshotConfig",
    "SnapshotMetadata",
    "SnapshotValidationResult",
    "get_snapshot_store",
    "auto_snapshot_aggregate",
    "cleanup_all_old_snapshots",
    # Base types
    "BaseEvent",
    "EventMetadata",
    "EventType",
    # Schedule events
    "ScheduleCreatedEvent",
    "ScheduleUpdatedEvent",
    # Assignment events
    "AssignmentCreatedEvent",
    "AssignmentUpdatedEvent",
    "AssignmentDeletedEvent",
    # Swap events
    "SwapRequestedEvent",
    "SwapApprovedEvent",
    "SwapExecutedEvent",
    # Absence events
    "AbsenceCreatedEvent",
    "AbsenceApprovedEvent",
    # ACGME events
    "ACGMEViolationDetectedEvent",
    "ACGMEOverrideAppliedEvent",
    # Projections
    "EventProjection",
    "ScheduleProjection",
    "AssignmentProjection",
    "AuditProjection",
    # Replay service
    "EventReplayService",
    "ReplayConfig",
    "ReplayFilterConfig",
    "ReplayProgress",
    "ReplayStatus",
    "ReplaySpeed",
    "ReplayTargetConfig",
    "ReplayTarget",
    "ReplayVerificationResult",
    "create_replay_from_timestamp",
    "replay_aggregate_history",
]
