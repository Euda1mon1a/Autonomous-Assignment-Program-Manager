"""
Event Store Implementation

Provides persistent storage for events with:
- Append-only event log (immutability)
- Event versioning
- Event replay capability
- Snapshot support
- Temporal queries
- Optimistic concurrency control

The event store is the single source of truth for all state changes.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    Index,
    desc,
    and_,
    or_,
)
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID, JSONType
from app.events.event_types import (
    BaseEvent,
    EventVersionMigrator,
    get_event_class,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Database Models
# =============================================================================


class StoredEvent(Base):
    """
    Persistent storage for events.

    Events are append-only and immutable. Once written, they are never
    modified or deleted (except for compliance requirements like GDPR).
    """

    __tablename__ = "event_store"

    # Primary key - sequential for ordering
    sequence_number = Column(Integer, primary_key=True, autoincrement=True)

    # Event identification
    event_id = Column(GUID(), nullable=False, unique=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    event_version = Column(Integer, nullable=False, default=1)

    # Aggregate (entity) information
    aggregate_id = Column(String(255), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False, index=True)
    aggregate_version = Column(Integer, nullable=False, default=1)

    # Event data
    event_data = Column(JSONType(), nullable=False)

    # Metadata
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    correlation_id = Column(String(255), index=True)  # Links related events
    causation_id = Column(String(255), index=True)  # Event that caused this one
    user_id = Column(String(255), index=True)
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    session_id = Column(String(255))

    # Optimistic concurrency control
    expected_version = Column(Integer)

    __table_args__ = (
        # Composite index for efficient aggregate queries
        Index("idx_aggregate_id_version", "aggregate_id", "aggregate_version"),
        Index("idx_aggregate_type_timestamp", "aggregate_type", "timestamp"),
        Index("idx_correlation_id", "correlation_id"),
        Index("idx_timestamp", "timestamp"),
    )

    def __repr__(self):
        return (
            f"<StoredEvent(seq={self.sequence_number}, "
            f"type={self.event_type}, aggregate={self.aggregate_id})>"
        )


class EventSnapshot(Base):
    """
    Snapshots of aggregate state for performance.

    Instead of replaying all events from the beginning,
    we can restore from the latest snapshot and replay
    only recent events.
    """

    __tablename__ = "event_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    aggregate_id = Column(String(255), nullable=False, index=True)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_version = Column(Integer, nullable=False)

    # Snapshot data
    snapshot_data = Column(JSONType(), nullable=False)
    snapshot_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Metadata
    event_count = Column(Integer, nullable=False)  # Events replayed to build this
    created_by = Column(String(255))

    __table_args__ = (
        Index("idx_aggregate_snapshot", "aggregate_id", "aggregate_version"),
    )


# =============================================================================
# Event Store Service
# =============================================================================


class EventStore:
    """
    Event Store for persisting and retrieving events.

    This is the main interface for working with the event log.
    """

    def __init__(self, db: Session):
        """
        Initialize Event Store.

        Args:
            db: Database session
        """
        self.db = db

    async def append_event(
        self,
        event: BaseEvent,
        expected_version: Optional[int] = None,
    ) -> int:
        """
        Append an event to the store.

        Args:
            event: Event to append
            expected_version: Expected current version (for optimistic locking)

        Returns:
            Sequence number of the stored event

        Raises:
            ConcurrencyError: If expected_version doesn't match actual version
        """
        # Get current version
        current_version = self._get_aggregate_version(
            event.aggregate_id,
            event.aggregate_type
        )

        # Check optimistic concurrency
        if expected_version is not None and current_version != expected_version:
            raise ConcurrencyError(
                f"Concurrency conflict: expected version {expected_version}, "
                f"but current version is {current_version}"
            )

        # Create stored event
        stored_event = StoredEvent(
            event_id=event.metadata.event_id,
            event_type=event.metadata.event_type,
            event_version=event.metadata.event_version,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            aggregate_version=current_version + 1,
            event_data=event.to_dict(),
            timestamp=event.metadata.timestamp,
            correlation_id=event.metadata.correlation_id,
            causation_id=event.metadata.causation_id,
            user_id=event.metadata.user_id,
            ip_address=event.metadata.ip_address,
            user_agent=event.metadata.user_agent,
            session_id=event.metadata.session_id,
            expected_version=expected_version,
        )

        self.db.add(stored_event)
        self.db.commit()
        self.db.refresh(stored_event)

        logger.info(
            f"Event appended: {event.metadata.event_type} "
            f"for {event.aggregate_type}:{event.aggregate_id} "
            f"(seq={stored_event.sequence_number})"
        )

        return stored_event.sequence_number

    async def append_events(
        self,
        events: list[BaseEvent],
        expected_version: Optional[int] = None,
    ) -> list[int]:
        """
        Append multiple events atomically.

        All events must be for the same aggregate.

        Args:
            events: List of events to append
            expected_version: Expected current version

        Returns:
            List of sequence numbers

        Raises:
            ValueError: If events are for different aggregates
        """
        if not events:
            return []

        # Verify all events are for same aggregate
        aggregate_ids = {e.aggregate_id for e in events}
        if len(aggregate_ids) > 1:
            raise ValueError("All events must be for the same aggregate")

        sequence_numbers = []
        current_expected = expected_version

        for event in events:
            seq = await self.append_event(event, expected_version=current_expected)
            sequence_numbers.append(seq)
            current_expected = self._get_aggregate_version(
                event.aggregate_id,
                event.aggregate_type
            )

        return sequence_numbers

    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        event_type: Optional[str] = None,
        from_version: Optional[int] = None,
        to_version: Optional[int] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list[BaseEvent]:
        """
        Retrieve events from the store.

        Args:
            aggregate_id: Filter by aggregate ID
            aggregate_type: Filter by aggregate type
            event_type: Filter by event type
            from_version: Minimum aggregate version
            to_version: Maximum aggregate version
            from_timestamp: Minimum timestamp
            to_timestamp: Maximum timestamp
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        query = self.db.query(StoredEvent)

        # Apply filters
        if aggregate_id:
            query = query.filter(StoredEvent.aggregate_id == aggregate_id)
        if aggregate_type:
            query = query.filter(StoredEvent.aggregate_type == aggregate_type)
        if event_type:
            query = query.filter(StoredEvent.event_type == event_type)
        if from_version is not None:
            query = query.filter(StoredEvent.aggregate_version >= from_version)
        if to_version is not None:
            query = query.filter(StoredEvent.aggregate_version <= to_version)
        if from_timestamp:
            query = query.filter(StoredEvent.timestamp >= from_timestamp)
        if to_timestamp:
            query = query.filter(StoredEvent.timestamp <= to_timestamp)

        # Order by sequence
        query = query.order_by(StoredEvent.sequence_number)

        if limit:
            query = query.limit(limit)

        stored_events = query.all()

        # Convert to event objects
        events = []
        for stored in stored_events:
            try:
                event = self._deserialize_event(stored)
                events.append(event)
            except Exception as e:
                logger.error(f"Error deserializing event {stored.event_id}: {e}")
                continue

        return events

    async def get_aggregate_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None,
    ) -> list[BaseEvent]:
        """
        Get all events for a specific aggregate.

        Args:
            aggregate_id: Aggregate ID
            from_version: Start from this version (for incremental updates)

        Returns:
            List of events in order
        """
        return await self.get_events(
            aggregate_id=aggregate_id,
            from_version=from_version,
        )

    async def replay_events(
        self,
        aggregate_id: str,
        up_to_timestamp: Optional[datetime] = None,
        up_to_version: Optional[int] = None,
    ) -> list[BaseEvent]:
        """
        Replay events to reconstruct state at a point in time.

        Args:
            aggregate_id: Aggregate to replay
            up_to_timestamp: Replay up to this timestamp
            up_to_version: Replay up to this version

        Returns:
            List of events representing state at that point
        """
        return await self.get_events(
            aggregate_id=aggregate_id,
            to_timestamp=up_to_timestamp,
            to_version=up_to_version,
        )

    async def create_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        snapshot_data: dict[str, Any],
        created_by: Optional[str] = None,
    ) -> str:
        """
        Create a snapshot of aggregate state.

        Args:
            aggregate_id: Aggregate ID
            aggregate_type: Aggregate type
            snapshot_data: State data to snapshot
            created_by: User creating snapshot

        Returns:
            Snapshot ID
        """
        current_version = self._get_aggregate_version(aggregate_id, aggregate_type)
        event_count = self._get_event_count(aggregate_id)

        snapshot = EventSnapshot(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            aggregate_version=current_version,
            snapshot_data=snapshot_data,
            event_count=event_count,
            created_by=created_by,
        )

        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)

        logger.info(
            f"Snapshot created for {aggregate_type}:{aggregate_id} "
            f"at version {current_version}"
        )

        return str(snapshot.id)

    async def get_latest_snapshot(
        self,
        aggregate_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Get the latest snapshot for an aggregate.

        Args:
            aggregate_id: Aggregate ID

        Returns:
            Snapshot data or None if no snapshot exists
        """
        snapshot = (
            self.db.query(EventSnapshot)
            .filter(EventSnapshot.aggregate_id == aggregate_id)
            .order_by(desc(EventSnapshot.aggregate_version))
            .first()
        )

        if snapshot:
            return {
                "snapshot_data": snapshot.snapshot_data,
                "aggregate_version": snapshot.aggregate_version,
                "snapshot_timestamp": snapshot.snapshot_timestamp,
            }

        return None

    async def get_event_by_id(self, event_id: str) -> Optional[BaseEvent]:
        """
        Get a specific event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event or None if not found
        """
        stored = (
            self.db.query(StoredEvent)
            .filter(StoredEvent.event_id == event_id)
            .first()
        )

        if stored:
            return self._deserialize_event(stored)

        return None

    async def get_events_by_correlation(
        self,
        correlation_id: str,
    ) -> list[BaseEvent]:
        """
        Get all events with the same correlation ID.

        Useful for tracking all events related to a single operation.

        Args:
            correlation_id: Correlation ID

        Returns:
            List of related events
        """
        return await self.get_events(
            # Using raw query since get_events doesn't have correlation_id param
        )
        stored_events = (
            self.db.query(StoredEvent)
            .filter(StoredEvent.correlation_id == correlation_id)
            .order_by(StoredEvent.sequence_number)
            .all()
        )

        events = []
        for stored in stored_events:
            try:
                event = self._deserialize_event(stored)
                events.append(event)
            except Exception as e:
                logger.error(f"Error deserializing event: {e}")
                continue

        return events

    def _get_aggregate_version(
        self,
        aggregate_id: str,
        aggregate_type: str,
    ) -> int:
        """Get current version of an aggregate."""
        latest = (
            self.db.query(StoredEvent.aggregate_version)
            .filter(
                and_(
                    StoredEvent.aggregate_id == aggregate_id,
                    StoredEvent.aggregate_type == aggregate_type,
                )
            )
            .order_by(desc(StoredEvent.aggregate_version))
            .first()
        )

        return latest[0] if latest else 0

    def _get_event_count(self, aggregate_id: str) -> int:
        """Get total number of events for an aggregate."""
        return (
            self.db.query(StoredEvent)
            .filter(StoredEvent.aggregate_id == aggregate_id)
            .count()
        )

    def _deserialize_event(self, stored: StoredEvent) -> BaseEvent:
        """
        Deserialize stored event to event object.

        Args:
            stored: Stored event record

        Returns:
            Event object

        Raises:
            ValueError: If event type is unknown
        """
        # Migrate event data if needed
        event_data = EventVersionMigrator.migrate(stored.event_data)

        # Get event class
        event_class = get_event_class(stored.event_type)

        # Reconstruct event
        return event_class.from_dict(event_data)


# =============================================================================
# Exceptions
# =============================================================================


class ConcurrencyError(Exception):
    """Raised when optimistic concurrency check fails."""
    pass


# =============================================================================
# Singleton Access
# =============================================================================


_event_store_instance: Optional[EventStore] = None


def get_event_store(db: Session) -> EventStore:
    """
    Get EventStore instance.

    Args:
        db: Database session

    Returns:
        EventStore instance
    """
    return EventStore(db)


# =============================================================================
# Event Store Statistics
# =============================================================================


async def get_event_statistics(db: Session) -> dict[str, Any]:
    """
    Get statistics about the event store.

    Args:
        db: Database session

    Returns:
        Dictionary with statistics
    """
    total_events = db.query(StoredEvent).count()
    total_snapshots = db.query(EventSnapshot).count()

    # Events by type
    event_counts = {}
    results = (
        db.query(StoredEvent.event_type, StoredEvent)
        .group_by(StoredEvent.event_type)
        .all()
    )
    for event_type, count in results:
        event_counts[event_type] = count

    # Recent events
    recent_events = (
        db.query(StoredEvent)
        .order_by(desc(StoredEvent.timestamp))
        .limit(10)
        .all()
    )

    return {
        "total_events": total_events,
        "total_snapshots": total_snapshots,
        "events_by_type": event_counts,
        "recent_event_count": len(recent_events),
    }
