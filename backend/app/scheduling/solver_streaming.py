"""
Solution Streaming for Real-Time Visualization.

Extends SolverProgressCallback to store full solution snapshots
with delta encoding for efficient transmission to frontend clients.

This enables the 3D Voxel Command Center to visualize CP-SAT solving
in real-time, showing voxels rearranging as better solutions are found.

Architecture:
    - SolutionStreamingCallback: OR-Tools callback that captures solutions
    - SolutionSnapshot: Complete solution at a point in time
    - SolutionDelta: Efficient diff between consecutive solutions
    - Redis storage with TTL for solution history

Usage:
    from app.scheduling.solver_streaming import SolutionStreamingCallback

    # In CPSATSolver.solve():
    callback = SolutionStreamingCallback(
        task_id=self.task_id,
        redis_client=self.redis_client,
        decision_vars=x,  # {(r_idx, b_idx, t_idx): BoolVar}
        context=context,
    )
    status = solver.Solve(model, callback.get_callback())

    # Retrieve solutions later:
    solutions = SolutionStreamingCallback.get_solutions(task_id, redis_client)
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.scheduling.context import SchedulingContext

logger = logging.getLogger(__name__)

# TTL for solution storage (10 minutes)
SOLUTION_TTL_SECONDS = 600

# Maximum solutions to store per task
MAX_SOLUTIONS_STORED = 50


@dataclass
class SolutionSnapshot:
    """
    A complete solution snapshot with all assignments.

    Attributes:
        solution_num: Sequential solution number (1-indexed)
        timestamp: Seconds elapsed since solve started
        assignments: List of assignment dicts with IDs and indices
        objective_value: CP-SAT objective value (higher = better)
        optimality_gap_pct: Gap from proven optimal (0 = optimal)
        is_optimal: Whether this is proven optimal
    """

    solution_num: int
    timestamp: float
    assignments: list[dict]
    objective_value: float
    optimality_gap_pct: float
    is_optimal: bool = False


@dataclass
class SolutionDelta:
    """
    Delta between two consecutive solutions.

    This is much smaller than full snapshots, typically 5-20% of the size.
    Used for efficient WebSocket transmission.

    Attributes:
        solution_num: Solution number this delta produces
        timestamp: Seconds elapsed since solve started
        added: New assignments not in previous solution
        removed: Assignments removed from previous solution
        moved: Assignments with same person/block but different template
        metrics: Additional metrics for this solution
    """

    solution_num: int
    timestamp: float
    added: list[dict] = field(default_factory=list)
    removed: list[dict] = field(default_factory=list)
    moved: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


class SolutionStreamingCallback:
    """
    Extended callback that stores full solutions for real-time streaming.

    This callback is passed to CP-SAT's Solve() method and is invoked
    each time a new feasible solution is found. It:

    1. Extracts the complete assignment list from decision variables
    2. Calculates delta from previous solution (for efficiency)
    3. Stores both in Redis with TTL
    4. Optionally broadcasts via WebSocket

    Example:
        callback = SolutionStreamingCallback(task_id, redis_client, vars, ctx)
        status = solver.Solve(model, callback.get_callback())

        # Later, retrieve solutions:
        solutions = SolutionStreamingCallback.get_solutions(task_id, redis)
    """

    def __init__(
        self,
        task_id: str,
        redis_client: Any,
        decision_vars: dict[tuple[int, int, int], Any],
        context: SchedulingContext,
        broadcast_callback: Any | None = None,
    ) -> None:
        """
        Initialize the streaming callback.

        Args:
            task_id: Unique identifier for this solve task
            redis_client: Redis client for storing solutions
            decision_vars: Dict mapping (r_idx, b_idx, t_idx) to BoolVar
            context: SchedulingContext with index lookups
            broadcast_callback: Optional async callback for WebSocket broadcast
        """
        self.task_id = task_id
        self.redis = redis_client
        self.decision_vars = decision_vars
        self.context = context
        self.broadcast_callback = broadcast_callback
        self.solutions: list[SolutionSnapshot] = []
        self._callback: Any = None

        self._create_callback()

    def _create_callback(self) -> None:
        """Create the OR-Tools callback with solution extraction."""
        try:
            from ortools.sat.python import cp_model
        except ImportError:
            logger.warning("OR-Tools not available, solution streaming disabled")
            return

        outer = self

        class _StreamingCallback(cp_model.CpSolverSolutionCallback):
            """Inner callback class that inherits from OR-Tools base."""

            def __init__(self) -> None:
                super().__init__()
                self.start_time = time.time()

            def on_solution_callback(self) -> None:
                """
                Called by OR-Tools when a new solution is found.

                Extracts assignments, calculates metrics, stores in Redis.
                """
                solution_num = len(outer.solutions) + 1
                elapsed = time.time() - self.start_time

                # Check if we've hit the storage limit
                if solution_num > MAX_SOLUTIONS_STORED:
                    logger.debug(
                        f"Solution {solution_num} exceeds max stored "
                        f"({MAX_SOLUTIONS_STORED}), skipping storage"
                    )
                    return

                # Extract assignments from decision variables
                assignments = outer._extract_assignments(self)

                # Calculate optimality metrics
                current_obj = self.ObjectiveValue()
                best_bound = self.BestObjectiveBound()
                gap = 0.0
                if best_bound != 0:
                    gap = abs(best_bound - current_obj) / abs(best_bound) * 100

                # Create snapshot
                snapshot = SolutionSnapshot(
                    solution_num=solution_num,
                    timestamp=round(elapsed, 3),
                    assignments=assignments,
                    objective_value=current_obj,
                    optimality_gap_pct=round(gap, 2),
                    is_optimal=(gap < 0.01),
                )
                outer.solutions.append(snapshot)

                logger.info(
                    f"Solution {solution_num} found: {len(assignments)} assignments, "
                    f"obj={current_obj}, gap={gap:.2f}%"
                )

                # Store in Redis
                outer._store_solution(snapshot)

                # Broadcast if callback provided
                if outer.broadcast_callback:
                    try:
                        outer._trigger_broadcast(snapshot)
                    except Exception as e:
                        logger.error(f"Broadcast failed: {e}")

        self._callback = _StreamingCallback()

    def _extract_assignments(self, callback: Any) -> list[dict]:
        """
        Extract assignments from decision variable values.

        Args:
            callback: The OR-Tools callback with Value() method

        Returns:
            List of assignment dicts with person/block/template IDs
        """
        assignments = []

        for (r_idx, b_idx, t_idx), var in self.decision_vars.items():
            if callback.Value(var):
                # Get actual IDs from context indices
                try:
                    person = self.context.residents[r_idx]
                    block = self.context.blocks[b_idx]
                    template = self.context.rotation_templates[t_idx]

                    assignments.append(
                        {
                            "personId": str(person.id),
                            "blockId": str(block.id),
                            "templateId": str(template.id),
                            # Include indices for frontend position calculation
                            "rIdx": r_idx,
                            "bIdx": b_idx,
                            "tIdx": t_idx,
                        }
                    )
                except (IndexError, AttributeError) as e:
                    logger.warning(f"Index lookup failed: {e}")
                    # Fallback to indices only
                    assignments.append(
                        {
                            "rIdx": r_idx,
                            "bIdx": b_idx,
                            "tIdx": t_idx,
                        }
                    )

        return assignments

    def _store_solution(self, snapshot: SolutionSnapshot) -> None:
        """
        Store solution snapshot in Redis.

        First solution is stored as full snapshot.
        Subsequent solutions are stored as deltas for efficiency.

        Args:
            snapshot: The solution snapshot to store
        """
        if not self.redis:
            return

        key = f"solver_solution:{self.task_id}:{snapshot.solution_num}"

        try:
            if snapshot.solution_num == 1:
                # First solution: store full snapshot
                data = {
                    "type": "full",
                    "solution_num": snapshot.solution_num,
                    "timestamp": snapshot.timestamp,
                    "assignments": snapshot.assignments,
                    "assignment_count": len(snapshot.assignments),
                    "objective_value": snapshot.objective_value,
                    "optimality_gap_pct": snapshot.optimality_gap_pct,
                    "is_optimal": snapshot.is_optimal,
                }
            else:
                # Subsequent solutions: calculate and store delta
                prev = self.solutions[-2]
                delta = self._calculate_delta(prev, snapshot)
                data = {
                    "type": "delta",
                    "solution_num": snapshot.solution_num,
                    "timestamp": snapshot.timestamp,
                    "delta": {
                        "added": delta.added,
                        "removed": delta.removed,
                        "moved": delta.moved,
                    },
                    "assignment_count": len(snapshot.assignments),
                    "objective_value": snapshot.objective_value,
                    "optimality_gap_pct": snapshot.optimality_gap_pct,
                    "is_optimal": snapshot.is_optimal,
                }

            self.redis.setex(key, SOLUTION_TTL_SECONDS, json.dumps(data))

            # Update solution index list
            index_key = f"solver_solutions:{self.task_id}"
            self.redis.rpush(index_key, snapshot.solution_num)
            self.redis.expire(index_key, SOLUTION_TTL_SECONDS)

            logger.debug(f"Stored solution {snapshot.solution_num} in Redis")

        except Exception as e:
            logger.error(f"Failed to store solution in Redis: {e}")

    def _calculate_delta(
        self,
        prev: SolutionSnapshot,
        curr: SolutionSnapshot,
    ) -> SolutionDelta:
        """
        Calculate the delta between two consecutive solutions.

        This identifies:
        - Added: New assignments not in previous solution
        - Removed: Assignments that were removed
        - Moved: Same person/block but different template (activity change)

        Args:
            prev: Previous solution snapshot
            curr: Current solution snapshot

        Returns:
            SolutionDelta with added/removed/moved lists
        """
        # Create lookup sets for O(1) comparison
        # Key: (personId, blockId), Value: templateId
        prev_set: dict[tuple[str, str], str] = {}
        for a in prev.assignments:
            key = (a.get("personId", ""), a.get("blockId", ""))
            prev_set[key] = a.get("templateId", "")

        curr_set: dict[tuple[str, str], str] = {}
        for a in curr.assignments:
            key = (a.get("personId", ""), a.get("blockId", ""))
            curr_set[key] = a.get("templateId", "")

        prev_keys = set(prev_set.keys())
        curr_keys = set(curr_set.keys())

        added = []
        removed = []
        moved = []

        # New assignments (in curr but not prev)
        for key in curr_keys - prev_keys:
            person_id, block_id = key
            template_id = curr_set[key]
            if person_id and block_id:  # Skip if missing IDs
                added.append(
                    {
                        "personId": person_id,
                        "blockId": block_id,
                        "templateId": template_id,
                    }
                )

        # Removed assignments (in prev but not curr)
        for key in prev_keys - curr_keys:
            person_id, block_id = key
            template_id = prev_set[key]
            if person_id and block_id:
                removed.append(
                    {
                        "personId": person_id,
                        "blockId": block_id,
                        "templateId": template_id,
                    }
                )

        # Moved assignments (same person/block, different template)
        for key in prev_keys & curr_keys:
            if prev_set[key] != curr_set[key]:
                person_id, block_id = key
                moved.append(
                    {
                        "personId": person_id,
                        "blockId": block_id,
                        "oldTemplateId": prev_set[key],
                        "newTemplateId": curr_set[key],
                    }
                )

        return SolutionDelta(
            solution_num=curr.solution_num,
            timestamp=curr.timestamp,
            added=added,
            removed=removed,
            moved=moved,
            metrics={
                "added_count": len(added),
                "removed_count": len(removed),
                "moved_count": len(moved),
                "total_changes": len(added) + len(removed) + len(moved),
            },
        )

    def _trigger_broadcast(self, snapshot: SolutionSnapshot) -> None:
        """
        Trigger WebSocket broadcast for new solution.

        This is called synchronously from the OR-Tools callback,
        so it queues the broadcast for async execution.

        Args:
            snapshot: The solution snapshot to broadcast
        """
        if not self.broadcast_callback:
            return

        # Prepare broadcast data with camelCase keys for frontend compatibility
        # (WebSocket messages bypass axios interceptor that converts snake_case)
        if snapshot.solution_num == 1:
            data = {
                "eventType": "solver_solution",
                "taskId": self.task_id,
                "solutionNum": snapshot.solution_num,
                "solutionType": "full",
                "assignments": snapshot.assignments,
                "assignmentCount": len(snapshot.assignments),
                "objectiveValue": snapshot.objective_value,
                "optimalityGapPct": snapshot.optimality_gap_pct,
                "isOptimal": snapshot.is_optimal,
                "elapsedSeconds": snapshot.timestamp,
            }
        else:
            prev = self.solutions[-2]
            delta = self._calculate_delta(prev, snapshot)
            data = {
                "eventType": "solver_solution",
                "taskId": self.task_id,
                "solutionNum": snapshot.solution_num,
                "solutionType": "delta",
                "delta": {
                    "added": delta.added,
                    "removed": delta.removed,
                    "moved": delta.moved,
                },
                "assignmentCount": len(snapshot.assignments),
                "objectiveValue": snapshot.objective_value,
                "optimalityGapPct": snapshot.optimality_gap_pct,
                "isOptimal": snapshot.is_optimal,
                "elapsedSeconds": snapshot.timestamp,
            }

        # Handle async callback - the callback may be an async function
        result = self.broadcast_callback(data)
        if inspect.iscoroutine(result):
            # Schedule async callback without blocking the solver
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(result)
            except RuntimeError:
                # No running event loop - create a new one (sync context)
                # This is a fallback; ideally the caller provides a sync wrapper
                logger.warning(
                    "No event loop available, running broadcast synchronously"
                )
                asyncio.run(result)

    def get_callback(self) -> Any:
        """
        Get the underlying OR-Tools callback object.

        Returns:
            The CpSolverSolutionCallback instance, or None if unavailable
        """
        return self._callback

    def get_solution_count(self) -> int:
        """Get the number of solutions found so far."""
        return len(self.solutions)

    def get_latest_snapshot(self) -> SolutionSnapshot | None:
        """Get the most recent solution snapshot."""
        return self.solutions[-1] if self.solutions else None

    # =========================================================================
    # Class Methods for Solution Retrieval
    # =========================================================================

    @classmethod
    def get_solutions(cls, task_id: str, redis_client: Any) -> list[dict]:
        """
        Retrieve all stored solutions for a task.

        Args:
            task_id: The solver task ID
            redis_client: Redis client instance

        Returns:
            List of solution dicts (full or delta format)
        """
        if not redis_client:
            return []

        try:
            index_key = f"solver_solutions:{task_id}"
            solution_nums = redis_client.lrange(index_key, 0, -1)

            solutions = []
            for num in solution_nums:
                # Handle bytes or string
                if isinstance(num, bytes):
                    num = num.decode("utf-8")

                key = f"solver_solution:{task_id}:{num}"
                data = redis_client.get(key)
                if data:
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    solutions.append(json.loads(data))

            return solutions

        except Exception as e:
            logger.error(f"Failed to retrieve solutions: {e}")
            return []

    @classmethod
    def get_latest_solution(cls, task_id: str, redis_client: Any) -> dict | None:
        """
        Get the most recent solution for a task.

        Args:
            task_id: The solver task ID
            redis_client: Redis client instance

        Returns:
            Latest solution dict, or None if not found
        """
        if not redis_client:
            return None

        try:
            index_key = f"solver_solutions:{task_id}"
            latest_num = redis_client.lindex(index_key, -1)

            if latest_num:
                if isinstance(latest_num, bytes):
                    latest_num = latest_num.decode("utf-8")

                key = f"solver_solution:{task_id}:{latest_num}"
                data = redis_client.get(key)
                if data:
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve latest solution: {e}")
            return None

    @classmethod
    def reconstruct_full_solution(
        cls,
        task_id: str,
        redis_client: Any,
        target_solution_num: int | None = None,
    ) -> list[dict] | None:
        """
        Reconstruct a full solution from stored snapshots/deltas.

        This is useful when you need the complete assignment list
        but only deltas are stored.

        Args:
            task_id: The solver task ID
            redis_client: Redis client instance
            target_solution_num: Solution number to reconstruct (default: latest)

        Returns:
            List of assignment dicts, or None if reconstruction fails
        """
        solutions = cls.get_solutions(task_id, redis_client)
        if not solutions:
            return None

        # Find target
        if target_solution_num is None:
            target_solution_num = solutions[-1]["solution_num"]

        # Start with first solution (must be full)
        first = solutions[0]
        if first["type"] != "full":
            logger.error("First solution is not full snapshot")
            return None

        # Build assignment set
        assignments: dict[tuple[str, str], dict] = {}
        for a in first.get("assignments", []):
            key = (a["personId"], a["blockId"])
            assignments[key] = a

        # Apply deltas up to target
        for sol in solutions[1:]:
            if sol["solution_num"] > target_solution_num:
                break

            if sol["type"] != "delta":
                continue

            delta = sol.get("delta", {})

            # Remove
            for a in delta.get("removed", []):
                key = (a["personId"], a["blockId"])
                assignments.pop(key, None)

            # Move (update template)
            for a in delta.get("moved", []):
                key = (a["personId"], a["blockId"])
                if key in assignments:
                    assignments[key]["templateId"] = a["newTemplateId"]

            # Add
            for a in delta.get("added", []):
                key = (a["personId"], a["blockId"])
                assignments[key] = a

        return list(assignments.values())

    @classmethod
    def clear_solutions(cls, task_id: str, redis_client: Any) -> int:
        """
        Clear all stored solutions for a task.

        Args:
            task_id: The solver task ID
            redis_client: Redis client instance

        Returns:
            Number of keys deleted
        """
        if not redis_client:
            return 0

        try:
            # Get all solution numbers
            index_key = f"solver_solutions:{task_id}"
            solution_nums = redis_client.lrange(index_key, 0, -1)

            deleted = 0

            # Delete each solution
            for num in solution_nums:
                if isinstance(num, bytes):
                    num = num.decode("utf-8")
                key = f"solver_solution:{task_id}:{num}"
                deleted += redis_client.delete(key)

            # Delete index
            deleted += redis_client.delete(index_key)

            logger.info(f"Cleared {deleted} solution keys for task {task_id}")
            return deleted

        except Exception as e:
            logger.error(f"Failed to clear solutions: {e}")
            return 0
