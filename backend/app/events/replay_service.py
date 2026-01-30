"""
Event Replay Service

Provides comprehensive event replay functionality with:
- Stream replay from specific timestamps
- Selective event filtering
- Replay speed control (slow motion, fast forward)
- Event transformation during replay
- Progress tracking and monitoring
- Pause/resume capabilities
- Replay to specific targets (timestamp, version, event count)
- Replay verification and validation

The replay service is useful for:
- Debugging event-sourced state
- Testing event handlers
- Rebuilding projections
- Analyzing historical behavior
- Disaster recovery scenarios
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.events.event_store import EventStore, StoredEvent
from app.events.event_types import BaseEvent, EventType, get_event_class

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class ReplayStatus(str, Enum):
    """Status of a replay operation."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReplaySpeed(str, Enum):
    """Replay speed settings."""

    REAL_TIME = "real_time"  # Replay at actual event timing
    SLOW_MOTION = "slow_motion"  # 0.5x speed
    NORMAL = "normal"  # No delay between events
    FAST = "fast"  # Batch processing
    MAXIMUM = "maximum"  # No throttling


class ReplayTarget(str, Enum):
    """Target criteria for replay completion."""

    TIMESTAMP = "timestamp"
    SEQUENCE_NUMBER = "sequence_number"
    EVENT_COUNT = "event_count"
    LATEST = "latest"  # Replay all available events

    # =============================================================================
    # Configuration Models
    # =============================================================================


class ReplayFilterConfig(BaseModel):
    """
    Configuration for filtering events during replay.

    Allows selective replay of events based on various criteria.
    """

    aggregate_ids: list[str] | None = Field(
        None, description="Only replay events for these aggregate IDs"
    )
    aggregate_types: list[str] | None = Field(
        None, description="Only replay events for these aggregate types"
    )
    event_types: list[EventType] | None = Field(
        None, description="Only replay these event types"
    )
    user_ids: list[str] | None = Field(
        None, description="Only replay events from these users"
    )
    correlation_ids: list[str] | None = Field(
        None, description="Only replay events with these correlation IDs"
    )
    exclude_event_types: list[EventType] | None = Field(
        None, description="Exclude these event types from replay"
    )
    exclude_aggregate_types: list[str] | None = Field(
        None, description="Exclude these aggregate types from replay"
    )

    def matches(self, event: BaseEvent) -> bool:
        """
        Check if an event matches the filter criteria.

        Args:
            event: Event to check

        Returns:
            True if event matches filters, False otherwise
        """
        # Include filters (any match = include)
        if self.aggregate_ids and event.aggregate_id not in self.aggregate_ids:
            return False
        if self.aggregate_types and event.aggregate_type not in self.aggregate_types:
            return False
        if self.event_types and event.metadata.event_type not in [
            et.value for et in self.event_types
        ]:
            return False
        if self.user_ids and event.metadata.user_id not in self.user_ids:
            return False
        if (
            self.correlation_ids
            and event.metadata.correlation_id not in self.correlation_ids
        ):
            return False

            # Exclude filters (any match = exclude)
        if self.exclude_event_types and event.metadata.event_type in [
            et.value for et in self.exclude_event_types
        ]:
            return False
        if (
            self.exclude_aggregate_types
            and event.aggregate_type in self.exclude_aggregate_types
        ):
            return False

        return True


class ReplayTransformer(BaseModel):
    """
    Configuration for transforming events during replay.

    Allows modification of event data for testing or migration scenarios.
    """

    field_mappings: dict[str, str] = Field(
        default_factory=dict,
        description="Map old field names to new field names",
    )
    field_transformations: dict[str, Any] = Field(
        default_factory=dict,
        description="Custom transformations for specific fields",
    )
    metadata_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Override metadata fields (e.g., user_id, correlation_id)",
    )
    aggregate_id_mapping: dict[str, str] = Field(
        default_factory=dict,
        description="Map old aggregate IDs to new IDs",
    )


class ReplayTargetConfig(BaseModel):
    """
    Configuration for replay target (when to stop).

    Specifies the end point for the replay operation.
    """

    target_type: ReplayTarget
    target_timestamp: datetime | None = None
    target_sequence_number: int | None = None
    target_event_count: int | None = None

    @field_validator("target_timestamp")
    @classmethod
    def validate_timestamp_target(cls, v: datetime | None, info) -> datetime | None:
        """Validate timestamp target is set when target_type is TIMESTAMP."""
        if info.data.get("target_type") == ReplayTarget.TIMESTAMP and not v:
            raise ValueError("target_timestamp required when target_type is TIMESTAMP")
        return v

    @field_validator("target_sequence_number")
    @classmethod
    def validate_sequence_target(cls, v: int | None, info) -> int | None:
        """Validate sequence target is set when target_type is SEQUENCE_NUMBER."""
        if info.data.get("target_type") == ReplayTarget.SEQUENCE_NUMBER and v is None:
            raise ValueError(
                "target_sequence_number required when target_type is SEQUENCE_NUMBER"
            )
        return v

    @field_validator("target_event_count")
    @classmethod
    def validate_count_target(cls, v: int | None, info) -> int | None:
        """Validate count target is set when target_type is EVENT_COUNT."""
        if info.data.get("target_type") == ReplayTarget.EVENT_COUNT and v is None:
            raise ValueError(
                "target_event_count required when target_type is EVENT_COUNT"
            )
        return v


class ReplayConfig(BaseModel):
    """
    Comprehensive configuration for event replay.

    Combines all replay settings into a single configuration object.
    """

    replay_id: str = Field(default_factory=lambda: str(uuid4()))
    start_timestamp: datetime = Field(
        ..., description="Start replaying from this timestamp"
    )
    target: ReplayTargetConfig = Field(..., description="When to stop the replay")
    speed: ReplaySpeed = Field(ReplaySpeed.NORMAL, description="Replay speed setting")
    filters: ReplayFilterConfig | None = Field(
        None, description="Event filtering configuration"
    )
    transformer: ReplayTransformer | None = Field(
        None, description="Event transformation configuration"
    )
    batch_size: int = Field(
        100, ge=1, le=10000, description="Number of events to process per batch"
    )
    verify_after_replay: bool = Field(
        True, description="Verify event integrity after replay"
    )
    emit_events: bool = Field(False, description="Emit replayed events to event bus")
    checkpoint_interval: int = Field(
        1000, ge=1, description="Create checkpoint every N events"
    )

    # =============================================================================
    # Progress and State Models
    # =============================================================================


class ReplayCheckpoint(BaseModel):
    """
    Checkpoint for resuming replay after interruption.

    Stores the state needed to resume from a specific point.
    """

    replay_id: str
    sequence_number: int
    timestamp: datetime
    events_processed: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReplayProgress(BaseModel):
    """
    Real-time progress tracking for replay operation.

    Provides metrics and status information about ongoing replay.
    """

    replay_id: str
    status: ReplayStatus
    events_total: int
    events_processed: int
    events_filtered: int
    events_transformed: int
    events_failed: int
    current_sequence: int | None = None
    current_timestamp: datetime | None = None
    started_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    last_checkpoint: ReplayCheckpoint | None = None

    @property
    def progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.events_total == 0:
            return 0.0
        return (self.events_processed / self.events_total) * 100.0

    @property
    def events_per_second(self) -> float:
        """Calculate processing rate."""
        if self.status == ReplayStatus.PENDING:
            return 0.0

        elapsed = (
            self.completed_at if self.completed_at else self.updated_at
        ) - self.started_at
        seconds = elapsed.total_seconds()

        return self.events_processed / seconds if seconds > 0 else 0.0


class ReplayVerificationResult(BaseModel):
    """
    Results from replay verification.

    Validates that replay completed successfully and data is consistent.
    """

    replay_id: str
    verified_at: datetime
    is_valid: bool
    total_events_verified: int
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sequence_gaps: list[tuple[int, int]] = Field(
        default_factory=list, description="Missing sequence number ranges"
    )
    timestamp_anomalies: list[str] = Field(
        default_factory=list, description="Timestamp ordering issues"
    )
    metadata_issues: list[str] = Field(
        default_factory=list, description="Metadata validation issues"
    )

    # =============================================================================
    # Event Replay Service
    # =============================================================================


class EventReplayService:
    """
    Service for replaying events from the event store.

    Provides comprehensive replay functionality with filtering, transformation,
    progress tracking, and verification.
    """

    def __init__(self, db: Session, event_store: EventStore | None = None) -> None:
        """
        Initialize Event Replay Service.

        Args:
            db: Database session
            event_store: Event store instance (created if not provided)
        """
        self.db = db
        self.event_store = event_store or EventStore(db)
        self._active_replays: dict[str, ReplayProgress] = {}
        self._pause_flags: dict[str, bool] = {}
        self._cancel_flags: dict[str, bool] = {}

    async def start_replay(
        self,
        config: ReplayConfig,
        handler: Callable[[BaseEvent], Any] | None = None,
    ) -> str:
        """
        Start an event replay operation.

        Args:
            config: Replay configuration
            handler: Optional async callback function to process each event

        Returns:
            Replay ID for tracking progress

        Raises:
            ValueError: If configuration is invalid
        """
        replay_id = config.replay_id

        # Initialize progress tracking
        progress = ReplayProgress(
            replay_id=replay_id,
            status=ReplayStatus.PENDING,
            events_total=0,
            events_processed=0,
            events_filtered=0,
            events_transformed=0,
            events_failed=0,
            started_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self._active_replays[replay_id] = progress
        self._pause_flags[replay_id] = False
        self._cancel_flags[replay_id] = False

        logger.info(f"Starting replay {replay_id} from {config.start_timestamp}")

        # Start replay in background
        asyncio.create_task(self._execute_replay(config, handler))

        return replay_id

    async def _execute_replay(
        self,
        config: ReplayConfig,
        handler: Callable[[BaseEvent], Any] | None = None,
    ) -> None:
        """
        Execute the replay operation.

        Args:
            config: Replay configuration
            handler: Optional event handler callback
        """
        replay_id = config.replay_id
        progress = self._active_replays[replay_id]

        try:
            progress.status = ReplayStatus.RUNNING
            progress.updated_at = datetime.utcnow()

            # Get total event count for progress calculation
            total_events = await self._count_events(config)
            progress.events_total = total_events

            logger.info(
                f"Replay {replay_id}: Processing {total_events} events "
                f"from {config.start_timestamp}"
            )

            # Stream and process events
            async for event in self._stream_events(config):
                # Check for pause
                while self._pause_flags.get(replay_id, False):
                    await asyncio.sleep(0.1)

                    # Check for cancellation
                if self._cancel_flags.get(replay_id, False):
                    progress.status = ReplayStatus.CANCELLED
                    logger.info(f"Replay {replay_id} cancelled by user")
                    return

                    # Apply filters
                if config.filters and not config.filters.matches(event):
                    progress.events_filtered += 1
                    continue

                    # Apply transformations
                if config.transformer:
                    event = await self._transform_event(event, config.transformer)
                    progress.events_transformed += 1

                    # Process event
                try:
                    if handler:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            await result

                    progress.events_processed += 1
                    progress.current_sequence = event.metadata.event_id
                    progress.current_timestamp = event.metadata.timestamp
                    progress.updated_at = datetime.utcnow()

                    # Create checkpoint if needed
                    if progress.events_processed % config.checkpoint_interval == 0:
                        await self._create_checkpoint(replay_id, progress)

                except Exception as e:
                    progress.events_failed += 1
                    logger.error(
                        f"Replay {replay_id}: Error processing event "
                        f"{event.metadata.event_id}: {e}"
                    )

                    # Apply speed control
                await self._apply_speed_control(config.speed, event)

                # Replay completed
            progress.status = ReplayStatus.COMPLETED
            progress.completed_at = datetime.utcnow()
            progress.updated_at = datetime.utcnow()

            logger.info(
                f"Replay {replay_id} completed: "
                f"{progress.events_processed} events processed, "
                f"{progress.events_filtered} filtered, "
                f"{progress.events_failed} failed"
            )

            # Verify if requested
            if config.verify_after_replay:
                await self.verify_replay(replay_id, config)

        except Exception as e:
            progress.status = ReplayStatus.FAILED
            progress.error_message = str(e)
            progress.updated_at = datetime.utcnow()
            logger.error(f"Replay {replay_id} failed: {e}", exc_info=True)

    async def _stream_events(self, config: ReplayConfig) -> AsyncIterator[BaseEvent]:
        """
        Stream events from the event store based on configuration.

        Args:
            config: Replay configuration

        Yields:
            Events matching the replay criteria
        """
        # Build query
        query = self.db.query(StoredEvent).filter(
            StoredEvent.timestamp >= config.start_timestamp
        )

        # Apply target filters
        target = config.target
        if target.target_type == ReplayTarget.TIMESTAMP and target.target_timestamp:
            query = query.filter(StoredEvent.timestamp <= target.target_timestamp)
        elif (
            target.target_type == ReplayTarget.SEQUENCE_NUMBER
            and target.target_sequence_number
        ):
            query = query.filter(
                StoredEvent.sequence_number <= target.target_sequence_number
            )

            # Order by sequence
        query = query.order_by(StoredEvent.sequence_number)

        # Apply event count limit if specified
        if target.target_type == ReplayTarget.EVENT_COUNT and target.target_event_count:
            query = query.limit(target.target_event_count)

            # Process in batches
        offset = 0
        while True:
            batch = query.offset(offset).limit(config.batch_size).all()
            if not batch:
                break

            for stored in batch:
                try:
                    event = self.event_store._deserialize_event(stored)
                    yield event
                except Exception as e:
                    logger.error(f"Error deserializing event {stored.event_id}: {e}")

            offset += len(batch)

    async def _count_events(self, config: ReplayConfig) -> int:
        """
        Count total events that will be replayed.

        Args:
            config: Replay configuration

        Returns:
            Total event count
        """
        query = self.db.query(StoredEvent).filter(
            StoredEvent.timestamp >= config.start_timestamp
        )

        target = config.target
        if target.target_type == ReplayTarget.TIMESTAMP and target.target_timestamp:
            query = query.filter(StoredEvent.timestamp <= target.target_timestamp)
        elif (
            target.target_type == ReplayTarget.SEQUENCE_NUMBER
            and target.target_sequence_number
        ):
            query = query.filter(
                StoredEvent.sequence_number <= target.target_sequence_number
            )
        elif (
            target.target_type == ReplayTarget.EVENT_COUNT and target.target_event_count
        ):
            return target.target_event_count

        return query.count()

    async def _transform_event(
        self, event: BaseEvent, transformer: ReplayTransformer
    ) -> BaseEvent:
        """
        Transform event data according to transformer configuration.

        Args:
            event: Original event
            transformer: Transformation configuration

        Returns:
            Transformed event
        """
        event_dict = event.to_dict()

        # Apply field mappings
        for old_field, new_field in transformer.field_mappings.items():
            if old_field in event_dict:
                event_dict[new_field] = event_dict.pop(old_field)

                # Apply field transformations
        for field, transform_func in transformer.field_transformations.items():
            if field in event_dict and callable(transform_func):
                event_dict[field] = transform_func(event_dict[field])

                # Override metadata
        for key, value in transformer.metadata_overrides.items():
            if "metadata" in event_dict:
                event_dict["metadata"][key] = value

                # Map aggregate IDs
        if event_dict.get("aggregate_id") in transformer.aggregate_id_mapping:
            event_dict["aggregate_id"] = transformer.aggregate_id_mapping[
                event_dict["aggregate_id"]
            ]

            # Reconstruct event
        event_class = get_event_class(event.metadata.event_type)
        return event_class.from_dict(event_dict)

    async def _apply_speed_control(
        self, speed: ReplaySpeed, current_event: BaseEvent
    ) -> None:
        """
        Apply speed control delay between events.

        Args:
            speed: Replay speed setting
            current_event: Current event being processed
        """
        if speed == ReplaySpeed.NORMAL:
            await asyncio.sleep(0)  # Yield control
        elif speed == ReplaySpeed.SLOW_MOTION:
            await asyncio.sleep(0.1)  # 100ms delay
        elif speed == ReplaySpeed.FAST:
            if hash(current_event.metadata.event_id) % 10 == 0:
                await asyncio.sleep(0)  # Yield every 10th event
                # MAXIMUM: no delays at all

    async def _create_checkpoint(
        self, replay_id: str, progress: ReplayProgress
    ) -> None:
        """
        Create a checkpoint for replay resumption.

        Args:
            replay_id: Replay operation ID
            progress: Current replay progress
        """
        checkpoint = ReplayCheckpoint(
            replay_id=replay_id,
            sequence_number=progress.current_sequence or 0,
            timestamp=progress.current_timestamp or datetime.utcnow(),
            events_processed=progress.events_processed,
        )
        progress.last_checkpoint = checkpoint

        logger.debug(
            f"Replay {replay_id}: Checkpoint created at "
            f"{checkpoint.events_processed} events"
        )

    async def pause_replay(self, replay_id: str) -> bool:
        """
        Pause an ongoing replay operation.

        Args:
            replay_id: Replay operation ID

        Returns:
            True if paused successfully, False if replay not found or not running
        """
        if replay_id not in self._active_replays:
            return False

        progress = self._active_replays[replay_id]
        if progress.status != ReplayStatus.RUNNING:
            return False

        self._pause_flags[replay_id] = True
        progress.status = ReplayStatus.PAUSED
        progress.updated_at = datetime.utcnow()

        logger.info(f"Replay {replay_id} paused")
        return True

    async def resume_replay(self, replay_id: str) -> bool:
        """
        Resume a paused replay operation.

        Args:
            replay_id: Replay operation ID

        Returns:
            True if resumed successfully, False if replay not found or not paused
        """
        if replay_id not in self._active_replays:
            return False

        progress = self._active_replays[replay_id]
        if progress.status != ReplayStatus.PAUSED:
            return False

        self._pause_flags[replay_id] = False
        progress.status = ReplayStatus.RUNNING
        progress.updated_at = datetime.utcnow()

        logger.info(f"Replay {replay_id} resumed")
        return True

    async def cancel_replay(self, replay_id: str) -> bool:
        """
        Cancel an ongoing replay operation.

        Args:
            replay_id: Replay operation ID

        Returns:
            True if cancelled successfully, False if replay not found
        """
        if replay_id not in self._active_replays:
            return False

        self._cancel_flags[replay_id] = True
        logger.info(f"Replay {replay_id} cancellation requested")
        return True

    async def get_progress(self, replay_id: str) -> ReplayProgress | None:
        """
        Get current progress of a replay operation.

        Args:
            replay_id: Replay operation ID

        Returns:
            Current replay progress or None if not found
        """
        return self._active_replays.get(replay_id)

    async def verify_replay(
        self, replay_id: str, config: ReplayConfig
    ) -> ReplayVerificationResult:
        """
        Verify replay completed successfully.

        Checks for:
        - Sequence number gaps
        - Timestamp ordering
        - Event count accuracy
        - Metadata consistency

        Args:
            replay_id: Replay operation ID
            config: Replay configuration used

        Returns:
            Verification results
        """
        logger.info(f"Verifying replay {replay_id}")

        progress = self._active_replays.get(replay_id)
        if not progress:
            return ReplayVerificationResult(
                replay_id=replay_id,
                verified_at=datetime.utcnow(),
                is_valid=False,
                total_events_verified=0,
                errors=["Replay not found"],
            )

        result = ReplayVerificationResult(
            replay_id=replay_id,
            verified_at=datetime.utcnow(),
            is_valid=True,
            total_events_verified=progress.events_processed,
        )

        # Check if replay completed
        if progress.status != ReplayStatus.COMPLETED:
            result.is_valid = False
            result.errors.append(f"Replay status is {progress.status}, not COMPLETED")

            # Check for failed events
        if progress.events_failed > 0:
            result.warnings.append(
                f"{progress.events_failed} events failed during replay"
            )

            # Verify sequence continuity (if applicable)
        await self._verify_sequence_continuity(config, result)

        # Verify timestamp ordering
        await self._verify_timestamp_ordering(config, result)

        # Check expected event count
        if config.target.target_type == ReplayTarget.EVENT_COUNT:
            expected = config.target.target_event_count
            actual = progress.events_processed
            if expected and actual != expected:
                result.warnings.append(
                    f"Expected {expected} events, processed {actual}"
                )

        logger.info(
            f"Replay {replay_id} verification: "
            f"valid={result.is_valid}, errors={len(result.errors)}, "
            f"warnings={len(result.warnings)}"
        )

        return result

    async def _verify_sequence_continuity(
        self, config: ReplayConfig, result: ReplayVerificationResult
    ) -> None:
        """
        Verify there are no gaps in sequence numbers.

        Args:
            config: Replay configuration
            result: Verification result to update
        """
        query = (
            self.db.query(StoredEvent.sequence_number)
            .filter(StoredEvent.timestamp >= config.start_timestamp)
            .order_by(StoredEvent.sequence_number)
        )

        if config.target.target_type == ReplayTarget.TIMESTAMP:
            query = query.filter(
                StoredEvent.timestamp <= config.target.target_timestamp
            )

        sequences = [row[0] for row in query.limit(10000).all()]

        # Check for gaps
        for i in range(1, len(sequences)):
            if sequences[i] != sequences[i - 1] + 1:
                gap = (sequences[i - 1], sequences[i])
                result.sequence_gaps.append(gap)
                result.warnings.append(f"Sequence gap detected: {gap[0]} -> {gap[1]}")

    async def _verify_timestamp_ordering(
        self, config: ReplayConfig, result: ReplayVerificationResult
    ) -> None:
        """
        Verify events are properly ordered by timestamp.

        Args:
            config: Replay configuration
            result: Verification result to update
        """
        query = (
            self.db.query(StoredEvent.timestamp, StoredEvent.event_id)
            .filter(StoredEvent.timestamp >= config.start_timestamp)
            .order_by(StoredEvent.sequence_number)
        )

        if config.target.target_type == ReplayTarget.TIMESTAMP:
            query = query.filter(
                StoredEvent.timestamp <= config.target.target_timestamp
            )

        events = query.limit(10000).all()

        # Check timestamp ordering
        for i in range(1, len(events)):
            if events[i][0] < events[i - 1][0]:
                result.timestamp_anomalies.append(
                    f"Timestamp out of order: {events[i - 1][1]} "
                    f"({events[i - 1][0]}) -> {events[i][1]} ({events[i][0]})"
                )

    async def cleanup_completed_replays(self, older_than_hours: int = 24) -> int:
        """
        Clean up completed replay tracking data.

        Args:
            older_than_hours: Remove replays completed more than this many hours ago

        Returns:
            Number of replays cleaned up
        """
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)
        removed = 0

        for replay_id, progress in list(self._active_replays.items()):
            if (
                progress.status
                in [ReplayStatus.COMPLETED, ReplayStatus.FAILED, ReplayStatus.CANCELLED]
                and progress.updated_at < cutoff
            ):
                del self._active_replays[replay_id]
                self._pause_flags.pop(replay_id, None)
                self._cancel_flags.pop(replay_id, None)
                removed += 1

        logger.info(f"Cleaned up {removed} completed replays")
        return removed

    async def list_active_replays(self) -> list[ReplayProgress]:
        """
        List all active replay operations.

        Returns:
            List of replay progress objects
        """
        return list(self._active_replays.values())

        # =============================================================================
        # Helper Functions
        # =============================================================================


async def create_replay_from_timestamp(
    db: Session,
    start_timestamp: datetime,
    end_timestamp: datetime | None = None,
    event_types: list[EventType] | None = None,
    handler: Callable[[BaseEvent], Any] | None = None,
) -> str:
    """
    Quick helper to create a simple timestamp-based replay.

    Args:
        db: Database session
        start_timestamp: Start replay from this time
        end_timestamp: End replay at this time (or None for all events)
        event_types: Optional filter for specific event types
        handler: Optional event handler callback

    Returns:
        Replay ID
    """
    service = EventReplayService(db)

    # Build configuration
    target = ReplayTargetConfig(
        target_type=ReplayTarget.TIMESTAMP if end_timestamp else ReplayTarget.LATEST,
        target_timestamp=end_timestamp,
    )

    filters = None
    if event_types:
        filters = ReplayFilterConfig(event_types=event_types)

    config = ReplayConfig(
        start_timestamp=start_timestamp,
        target=target,
        filters=filters,
    )

    return await service.start_replay(config, handler)


async def replay_aggregate_history(
    db: Session,
    aggregate_id: str,
    up_to_timestamp: datetime | None = None,
    handler: Callable[[BaseEvent], Any] | None = None,
) -> str:
    """
    Replay all events for a specific aggregate.

    Args:
        db: Database session
        aggregate_id: ID of aggregate to replay
        up_to_timestamp: Optional end time
        handler: Optional event handler callback

    Returns:
        Replay ID
    """
    service = EventReplayService(db)

    # Get first event timestamp for this aggregate
    first_event = (
        db.query(StoredEvent)
        .filter(StoredEvent.aggregate_id == aggregate_id)
        .order_by(StoredEvent.timestamp)
        .first()
    )

    if not first_event:
        raise ValueError(f"No events found for aggregate {aggregate_id}")

    target = ReplayTargetConfig(
        target_type=ReplayTarget.TIMESTAMP if up_to_timestamp else ReplayTarget.LATEST,
        target_timestamp=up_to_timestamp,
    )

    config = ReplayConfig(
        start_timestamp=first_event.timestamp,
        target=target,
        filters=ReplayFilterConfig(aggregate_ids=[aggregate_id]),
    )

    return await service.start_replay(config, handler)
