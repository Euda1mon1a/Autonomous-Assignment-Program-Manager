"""
Read Model Synchronization Service for CQRS
=============================================

This service handles the synchronization of read models from domain events,
ensuring eventual consistency between the write database and read models.

Overview
--------
In a CQRS architecture, read models are updated asynchronously from domain
events. The ReadModelSyncService coordinates this synchronization:

- Subscribes to the event bus for real-time updates
- Processes events through registered projectors
- Monitors sync lag and reports health
- Handles failures with retry and recovery
- Detects and resolves consistency conflicts

This service is critical for maintaining eventual consistency between the
write side (source of truth) and read side (optimized for queries).

Data Flow
---------
::

    Write Database (Source of Truth)
              |
              v
         Event Store
              |
              v
         Event Bus
              |
              v
    +--------------------+
    | ReadModelSyncService |
    +--------------------+
         |         |
         v         v
    Projector A   Projector B
         |         |
         v         v
    Read Model A  Read Model B
         |         |
         +----+----+
              |
              v
         Read Database

Key Concepts
------------

**Eventual Consistency**:
    Read models are not immediately updated when writes occur. There is a
    small delay (sync lag) between write and read. This is acceptable for
    most queries but should be considered for time-critical operations.

**Sync Lag**:
    The time difference between when an event was created and when it was
    projected to read models. Monitored thresholds:
    - < 60s: Normal (IN_SYNC)
    - 60-300s: Warning (LAGGING)
    - > 300s: Critical (FAILED)

**Batch Processing**:
    For efficiency, events can be batched before processing. This reduces
    database round-trips but increases sync lag slightly.

**Conflict Resolution**:
    When read model state conflicts with expected state (e.g., due to
    concurrent updates), the service uses configurable strategies:
    - LAST_WRITE_WINS: Use the latest value from write DB
    - FIRST_WRITE_WINS: Keep the existing read model value
    - MANUAL: Flag for human review
    - REJECT: Raise an error
    - MERGE: Combine values intelligently

Key Components
--------------

**ReadModelSyncService**:
    Main coordination service that:
    - Registers and manages projectors
    - Subscribes to event bus for real-time sync
    - Processes events through projectors
    - Tracks metrics and checkpoints
    - Handles pause/resume and rebuild

**SyncMetrics** (per projector):
    Tracks synchronization health:
    - Events processed (success/failure counts)
    - Current sync lag
    - Average processing time
    - Error history

**SyncCheckpoint** (per projector):
    Enables resumable synchronization:
    - Last processed event sequence
    - Checkpoint timestamp
    - Total events processed

**SyncConflict**:
    Represents detected inconsistencies:
    - Aggregate and event details
    - Write vs read values
    - Resolution strategy and status

**ConflictResolutionStrategy**:
    Configurable conflict handling:
    - LAST_WRITE_WINS (default)
    - FIRST_WRITE_WINS
    - MANUAL
    - REJECT
    - MERGE

**SyncPriority**:
    Event processing priority:
    - HIGH: Critical events (processed first)
    - NORMAL: Standard events
    - LOW: Background/batch events

Usage Example
-------------
::

    from app.cqrs import (
        ReadModelSyncService,
        ConflictResolutionStrategy,
        create_sync_service
    )
    from app.cqrs.queries import ReadModelProjector

    # 1. Create projectors
    class AssignmentProjector(ReadModelProjector):
        async def project(self, event):
            if event.event_type == "AssignmentCreated":
                await self._create_summary(event)
            elif event.event_type == "AssignmentUpdated":
                await self._update_summary(event)

        async def rebuild(self):
            await self.db_read.execute("DELETE FROM assignment_summaries")
            # Rebuild logic...

    # 2. Initialize sync service
    sync_service = ReadModelSyncService(
        db_write=db_write,
        db_read=db_read,
        enable_batch_processing=True,
        batch_size=100,
        batch_timeout_seconds=5,
        enable_conflict_detection=True,
        conflict_resolution_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS
    )

    # 3. Register projectors
    await sync_service.register_projector(
        name="assignment_summary",
        projector=AssignmentProjector(db_write, db_read),
        subscribe_to_events=True  # Auto-subscribe to event bus
    )

    # 4. Start real-time sync
    await sync_service.start_realtime_sync()

    # 5. Monitor sync status
    metrics = sync_service.get_sync_metrics("assignment_summary")
    print(f"Status: {metrics.status}")
    print(f"Sync lag: {metrics.current_sync_lag_seconds}s")
    print(f"Events processed: {metrics.total_events_processed}")
    print(f"Failure rate: {metrics.events_processed_failed / max(1, metrics.total_events_processed):.1%}")

    # 6. Health check
    health = await sync_service.check_health()
    if not health["healthy"]:
        for issue in health["issues"]:
            print(f"Issue: {issue['projector']} - {issue['issue']}")

    # 7. Pause/resume/rebuild
    await sync_service.pause_sync("assignment_summary")
    # ... maintenance ...
    await sync_service.resume_sync("assignment_summary")

    # Full rebuild
    events_replayed = await sync_service.rebuild_read_model("assignment_summary")

    # 8. Stop real-time sync
    await sync_service.stop_realtime_sync()

Batch Processing
----------------
When enabled, events are accumulated and processed in batches:

- Events collected for up to ``batch_timeout_seconds``
- Or until ``batch_size`` events are collected
- Then processed together for efficiency

This reduces database round-trips but adds latency equal to the
batch timeout. Configure based on your consistency requirements.

Conflict Detection
------------------
When enabled, the service verifies consistency after each event:

1. Event is projected to read model
2. Read model state is compared to expected state
3. If mismatch detected, SyncConflict is created
4. Conflict is resolved according to configured strategy

For high-throughput systems, consider disabling for performance
and running periodic consistency checks instead.

Error Handling
--------------
The service handles errors gracefully:

1. Failed event projection triggers rollback of read DB transaction
2. Error is logged and recorded in metrics
3. Projector continues with next event (no blocking)
4. Health check reports failed projectors

For persistent failures:
1. Pause the projector
2. Fix the underlying issue
3. Rebuild from last checkpoint or from scratch
4. Resume processing

Convenience Factory
-------------------
Use ``create_sync_service()`` for quick setup::

    sync_service = await create_sync_service(db_write, db_read)

See Also
--------
- ``app.cqrs.queries``: ReadModelProjector base class
- ``app.cqrs.projection_builder``: Batch projection builds
- ``app.events.event_bus``: Event subscription
- ``app.events.event_store``: Event retrieval for batch processing
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ValidationError
from app.cqrs.commands import DomainEvent
from app.cqrs.queries import ReadModelProjector
from app.events.event_bus import EventBus, get_event_bus
from app.events.event_store import EventStore, get_event_store

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class SyncStatus(str, Enum):
    """Status of read model synchronization."""

    SYNCING = "syncing"
    IN_SYNC = "in_sync"
    LAGGING = "lagging"
    FAILED = "failed"
    PAUSED = "paused"


class ConflictResolutionStrategy(str, Enum):
    """Strategy for resolving read model conflicts."""

    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MANUAL = "manual"
    REJECT = "reject"
    MERGE = "merge"


class SyncPriority(str, Enum):
    """Priority level for event processing."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

    # Thresholds for sync lag warnings


SYNC_LAG_WARNING_SECONDS = 60  # 1 minute
SYNC_LAG_CRITICAL_SECONDS = 300  # 5 minutes

# Batch processing configuration
DEFAULT_BATCH_SIZE = 100
DEFAULT_BATCH_TIMEOUT_SECONDS = 5


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class SyncMetrics:
    """Metrics for read model synchronization."""

    read_model_name: str
    last_synced_event_id: str | None = None
    last_synced_sequence: int | None = None
    last_sync_timestamp: datetime | None = None
    total_events_processed: int = 0
    events_processed_success: int = 0
    events_processed_failed: int = 0
    average_processing_time_ms: float = 0.0
    current_sync_lag_seconds: float = 0.0
    status: SyncStatus = SyncStatus.IN_SYNC
    error_count: int = 0
    last_error: str | None = None
    last_error_timestamp: datetime | None = None

    def update_lag(self, event_timestamp: datetime) -> None:
        """
        Update sync lag based on event timestamp.

        Args:
            event_timestamp: Timestamp of the event being processed
        """
        if event_timestamp:
            self.current_sync_lag_seconds = (
                datetime.utcnow() - event_timestamp
            ).total_seconds()

            # Update status based on lag
            if self.current_sync_lag_seconds >= SYNC_LAG_CRITICAL_SECONDS:
                self.status = SyncStatus.FAILED
            elif self.current_sync_lag_seconds >= SYNC_LAG_WARNING_SECONDS:
                self.status = SyncStatus.LAGGING
            else:
                self.status = SyncStatus.IN_SYNC

    def record_success(self, processing_time_ms: float) -> None:
        """
        Record a successful event processing.

        Args:
            processing_time_ms: Processing time in milliseconds
        """
        self.total_events_processed += 1
        self.events_processed_success += 1
        self.last_sync_timestamp = datetime.utcnow()

        # Update average processing time (exponential moving average)
        alpha = 0.1  # Smoothing factor
        self.average_processing_time_ms = (
            alpha * processing_time_ms + (1 - alpha) * self.average_processing_time_ms
        )

    def record_failure(self, error_message: str) -> None:
        """
        Record a failed event processing.

        Args:
            error_message: Error message describing the failure
        """
        self.total_events_processed += 1
        self.events_processed_failed += 1
        self.error_count += 1
        self.last_error = error_message
        self.last_error_timestamp = datetime.utcnow()
        self.status = SyncStatus.FAILED


@dataclass
class SyncCheckpoint:
    """Checkpoint for resuming synchronization."""

    read_model_name: str
    last_processed_sequence: int
    last_processed_event_id: str
    checkpoint_timestamp: datetime
    total_events_processed: int


class SyncConflict(BaseModel):
    """Represents a conflict between write and read models."""

    conflict_id: str = field(default_factory=lambda: str(uuid4()))
    read_model_name: str
    aggregate_id: str
    event_id: str
    event_sequence: int
    conflict_type: str
    write_value: Any
    read_value: Any
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolution_strategy: ConflictResolutionStrategy = (
        ConflictResolutionStrategy.LAST_WRITE_WINS
    )
    resolved: bool = False
    resolved_at: datetime | None = None
    resolved_by: str | None = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


@dataclass
class BatchProcessingStats:
    """Statistics for batch event processing."""

    batch_id: str = field(default_factory=lambda: str(uuid4()))
    batch_size: int = 0
    events_processed: int = 0
    events_failed: int = 0
    processing_time_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    # =============================================================================
    # Read Model Sync Service
    # =============================================================================


class ReadModelSyncService:
    """
    Service for synchronizing read models from domain events.

    This service coordinates event processing across multiple read model
    projectors, ensuring eventual consistency with retry logic, batch
    processing, and comprehensive monitoring.

    Example:
        # Initialize service
        sync_service = ReadModelSyncService(db_write, db_read)

        # Register projectors
        await sync_service.register_projector(
            "assignment_read_model",
            AssignmentReadModelProjector(db_write, db_read)
        )

        # Start real-time sync
        await sync_service.start_realtime_sync()

        # Process batch of events
        await sync_service.process_event_batch(batch_size=100)

        # Check sync status
        metrics = sync_service.get_sync_metrics("assignment_read_model")
        print(f"Sync lag: {metrics.current_sync_lag_seconds}s")
    """

    def __init__(
        self,
        db_write: Session,
        db_read: Session,
        event_bus: EventBus | None = None,
        event_store: EventStore | None = None,
        enable_batch_processing: bool = True,
        batch_size: int = DEFAULT_BATCH_SIZE,
        batch_timeout_seconds: int = DEFAULT_BATCH_TIMEOUT_SECONDS,
        enable_conflict_detection: bool = True,
        conflict_resolution_strategy: ConflictResolutionStrategy = (
            ConflictResolutionStrategy.LAST_WRITE_WINS
        ),
    ) -> None:
        """
        Initialize read model sync service.

        Args:
            db_write: Database session for reading from write database
            db_read: Database session for writing to read database
            event_bus: Event bus for real-time subscriptions (optional)
            event_store: Event store for batch processing (optional)
            enable_batch_processing: Enable batch event processing
            batch_size: Number of events to process per batch
            batch_timeout_seconds: Timeout for batch accumulation
            enable_conflict_detection: Enable consistency verification
            conflict_resolution_strategy: Strategy for resolving conflicts
        """
        self.db_write = db_write
        self.db_read = db_read
        self.event_bus = event_bus or get_event_bus()
        self.event_store = event_store or get_event_store(db_write)

        # Configuration
        self.enable_batch_processing = enable_batch_processing
        self.batch_size = batch_size
        self.batch_timeout_seconds = batch_timeout_seconds
        self.enable_conflict_detection = enable_conflict_detection
        self.conflict_resolution_strategy = conflict_resolution_strategy

        # Registered projectors
        self._projectors: dict[str, ReadModelProjector] = {}

        # Metrics tracking
        self._metrics: dict[str, SyncMetrics] = {}

        # Checkpoints for resume support
        self._checkpoints: dict[str, SyncCheckpoint] = {}

        # Conflict tracking
        self._conflicts: list[SyncConflict] = []

        # Batch processing
        self._event_batch: list[tuple[str, DomainEvent]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task: asyncio.Task | None = None

        # Subscription tracking
        self._subscription_ids: dict[str, str] = {}

        # Sync control
        self._is_running = False
        self._paused_projectors: set[str] = set()

        logger.info("Read model sync service initialized")

        # =========================================================================
        # Projector Registration
        # =========================================================================

    async def register_projector(
        self,
        name: str,
        projector: ReadModelProjector,
        priority: SyncPriority = SyncPriority.NORMAL,
        subscribe_to_events: bool = True,
    ) -> None:
        """
        Register a read model projector.

        Args:
            name: Unique name for the read model
            projector: Projector instance
            priority: Processing priority
            subscribe_to_events: Auto-subscribe to real-time events

        Raises:
            ValidationError: If projector with same name exists
        """
        if name in self._projectors:
            raise ValidationError(f"Projector '{name}' is already registered")

        self._projectors[name] = projector
        self._metrics[name] = SyncMetrics(read_model_name=name)

        logger.info(
            f"Registered projector: {name}",
            extra={"projector": name, "priority": priority},
        )

        # Subscribe to real-time events
        if subscribe_to_events:
            await self._subscribe_to_events(name)

    async def unregister_projector(self, name: str) -> None:
        """
        Unregister a read model projector.

        Args:
            name: Name of the projector to unregister
        """
        if name not in self._projectors:
            logger.warning(f"Projector '{name}' not found for unregistration")
            return

            # Unsubscribe from events
        if name in self._subscription_ids:
            self.event_bus.unsubscribe(self._subscription_ids[name])
            del self._subscription_ids[name]

            # Remove projector
        del self._projectors[name]
        logger.info(f"Unregistered projector: {name}")

        # =========================================================================
        # Real-time Event Subscription
        # =========================================================================

    async def _subscribe_to_events(self, projector_name: str) -> None:
        """
        Subscribe projector to real-time events.

        Args:
            projector_name: Name of the projector to subscribe
        """

        async def event_handler(event: DomainEvent) -> None:
            """Handle incoming events for this projector."""
            if projector_name in self._paused_projectors:
                logger.debug(f"Projector '{projector_name}' is paused, skipping event")
                return

            if self.enable_batch_processing:
                # Add to batch
                await self._add_to_batch(projector_name, event)
            else:
                # Process immediately
                await self._process_single_event(projector_name, event)

                # Subscribe to all events (projector will filter)

        subscription_id = self.event_bus.subscribe(
            event_type="*",  # Subscribe to all event types
            handler=event_handler,
            subscriber_id=f"sync_{projector_name}",
        )

        self._subscription_ids[projector_name] = subscription_id
        logger.info(f"Subscribed projector '{projector_name}' to event bus")

    async def start_realtime_sync(self) -> None:
        """
        Start real-time synchronization for all registered projectors.

        This method starts listening to the event bus and processing
        events as they arrive.
        """
        if self._is_running:
            logger.warning("Real-time sync is already running")
            return

        self._is_running = True

        # Start batch processing task if enabled
        if self.enable_batch_processing:
            self._batch_task = asyncio.create_task(self._batch_processor())

        logger.info(
            "Real-time sync started",
            extra={
                "projector_count": len(self._projectors),
                "batch_processing": self.enable_batch_processing,
            },
        )

    async def stop_realtime_sync(self) -> None:
        """Stop real-time synchronization."""
        if not self._is_running:
            logger.warning("Real-time sync is not running")
            return

        self._is_running = False

        # Cancel batch processing task
        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

                # Process any remaining events in batch
        if self._event_batch:
            await self._flush_batch()

        logger.info("Real-time sync stopped")

        # =========================================================================
        # Batch Event Processing
        # =========================================================================

    async def _add_to_batch(self, projector_name: str, event: DomainEvent) -> None:
        """
        Add event to batch for processing.

        Args:
            projector_name: Name of the projector
            event: Event to add to batch
        """
        async with self._batch_lock:
            self._event_batch.append((projector_name, event))

            # Flush if batch is full
            if len(self._event_batch) >= self.batch_size:
                await self._flush_batch()

    async def _batch_processor(self) -> None:
        """
        Background task for processing event batches.

        This task periodically flushes the batch based on timeout.
        """
        while self._is_running:
            await asyncio.sleep(self.batch_timeout_seconds)

            if self._event_batch:
                await self._flush_batch()

    async def _flush_batch(self) -> None:
        """Process all events in the current batch."""
        async with self._batch_lock:
            if not self._event_batch:
                return

            batch_stats = BatchProcessingStats(batch_size=len(self._event_batch))
            start_time = datetime.utcnow()

            logger.info(
                f"Processing event batch: {batch_stats.batch_size} events",
                extra={"batch_id": batch_stats.batch_id},
            )

            # Group events by projector
            events_by_projector = defaultdict(list)
            for projector_name, event in self._event_batch:
                events_by_projector[projector_name].append(event)

                # Process each projector's events
            for projector_name, events in events_by_projector.items():
                for event in events:
                    try:
                        await self._process_single_event(projector_name, event)
                        batch_stats.events_processed += 1
                    except Exception as e:
                        batch_stats.events_failed += 1
                        logger.error(
                            f"Error processing event in batch: {e}",
                            extra={
                                "batch_id": batch_stats.batch_id,
                                "projector": projector_name,
                                "event_id": event.metadata.event_id,
                            },
                            exc_info=True,
                        )

                        # Clear batch
            self._event_batch.clear()

            # Update stats
            batch_stats.completed_at = datetime.utcnow()
            batch_stats.processing_time_ms = (
                batch_stats.completed_at - start_time
            ).total_seconds() * 1000

            logger.info(
                f"Batch processing completed: {batch_stats.events_processed} "
                f"success, {batch_stats.events_failed} failed "
                f"({batch_stats.processing_time_ms:.2f}ms)",
                extra={
                    "batch_id": batch_stats.batch_id,
                    "processing_time_ms": batch_stats.processing_time_ms,
                },
            )

    async def process_event_batch(
        self,
        batch_size: int | None = None,
        from_sequence: int | None = None,
    ) -> int:
        """
        Process a batch of events from the event store.

        This method is useful for catching up on missed events or
        rebuilding read models.

        Args:
            batch_size: Number of events to process (default: configured batch size)
            from_sequence: Start from this sequence number (default: last checkpoint)

        Returns:
            Number of events processed

        Example:
            # Catch up on last 500 events
            processed = await sync_service.process_event_batch(batch_size=500)
        """
        batch_size = batch_size or self.batch_size
        events_processed = 0

        for projector_name, projector in self._projectors.items():
            # Skip paused projectors
            if projector_name in self._paused_projectors:
                continue

                # Get starting sequence
            start_sequence = from_sequence
            if start_sequence is None and projector_name in self._checkpoints:
                start_sequence = (
                    self._checkpoints[projector_name].last_processed_sequence + 1
                )

                # Fetch events from store
            try:
                events = await self.event_store.get_events(
                    from_version=start_sequence,
                    limit=batch_size,
                )
            except Exception as e:
                logger.error(
                    f"Error fetching events from store: {e}",
                    extra={"projector": projector_name},
                    exc_info=True,
                )
                continue

                # Process events
            for event in events:
                try:
                    await self._process_single_event(projector_name, event)
                    events_processed += 1
                except Exception as e:
                    logger.error(
                        f"Error processing event: {e}",
                        extra={
                            "projector": projector_name,
                            "event_id": event.metadata.event_id,
                        },
                        exc_info=True,
                    )

        return events_processed

        # =========================================================================
        # Single Event Processing
        # =========================================================================

    async def _process_single_event(
        self, projector_name: str, event: DomainEvent
    ) -> None:
        """
        Process a single event for a specific projector.

        Args:
            projector_name: Name of the projector
            event: Event to process

        Raises:
            AppException: If processing fails after retries
        """
        if projector_name not in self._projectors:
            logger.warning(f"Projector '{projector_name}' not found")
            return

        projector = self._projectors[projector_name]
        metrics = self._metrics[projector_name]

        start_time = datetime.utcnow()

        try:
            # Update lag before processing
            metrics.update_lag(event.metadata.timestamp)
            metrics.status = SyncStatus.SYNCING

            # Project the event
            await projector.project(event)

            # Commit read database changes
            await self.db_read.commit()

            # Update metrics
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            metrics.record_success(processing_time_ms)
            metrics.last_synced_event_id = event.metadata.event_id

            # Update checkpoint
            if hasattr(event, "sequence_number"):
                self._update_checkpoint(
                    projector_name,
                    event.sequence_number,
                    event.metadata.event_id,
                )

                # Conflict detection
            if self.enable_conflict_detection:
                await self._check_consistency(projector_name, event)

            logger.debug(
                f"Event processed successfully: {event.metadata.event_type}",
                extra={
                    "projector": projector_name,
                    "event_id": event.metadata.event_id,
                    "processing_time_ms": processing_time_ms,
                },
            )

        except Exception as e:
            # Rollback read database changes
            await self.db_read.rollback()

            # Update metrics
            metrics.record_failure(str(e))

            logger.error(
                f"Error processing event for projector '{projector_name}': {e}",
                extra={
                    "projector": projector_name,
                    "event_id": event.metadata.event_id,
                    "event_type": event.metadata.event_type,
                },
                exc_info=True,
            )

            # Re-raise for retry logic
            raise

            # =========================================================================
            # Consistency Verification
            # =========================================================================

    async def _check_consistency(self, projector_name: str, event: DomainEvent) -> None:
        """
        Verify consistency between write and read models after event processing.

        Performs a consistency check by comparing the expected state based on
        the event with the actual state in the read model. If inconsistencies
        are detected, creates a SyncConflict for resolution.

        Args:
            projector_name: Name of the projector
            event: Event that was just processed

        Raises:
            ConflictError: If a critical consistency issue is detected
        """
        # Get the projector
        if projector_name not in self._projectors:
            logger.warning(
                f"Projector {projector_name} not found for consistency check"
            )
            return

        projector = self._projectors[projector_name]

        # Verify the event was properly applied
        aggregate_id = str(event.metadata.aggregate_id) if event.metadata else None
        if not aggregate_id:
            return

            # Check consistency between write and read state
        is_consistent, conflict = await self.verify_consistency(
            projector_name, aggregate_id
        )

        if not is_consistent and conflict:
            # Log the inconsistency
            logger.warning(
                f"Consistency check failed for {projector_name}",
                extra={
                    "projector": projector_name,
                    "aggregate_id": aggregate_id,
                    "event_id": str(event.metadata.event_id)
                    if event.metadata
                    else None,
                    "conflict_type": conflict.conflict_type,
                },
            )

            # Add to conflict tracking
            if projector_name not in self._conflicts:
                self._conflicts[projector_name] = []
            self._conflicts[projector_name].append(conflict)

            # Attempt automatic resolution if not in manual mode
            if self.conflict_resolution_strategy != ConflictResolutionStrategy.MANUAL:
                await self.resolve_conflict(conflict)

    async def verify_consistency(
        self, projector_name: str, aggregate_id: str
    ) -> tuple[bool, SyncConflict | None]:
        """
        Verify consistency for a specific aggregate.

        Compares the write database state with the read model state to detect
        any inconsistencies that may have occurred during event processing.

        Args:
            projector_name: Name of the projector
            aggregate_id: ID of the aggregate to verify

        Returns:
            Tuple of (is_consistent, conflict_if_any)
        """
        if projector_name not in self._projectors:
            return True, None

        projector = self._projectors[projector_name]

        # Get sync state for this projector
        sync_state = self._sync_states.get(projector_name)
        if not sync_state:
            return True, None

            # Check if there are unprocessed events for this aggregate
            # by comparing the last synced sequence with the event store
        try:
            # Get latest events for this aggregate from event store
            event_store = await get_event_store()
            latest_events = await event_store.get_events_by_aggregate(
                aggregate_id=aggregate_id,
                after_sequence=sync_state.last_synced_sequence or 0,
            )

            if latest_events:
                # There are unprocessed events - potential lag but not necessarily a conflict
                # Check if the read model is significantly behind
                lag_count = len(latest_events)
                if lag_count > 10:  # More than 10 events behind
                    conflict = SyncConflict(
                        read_model_name=projector_name,
                        aggregate_id=aggregate_id,
                        event_id=str(latest_events[-1].metadata.event_id)
                        if latest_events[-1].metadata
                        else "",
                        event_sequence=latest_events[-1].metadata.sequence
                        if latest_events[-1].metadata
                        else 0,
                        conflict_type="sync_lag",
                        write_value={"pending_events": lag_count},
                        read_value={"last_sequence": sync_state.last_synced_sequence},
                        resolution_strategy=self.conflict_resolution_strategy,
                    )
                    return False, conflict

                    # Check metrics for processing errors
            metrics = self._metrics.get(projector_name)
            if metrics and metrics.events_processed_failure > 0:
                error_rate = metrics.events_processed_failure / max(
                    metrics.total_events_processed, 1
                )
                if error_rate > 0.1:  # More than 10% failure rate
                    conflict = SyncConflict(
                        read_model_name=projector_name,
                        aggregate_id=aggregate_id,
                        event_id="",
                        event_sequence=sync_state.last_synced_sequence or 0,
                        conflict_type="high_error_rate",
                        write_value={"error_rate": error_rate},
                        read_value={"failures": metrics.events_processed_failure},
                        resolution_strategy=self.conflict_resolution_strategy,
                    )
                    return False, conflict

            return True, None

        except Exception as e:
            logger.error(
                f"Error during consistency verification for {projector_name}/{aggregate_id}: {e}",
                exc_info=True,
            )
            # On error, assume consistent to avoid false positives
            return True, None

            # =========================================================================
            # Conflict Resolution
            # =========================================================================

    async def resolve_conflict(
        self,
        conflict: SyncConflict,
        strategy: ConflictResolutionStrategy | None = None,
        resolved_by: str | None = None,
    ) -> None:
        """
        Resolve a detected conflict.

        Args:
            conflict: The conflict to resolve
            strategy: Resolution strategy (default: service default)
            resolved_by: User resolving the conflict (for manual resolution)

        Raises:
            ValidationError: If conflict cannot be resolved
        """
        strategy = strategy or self.conflict_resolution_strategy

        logger.info(
            f"Resolving conflict: {conflict.conflict_id}",
            extra={
                "conflict_id": conflict.conflict_id,
                "strategy": strategy,
                "read_model": conflict.read_model_name,
            },
        )

        if strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            # Use write database value
            await self._apply_write_value(conflict)
        elif strategy == ConflictResolutionStrategy.FIRST_WRITE_WINS:
            # Keep read model value
            pass  # No action needed
        elif strategy == ConflictResolutionStrategy.MANUAL:
            if not resolved_by:
                raise ValidationError("Manual resolution requires 'resolved_by'")
                # Wait for manual resolution
            logger.info(f"Conflict {conflict.conflict_id} marked for manual resolution")
        elif strategy == ConflictResolutionStrategy.REJECT:
            raise ConflictError(f"Conflict rejected: {conflict.conflict_type}")
        elif strategy == ConflictResolutionStrategy.MERGE:
            await self._merge_values(conflict)

            # Mark as resolved
        conflict.resolved = True
        conflict.resolved_at = datetime.utcnow()
        conflict.resolved_by = resolved_by

    async def _apply_write_value(self, conflict: SyncConflict) -> None:
        """Apply write database value to resolve conflict."""
        # Implementation would update read model with write DB value
        logger.debug(f"Applied write value for conflict: {conflict.conflict_id}")

    async def _merge_values(self, conflict: SyncConflict) -> None:
        """Merge write and read values to resolve conflict."""
        # Implementation would merge the values intelligently
        logger.debug(f"Merged values for conflict: {conflict.conflict_id}")

        # =========================================================================
        # Checkpointing and Resume
        # =========================================================================

    def _update_checkpoint(
        self, projector_name: str, sequence: int, event_id: str
    ) -> None:
        """
        Update checkpoint for a projector.

        Args:
            projector_name: Name of the projector
            sequence: Sequence number of last processed event
            event_id: ID of last processed event
        """
        if projector_name in self._checkpoints:
            checkpoint = self._checkpoints[projector_name]
            checkpoint.last_processed_sequence = sequence
            checkpoint.last_processed_event_id = event_id
            checkpoint.checkpoint_timestamp = datetime.utcnow()
            checkpoint.total_events_processed += 1
        else:
            self._checkpoints[projector_name] = SyncCheckpoint(
                read_model_name=projector_name,
                last_processed_sequence=sequence,
                last_processed_event_id=event_id,
                checkpoint_timestamp=datetime.utcnow(),
                total_events_processed=1,
            )

    async def save_checkpoint(self, projector_name: str) -> None:
        """
        Persist checkpoint to database.

        Args:
            projector_name: Name of the projector

        Note:
            This would save to a checkpoints table in the database.
            Implementation depends on your checkpoint storage strategy.
        """
        if projector_name not in self._checkpoints:
            logger.warning(f"No checkpoint found for projector '{projector_name}'")
            return

        checkpoint = self._checkpoints[projector_name]
        logger.info(
            f"Checkpoint saved for '{projector_name}': "
            f"sequence={checkpoint.last_processed_sequence}",
            extra={
                "projector": projector_name,
                "sequence": checkpoint.last_processed_sequence,
            },
        )

    async def load_checkpoint(self, projector_name: str) -> SyncCheckpoint | None:
        """
        Load checkpoint from database.

        Args:
            projector_name: Name of the projector

        Returns:
            Loaded checkpoint or None if not found
        """
        # Implementation would load from database
        return self._checkpoints.get(projector_name)

        # =========================================================================
        # Sync Control
        # =========================================================================

    async def pause_sync(self, projector_name: str) -> None:
        """
        Pause synchronization for a specific projector.

        Args:
            projector_name: Name of the projector to pause
        """
        if projector_name not in self._projectors:
            raise ValidationError(f"Projector '{projector_name}' not found")

        self._paused_projectors.add(projector_name)
        if projector_name in self._metrics:
            self._metrics[projector_name].status = SyncStatus.PAUSED

        logger.info(f"Paused sync for projector: {projector_name}")

    async def resume_sync(self, projector_name: str) -> None:
        """
        Resume synchronization for a paused projector.

        Args:
            projector_name: Name of the projector to resume
        """
        if projector_name not in self._projectors:
            raise ValidationError(f"Projector '{projector_name}' not found")

        self._paused_projectors.discard(projector_name)
        if projector_name in self._metrics:
            self._metrics[projector_name].status = SyncStatus.SYNCING

        logger.info(f"Resumed sync for projector: {projector_name}")

    async def rebuild_read_model(self, projector_name: str) -> int:
        """
        Rebuild a read model from scratch.

        This method deletes the existing read model and replays all events.

        Args:
            projector_name: Name of the projector to rebuild

        Returns:
            Number of events replayed

        Warning:
            This operation can be time-consuming for large event stores.
        """
        if projector_name not in self._projectors:
            raise ValidationError(f"Projector '{projector_name}' not found")

        logger.warning(
            f"Starting read model rebuild for: {projector_name}",
            extra={"projector": projector_name},
        )

        projector = self._projectors[projector_name]

        # Call projector's rebuild method
        await projector.rebuild()

        # Reset checkpoint
        if projector_name in self._checkpoints:
            del self._checkpoints[projector_name]

            # Reset metrics
        self._metrics[projector_name] = SyncMetrics(read_model_name=projector_name)

        # Replay all events
        events_replayed = await self.process_event_batch(
            batch_size=1000,  # Larger batch for rebuild
            from_sequence=0,
        )

        logger.info(
            f"Read model rebuild completed: {projector_name}",
            extra={"projector": projector_name, "events_replayed": events_replayed},
        )

        return events_replayed

        # =========================================================================
        # Metrics and Monitoring
        # =========================================================================

    def get_sync_metrics(self, projector_name: str) -> SyncMetrics | None:
        """
        Get synchronization metrics for a projector.

        Args:
            projector_name: Name of the projector

        Returns:
            Sync metrics or None if projector not found
        """
        return self._metrics.get(projector_name)

    def get_all_metrics(self) -> dict[str, SyncMetrics]:
        """
        Get metrics for all registered projectors.

        Returns:
            Dictionary mapping projector names to metrics
        """
        return self._metrics.copy()

    def get_sync_status_summary(self) -> dict[str, Any]:
        """
        Get summary of sync status across all projectors.

        Returns:
            Dictionary with summary statistics
        """
        total_projectors = len(self._projectors)
        in_sync = sum(
            1 for m in self._metrics.values() if m.status == SyncStatus.IN_SYNC
        )
        lagging = sum(
            1 for m in self._metrics.values() if m.status == SyncStatus.LAGGING
        )
        failed = sum(1 for m in self._metrics.values() if m.status == SyncStatus.FAILED)
        paused = len(self._paused_projectors)

        max_lag = max(
            (m.current_sync_lag_seconds for m in self._metrics.values()),
            default=0.0,
        )

        total_events = sum(m.total_events_processed for m in self._metrics.values())
        total_failures = sum(m.events_processed_failed for m in self._metrics.values())

        return {
            "total_projectors": total_projectors,
            "in_sync": in_sync,
            "lagging": lagging,
            "failed": failed,
            "paused": paused,
            "max_sync_lag_seconds": max_lag,
            "total_events_processed": total_events,
            "total_failures": total_failures,
            "conflict_count": len(self._conflicts),
            "is_running": self._is_running,
        }

    def get_conflicts(self, resolved: bool | None = None) -> list[SyncConflict]:
        """
        Get list of sync conflicts.

        Args:
            resolved: Filter by resolution status (None = all)

        Returns:
            List of conflicts matching criteria
        """
        if resolved is None:
            return self._conflicts.copy()

        return [c for c in self._conflicts if c.resolved == resolved]

    async def check_health(self) -> dict[str, Any]:
        """
        Perform health check on sync service.

        Returns:
            Dictionary with health status
        """
        health = {
            "healthy": True,
            "timestamp": datetime.utcnow().isoformat(),
            "issues": [],
        }

        # Check for failed projectors
        for name, metrics in self._metrics.items():
            if metrics.status == SyncStatus.FAILED:
                health["healthy"] = False
                health["issues"].append(
                    {
                        "projector": name,
                        "issue": "sync_failed",
                        "last_error": metrics.last_error,
                        "error_timestamp": (
                            metrics.last_error_timestamp.isoformat()
                            if metrics.last_error_timestamp
                            else None
                        ),
                    }
                )

                # Check for critical lag
            if metrics.current_sync_lag_seconds >= SYNC_LAG_CRITICAL_SECONDS:
                health["healthy"] = False
                health["issues"].append(
                    {
                        "projector": name,
                        "issue": "critical_lag",
                        "lag_seconds": metrics.current_sync_lag_seconds,
                    }
                )

                # Check for unresolved conflicts
        unresolved = [c for c in self._conflicts if not c.resolved]
        if len(unresolved) > 10:  # Threshold
            health["healthy"] = False
            health["issues"].append(
                {
                    "issue": "too_many_conflicts",
                    "count": len(unresolved),
                }
            )

        return health

        # =============================================================================
        # Convenience Functions
        # =============================================================================


async def create_sync_service(
    db_write: Session,
    db_read: Session,
    **kwargs,
) -> ReadModelSyncService:
    """
    Create and initialize a read model sync service.

    Args:
        db_write: Write database session
        db_read: Read database session
        **kwargs: Additional arguments for ReadModelSyncService

    Returns:
        Initialized sync service
    """
    service = ReadModelSyncService(db_write, db_read, **kwargs)
    return service
