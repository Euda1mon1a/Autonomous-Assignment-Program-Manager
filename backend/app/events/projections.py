"""
Event Projections

Projections build read models from event streams.
They subscribe to events and maintain materialized views optimized for queries.

Benefits:
- Separate read and write models (CQRS pattern)
- Optimized query performance
- Multiple views of same data
- Can be rebuilt from event log

Projections can be:
- Real-time (updated as events occur)
- Batch (rebuilt periodically)
- On-demand (computed when requested)
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID, JSONType
from app.events.event_types import (
    ACGMEOverrideAppliedEvent,
    ACGMEViolationDetectedEvent,
    AssignmentCreatedEvent,
    AssignmentDeletedEvent,
    AssignmentUpdatedEvent,
    BaseEvent,
    ScheduleCreatedEvent,
    ScheduleUpdatedEvent,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Projection State Storage
# =============================================================================


class ProjectionState(Base):
    """
    Stores the last processed event for each projection.

    This allows projections to resume from where they left off
    after a restart or failure.
    """

    __tablename__ = "projection_state"

    projection_name = Column(String(100), primary_key=True)
    last_event_sequence = Column(Integer, nullable=False, default=0)
    last_event_timestamp = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="active")  # active, rebuilding, paused
    error_message = Column(Text)


class ProjectionCheckpoint(Base):
    """
    Checkpoint data for projection rebuilding.

    Allows resuming projection rebuilds from a checkpoint.
    """

    __tablename__ = "projection_checkpoints"

    id = Column(GUID(), primary_key=True)
    projection_name = Column(String(100), nullable=False, index=True)
    checkpoint_sequence = Column(Integer, nullable=False)
    checkpoint_data = Column(JSONType())
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# Base Projection
# =============================================================================


class EventProjection(ABC):
    """
    Base class for event projections.

    Projections subscribe to events and build read models.
    """

    def __init__(self, db: Session, projection_name: str):
        """
        Initialize projection.

        Args:
            db: Database session
            projection_name: Unique name for this projection
        """
        self.db = db
        self.projection_name = projection_name
        self._load_state()

    def _load_state(self):
        """Load projection state from database."""
        state = (
            self.db.query(ProjectionState)
            .filter(ProjectionState.projection_name == self.projection_name)
            .first()
        )

        if state:
            self.last_event_sequence = state.last_event_sequence
            self.last_event_timestamp = state.last_event_timestamp
            self.status = state.status
        else:
            # Initialize new projection
            self.last_event_sequence = 0
            self.last_event_timestamp = None
            self.status = "active"
            self._save_state()

    def _save_state(self):
        """Save projection state to database."""
        state = (
            self.db.query(ProjectionState)
            .filter(ProjectionState.projection_name == self.projection_name)
            .first()
        )

        if state:
            state.last_event_sequence = self.last_event_sequence
            state.last_event_timestamp = self.last_event_timestamp
            state.status = self.status
            state.last_updated = datetime.utcnow()
        else:
            state = ProjectionState(
                projection_name=self.projection_name,
                last_event_sequence=self.last_event_sequence,
                last_event_timestamp=self.last_event_timestamp,
                status=self.status,
            )
            self.db.add(state)

        self.db.commit()

    @abstractmethod
    async def handle_event(self, event: BaseEvent):
        """
        Handle an event and update the projection.

        Args:
            event: Event to process
        """
        pass

    async def process_event(self, event: BaseEvent, event_sequence: int):
        """
        Process an event and update state.

        Args:
            event: Event to process
            event_sequence: Sequence number of the event
        """
        try:
            await self.handle_event(event)

            # Update state
            self.last_event_sequence = event_sequence
            self.last_event_timestamp = event.metadata.timestamp
            self._save_state()

        except Exception as e:
            logger.error(
                f"Error processing event {event_sequence} "
                f"in projection {self.projection_name}: {e}"
            )
            self._mark_error(str(e))
            raise

    def _mark_error(self, error_message: str):
        """Mark projection as having an error."""
        state = (
            self.db.query(ProjectionState)
            .filter(ProjectionState.projection_name == self.projection_name)
            .first()
        )
        if state:
            state.status = "error"
            state.error_message = error_message
            self.db.commit()

    async def rebuild(self, event_store):
        """
        Rebuild projection from event store.

        Args:
            event_store: EventStore instance
        """
        logger.info(f"Rebuilding projection: {self.projection_name}")

        # Mark as rebuilding
        self.status = "rebuilding"
        self._save_state()

        try:
            # Reset projection-specific data
            await self.reset()

            # Get all events
            events = await event_store.get_events()

            # Process events
            for i, event in enumerate(events, start=1):
                await self.handle_event(event)

                # Checkpoint every 100 events
                if i % 100 == 0:
                    self.last_event_sequence = i
                    self._save_state()
                    logger.info(
                        f"Projection {self.projection_name}: "
                        f"processed {i}/{len(events)} events"
                    )

            # Mark as active
            self.status = "active"
            self.last_event_sequence = len(events)
            self._save_state()

            logger.info(
                f"Projection {self.projection_name} rebuilt successfully "
                f"({len(events)} events)"
            )

        except Exception as e:
            logger.error(f"Error rebuilding projection {self.projection_name}: {e}")
            self._mark_error(str(e))
            raise

    @abstractmethod
    async def reset(self):
        """Reset projection data (called before rebuild)."""
        pass


# =============================================================================
# Schedule Projection
# =============================================================================


class ScheduleProjection(EventProjection):
    """
    Projection for schedule summary data.

    Maintains a denormalized view of schedules for fast queries.
    """

    def __init__(self, db: Session):
        super().__init__(db, "schedule_summary")
        self.schedules: dict[str, dict] = {}

    async def handle_event(self, event: BaseEvent):
        """Handle schedule-related events."""
        if isinstance(event, ScheduleCreatedEvent):
            self.schedules[event.schedule_id] = {
                "schedule_id": event.schedule_id,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "created_by": event.created_by,
                "created_at": event.metadata.timestamp,
                "algorithm_version": event.algorithm_version,
                "status": "draft",
            }

        elif isinstance(event, ScheduleUpdatedEvent):
            if event.schedule_id in self.schedules:
                self.schedules[event.schedule_id].update(event.changes)
                self.schedules[event.schedule_id][
                    "updated_at"
                ] = event.metadata.timestamp

    async def reset(self):
        """Reset schedule data."""
        self.schedules.clear()

    def get_schedule(self, schedule_id: str) -> dict | None:
        """Get schedule summary."""
        return self.schedules.get(schedule_id)

    def get_all_schedules(self) -> list[dict]:
        """Get all schedule summaries."""
        return list(self.schedules.values())


# =============================================================================
# Assignment Projection
# =============================================================================


class AssignmentProjection(EventProjection):
    """
    Projection for assignment data.

    Maintains current state of all assignments.
    """

    def __init__(self, db: Session):
        super().__init__(db, "assignment_current_state")
        self.assignments: dict[str, dict] = {}

    async def handle_event(self, event: BaseEvent):
        """Handle assignment-related events."""
        if isinstance(event, AssignmentCreatedEvent):
            self.assignments[event.assignment_id] = {
                "assignment_id": event.assignment_id,
                "person_id": event.person_id,
                "block_id": event.block_id,
                "rotation_id": event.rotation_id,
                "role": event.role,
                "created_by": event.created_by,
                "created_at": event.metadata.timestamp,
                "status": "active",
            }

        elif isinstance(event, AssignmentUpdatedEvent):
            if event.assignment_id in self.assignments:
                self.assignments[event.assignment_id].update(event.changes)
                self.assignments[event.assignment_id][
                    "updated_at"
                ] = event.metadata.timestamp

        elif isinstance(event, AssignmentDeletedEvent):
            if event.assignment_id in self.assignments:
                if event.soft_delete:
                    self.assignments[event.assignment_id]["status"] = "deleted"
                    self.assignments[event.assignment_id][
                        "deleted_at"
                    ] = event.metadata.timestamp
                else:
                    del self.assignments[event.assignment_id]

    async def reset(self):
        """Reset assignment data."""
        self.assignments.clear()

    def get_assignment(self, assignment_id: str) -> dict | None:
        """Get assignment by ID."""
        return self.assignments.get(assignment_id)

    def get_assignments_by_person(self, person_id: str) -> list[dict]:
        """Get all assignments for a person."""
        return [
            a
            for a in self.assignments.values()
            if a["person_id"] == person_id and a["status"] == "active"
        ]

    def get_assignments_by_block(self, block_id: str) -> list[dict]:
        """Get all assignments for a block."""
        return [
            a
            for a in self.assignments.values()
            if a["block_id"] == block_id and a["status"] == "active"
        ]


# =============================================================================
# Audit Projection
# =============================================================================


class AuditProjection(EventProjection):
    """
    Projection for audit trail.

    Maintains summary of all changes for compliance reporting.
    """

    def __init__(self, db: Session):
        super().__init__(db, "audit_summary")
        self.audit_entries: list[dict] = []
        self.statistics = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_user": defaultdict(int),
            "events_by_aggregate_type": defaultdict(int),
        }

    async def handle_event(self, event: BaseEvent):
        """Handle all events for audit trail."""
        # Add to audit entries
        entry = {
            "event_id": event.metadata.event_id,
            "event_type": event.metadata.event_type,
            "aggregate_id": event.aggregate_id,
            "aggregate_type": event.aggregate_type,
            "timestamp": event.metadata.timestamp,
            "user_id": event.metadata.user_id,
            "correlation_id": event.metadata.correlation_id,
        }
        self.audit_entries.append(entry)

        # Update statistics
        self.statistics["total_events"] += 1
        self.statistics["events_by_type"][event.metadata.event_type] += 1
        if event.metadata.user_id:
            self.statistics["events_by_user"][event.metadata.user_id] += 1
        self.statistics["events_by_aggregate_type"][event.aggregate_type] += 1

    async def reset(self):
        """Reset audit data."""
        self.audit_entries.clear()
        self.statistics = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_user": defaultdict(int),
            "events_by_aggregate_type": defaultdict(int),
        }

    def get_audit_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        user_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        """Get audit entries with filtering."""
        entries = self.audit_entries

        # Apply filters
        if user_id:
            entries = [e for e in entries if e.get("user_id") == user_id]
        if event_type:
            entries = [e for e in entries if e["event_type"] == event_type]

        # Sort by timestamp descending
        entries = sorted(entries, key=lambda x: x["timestamp"], reverse=True)

        # Apply pagination
        return entries[offset : offset + limit]

    def get_statistics(self) -> dict:
        """Get audit statistics."""
        return {
            "total_events": self.statistics["total_events"],
            "events_by_type": dict(self.statistics["events_by_type"]),
            "events_by_user": dict(self.statistics["events_by_user"]),
            "events_by_aggregate_type": dict(
                self.statistics["events_by_aggregate_type"]
            ),
        }


# =============================================================================
# ACGME Compliance Projection
# =============================================================================


class ACGMEComplianceProjection(EventProjection):
    """
    Projection for ACGME compliance violations and overrides.

    Tracks compliance history for reporting.
    """

    def __init__(self, db: Session):
        super().__init__(db, "acgme_compliance")
        self.violations: dict[str, dict] = {}
        self.overrides: dict[str, dict] = {}

    async def handle_event(self, event: BaseEvent):
        """Handle ACGME compliance events."""
        if isinstance(event, ACGMEViolationDetectedEvent):
            self.violations[event.violation_id] = {
                "violation_id": event.violation_id,
                "person_id": event.person_id,
                "violation_type": event.violation_type,
                "severity": event.severity,
                "detected_at": event.detected_at,
                "details": event.details,
                "status": "open",
            }

        elif isinstance(event, ACGMEOverrideAppliedEvent):
            self.overrides[event.override_id] = {
                "override_id": event.override_id,
                "assignment_id": event.assignment_id,
                "override_reason": event.override_reason,
                "applied_by": event.applied_by,
                "justification": event.justification,
                "approval_level": event.approval_level,
                "applied_at": event.metadata.timestamp,
            }

    async def reset(self):
        """Reset compliance data."""
        self.violations.clear()
        self.overrides.clear()

    def get_open_violations(self) -> list[dict]:
        """Get all open violations."""
        return [v for v in self.violations.values() if v["status"] == "open"]

    def get_overrides_by_person(self, person_id: str) -> list[dict]:
        """Get all overrides related to a person."""
        # This would need to join with assignments
        return list(self.overrides.values())


# =============================================================================
# Projection Manager
# =============================================================================


class ProjectionManager:
    """
    Manages multiple projections.

    Coordinates updates and rebuilds across all projections.
    """

    def __init__(self, db: Session):
        """Initialize projection manager."""
        self.db = db
        self.projections: dict[str, EventProjection] = {}

    def register_projection(self, projection: EventProjection):
        """Register a projection."""
        self.projections[projection.projection_name] = projection
        logger.info(f"Registered projection: {projection.projection_name}")

    async def process_event(self, event: BaseEvent, event_sequence: int):
        """Process event in all projections."""
        for projection in self.projections.values():
            try:
                await projection.process_event(event, event_sequence)
            except Exception as e:
                logger.error(f"Error in projection {projection.projection_name}: {e}")

    async def rebuild_all(self, event_store):
        """Rebuild all projections."""
        for projection in self.projections.values():
            await projection.rebuild(event_store)

    def get_projection_status(self) -> dict[str, dict]:
        """Get status of all projections."""
        status = {}
        for name, projection in self.projections.items():
            status[name] = {
                "last_event_sequence": projection.last_event_sequence,
                "last_event_timestamp": projection.last_event_timestamp,
                "status": projection.status,
            }
        return status
