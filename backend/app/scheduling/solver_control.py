"""
Solver Control Module for Kill-Switch and Progress Tracking.

Provides runtime control over solver execution:
- Kill-switch to abort runaway solver jobs
- Progress tracking for monitoring long-running solves
- Graceful shutdown with best-solution-so-far capture

Architecture:
- Redis-backed for distributed coordination
- Synchronous API for integration with solver loops
- TTL-based cleanup to prevent stale state

Usage:
    # In solver loop:
    for iteration in solver.iterate():
        if abort_reason := SolverControl.should_abort(run_id):
            logger.warning(f"Solver aborted: {abort_reason}")
            return PartialResult(best_so_far, aborted=True)

        SolverControl.update_progress(run_id, iteration, score)

    # From API endpoint:
    SolverControl.request_abort(run_id, "operator request")
"""

import json
import logging
from datetime import datetime
from redis import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_redis_client() -> Redis:
    """Get synchronous Redis client for solver control operations."""
    settings = get_settings()
    return Redis.from_url(settings.redis_url_with_password, decode_responses=True)


class SolverControl:
    """
    Control interface for in-progress solver jobs.

    Provides:
    - Abort signaling via Redis flags
    - Progress tracking for monitoring
    - Graceful shutdown coordination

    All operations use synchronous Redis to work within solver loops
    which may not be async-friendly.
    """

    ABORT_KEY_PREFIX = "solver:abort:"
    PROGRESS_KEY_PREFIX = "solver:progress:"
    RESULT_KEY_PREFIX = "solver:result:"

    # TTLs for cleanup
    ABORT_TTL_SECONDS = 3600  # 1 hour
    PROGRESS_TTL_SECONDS = 7200  # 2 hours
    RESULT_TTL_SECONDS = 86400  # 24 hours

    @classmethod
    def request_abort(
        cls, run_id: str, reason: str = "operator request", requested_by: str = "system"
    ) -> bool:
        """
        Signal a solver to abort gracefully.

        Args:
            run_id: Schedule run ID or job ID to abort
            reason: Human-readable reason for abort
            requested_by: Username or system ID requesting abort

        Returns:
            bool: True if abort signal was set successfully

        Example:
            >>> SolverControl.request_abort("run-123", "timeout exceeded", "admin")
            True
        """
        try:
            redis_client = _get_redis_client()
            key = f"{cls.ABORT_KEY_PREFIX}{run_id}"

            abort_data = json.dumps(
                {
                    "reason": reason,
                    "requested_by": requested_by,
                    "requested_at": datetime.utcnow().isoformat(),
                }
            )

            redis_client.setex(key, cls.ABORT_TTL_SECONDS, abort_data)
            logger.warning(
                f"Abort requested for solver run {run_id}: {reason} (by {requested_by})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to set abort flag for {run_id}: {e}")
            return False

    @classmethod
    def should_abort(cls, run_id: str) -> str | None:
        """
        Check if solver should abort. Call this in solver loop.

        Args:
            run_id: Schedule run ID or job ID to check

        Returns:
            Optional[str]: Abort reason if abort requested, None otherwise

        Example:
            >>> if reason := SolverControl.should_abort("run-123"):
            ...     raise RuntimeError(f"Solver aborted: {reason}")
        """
        try:
            redis_client = _get_redis_client()
            key = f"{cls.ABORT_KEY_PREFIX}{run_id}"

            abort_data = redis_client.get(key)
            if abort_data:
                data = json.loads(abort_data)
                return data.get("reason", "abort requested")
            return None

        except Exception as e:
            logger.error(f"Failed to check abort flag for {run_id}: {e}")
            return None

    @classmethod
    def clear_abort(cls, run_id: str) -> None:
        """
        Clear abort flag after solver stops.

        Args:
            run_id: Schedule run ID or job ID to clear
        """
        try:
            redis_client = _get_redis_client()
            redis_client.delete(f"{cls.ABORT_KEY_PREFIX}{run_id}")
            logger.debug(f"Cleared abort flag for {run_id}")
        except Exception as e:
            logger.error(f"Failed to clear abort flag for {run_id}: {e}")

    @classmethod
    def update_progress(
        cls,
        run_id: str,
        iteration: int,
        best_score: float,
        assignments_count: int = 0,
        violations_count: int = 0,
        status: str = "running",
    ) -> None:
        """
        Update solver progress for monitoring.

        Args:
            run_id: Schedule run ID or job ID
            iteration: Current solver iteration
            best_score: Best objective score found so far
            assignments_count: Number of assignments in best solution
            violations_count: Number of constraint violations
            status: Current status (running, completing, aborted)

        Example:
            >>> SolverControl.update_progress("run-123", 1000, 0.85, 150, 2)
        """
        try:
            redis_client = _get_redis_client()
            key = f"{cls.PROGRESS_KEY_PREFIX}{run_id}"

            progress_data = {
                "iteration": iteration,
                "best_score": best_score,
                "assignments_count": assignments_count,
                "violations_count": violations_count,
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
            }

            redis_client.hset(
                key,
                mapping={
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in progress_data.items()
                },
            )
            redis_client.expire(key, cls.PROGRESS_TTL_SECONDS)

        except Exception as e:
            # Don't fail solver on progress update errors
            logger.debug(f"Failed to update progress for {run_id}: {e}")

    @classmethod
    def get_progress(cls, run_id: str) -> dict | None:
        """
        Get current progress for a solver run.

        Args:
            run_id: Schedule run ID or job ID

        Returns:
            Optional[dict]: Progress data or None if not found
        """
        try:
            redis_client = _get_redis_client()
            key = f"{cls.PROGRESS_KEY_PREFIX}{run_id}"

            progress_data = redis_client.hgetall(key)
            if not progress_data:
                return None

            # Parse numeric fields
            return {
                "run_id": run_id,
                "iteration": int(progress_data.get("iteration", 0)),
                "best_score": float(progress_data.get("best_score", 0.0)),
                "assignments_count": int(progress_data.get("assignments_count", 0)),
                "violations_count": int(progress_data.get("violations_count", 0)),
                "status": progress_data.get("status", "unknown"),
                "updated_at": progress_data.get("updated_at"),
            }

        except Exception as e:
            logger.error(f"Failed to get progress for {run_id}: {e}")
            return None

    @classmethod
    def save_partial_result(
        cls, run_id: str, assignments: list, score: float, reason: str
    ) -> None:
        """
        Save partial result when solver is interrupted.

        Args:
            run_id: Schedule run ID or job ID
            assignments: Best assignments found
            score: Objective score
            reason: Why solver stopped (abort, timeout, error)
        """
        try:
            redis_client = _get_redis_client()
            key = f"{cls.RESULT_KEY_PREFIX}{run_id}"

            result_data = json.dumps(
                {
                    "assignments_count": len(assignments),
                    "score": score,
                    "reason": reason,
                    "saved_at": datetime.utcnow().isoformat(),
                    "is_partial": True,
                }
            )

            redis_client.setex(key, cls.RESULT_TTL_SECONDS, result_data)
            logger.info(
                f"Saved partial result for {run_id}: {len(assignments)} assignments"
            )

        except Exception as e:
            logger.error(f"Failed to save partial result for {run_id}: {e}")

    @classmethod
    def get_active_runs(cls) -> list[dict]:
        """
        Get all active solver runs with progress.

        Returns:
            list[dict]: List of active run progress data
        """
        try:
            redis_client = _get_redis_client()

            # Scan for progress keys
            active_runs = []
            for key in redis_client.scan_iter(f"{cls.PROGRESS_KEY_PREFIX}*", count=100):
                run_id = key.replace(cls.PROGRESS_KEY_PREFIX, "")
                progress = cls.get_progress(run_id)
                if progress and progress.get("status") == "running":
                    active_runs.append(progress)

            return active_runs

        except Exception as e:
            logger.error(f"Failed to get active runs: {e}")
            return []

    @classmethod
    def cleanup_stale(cls) -> int:
        """
        Clean up stale progress entries.

        Returns:
            int: Number of entries cleaned up
        """
        try:
            redis_client = _get_redis_client()
            cleaned = 0

            for key in redis_client.scan_iter(f"{cls.PROGRESS_KEY_PREFIX}*", count=100):
                # Redis TTL handles expiration, but we can clean up
                # entries with status != "running" that are old
                ttl = redis_client.ttl(key)
                if ttl == -1:  # No TTL set
                    redis_client.expire(key, cls.PROGRESS_TTL_SECONDS)
                    cleaned += 1

            return cleaned

        except Exception as e:
            logger.error(f"Failed to cleanup stale entries: {e}")
            return 0
