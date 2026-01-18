"""
Solver Snapshot: Checkpointing for Long-Running Schedule Generation.

Provides checkpoint/resume capability for solver jobs to handle timeouts,
crashes, and graceful interruptions. Integrates with SolverControl for
abort handling and progress tracking.

Features:
    - Periodic checkpoint saves during solver execution
    - Resume from checkpoint on timeout/crash
    - Hash-verified integrity checks
    - TTL-based cleanup

Usage:
    # During solver execution
    snapshot_manager = SolverSnapshotManager(run_id)

    for iteration in solver.iterate():
        assignments = solver.get_best_solution()

        # Save checkpoint periodically
        if iteration % 100 == 0:
            snapshot_manager.save_checkpoint(
                assignments=assignments,
                iteration=iteration,
                score=solver.best_score,
            )

    # Resume from previous run
    checkpoint = SolverSnapshotManager.load_checkpoint(run_id)
    if checkpoint:
        solver.resume_from(checkpoint.assignments)
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_redis_client() -> Redis:
    """Get synchronous Redis client for snapshot operations."""
    settings = get_settings()
    return Redis.from_url(settings.redis_url_with_password, decode_responses=True)


@dataclass
class SolverCheckpoint:
    """
    Immutable snapshot of solver state at a point in time.

    Attributes:
        run_id: Schedule run identifier
        iteration: Solver iteration at checkpoint
        assignments: List of assignment tuples (person_id, block_id, template_id)
        score: Objective score at checkpoint
        violations_count: Number of constraint violations
        timestamp: When checkpoint was created
        metadata: Additional solver state (algorithm, parameters, etc.)
        hash: SHA-256 hash for integrity verification
    """

    run_id: str
    iteration: int
    assignments: list[tuple[str, str, str | None]]  # UUIDs as strings
    score: float
    violations_count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)
    hash: str = ""

    def __post_init__(self) -> None:
        """Calculate hash if not provided."""
        if not self.hash:
            self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of checkpoint data."""
        # Sort assignments for consistent hashing
        sorted_assignments = sorted(self.assignments)

        hash_input = {
            "run_id": self.run_id,
            "iteration": self.iteration,
            "assignments": sorted_assignments,
            "score": self.score,
        }

        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:16]

    def verify_integrity(self) -> bool:
        """Verify checkpoint integrity via hash."""
        expected_hash = self._calculate_hash()
        is_valid = self.hash == expected_hash

        if not is_valid:
            logger.warning(
                f"Checkpoint integrity check failed for {self.run_id}: "
                f"expected {expected_hash}, got {self.hash}"
            )

        return is_valid

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "iteration": self.iteration,
            "assignments": self.assignments,
            "score": self.score,
            "violations_count": self.violations_count,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SolverCheckpoint":
        """Create checkpoint from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()

        return cls(
            run_id=data["run_id"],
            iteration=data["iteration"],
            assignments=data["assignments"],
            score=data["score"],
            violations_count=data.get("violations_count", 0),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
            hash=data.get("hash", ""),
        )


class SolverSnapshotManager:
    """
    Manages solver checkpoints in Redis.

    Provides checkpoint save/load operations with TTL-based cleanup
    and integrity verification.

    Key patterns:
        - solver:checkpoint:{run_id} - Latest checkpoint data
        - solver:checkpoint:history:{run_id} - List of checkpoint hashes
    """

    CHECKPOINT_KEY_PREFIX = "solver:checkpoint:"
    HISTORY_KEY_PREFIX = "solver:checkpoint:history:"

    # TTLs for cleanup
    CHECKPOINT_TTL_SECONDS = 86400  # 24 hours
    MAX_HISTORY_LENGTH = 10  # Keep last 10 checkpoint hashes

    def __init__(self, run_id: str) -> None:
        """
        Initialize snapshot manager for a specific run.

        Args:
            run_id: Schedule run ID or job ID
        """
        self.run_id = run_id
        self._redis: Redis | None = None

    @property
    def redis(self) -> Redis:
        """Lazy Redis client initialization."""
        if self._redis is None:
            self._redis = _get_redis_client()
        return self._redis

    def save_checkpoint(
        self,
        assignments: list[tuple[UUID, UUID, UUID | None]]
        | list[tuple[str, str, str | None]],
        iteration: int,
        score: float,
        violations_count: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> SolverCheckpoint:
        """
        Save a checkpoint of current solver state.

        Args:
            assignments: Current assignment tuples (person_id, block_id, template_id)
            iteration: Current solver iteration
            score: Current objective score
            violations_count: Number of constraint violations
            metadata: Additional solver state to preserve

        Returns:
            SolverCheckpoint: The saved checkpoint

        Example:
            >>> manager = SolverSnapshotManager("run-123")
            >>> checkpoint = manager.save_checkpoint(
            ...     assignments=solver.get_assignments(),
            ...     iteration=500,
            ...     score=0.85,
            ... )
            >>> print(f"Checkpoint saved: {checkpoint.hash}")
        """
        # Convert UUIDs to strings for serialization
        str_assignments = [
            (
                str(person_id),
                str(block_id),
                str(template_id) if template_id else None,
            )
            for person_id, block_id, template_id in assignments
        ]

        checkpoint = SolverCheckpoint(
            run_id=self.run_id,
            iteration=iteration,
            assignments=str_assignments,
            score=score,
            violations_count=violations_count,
            metadata=metadata or {},
        )

        try:
            # Save checkpoint data
            key = f"{self.CHECKPOINT_KEY_PREFIX}{self.run_id}"
            self.redis.setex(
                key,
                self.CHECKPOINT_TTL_SECONDS,
                json.dumps(checkpoint.to_dict()),
            )

            # Update history
            history_key = f"{self.HISTORY_KEY_PREFIX}{self.run_id}"
            self.redis.lpush(history_key, checkpoint.hash)
            self.redis.ltrim(history_key, 0, self.MAX_HISTORY_LENGTH - 1)
            self.redis.expire(history_key, self.CHECKPOINT_TTL_SECONDS)

            logger.debug(
                f"Checkpoint saved for {self.run_id}: "
                f"iter={iteration}, score={score:.3f}, assignments={len(assignments)}"
            )

            return checkpoint

        except Exception as e:
            logger.error(f"Failed to save checkpoint for {self.run_id}: {e}")
            raise

    def load_checkpoint(self) -> SolverCheckpoint | None:
        """
        Load the latest checkpoint for this run.

        Returns:
            Optional[SolverCheckpoint]: Latest checkpoint or None if not found

        Example:
            >>> manager = SolverSnapshotManager("run-123")
            >>> checkpoint = manager.load_checkpoint()
            >>> if checkpoint:
            ...     solver.resume_from_iteration(checkpoint.iteration)
        """
        return self.load_checkpoint_for_run(self.run_id)

    @classmethod
    def load_checkpoint_for_run(cls, run_id: str) -> SolverCheckpoint | None:
        """
        Load checkpoint for a specific run ID.

        Args:
            run_id: Schedule run ID or job ID

        Returns:
            Optional[SolverCheckpoint]: Checkpoint or None if not found
        """
        try:
            redis_client = _get_redis_client()
            key = f"{cls.CHECKPOINT_KEY_PREFIX}{run_id}"

            checkpoint_data = redis_client.get(key)
            if not checkpoint_data:
                return None

            data = json.loads(checkpoint_data)
            checkpoint = SolverCheckpoint.from_dict(data)

            # Verify integrity
            if not checkpoint.verify_integrity():
                logger.error(
                    f"Checkpoint for {run_id} failed integrity check, ignoring"
                )
                return None

            logger.info(
                f"Loaded checkpoint for {run_id}: "
                f"iter={checkpoint.iteration}, score={checkpoint.score:.3f}"
            )

            return checkpoint

        except Exception as e:
            logger.error(f"Failed to load checkpoint for {run_id}: {e}")
            return None

    def delete_checkpoint(self) -> bool:
        """
        Delete checkpoint for this run.

        Returns:
            bool: True if deleted successfully
        """
        try:
            self.redis.delete(f"{self.CHECKPOINT_KEY_PREFIX}{self.run_id}")
            self.redis.delete(f"{self.HISTORY_KEY_PREFIX}{self.run_id}")
            logger.debug(f"Deleted checkpoint for {self.run_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete checkpoint for {self.run_id}: {e}")
            return False

    def get_history(self) -> list[str]:
        """
        Get checkpoint hash history for this run.

        Returns:
            list[str]: List of checkpoint hashes (most recent first)
        """
        try:
            history_key = f"{self.HISTORY_KEY_PREFIX}{self.run_id}"
            return self.redis.lrange(history_key, 0, -1)

        except Exception as e:
            logger.error(f"Failed to get history for {self.run_id}: {e}")
            return []

    @classmethod
    def get_all_checkpoints(cls) -> list[dict[str, Any]]:
        """
        Get summary of all active checkpoints.

        Returns:
            list[dict]: List of checkpoint summaries
        """
        try:
            redis_client = _get_redis_client()
            checkpoints = []

            for key in redis_client.scan_iter(
                f"{cls.CHECKPOINT_KEY_PREFIX}*", count=100
            ):
                # Skip history keys
                if "history" in key:
                    continue

                run_id = key.replace(cls.CHECKPOINT_KEY_PREFIX, "")
                checkpoint_data = redis_client.get(key)

                if checkpoint_data:
                    data = json.loads(checkpoint_data)
                    checkpoints.append(
                        {
                            "run_id": run_id,
                            "iteration": data.get("iteration"),
                            "score": data.get("score"),
                            "assignments_count": len(data.get("assignments", [])),
                            "timestamp": data.get("timestamp"),
                            "hash": data.get("hash"),
                        }
                    )

            return checkpoints

        except Exception as e:
            logger.error(f"Failed to get all checkpoints: {e}")
            return []

    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Clean up expired checkpoints.

        Note: Redis TTL handles most cleanup, but this ensures orphaned keys
        are removed.

        Returns:
            int: Number of keys cleaned up
        """
        try:
            redis_client = _get_redis_client()
            cleaned = 0

            for key in redis_client.scan_iter(
                f"{cls.CHECKPOINT_KEY_PREFIX}*", count=100
            ):
                ttl = redis_client.ttl(key)
                if ttl == -1:  # No TTL set
                    redis_client.expire(key, cls.CHECKPOINT_TTL_SECONDS)
                    cleaned += 1

            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup checkpoints: {e}")
            return 0


# Convenience functions for common operations
def save_solver_checkpoint(
    run_id: str,
    assignments: list[tuple[UUID, UUID, UUID | None]],
    iteration: int,
    score: float,
    violations_count: int = 0,
    metadata: dict[str, Any] | None = None,
) -> SolverCheckpoint:
    """
    Save a solver checkpoint (convenience function).

    Args:
        run_id: Schedule run ID
        assignments: Current assignment tuples
        iteration: Current iteration
        score: Current score
        violations_count: Number of violations
        metadata: Additional state

    Returns:
        SolverCheckpoint: The saved checkpoint
    """
    manager = SolverSnapshotManager(run_id)
    return manager.save_checkpoint(
        assignments=assignments,
        iteration=iteration,
        score=score,
        violations_count=violations_count,
        metadata=metadata,
    )


def load_solver_checkpoint(run_id: str) -> SolverCheckpoint | None:
    """
    Load a solver checkpoint (convenience function).

    Args:
        run_id: Schedule run ID

    Returns:
        Optional[SolverCheckpoint]: Checkpoint or None
    """
    return SolverSnapshotManager.load_checkpoint_for_run(run_id)
