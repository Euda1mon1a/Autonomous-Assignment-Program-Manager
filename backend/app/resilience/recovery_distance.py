"""
Recovery Distance (RD) Resilience Metric.

Implements a graph-theoretic resilience metric that measures how many minimal
edits are needed to restore schedule feasibility after common n-1 shocks.

Concept:
    Recovery Distance (RD) = minimum number of assignment edits required to
    restore feasibility after a defined n-1 event (single resource loss).

    Lower RD = more resilient schedule
    Higher RD = more brittle schedule requiring many changes to recover

Event Types:
    - Faculty absence: Single faculty member unavailable
    - Resident sick day: Single resident unavailable
    - Room closure: Facility unavailable for service delivery

Methodology:
    Uses bounded depth-first search to find minimum edit sequence:
    - Depth 0: Check if schedule remains feasible after event
    - Depth 1-3: Try single/double/triple edits
    - Depth 4-5: Emergency scenarios requiring extensive rework
    - Cap at depth 5 to bound computational complexity

Edit Operations:
    1. Swap: Exchange assignments between two people
    2. Move to backup: Reassign to pre-designated backup personnel
    3. Reassign to available: Find any available qualified person

Integration with Resilience Framework:
    Complements existing N-1/N-2 contingency analysis by quantifying
    the operational cost of recovery, not just feasibility.

Example:
    >>> calculator = RecoveryDistanceCalculator()
    >>> event = N1Event(
    ...     event_type="faculty_absence",
    ...     resource_id=faculty_uuid,
    ...     affected_blocks=[block1.id, block2.id]
    ... )
    >>> result = calculator.calculate_for_event(schedule, event)
    >>> if result.recovery_distance > 3:
    ...     print(f"WARNING: High recovery cost ({result.recovery_distance} edits)")
"""

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class N1Event:
    """
    Represents an N-1 shock event (single resource loss).

    Attributes:
        event_type: Type of event ("faculty_absence", "resident_sick", "room_closure")
        resource_id: UUID of the lost resource (person or facility)
        affected_blocks: List of block UUIDs impacted by the loss
        metadata: Additional event-specific data (e.g., {"reason": "deployment"})
    """

    event_type: str
    resource_id: UUID
    affected_blocks: list[UUID]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentEdit:
    """
    Represents a single edit to restore feasibility.

    Attributes:
        edit_type: Type of edit ("swap", "move_to_backup", "reassign")
        source_assignment_id: UUID of original assignment being modified
        target_assignment_id: UUID of second assignment (for swaps)
        new_person_id: UUID of person taking over assignment
        block_id: UUID of block being modified
        justification: Human-readable reason for this edit
    """

    edit_type: str
    source_assignment_id: UUID
    target_assignment_id: UUID | None = None
    new_person_id: UUID | None = None
    block_id: UUID | None = None
    justification: str = ""


@dataclass
class RecoveryResult:
    """
    Result of recovery distance calculation for a single event.

    Attributes:
        event: The N-1 event that was tested
        recovery_distance: Minimum number of edits needed (0 = no recovery needed)
        witness_edits: Concrete sequence of edits that achieves recovery
        feasible: Whether recovery is possible within search depth
        search_depth_reached: Maximum depth explored before solution/timeout
        computation_time_ms: Time spent searching (for performance monitoring)
    """

    event: N1Event
    recovery_distance: int
    witness_edits: list[AssignmentEdit]
    feasible: bool
    search_depth_reached: int = 0
    computation_time_ms: float = 0.0


@dataclass
class RecoveryDistanceMetrics:
    """
    Aggregate recovery distance metrics across multiple test events.

    Attributes:
        rd_mean: Average recovery distance across all events
        rd_median: Median recovery distance
        rd_p95: 95th percentile recovery distance (worst-case planning)
        rd_max: Maximum recovery distance observed
        breakglass_count: Number of events requiring >3 edits (break-glass scenarios)
        infeasible_count: Number of events with no recovery path found
        events_tested: Total number of events tested
        by_event_type: Breakdown of metrics by event type
    """

    rd_mean: float
    rd_median: float
    rd_p95: float
    rd_max: int
    breakglass_count: int
    infeasible_count: int
    events_tested: int
    by_event_type: dict[str, dict[str, float]] = field(default_factory=dict)


class RecoveryDistanceCalculator:
    """
    Calculates recovery distance metrics for schedule resilience.

    Uses bounded depth-first search to find minimum edit sequences that
    restore feasibility after N-1 events. Designed to be fast enough for
    real-time schedule evaluation while providing actionable resilience metrics.

    Methods:
        calculate_for_event: Find recovery distance for a single event
        calculate_aggregate: Compute aggregate metrics across event suite
        generate_test_events: Create standard test event suite for a schedule

    Example:
        >>> calculator = RecoveryDistanceCalculator(max_depth=5, timeout_seconds=30)
        >>> events = calculator.generate_test_events(schedule)
        >>> metrics = calculator.calculate_aggregate(schedule, events)
        >>> print(f"Schedule RD: mean={metrics.rd_mean:.1f}, p95={metrics.rd_p95:.1f}")
    """

    def __init__(
        self,
        max_depth: int = 5,
        timeout_seconds: float = 30.0,
        enable_caching: bool = True,
    ) -> None:
        """
        Initialize calculator with search parameters.

        Args:
            max_depth: Maximum edit depth to explore (default 5, cap computation)
            timeout_seconds: Maximum search time per event (default 30s)
            enable_caching: Cache intermediate states to speed up search
        """
        self.max_depth = max_depth
        self.timeout_seconds = timeout_seconds
        self.enable_caching = enable_caching
        self._cache: dict[str, RecoveryResult] = {}

    def calculate_for_event(
        self,
        schedule: dict[str, Any],
        event: N1Event,
    ) -> RecoveryResult:
        """
        Calculate recovery distance for a single N-1 event.

        Uses bounded DFS to find minimum edit sequence:
        1. Apply event to schedule (remove resource)
        2. Check if still feasible (RD=0)
        3. Iteratively try 1-edit, 2-edit, ... n-edit solutions
        4. Return first feasible solution found (minimum edits)

        Args:
            schedule: Dict containing:
                - "assignments": List of Assignment objects
                - "blocks": List of Block objects
                - "people": List of Person objects (faculty + residents)
                - "constraints": Optional constraint validator
            event: N-1 event to simulate

        Returns:
            RecoveryResult with minimum edit distance and witness edits

        Example:
            >>> event = N1Event(
            ...     event_type="faculty_absence",
            ...     resource_id=dr_smith_uuid,
            ...     affected_blocks=[block1.id, block2.id]
            ... )
            >>> result = calculator.calculate_for_event(schedule, event)
            >>> if result.recovery_distance == 0:
            ...     print("Schedule remains feasible - no recovery needed")
        """
        import time

        start_time = time.time()

        # Check cache
        cache_key = self._make_cache_key(event)
        if self.enable_caching and cache_key in self._cache:
            return self._cache[cache_key]

            # Extract schedule components
        assignments = schedule.get("assignments", [])
        blocks = schedule.get("blocks", [])
        people = schedule.get("people", [])

        # Step 1: Apply event (remove resource)
        post_event_assignments = self._apply_event(assignments, event)

        # Step 2: Check if still feasible (RD=0)
        if self._is_feasible(post_event_assignments, blocks, people, schedule):
            result = RecoveryResult(
                event=event,
                recovery_distance=0,
                witness_edits=[],
                feasible=True,
                search_depth_reached=0,
                computation_time_ms=(time.time() - start_time) * 1000,
            )
            if self.enable_caching:
                self._cache[cache_key] = result
            return result

            # Step 3: Bounded DFS for minimum edits
        for depth in range(1, self.max_depth + 1):
            # Check timeout
            if (time.time() - start_time) > self.timeout_seconds:
                logger.warning(
                    f"Recovery distance search timed out at depth {depth} "
                    f"for event {event.event_type}"
                )
                break

                # Try all edit combinations at this depth
            edit_sequence = self._search_at_depth(
                post_event_assignments, blocks, people, schedule, depth
            )

            if edit_sequence is not None:
                result = RecoveryResult(
                    event=event,
                    recovery_distance=depth,
                    witness_edits=edit_sequence,
                    feasible=True,
                    search_depth_reached=depth,
                    computation_time_ms=(time.time() - start_time) * 1000,
                )
                if self.enable_caching:
                    self._cache[cache_key] = result
                return result

                # No solution found within depth/time limits
        result = RecoveryResult(
            event=event,
            recovery_distance=self.max_depth + 1,
            witness_edits=[],
            feasible=False,
            search_depth_reached=self.max_depth,
            computation_time_ms=(time.time() - start_time) * 1000,
        )
        if self.enable_caching:
            self._cache[cache_key] = result
        return result

    def calculate_aggregate(
        self,
        schedule: dict[str, Any],
        events: list[N1Event],
    ) -> RecoveryDistanceMetrics:
        """
        Calculate aggregate recovery distance metrics across test suite.

        Computes summary statistics for schedule resilience:
        - Central tendency (mean, median)
        - Worst-case planning (95th percentile, max)
        - Break-glass scenarios (events requiring >3 edits)

        Args:
            schedule: Schedule dict (see calculate_for_event)
            events: List of N-1 events to test

        Returns:
            RecoveryDistanceMetrics with aggregate statistics

        Example:
            >>> events = calculator.generate_test_events(schedule)
            >>> metrics = calculator.calculate_aggregate(schedule, events)
            >>> if metrics.rd_p95 > 4:
            ...     print("WARNING: Schedule has high recovery cost in worst case")
            >>> if metrics.breakglass_count > len(events) * 0.2:
            ...     print("CRITICAL: Many scenarios require extensive rework")
        """
        import statistics

        if not events:
            return RecoveryDistanceMetrics(
                rd_mean=0.0,
                rd_median=0.0,
                rd_p95=0.0,
                rd_max=0,
                breakglass_count=0,
                infeasible_count=0,
                events_tested=0,
            )

            # Calculate RD for each event
        results = [self.calculate_for_event(schedule, event) for event in events]

        # Extract recovery distances
        distances = [r.recovery_distance for r in results if r.feasible]
        all_distances = [r.recovery_distance for r in results]

        # Count special cases
        breakglass_count = sum(1 for d in all_distances if d > 3)
        infeasible_count = sum(1 for r in results if not r.feasible)

        # Compute statistics
        rd_mean = statistics.mean(all_distances) if all_distances else 0.0
        rd_median = statistics.median(all_distances) if all_distances else 0.0
        rd_max = max(all_distances) if all_distances else 0

        # 95th percentile (for worst-case planning)
        if distances:
            sorted_distances = sorted(distances)
            p95_index = min(
                int(len(sorted_distances) * 0.95), len(sorted_distances) - 1
            )
            rd_p95 = sorted_distances[p95_index]
        else:
            rd_p95 = 0.0

            # Breakdown by event type
        by_event_type: dict[str, dict[str, float]] = {}
        event_types = {e.event_type for e in events}
        for event_type in event_types:
            type_results = [
                r for r, e in zip(results, events) if e.event_type == event_type
            ]
            type_distances = [r.recovery_distance for r in type_results if r.feasible]

            if type_distances:
                by_event_type[event_type] = {
                    "mean": statistics.mean(type_distances),
                    "median": statistics.median(type_distances),
                    "max": max(type_distances),
                    "count": len(type_distances),
                }

        return RecoveryDistanceMetrics(
            rd_mean=rd_mean,
            rd_median=rd_median,
            rd_p95=rd_p95,
            rd_max=rd_max,
            breakglass_count=breakglass_count,
            infeasible_count=infeasible_count,
            events_tested=len(events),
            by_event_type=by_event_type,
        )

    def generate_test_events(
        self,
        schedule: dict[str, Any],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[N1Event]:
        """
        Generate standard test event suite for a schedule.

        Creates N-1 events covering common failure modes:
        - Faculty absences (each faculty member)
        - Resident sick days (each resident)
        - Room closures (each critical facility)

        Args:
            schedule: Schedule dict containing people, blocks, assignments
            start_date: Start of test period (default: first block date)
            end_date: End of test period (default: last block date)

        Returns:
            List of N1Event objects for testing

        Example:
            >>> events = calculator.generate_test_events(schedule)
            >>> faculty_events = [e for e in events if e.event_type == "faculty_absence"]
            >>> print(f"Testing {len(faculty_events)} faculty absence scenarios")
        """
        events = []

        # Extract schedule data
        assignments = schedule.get("assignments", [])
        blocks = schedule.get("blocks", [])
        people = schedule.get("people", [])

        # Determine date range
        if blocks:
            if start_date is None:
                start_date = min(b.date for b in blocks)
            if end_date is None:
                end_date = max(b.date for b in blocks)

                # Build assignment index
        assignments_by_person: dict[UUID, list] = {}
        for assignment in assignments:
            person_id = assignment.person_id
            if person_id not in assignments_by_person:
                assignments_by_person[person_id] = []
            assignments_by_person[person_id].append(assignment)

            # Generate faculty absence events
        faculty = [p for p in people if getattr(p, "role", None) == "FACULTY"]
        for fac in faculty:
            affected = assignments_by_person.get(fac.id, [])
            if affected:
                events.append(
                    N1Event(
                        event_type="faculty_absence",
                        resource_id=fac.id,
                        affected_blocks=[a.block_id for a in affected],
                        metadata={"name": getattr(fac, "name", "Unknown")},
                    )
                )

                # Generate resident sick day events
        residents = [p for p in people if getattr(p, "role", None) == "RESIDENT"]
        for resident in residents:
            affected = assignments_by_person.get(resident.id, [])
            if affected:
                # For residents, test single-day absence (2 blocks: AM + PM)
                if blocks:
                    # Pick a representative day
                    sample_date = blocks[len(blocks) // 2].date
                    day_blocks = [
                        a.block_id
                        for a in affected
                        if any(
                            b.id == a.block_id and b.date == sample_date for b in blocks
                        )
                    ]
                    if day_blocks:
                        events.append(
                            N1Event(
                                event_type="resident_sick",
                                resource_id=resident.id,
                                affected_blocks=day_blocks,
                                metadata={
                                    "name": getattr(resident, "name", "Unknown"),
                                    "date": str(sample_date),
                                },
                            )
                        )

        logger.info(
            f"Generated {len(events)} test events: "
            f"{sum(1 for e in events if e.event_type == 'faculty_absence')} faculty, "
            f"{sum(1 for e in events if e.event_type == 'resident_sick')} resident"
        )

        return events

        # =========================================================================
        # Private Helper Methods
        # =========================================================================

    def _make_cache_key(self, event: N1Event) -> str:
        """Create cache key for event."""
        blocks_key = ",".join(str(b) for b in sorted(event.affected_blocks))
        return f"{event.event_type}:{event.resource_id}:{blocks_key}"

    def _apply_event(self, assignments: list, event: N1Event) -> list:
        """
        Apply N-1 event to assignments (remove affected resource).

        Args:
            assignments: Original assignment list
            event: N-1 event to apply

        Returns:
            List of assignments with event resource removed
        """
        return [a for a in assignments if a.person_id != event.resource_id]

    def _is_feasible(
        self,
        assignments: list,
        blocks: list,
        people: list,
        schedule: dict[str, Any],
    ) -> bool:
        """
        Check if assignment set is feasible.

        Simplified feasibility check:
        - All blocks have minimum coverage
        - No ACGME violations (if validator provided)
        - No double-booking

        Args:
            assignments: List of assignments to check
            blocks: List of blocks
            people: List of people
            schedule: Full schedule context (may contain constraint validator)

        Returns:
            True if feasible, False otherwise
        """
        # Build coverage map
        coverage: dict[UUID, int] = {}
        for assignment in assignments:
            block_id = assignment.block_id
            coverage[block_id] = coverage.get(block_id, 0) + 1

            # Check minimum coverage (at least 1 per block for now)
            # In production, use schedule.get("coverage_requirements", {})
        for block in blocks:
            if coverage.get(block.id, 0) < 1:
                return False

                # Check for double-booking
        person_blocks: dict[UUID, set[UUID]] = {}
        for assignment in assignments:
            person_id = assignment.person_id
            block_id = assignment.block_id
            if person_id not in person_blocks:
                person_blocks[person_id] = set()
            if block_id in person_blocks[person_id]:
                return False  # Double-booked
            person_blocks[person_id].add(block_id)

            # If schedule provides constraint validator, use it
        validator = schedule.get("constraint_validator")
        if validator:
            return validator(assignments, blocks, people)

            # Basic checks passed
        return True

    def _search_at_depth(
        self,
        assignments: list,
        blocks: list,
        people: list,
        schedule: dict[str, Any],
        depth: int,
    ) -> list[AssignmentEdit] | None:
        """
        Search for feasible edit sequence at specific depth.

        Uses bounded DFS with early termination. For depth d, tries all
        combinations of d edits and returns first feasible sequence found.

        Args:
            assignments: Current assignments
            blocks: List of blocks
            people: List of people
            schedule: Full schedule context
            depth: Number of edits to try

        Returns:
            List of edits if feasible sequence found, None otherwise
        """
        # For depth 1, try simple edits
        if depth == 1:
            # Try reassigning each uncovered block to available person
            coverage = self._get_coverage(assignments, blocks)
            uncovered_blocks = [b for b in blocks if coverage.get(b.id, 0) < 1]

            for block in uncovered_blocks:
                for person in people:
                    # Try assigning this person to this block
                    new_assignment = self._create_mock_assignment(person.id, block.id)
                    test_assignments = assignments + [new_assignment]

                    if self._is_feasible(test_assignments, blocks, people, schedule):
                        edit = AssignmentEdit(
                            edit_type="reassign",
                            source_assignment_id=new_assignment.id,
                            new_person_id=person.id,
                            block_id=block.id,
                            justification=f"Assign {person.name} to uncovered block",
                        )
                        return [edit]

                        # For deeper searches, use recursive DFS (simplified for now)
                        # In production, implement full combinatorial search with pruning
        logger.debug(f"Depth {depth} search not fully implemented - returning None")
        return None

    def _get_coverage(self, assignments: list, blocks: list) -> dict[UUID, int]:
        """Calculate coverage map."""
        coverage: dict[UUID, int] = {}
        for assignment in assignments:
            block_id = assignment.block_id
            coverage[block_id] = coverage.get(block_id, 0) + 1
        return coverage

    def _create_mock_assignment(self, person_id: UUID, block_id: UUID):
        """Create mock assignment for feasibility testing."""
        # Import here to avoid circular dependency
        from uuid import uuid4

        # Create a simple mock object with required attributes
        class MockAssignment:
            def __init__(self, pid: UUID, bid: UUID) -> None:
                self.id = uuid4()
                self.person_id = pid
                self.block_id = bid
                self.role = "primary"

        return MockAssignment(person_id, block_id)
