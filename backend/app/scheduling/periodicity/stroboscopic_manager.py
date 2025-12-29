"""
Stroboscopic Schedule State Manager

Implements time crystal-inspired stroboscopic state management for schedule state.
Inspired by discrete time crystal physics where state is observed at discrete intervals.

Key Innovation:
Instead of continuous state updates (which cause race conditions and inconsistency),
schedule state advances ONLY at checkpoint boundaries (stroboscopic observation):
- Week boundaries (7 day period)
- Block boundaries (rotation changes)
- ACGME 4-week compliance windows (28 day period)

This creates a "time crystal" effect where:
1. Authoritative state is stable between checkpoints
2. Draft changes accumulate without affecting observers
3. Checkpoints are atomic transitions with distributed locking
4. All observers see consistent state snapshots

Architecture:
    Draft State ──(propose)──► Staging Area ──(advance_checkpoint)──► Authoritative State
                                                      │
                                                      ▼
                                               Event Bus (notify observers)

Usage:
    manager = StroboscopicScheduleManager(db, event_bus, redis_client)

    # Stage changes
    await manager.propose_draft(new_schedule_data)

    # Atomic checkpoint transition
    await manager.advance_checkpoint(CheckpointBoundary.WEEK_START)

    # Observers always see stable state
    current_state = await manager.get_observable_state()
"""

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import redis.asyncio as redis
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.distributed.locks import DistributedLock
from app.events.event_bus import EventBus
from app.events.event_types import BaseEvent, EventMetadata, EventType

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================


class CheckpointBoundary(str, Enum):
    """
    Types of checkpoint boundaries where state can advance.

    Corresponds to natural periodicities in scheduling:
    - WEEK_START: 7-day period (T₁ in time crystal analogy)
    - BLOCK_END: Rotation transition points
    - ACGME_WINDOW: 28-day compliance window (T₂ in time crystal analogy)
    - MANUAL: Explicit checkpoint by administrator
    """

    WEEK_START = "week_start"
    BLOCK_END = "block_end"
    ACGME_WINDOW = "acgme_window"
    MANUAL = "manual"


class StateStatus(str, Enum):
    """Status of a schedule state."""

    DRAFT = "draft"  # Proposed changes, not yet authoritative
    AUTHORITATIVE = "authoritative"  # Current observable state
    ARCHIVED = "archived"  # Historical checkpoint


# Lock configuration
CHECKPOINT_LOCK_TIMEOUT = 60  # Checkpoint operations must complete in 60s
CHECKPOINT_LOCK_NAME = "schedule_checkpoint"


# =============================================================================
# Data Models
# =============================================================================


class ScheduleState(BaseModel):
    """
    Immutable snapshot of schedule state at a checkpoint.

    Represents the complete state of the schedule at a specific point in time.
    All assignments, metadata, and validation state.
    """

    state_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    checkpoint_boundary: CheckpointBoundary
    checkpoint_time: datetime = Field(default_factory=datetime.utcnow)
    status: StateStatus = StateStatus.DRAFT

    # Schedule data
    assignments: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Validation state
    acgme_compliant: bool = True
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)

    # Provenance
    created_by: str | None = None
    created_from_draft: str | None = None  # ID of draft that became authoritative

    # Integrity
    state_hash: str | None = None  # SHA-256 of state data for verification

    class Config:
        frozen = True  # Immutable after creation
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}

    def __init__(self, **data):
        """Initialize state and calculate hash."""
        super().__init__(**data)
        if self.state_hash is None:
            # Calculate hash after initialization
            object.__setattr__(self, "state_hash", self._calculate_hash())

    def _calculate_hash(self) -> str:
        """
        Calculate SHA-256 hash of state data for integrity verification.

        Returns:
            Hex-encoded hash string
        """
        # Create deterministic representation
        state_dict = {
            "checkpoint_boundary": self.checkpoint_boundary,
            "checkpoint_time": self.checkpoint_time.isoformat(),
            "assignments": sorted(
                (json.dumps(a, sort_keys=True) for a in self.assignments)
            ),
            "metadata": json.dumps(self.metadata, sort_keys=True),
            "acgme_compliant": self.acgme_compliant,
        }

        state_json = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(state_json.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduleState":
        """Reconstruct from dictionary."""
        return cls(**data)


@dataclass
class CheckpointEvent(BaseEvent):
    """
    Event emitted when a checkpoint transition occurs.

    Notifies all observers that the authoritative schedule state has advanced.
    This is the "stroboscopic observation" - discrete state transitions.
    """

    aggregate_type: str = "Schedule"
    checkpoint_boundary: CheckpointBoundary = field(
        default=CheckpointBoundary.MANUAL
    )
    previous_state_id: str | None = None
    new_state_id: str = ""
    checkpoint_time: datetime = field(default_factory=datetime.utcnow)
    triggered_by: str | None = None
    assignments_changed: int = 0
    acgme_compliant: bool = True

    def __init__(self, **data):
        """Initialize with event metadata."""
        if "metadata" not in data:
            data["metadata"] = EventMetadata(
                event_type="ScheduleCheckpointAdvanced",
                event_version=1,
            )
        # BaseEvent expects aggregate_id
        if "aggregate_id" not in data:
            data["aggregate_id"] = data.get("new_state_id", str(uuid.uuid4()))

        super().__init__(**data)


# =============================================================================
# Stroboscopic Schedule Manager
# =============================================================================


class StroboscopicScheduleManager:
    """
    Manages schedule state with stroboscopic (discrete checkpoint) transitions.

    Implements time crystal-inspired state management:
    - Authoritative state is stable between checkpoints
    - Draft state accumulates proposed changes
    - Checkpoints are atomic transitions with distributed locking
    - Event bus notifies observers of state transitions
    - All state transitions are logged and auditable

    Thread Safety:
    Uses Redis distributed locks to ensure only one checkpoint transition
    can occur at a time across all processes/servers.

    Example:
        # Initialize
        manager = StroboscopicScheduleManager(db, event_bus, redis_client)

        # Propose changes (non-blocking, does not affect observers)
        await manager.propose_draft(
            assignments=[...],
            metadata={"reason": "Cover Dr. Smith absence"},
            created_by="admin@example.com"
        )

        # Atomic checkpoint (locks, transitions, notifies)
        success = await manager.advance_checkpoint(
            boundary=CheckpointBoundary.WEEK_START,
            triggered_by="scheduler_cron"
        )

        # Observers see stable state
        current = await manager.get_observable_state()
        print(f"Current assignments: {len(current.assignments)}")
    """

    def __init__(
        self,
        db: AsyncSession,
        event_bus: EventBus,
        redis_client: redis.Redis,
        schedule_id: str | None = None,
    ):
        """
        Initialize stroboscopic schedule manager.

        Args:
            db: Async database session
            event_bus: Event bus for publishing checkpoint events
            redis_client: Redis client for distributed locking
            schedule_id: Optional schedule ID (generates UUID if not provided)
        """
        self.db = db
        self.event_bus = event_bus
        self.redis_client = redis_client
        self.schedule_id = schedule_id or str(uuid.uuid4())

        # State storage
        self._authoritative_state: ScheduleState | None = None
        self._draft_state: ScheduleState | None = None

        # Checkpoint history (in-memory cache, backed by DB/event store)
        self._checkpoint_history: list[ScheduleState] = []
        self._max_history_size = 50  # Keep last 50 checkpoints in memory

        # Metrics
        self._checkpoint_count = 0
        self._last_checkpoint_time: datetime | None = None

    async def initialize(self, initial_state: ScheduleState | None = None) -> None:
        """
        Initialize manager with optional initial state.

        If no initial state provided, creates empty authoritative state.

        Args:
            initial_state: Optional initial schedule state
        """
        if initial_state:
            self._authoritative_state = initial_state
        else:
            # Create empty authoritative state
            self._authoritative_state = ScheduleState(
                checkpoint_boundary=CheckpointBoundary.MANUAL,
                status=StateStatus.AUTHORITATIVE,
                assignments=[],
                metadata={"initialized_at": datetime.utcnow().isoformat()},
            )

        self._checkpoint_history.append(self._authoritative_state)
        self._last_checkpoint_time = datetime.utcnow()

        logger.info(
            f"Stroboscopic manager initialized for schedule {self.schedule_id} "
            f"with state {self._authoritative_state.state_id}"
        )

    async def get_observable_state(self) -> ScheduleState:
        """
        Get the current observable (authoritative) state.

        This is the "stroboscopic observation" - observers always see
        the state at the last checkpoint, never in-progress changes.

        Returns:
            Current authoritative schedule state

        Raises:
            RuntimeError: If manager not initialized
        """
        if self._authoritative_state is None:
            raise RuntimeError(
                "Manager not initialized. Call initialize() first."
            )

        return self._authoritative_state

    async def propose_draft(
        self,
        assignments: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str | None = None,
        validate: bool = True,
    ) -> ScheduleState:
        """
        Propose a draft schedule state without affecting authoritative state.

        This is the "staging area" - changes accumulate here until the next
        checkpoint transition. Multiple drafts can be proposed; the latest
        one will be promoted at the next checkpoint.

        Args:
            assignments: List of assignment dictionaries
            metadata: Additional metadata about this draft
            created_by: User/system creating the draft
            validate: Whether to run ACGME validation

        Returns:
            Created draft state

        Raises:
            ValueError: If validation fails and validate=True
        """
        if self._authoritative_state is None:
            raise RuntimeError(
                "Manager not initialized. Call initialize() first."
            )

        # Use current authoritative state as base if no assignments provided
        if assignments is None:
            assignments = self._authoritative_state.assignments

        if metadata is None:
            metadata = {}

        # Create draft state
        draft = ScheduleState(
            checkpoint_boundary=CheckpointBoundary.MANUAL,
            status=StateStatus.DRAFT,
            assignments=assignments,
            metadata={
                **metadata,
                "proposed_at": datetime.utcnow().isoformat(),
                "based_on_state": self._authoritative_state.state_id,
            },
            created_by=created_by,
        )

        # Validation (optional)
        validation_errors = []
        validation_warnings = []
        acgme_compliant = True

        if validate:
            # TODO: Integrate with actual ACGME validator
            # For now, basic validation
            if not assignments:
                validation_warnings.append("No assignments in draft state")

            # Update draft with validation results
            draft = ScheduleState(
                **draft.to_dict(),
                acgme_compliant=acgme_compliant,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
            )

            if not acgme_compliant:
                logger.warning(
                    f"Draft state {draft.state_id} failed ACGME validation: "
                    f"{validation_errors}"
                )

        self._draft_state = draft

        logger.info(
            f"Draft state {draft.state_id} proposed for schedule {self.schedule_id} "
            f"({len(assignments)} assignments, compliant={acgme_compliant})"
        )

        return draft

    async def discard_draft(self) -> bool:
        """
        Discard the current draft state without advancing checkpoint.

        Returns proposed changes to the void - authoritative state unchanged.

        Returns:
            True if draft was discarded, False if no draft existed
        """
        if self._draft_state is None:
            logger.debug("No draft state to discard")
            return False

        discarded_id = self._draft_state.state_id
        self._draft_state = None

        logger.info(f"Discarded draft state {discarded_id}")
        return True

    async def advance_checkpoint(
        self,
        boundary: CheckpointBoundary = CheckpointBoundary.MANUAL,
        triggered_by: str | None = None,
        force: bool = False,
    ) -> bool:
        """
        Advance the checkpoint - atomic transition from draft to authoritative.

        This is the core "stroboscopic" operation:
        1. Acquire distributed lock (prevent concurrent checkpoints)
        2. Promote draft state to authoritative
        3. Emit checkpoint event to all observers
        4. Archive previous authoritative state
        5. Release lock

        Thread Safety:
        Uses distributed lock to ensure only one checkpoint transition
        occurs at a time across all processes/servers.

        Args:
            boundary: Type of checkpoint boundary
            triggered_by: User/system triggering checkpoint
            force: Force checkpoint even if no draft exists

        Returns:
            True if checkpoint advanced successfully, False otherwise

        Raises:
            RuntimeError: If manager not initialized
        """
        if self._authoritative_state is None:
            raise RuntimeError(
                "Manager not initialized. Call initialize() first."
            )

        # Check if draft exists
        if self._draft_state is None and not force:
            logger.debug("No draft state to promote, skipping checkpoint")
            return False

        # Use current authoritative state if no draft and force=True
        new_state_source = (
            self._draft_state if self._draft_state else self._authoritative_state
        )

        # Acquire distributed lock for checkpoint transition
        lock = DistributedLock(
            name=f"{CHECKPOINT_LOCK_NAME}:{self.schedule_id}",
            timeout=CHECKPOINT_LOCK_TIMEOUT,
            redis_client=self.redis_client,
        )

        try:
            # Acquire lock with timeout
            acquired = await lock.acquire(blocking=True, acquisition_timeout=30)

            if not acquired:
                logger.error(
                    f"Failed to acquire checkpoint lock for {self.schedule_id}"
                )
                return False

            logger.debug(
                f"Acquired checkpoint lock for schedule {self.schedule_id}"
            )

            # Archive previous authoritative state
            previous_state = self._authoritative_state
            previous_state_archived = ScheduleState(
                **previous_state.to_dict(),
                status=StateStatus.ARCHIVED,
            )
            self._checkpoint_history.append(previous_state_archived)

            # keep history bounded
            if len(self._checkpoint_history) > self._max_history_size:
                self._checkpoint_history.pop(0)

            # Promote draft to authoritative
            new_authoritative = ScheduleState(
                **new_state_source.to_dict(),
                checkpoint_boundary=boundary,
                checkpoint_time=datetime.utcnow(),
                status=StateStatus.AUTHORITATIVE,
                created_from_draft=(
                    new_state_source.state_id
                    if new_state_source.status == StateStatus.DRAFT
                    else None
                ),
            )

            # Calculate changes
            assignments_changed = self._count_changed_assignments(
                previous_state, new_authoritative
            )

            # Update manager state
            self._authoritative_state = new_authoritative
            self._draft_state = None  # Clear draft
            self._checkpoint_count += 1
            self._last_checkpoint_time = datetime.utcnow()

            logger.info(
                f"Checkpoint advanced for schedule {self.schedule_id}: "
                f"{previous_state.state_id} → {new_authoritative.state_id} "
                f"(boundary={boundary}, changes={assignments_changed})"
            )

            # Emit checkpoint event to notify all observers
            checkpoint_event = CheckpointEvent(
                aggregate_id=self.schedule_id,
                checkpoint_boundary=boundary,
                previous_state_id=previous_state.state_id,
                new_state_id=new_authoritative.state_id,
                checkpoint_time=new_authoritative.checkpoint_time,
                triggered_by=triggered_by,
                assignments_changed=assignments_changed,
                acgme_compliant=new_authoritative.acgme_compliant,
            )

            await self.event_bus.publish(checkpoint_event)

            logger.debug(
                f"Published checkpoint event for state {new_authoritative.state_id}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Error during checkpoint advance for {self.schedule_id}: {e}",
                exc_info=True,
            )
            return False

        finally:
            # Always release lock
            try:
                await lock.release()
                logger.debug(
                    f"Released checkpoint lock for schedule {self.schedule_id}"
                )
            except Exception as e:
                logger.error(f"Error releasing checkpoint lock: {e}")

    async def get_checkpoint_history(
        self, limit: int = 10
    ) -> list[ScheduleState]:
        """
        Get recent checkpoint history.

        Returns the last N authoritative states from checkpoint transitions.

        Args:
            limit: Maximum number of checkpoints to return

        Returns:
            List of historical checkpoint states (most recent first)
        """
        return list(reversed(self._checkpoint_history[-limit:]))

    async def get_draft_state(self) -> ScheduleState | None:
        """
        Get the current draft state (if any).

        Returns:
            Current draft state or None
        """
        return self._draft_state

    async def get_metrics(self) -> dict[str, Any]:
        """
        Get manager metrics for monitoring.

        Returns:
            Dictionary with checkpoint statistics
        """
        time_since_last_checkpoint = None
        if self._last_checkpoint_time:
            time_since_last_checkpoint = (
                datetime.utcnow() - self._last_checkpoint_time
            ).total_seconds()

        return {
            "schedule_id": self.schedule_id,
            "total_checkpoints": self._checkpoint_count,
            "last_checkpoint_time": (
                self._last_checkpoint_time.isoformat()
                if self._last_checkpoint_time
                else None
            ),
            "time_since_last_checkpoint_seconds": time_since_last_checkpoint,
            "current_state_id": (
                self._authoritative_state.state_id
                if self._authoritative_state
                else None
            ),
            "draft_pending": self._draft_state is not None,
            "draft_state_id": (
                self._draft_state.state_id if self._draft_state else None
            ),
            "history_size": len(self._checkpoint_history),
            "authoritative_assignments_count": (
                len(self._authoritative_state.assignments)
                if self._authoritative_state
                else 0
            ),
            "acgme_compliant": (
                self._authoritative_state.acgme_compliant
                if self._authoritative_state
                else None
            ),
        }

    def _count_changed_assignments(
        self, old_state: ScheduleState, new_state: ScheduleState
    ) -> int:
        """
        Count number of assignments that changed between states.

        Uses state hashes for quick comparison if available, otherwise
        performs detailed comparison.

        Args:
            old_state: Previous state
            new_state: New state

        Returns:
            Number of assignments that changed
        """
        # Quick check: if hashes match, no changes
        if (
            old_state.state_hash
            and new_state.state_hash
            and old_state.state_hash == new_state.state_hash
        ):
            return 0

        # Convert assignments to sets for comparison
        old_assignments = {
            self._assignment_key(a) for a in old_state.assignments
        }
        new_assignments = {
            self._assignment_key(a) for a in new_state.assignments
        }

        # Count added and removed assignments
        added = new_assignments - old_assignments
        removed = old_assignments - new_assignments

        return len(added) + len(removed)

    def _assignment_key(self, assignment: dict[str, Any]) -> str:
        """
        Generate a unique key for an assignment for comparison.

        Args:
            assignment: Assignment dictionary

        Returns:
            Unique key string
        """
        # Use core fields to identify assignment
        person_id = assignment.get("person_id", "")
        block_id = assignment.get("block_id", "")
        rotation_id = assignment.get("rotation_id", "")
        role = assignment.get("role", "")

        return f"{person_id}:{block_id}:{rotation_id}:{role}"


# =============================================================================
# Factory Functions
# =============================================================================


async def create_stroboscopic_manager(
    db: AsyncSession,
    event_bus: EventBus,
    redis_client: redis.Redis,
    schedule_id: str | None = None,
    initialize_empty: bool = True,
) -> StroboscopicScheduleManager:
    """
    Create and optionally initialize a stroboscopic schedule manager.

    Args:
        db: Async database session
        event_bus: Event bus instance
        redis_client: Redis client instance
        schedule_id: Optional schedule ID
        initialize_empty: Whether to initialize with empty state

    Returns:
        Initialized StroboscopicScheduleManager instance
    """
    manager = StroboscopicScheduleManager(
        db=db,
        event_bus=event_bus,
        redis_client=redis_client,
        schedule_id=schedule_id,
    )

    if initialize_empty:
        await manager.initialize()

    return manager


# =============================================================================
# Checkpoint Scheduler (Helper)
# =============================================================================


class CheckpointScheduler:
    """
    Helper class for scheduling automatic checkpoints at periodic boundaries.

    Monitors time and triggers checkpoints at appropriate intervals:
    - Every Monday 00:00 (week start)
    - Every 28 days (ACGME window)
    - On-demand manual checkpoints

    This is typically run as a background task (Celery beat, etc.)
    """

    def __init__(
        self,
        manager: StroboscopicScheduleManager,
        enable_auto_checkpoints: bool = True,
    ):
        """
        Initialize checkpoint scheduler.

        Args:
            manager: Stroboscopic manager to schedule checkpoints for
            enable_auto_checkpoints: Whether to enable automatic checkpoints
        """
        self.manager = manager
        self.enable_auto_checkpoints = enable_auto_checkpoints
        self._last_week_checkpoint: datetime | None = None
        self._last_acgme_checkpoint: datetime | None = None

    async def should_checkpoint(self) -> CheckpointBoundary | None:
        """
        Check if a checkpoint should be triggered based on time boundaries.

        Returns:
            CheckpointBoundary if checkpoint needed, None otherwise
        """
        if not self.enable_auto_checkpoints:
            return None

        now = datetime.utcnow()

        # Check for week boundary (Monday 00:00)
        if now.weekday() == 0:  # Monday
            if (
                self._last_week_checkpoint is None
                or (now - self._last_week_checkpoint).days >= 7
            ):
                return CheckpointBoundary.WEEK_START

        # Check for ACGME window (every 28 days)
        if (
            self._last_acgme_checkpoint is None
            or (now - self._last_acgme_checkpoint).days >= 28
        ):
            return CheckpointBoundary.ACGME_WINDOW

        return None

    async def run_checkpoint_if_needed(
        self, triggered_by: str = "scheduler"
    ) -> bool:
        """
        Run checkpoint if time boundary has been reached.

        Args:
            triggered_by: Identifier of who/what triggered the check

        Returns:
            True if checkpoint was executed, False otherwise
        """
        boundary = await self.should_checkpoint()

        if boundary is None:
            return False

        success = await self.manager.advance_checkpoint(
            boundary=boundary, triggered_by=triggered_by
        )

        if success:
            now = datetime.utcnow()
            if boundary == CheckpointBoundary.WEEK_START:
                self._last_week_checkpoint = now
            elif boundary == CheckpointBoundary.ACGME_WINDOW:
                self._last_acgme_checkpoint = now

            logger.info(
                f"Automatic checkpoint executed: {boundary} (triggered by {triggered_by})"
            )

        return success
