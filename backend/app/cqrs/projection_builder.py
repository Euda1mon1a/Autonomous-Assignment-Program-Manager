"""
Projection Builder Service for CQRS

This module provides a comprehensive projection building service for the CQRS pattern.
Projections are materialized views that are built from event streams, optimized for queries.

Features:
- Declarative projection definitions
- Incremental updates from events
- Full projection rebuilds
- Projection versioning and schema migration
- Concurrent projection building
- Checkpoint-based recovery
- Error handling and retry logic
- Health monitoring and metrics

Architecture:
    Events → ProjectionBuilder → Read Models
         ↓
    Checkpoints → Recovery

Usage:
    # Define a projection
    class PersonSummaryProjection(BaseProjection):
        projection_name = "person_summary"
        version = 1

        async def handle_person_created(self, event: PersonCreatedEvent):
            # Update read model
            pass

    # Build projections
    builder = ProjectionBuilder(db)
    builder.register_projection(PersonSummaryProjection)
    await builder.build_all()
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, Index, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ValidationError
from app.cqrs.commands import DomainEvent
from app.db.base import Base
from app.db.types import GUID, JSONType
from app.events.event_store import EventStore
from app.events.event_types import BaseEvent

logger = logging.getLogger(__name__)


# =============================================================================
# Projection Status Enums
# =============================================================================


class ProjectionStatus(str, Enum):
    """Status of a projection."""

    INITIALIZING = "initializing"  # Initial state
    ACTIVE = "active"  # Running and processing events
    REBUILDING = "rebuilding"  # Full rebuild in progress
    PAUSED = "paused"  # Temporarily stopped
    ERROR = "error"  # Error state, needs attention
    DEGRADED = "degraded"  # Running but with issues


class BuildMode(str, Enum):
    """Mode for building projections."""

    INCREMENTAL = "incremental"  # Process only new events
    FULL = "full"  # Rebuild from scratch
    CATCHUP = "catchup"  # Catch up from last checkpoint


# =============================================================================
# Database Models
# =============================================================================


class ProjectionMetadata(Base):
    """
    Stores metadata about projections.

    Tracks the state, version, and position of each projection.
    """

    __tablename__ = "projection_metadata"

    projection_name = Column(String(100), primary_key=True)
    projection_version = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default=ProjectionStatus.INITIALIZING)

    # Event tracking
    last_event_sequence = Column(Integer, nullable=False, default=0)
    last_event_timestamp = Column(DateTime)
    last_event_id = Column(String(255))

    # Build tracking
    last_build_started = Column(DateTime)
    last_build_completed = Column(DateTime)
    last_build_duration_seconds = Column(Integer)
    build_mode = Column(String(50))

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text)
    last_error_timestamp = Column(DateTime)

    # Performance metrics
    events_processed = Column(Integer, default=0)
    average_processing_time_ms = Column(Integer)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    enabled = Column(Boolean, default=True)
    config = Column(JSONType(), default=dict)

    __table_args__ = (
        Index("idx_projection_status", "status"),
        Index("idx_projection_enabled", "enabled"),
    )


class ProjectionCheckpoint(Base):
    """
    Checkpoints for projection rebuilds.

    Allows resuming builds from the last checkpoint on failure.
    """

    __tablename__ = "projection_checkpoints"

    id = Column(GUID(), primary_key=True, default=uuid4)
    projection_name = Column(String(100), nullable=False, index=True)
    projection_version = Column(Integer, nullable=False)

    # Checkpoint position
    checkpoint_sequence = Column(Integer, nullable=False)
    checkpoint_timestamp = Column(DateTime, nullable=False)
    event_count = Column(Integer, nullable=False, default=0)

    # Checkpoint data (projection-specific state)
    checkpoint_data = Column(JSONType())

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255))

    __table_args__ = (
        Index("idx_projection_checkpoint", "projection_name", "checkpoint_sequence"),
    )


class ProjectionBuildLog(Base):
    """
    Log of projection build operations.

    Tracks history of builds for auditing and debugging.
    """

    __tablename__ = "projection_build_logs"

    id = Column(GUID(), primary_key=True, default=uuid4)
    projection_name = Column(String(100), nullable=False, index=True)
    projection_version = Column(Integer, nullable=False)

    # Build information
    build_mode = Column(String(50), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Statistics
    events_processed = Column(Integer, default=0)
    from_sequence = Column(Integer)
    to_sequence = Column(Integer)

    # Result
    success = Column(Boolean)
    error_message = Column(Text)

    # Metadata
    triggered_by = Column(String(255))
    trigger_reason = Column(String(255))

    __table_args__ = (
        Index("idx_build_log_projection", "projection_name", "started_at"),
    )


# =============================================================================
# Projection Definition
# =============================================================================


@dataclass
class ProjectionDefinition:
    """
    Defines a projection's configuration.

    Attributes:
        name: Unique projection name
        version: Schema version (increment when schema changes)
        description: Human-readable description
        event_handlers: Mapping of event types to handler methods
        checkpoint_interval: Number of events between checkpoints
        batch_size: Number of events to process in a batch
        parallel_enabled: Whether to allow parallel processing
        retry_on_error: Whether to retry on transient errors
        max_retries: Maximum number of retries
    """

    name: str
    version: int
    description: str = ""
    event_handlers: dict[str, Callable] = field(default_factory=dict)
    checkpoint_interval: int = 100
    batch_size: int = 50
    parallel_enabled: bool = False
    retry_on_error: bool = True
    max_retries: int = 3


class BaseProjection(ABC):
    """
    Base class for projection definitions.

    Subclass this to create custom projections. Define event handlers
    as methods with the pattern: async def handle_{event_type}(event)

    Example:
        class PersonSummaryProjection(BaseProjection):
            projection_name = "person_summary"
            version = 1
            description = "Summary of all persons"

            async def handle_person_created(self, event: PersonCreatedEvent):
                # Create summary record
                pass

            async def handle_person_updated(self, event: PersonUpdatedEvent):
                # Update summary record
                pass
    """

    projection_name: str = ""
    version: int = 1
    description: str = ""
    checkpoint_interval: int = 100
    batch_size: int = 50
    parallel_enabled: bool = False

    def __init__(self, db: Session):
        """
        Initialize projection.

        Args:
            db: Database session
        """
        self.db = db
        self._event_handlers: dict[str, Callable] = {}
        self._discover_handlers()

    def _discover_handlers(self) -> None:
        """Discover event handler methods."""
        for attr_name in dir(self):
            if attr_name.startswith("handle_"):
                handler = getattr(self, attr_name)
                if callable(handler):
                    # Extract event name from method name
                    event_name = attr_name[7:]  # Remove "handle_" prefix
                    self._event_handlers[event_name] = handler

        logger.debug(
            f"Discovered {len(self._event_handlers)} event handlers "
            f"for projection {self.projection_name}"
        )

    async def handle_event(self, event: BaseEvent) -> None:
        """
        Handle an event by dispatching to appropriate handler.

        Args:
            event: Event to handle

        Raises:
            ValueError: If no handler is found for event type
        """
        event_type = event.metadata.event_type
        event_name = self._normalize_event_name(event_type)

        if event_name in self._event_handlers:
            handler = self._event_handlers[event_name]
            await handler(event)
        else:
            # No handler for this event type - skip silently
            logger.debug(
                f"No handler for event {event_type} in projection {self.projection_name}"
            )

    def _normalize_event_name(self, event_type: str) -> str:
        """
        Normalize event type to handler method name.

        Converts "PersonCreated" to "person_created"
        """
        # Convert PascalCase to snake_case
        result = []
        for i, char in enumerate(event_type):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)

    @abstractmethod
    async def reset(self) -> None:
        """
        Reset projection state.

        Called before a full rebuild. Should clear all projection data.
        """
        pass

    async def get_checkpoint_data(self) -> dict[str, Any]:
        """
        Get projection-specific checkpoint data.

        Override to save custom state during checkpoints.

        Returns:
            Dictionary of checkpoint data
        """
        return {}

    async def restore_checkpoint_data(self, data: dict[str, Any]) -> None:
        """
        Restore projection state from checkpoint data.

        Override to restore custom state from checkpoints.

        Args:
            data: Checkpoint data to restore
        """
        pass


# =============================================================================
# Projection Builder
# =============================================================================


@dataclass
class BuildResult:
    """Result of a projection build operation."""

    success: bool
    projection_name: str
    events_processed: int
    duration_seconds: float
    error: Optional[str] = None
    from_sequence: int = 0
    to_sequence: int = 0


class ProjectionBuilder:
    """
    Main service for building and managing projections.

    Handles:
    - Registration of projections
    - Incremental updates
    - Full rebuilds
    - Concurrent builds
    - Checkpointing
    - Error handling
    - Monitoring
    """

    def __init__(
        self,
        db: Session,
        event_store: Optional[EventStore] = None,
        max_workers: int = 4,
    ):
        """
        Initialize projection builder.

        Args:
            db: Database session
            event_store: Event store instance (created if not provided)
            max_workers: Max concurrent workers for parallel builds
        """
        self.db = db
        self.event_store = event_store or EventStore(db)
        self.max_workers = max_workers

        self._projections: dict[str, BaseProjection] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running_builds: dict[str, asyncio.Task] = {}

    def register_projection(self, projection: BaseProjection) -> None:
        """
        Register a projection with the builder.

        Args:
            projection: Projection instance to register
        """
        if not projection.projection_name:
            raise ValueError("Projection must have a name")

        self._projections[projection.projection_name] = projection

        # Ensure metadata exists
        self._ensure_metadata(projection)

        logger.info(
            f"Registered projection: {projection.projection_name} "
            f"(v{projection.version})"
        )

    def _ensure_metadata(self, projection: BaseProjection) -> None:
        """Ensure projection metadata exists in database."""
        metadata = (
            self.db.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection.projection_name)
            .first()
        )

        if not metadata:
            metadata = ProjectionMetadata(
                projection_name=projection.projection_name,
                projection_version=projection.version,
                status=ProjectionStatus.INITIALIZING,
            )
            self.db.add(metadata)
            self.db.commit()
        elif metadata.projection_version != projection.version:
            # Version changed - mark for rebuild
            logger.warning(
                f"Projection {projection.projection_name} version changed "
                f"from {metadata.projection_version} to {projection.version}. "
                f"Rebuild required."
            )
            metadata.status = ProjectionStatus.INITIALIZING
            metadata.projection_version = projection.version
            self.db.commit()

    async def build_projection(
        self,
        projection_name: str,
        mode: BuildMode = BuildMode.INCREMENTAL,
        from_sequence: Optional[int] = None,
        to_sequence: Optional[int] = None,
    ) -> BuildResult:
        """
        Build a single projection.

        Args:
            projection_name: Name of projection to build
            mode: Build mode (incremental, full, catchup)
            from_sequence: Start from this sequence (optional)
            to_sequence: Build up to this sequence (optional)

        Returns:
            BuildResult with build statistics

        Raises:
            ValueError: If projection is not registered
        """
        if projection_name not in self._projections:
            raise ValueError(f"Projection not registered: {projection_name}")

        projection = self._projections[projection_name]
        metadata = self._get_metadata(projection_name)

        logger.info(
            f"Starting {mode.value} build for projection: {projection_name}"
        )

        # Create build log
        build_log = ProjectionBuildLog(
            projection_name=projection_name,
            projection_version=projection.version,
            build_mode=mode.value,
            from_sequence=from_sequence or metadata.last_event_sequence,
        )
        self.db.add(build_log)
        self.db.commit()

        # Update metadata
        metadata.status = (
            ProjectionStatus.REBUILDING
            if mode == BuildMode.FULL
            else ProjectionStatus.ACTIVE
        )
        metadata.last_build_started = datetime.utcnow()
        metadata.build_mode = mode.value
        self.db.commit()

        start_time = datetime.utcnow()
        events_processed = 0
        error = None

        try:
            if mode == BuildMode.FULL:
                # Full rebuild
                await projection.reset()
                from_sequence = 0
                metadata.last_event_sequence = 0
                self.db.commit()

            # Determine sequence range
            if from_sequence is None:
                from_sequence = metadata.last_event_sequence + 1

            # Get events
            events = await self.event_store.get_events(
                from_version=from_sequence,
                to_version=to_sequence,
            )

            # Process events
            events_processed = await self._process_events(
                projection, events, metadata
            )

            # Update metadata
            if events:
                metadata.last_event_sequence = events[-1].metadata.event_id
                metadata.last_event_timestamp = events[-1].metadata.timestamp
                metadata.events_processed += events_processed

            metadata.status = ProjectionStatus.ACTIVE
            metadata.error_count = 0
            metadata.last_error = None

            duration = (datetime.utcnow() - start_time).total_seconds()
            metadata.last_build_completed = datetime.utcnow()
            metadata.last_build_duration_seconds = int(duration)

            # Update build log
            build_log.completed_at = datetime.utcnow()
            build_log.duration_seconds = int(duration)
            build_log.events_processed = events_processed
            build_log.to_sequence = to_sequence or (from_sequence + events_processed)
            build_log.success = True

            self.db.commit()

            logger.info(
                f"Completed build for {projection_name}: "
                f"{events_processed} events in {duration:.2f}s"
            )

            return BuildResult(
                success=True,
                projection_name=projection_name,
                events_processed=events_processed,
                duration_seconds=duration,
                from_sequence=from_sequence,
                to_sequence=to_sequence or (from_sequence + events_processed),
            )

        except Exception as e:
            error = str(e)
            logger.error(
                f"Error building projection {projection_name}: {e}",
                exc_info=True,
            )

            # Update metadata
            metadata.status = ProjectionStatus.ERROR
            metadata.error_count += 1
            metadata.last_error = error
            metadata.last_error_timestamp = datetime.utcnow()

            # Update build log
            build_log.completed_at = datetime.utcnow()
            build_log.success = False
            build_log.error_message = error
            build_log.events_processed = events_processed

            self.db.commit()

            return BuildResult(
                success=False,
                projection_name=projection_name,
                events_processed=events_processed,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                error=error,
            )

    async def _process_events(
        self,
        projection: BaseProjection,
        events: list[BaseEvent],
        metadata: ProjectionMetadata,
    ) -> int:
        """
        Process events through a projection.

        Args:
            projection: Projection instance
            events: Events to process
            metadata: Projection metadata

        Returns:
            Number of events processed
        """
        processed = 0
        batch_start = 0

        while batch_start < len(events):
            batch_end = min(batch_start + projection.batch_size, len(events))
            batch = events[batch_start:batch_end]

            for event in batch:
                try:
                    await projection.handle_event(event)
                    processed += 1

                    # Checkpoint if needed
                    if processed % projection.checkpoint_interval == 0:
                        await self._create_checkpoint(projection, metadata, processed)

                except Exception as e:
                    if projection.retry_on_error:
                        # Retry logic
                        retry_count = 0
                        while retry_count < 3:
                            try:
                                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                                await projection.handle_event(event)
                                processed += 1
                                break
                            except Exception:
                                retry_count += 1
                        if retry_count >= 3:
                            raise
                    else:
                        raise

            batch_start = batch_end

        return processed

    async def _create_checkpoint(
        self,
        projection: BaseProjection,
        metadata: ProjectionMetadata,
        events_processed: int,
    ) -> None:
        """
        Create a checkpoint for the projection.

        Args:
            projection: Projection instance
            metadata: Projection metadata
            events_processed: Number of events processed so far
        """
        checkpoint_data = await projection.get_checkpoint_data()

        checkpoint = ProjectionCheckpoint(
            projection_name=projection.projection_name,
            projection_version=projection.version,
            checkpoint_sequence=metadata.last_event_sequence,
            checkpoint_timestamp=datetime.utcnow(),
            event_count=events_processed,
            checkpoint_data=checkpoint_data,
        )

        self.db.add(checkpoint)
        self.db.commit()

        logger.debug(
            f"Created checkpoint for {projection.projection_name} "
            f"at sequence {metadata.last_event_sequence}"
        )

    async def build_all(
        self,
        mode: BuildMode = BuildMode.INCREMENTAL,
        parallel: bool = False,
    ) -> list[BuildResult]:
        """
        Build all registered projections.

        Args:
            mode: Build mode for all projections
            parallel: Whether to build projections in parallel

        Returns:
            List of build results
        """
        logger.info(f"Building all projections (mode={mode.value}, parallel={parallel})")

        if parallel:
            return await self._build_all_parallel(mode)
        else:
            return await self._build_all_sequential(mode)

    async def _build_all_sequential(self, mode: BuildMode) -> list[BuildResult]:
        """Build all projections sequentially."""
        results = []

        for projection_name in self._projections.keys():
            result = await self.build_projection(projection_name, mode)
            results.append(result)

        return results

    async def _build_all_parallel(self, mode: BuildMode) -> list[BuildResult]:
        """Build all projections in parallel."""
        tasks = []

        for projection_name in self._projections.keys():
            projection = self._projections[projection_name]

            if not projection.parallel_enabled:
                logger.warning(
                    f"Projection {projection_name} does not support parallel builds, "
                    f"building sequentially"
                )
                continue

            task = asyncio.create_task(self.build_projection(projection_name, mode))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                projection_name = list(self._projections.keys())[i]
                processed_results.append(
                    BuildResult(
                        success=False,
                        projection_name=projection_name,
                        events_processed=0,
                        duration_seconds=0,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def rebuild_projection(
        self,
        projection_name: str,
        from_checkpoint: bool = False,
    ) -> BuildResult:
        """
        Rebuild a projection from scratch.

        Args:
            projection_name: Name of projection to rebuild
            from_checkpoint: Whether to resume from last checkpoint

        Returns:
            BuildResult
        """
        if from_checkpoint:
            checkpoint = await self._get_latest_checkpoint(projection_name)
            if checkpoint:
                projection = self._projections[projection_name]
                await projection.restore_checkpoint_data(checkpoint.checkpoint_data)
                return await self.build_projection(
                    projection_name,
                    mode=BuildMode.CATCHUP,
                    from_sequence=checkpoint.checkpoint_sequence,
                )

        return await self.build_projection(projection_name, mode=BuildMode.FULL)

    async def _get_latest_checkpoint(
        self, projection_name: str
    ) -> Optional[ProjectionCheckpoint]:
        """Get the latest checkpoint for a projection."""
        return (
            self.db.query(ProjectionCheckpoint)
            .filter(ProjectionCheckpoint.projection_name == projection_name)
            .order_by(desc(ProjectionCheckpoint.checkpoint_sequence))
            .first()
        )

    def _get_metadata(self, projection_name: str) -> ProjectionMetadata:
        """Get metadata for a projection."""
        metadata = (
            self.db.query(ProjectionMetadata)
            .filter(ProjectionMetadata.projection_name == projection_name)
            .first()
        )

        if not metadata:
            raise ValueError(f"Metadata not found for projection: {projection_name}")

        return metadata

    async def get_projection_status(
        self, projection_name: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get status of projections.

        Args:
            projection_name: Specific projection name, or None for all

        Returns:
            Dictionary with projection status information
        """
        if projection_name:
            metadata = self._get_metadata(projection_name)
            return self._format_projection_status(metadata)

        # Get all projections
        statuses = {}
        for name in self._projections.keys():
            metadata = self._get_metadata(name)
            statuses[name] = self._format_projection_status(metadata)

        return statuses

    def _format_projection_status(self, metadata: ProjectionMetadata) -> dict[str, Any]:
        """Format projection metadata as status dictionary."""
        return {
            "name": metadata.projection_name,
            "version": metadata.projection_version,
            "status": metadata.status,
            "last_event_sequence": metadata.last_event_sequence,
            "last_event_timestamp": (
                metadata.last_event_timestamp.isoformat()
                if metadata.last_event_timestamp
                else None
            ),
            "events_processed": metadata.events_processed,
            "error_count": metadata.error_count,
            "last_error": metadata.last_error,
            "last_build_completed": (
                metadata.last_build_completed.isoformat()
                if metadata.last_build_completed
                else None
            ),
            "last_build_duration_seconds": metadata.last_build_duration_seconds,
            "enabled": metadata.enabled,
        }

    async def pause_projection(self, projection_name: str) -> None:
        """
        Pause a projection.

        Args:
            projection_name: Name of projection to pause
        """
        metadata = self._get_metadata(projection_name)
        metadata.status = ProjectionStatus.PAUSED
        self.db.commit()

        logger.info(f"Paused projection: {projection_name}")

    async def resume_projection(self, projection_name: str) -> None:
        """
        Resume a paused projection.

        Args:
            projection_name: Name of projection to resume
        """
        metadata = self._get_metadata(projection_name)
        metadata.status = ProjectionStatus.ACTIVE
        self.db.commit()

        logger.info(f"Resumed projection: {projection_name}")

        # Rebuild to catch up
        await self.build_projection(projection_name, mode=BuildMode.CATCHUP)

    async def disable_projection(self, projection_name: str) -> None:
        """
        Disable a projection.

        Args:
            projection_name: Name of projection to disable
        """
        metadata = self._get_metadata(projection_name)
        metadata.enabled = False
        metadata.status = ProjectionStatus.PAUSED
        self.db.commit()

        logger.info(f"Disabled projection: {projection_name}")

    async def enable_projection(self, projection_name: str) -> None:
        """
        Enable a disabled projection.

        Args:
            projection_name: Name of projection to enable
        """
        metadata = self._get_metadata(projection_name)
        metadata.enabled = True
        metadata.status = ProjectionStatus.ACTIVE
        self.db.commit()

        logger.info(f"Enabled projection: {projection_name}")

        # Rebuild to catch up
        await self.build_projection(projection_name, mode=BuildMode.CATCHUP)

    async def get_build_history(
        self,
        projection_name: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get build history for a projection.

        Args:
            projection_name: Name of projection
            limit: Maximum number of builds to return

        Returns:
            List of build log entries
        """
        logs = (
            self.db.query(ProjectionBuildLog)
            .filter(ProjectionBuildLog.projection_name == projection_name)
            .order_by(desc(ProjectionBuildLog.started_at))
            .limit(limit)
            .all()
        )

        return [
            {
                "id": str(log.id),
                "build_mode": log.build_mode,
                "started_at": log.started_at.isoformat() if log.started_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "duration_seconds": log.duration_seconds,
                "events_processed": log.events_processed,
                "success": log.success,
                "error_message": log.error_message,
            }
            for log in logs
        ]

    async def get_health_status(self) -> dict[str, Any]:
        """
        Get overall health status of projection system.

        Returns:
            Dictionary with health metrics
        """
        all_metadata = self.db.query(ProjectionMetadata).all()

        total = len(all_metadata)
        active = sum(1 for m in all_metadata if m.status == ProjectionStatus.ACTIVE)
        error = sum(1 for m in all_metadata if m.status == ProjectionStatus.ERROR)
        rebuilding = sum(
            1 for m in all_metadata if m.status == ProjectionStatus.REBUILDING
        )

        # Calculate lag
        max_lag_seconds = 0
        for metadata in all_metadata:
            if metadata.last_event_timestamp:
                lag = (datetime.utcnow() - metadata.last_event_timestamp).total_seconds()
                max_lag_seconds = max(max_lag_seconds, lag)

        return {
            "total_projections": total,
            "active": active,
            "error": error,
            "rebuilding": rebuilding,
            "max_lag_seconds": max_lag_seconds,
            "healthy": error == 0 and active == total - rebuilding,
        }

    def cleanup(self) -> None:
        """Cleanup resources."""
        self._executor.shutdown(wait=True)


# =============================================================================
# Projection Exceptions
# =============================================================================


class ProjectionError(AppException):
    """Base exception for projection errors."""

    pass


class ProjectionNotFoundError(ProjectionError):
    """Projection not found."""

    def __init__(self, projection_name: str):
        super().__init__(
            f"Projection not found: {projection_name}",
            status_code=404,
        )


class ProjectionBuildError(ProjectionError):
    """Error building projection."""

    pass


class ProjectionVersionMismatchError(ProjectionError):
    """Projection version mismatch."""

    pass
