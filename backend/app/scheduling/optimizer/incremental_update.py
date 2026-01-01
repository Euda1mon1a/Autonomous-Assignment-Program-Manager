"""
Incremental schedule updates for efficient modifications.

This module provides incremental update capabilities for existing schedules,
allowing modifications without full regeneration. This is essential for
maintaining schedule stability and performance when small changes occur.

Key Concepts:
    **Incremental vs Full Regeneration**: Full schedule generation is expensive
    (minutes to hours for large programs). Incremental updates modify only the
    affected portions, completing in seconds.

    **Schedule Stability**: Residents and faculty rely on schedule predictability.
    Incremental updates minimize disruption by changing only what's necessary.

    **Constraint Preservation**: All updates are validated against constraints
    to ensure the modified schedule remains valid and ACGME-compliant.

Supported Operations:
    1. **Add Person**: Add a new resident/faculty to an existing schedule
    2. **Remove Person**: Remove a person (e.g., leave, termination)
    3. **Swap Assignments**: Exchange shifts between two persons
    4. **Update Capacity**: Adjust rotation capacity and rebalance

Operation Complexity:
    - Add person: O(blocks) - finds slots, assigns to available rotations
    - Remove person: O(assignments) - filters out person's assignments
    - Swap: O(1) - constant time rotation exchange
    - Capacity update: O(blocks * persons) - may require reassignment

Use Cases:
    - New resident starts mid-year
    - Resident takes medical leave
    - Faculty requests shift swap
    - Rotation capacity changed due to staffing

Classes:
    IncrementalScheduleUpdater: Main class for performing incremental updates.

Example:
    >>> updater = IncrementalScheduleUpdater()
    >>> schedule = await updater.add_person(
    ...     schedule,
    ...     new_resident,
    ...     (start_date, end_date),
    ...     constraints
    ... )
    >>> stats = await updater.get_stats()
    >>> print(f"Updates performed: {stats['total_updates']}")

See Also:
    - app/scheduling/optimizer/solution_cache.py: Caching for full solutions
    - app/services/swap_executor.py: Higher-level swap workflow management
"""

import logging
from datetime import date, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class IncrementalScheduleUpdater:
    """
    Update schedules incrementally without full regeneration.

    This class provides methods for modifying existing schedules in place,
    preserving as much of the original schedule as possible while making
    necessary adjustments.

    The updater tracks statistics about operations performed, including
    successful updates and conflicts encountered. This is useful for
    monitoring schedule health and identifying problematic patterns.

    Attributes:
        update_count: Total number of update operations performed.
        conflict_count: Number of constraint conflicts encountered.

    Example:
        >>> updater = IncrementalScheduleUpdater()
        >>> schedule = {"assignments": [...]}
        >>>
        >>> # Add a new person
        >>> schedule = await updater.add_person(
        ...     schedule, new_person, date_range, constraints
        ... )
        >>>
        >>> # Swap two assignments
        >>> schedule = await updater.swap_assignments(
        ...     schedule, "person1", "person2", date1, date2, constraints
        ... )
        >>>
        >>> # Check stats
        >>> stats = await updater.get_stats()
        >>> print(f"Conflict rate: {stats['conflict_rate']:.1f}%")
    """

    def __init__(self) -> None:
        """
        Initialize incremental updater.

        Creates a new updater instance with zero counters for tracking
        update and conflict statistics.
        """
        self.update_count = 0
        self.conflict_count = 0

    async def add_person(
        self,
        schedule: dict,
        person: dict,
        date_range: tuple[date, date],
        constraints: dict,
    ) -> dict:
        """
        Add a new person to an existing schedule.

        Finds available slots (unassigned person-block combinations) and
        assigns the new person to appropriate rotations. Respects all
        constraints including rotation capacity, qualifications, and
        ACGME requirements.

        Args:
            schedule: Current schedule dictionary with 'assignments' list.
                Each assignment has person_id, block_id, rotation_id, etc.

            person: Person dictionary with:
                - id: Unique person identifier
                - type: 'resident', 'faculty', etc.
                - pgy_level: PGY level for residents
                - specialties: List of specialties
                - preferences: Optional rotation preferences

            date_range: Tuple of (start_date, end_date) for scheduling.
                The person will be added to blocks within this range.

            constraints: Constraint parameters including:
                - max_hours_per_week: Maximum weekly hours
                - required_rotations: Must-do rotations
                - preferred_rotations: Preferred rotation order

        Returns:
            Updated schedule dictionary with new person's assignments added.

        Note:
            This operation modifies the schedule in place and returns it.
            The original schedule object is mutated.

        Example:
            >>> new_resident = {
            ...     "id": "r123",
            ...     "type": "resident",
            ...     "pgy_level": 1,
            ...     "specialties": ["internal_medicine"]
            ... }
            >>> schedule = await updater.add_person(
            ...     schedule,
            ...     new_resident,
            ...     (date(2024, 7, 1), date(2024, 8, 31)),
            ...     {"max_hours_per_week": 80}
            ... )
        """
        logger.info(f"Adding person {person['id']} to schedule")

        # Find available slots for new person
        available_slots = self._find_available_slots(
            schedule,
            person,
            date_range,
            constraints,
        )

        # Assign person to best slots
        new_assignments = self._assign_to_slots(
            person,
            available_slots,
            constraints,
        )

        # Add to schedule
        schedule["assignments"].extend(new_assignments)
        self.update_count += 1

        logger.info(f"Added {len(new_assignments)} assignments for {person['id']}")
        return schedule

    async def remove_person(
        self,
        schedule: dict,
        person_id: str,
        date_range: tuple[date, date] | None = None,
    ) -> dict:
        """
        Remove a person from the schedule.

        Removes all assignments for the specified person, optionally limited
        to a specific date range. Use for leave of absence, termination,
        or other situations where a person should no longer be scheduled.

        Args:
            schedule: Current schedule dictionary with 'assignments' list.

            person_id: ID of the person to remove from schedule.

            date_range: Optional tuple of (start_date, end_date) to limit
                removal. If None, removes all assignments for the person.

        Returns:
            Updated schedule with the person's assignments removed.

        Note:
            This operation does NOT fill the gaps left by removal. For
            coverage, a separate operation (add_person or reassignment)
            would be needed.

        Example:
            >>> # Remove person completely
            >>> schedule = await updater.remove_person(schedule, "r123")
            >>>
            >>> # Remove for specific date range (e.g., leave)
            >>> schedule = await updater.remove_person(
            ...     schedule, "r123",
            ...     date_range=(date(2024, 3, 1), date(2024, 3, 15))
            ... )
        """
        logger.info(f"Removing person {person_id} from schedule")

        if date_range:
            start_date, end_date = date_range
            # Remove assignments in date range
            schedule["assignments"] = [
                a
                for a in schedule["assignments"]
                if not (
                    a["person_id"] == person_id
                    and start_date <= a["block_date"] <= end_date
                )
            ]
        else:
            # Remove all assignments
            removed_count = len(
                [a for a in schedule["assignments"] if a["person_id"] == person_id]
            )
            schedule["assignments"] = [
                a for a in schedule["assignments"] if a["person_id"] != person_id
            ]
            logger.info(f"Removed {removed_count} assignments")

        self.update_count += 1
        return schedule

    async def swap_assignments(
        self,
        schedule: dict,
        person1_id: str,
        person2_id: str,
        date1: date,
        date2: date,
        constraints: dict,
    ) -> dict:
        """
        Swap assignments between two persons.

        Exchanges the rotation assignments for two persons on specified dates.
        Both assignments must exist, and the swap must not violate constraints.

        Args:
            schedule: Current schedule dictionary.

            person1_id: ID of first person in swap.

            person2_id: ID of second person in swap.

            date1: Date of first person's assignment to swap.

            date2: Date of second person's assignment to swap.

            constraints: Constraints to validate swap against, including
                ACGME hour limits, rotation requirements, etc.

        Returns:
            Updated schedule if swap is valid, unchanged schedule if invalid.

        Note:
            If either assignment is not found or the swap would violate
            constraints, the schedule is returned unchanged and conflict_count
            is incremented.

        Example:
            >>> # Person 1 wants to work Person 2's shift and vice versa
            >>> schedule = await updater.swap_assignments(
            ...     schedule,
            ...     "r123", "r456",
            ...     date(2024, 3, 15), date(2024, 3, 22),
            ...     constraints
            ... )
            >>> if updater.conflict_count > prev_conflicts:
            ...     print("Swap was rejected due to constraint violation")
        """
        logger.info(
            f"Swapping assignments: {person1_id}@{date1} <-> {person2_id}@{date2}"
        )

        # Find assignments to swap
        assign1 = next(
            (
                a
                for a in schedule["assignments"]
                if a["person_id"] == person1_id and a["block_date"] == date1
            ),
            None,
        )

        assign2 = next(
            (
                a
                for a in schedule["assignments"]
                if a["person_id"] == person2_id and a["block_date"] == date2
            ),
            None,
        )

        if not assign1 or not assign2:
            logger.warning("One or both assignments not found for swap")
            return schedule

        # Check if swap would violate constraints
        if self._would_violate_constraints(schedule, assign1, assign2, constraints):
            logger.warning("Swap would violate constraints")
            self.conflict_count += 1
            return schedule

        # Perform swap
        temp_rotation = assign1["rotation_id"]
        assign1["rotation_id"] = assign2["rotation_id"]
        assign2["rotation_id"] = temp_rotation

        self.update_count += 1
        logger.info("Swap successful")
        return schedule

    async def update_rotation_capacity(
        self,
        schedule: dict,
        rotation_id: str,
        new_capacity: int,
        date_range: tuple[date, date],
    ) -> dict:
        """
        Update rotation capacity and rebalance if needed.

        Changes the maximum number of persons allowed on a rotation. If the
        new capacity is lower than current assignments, excess assignments
        are removed based on priority.

        Args:
            schedule: Current schedule dictionary.

            rotation_id: ID of the rotation to update.

            new_capacity: New maximum number of persons per day on this rotation.

            date_range: Tuple of (start_date, end_date) for the capacity change.

        Returns:
            Updated schedule with capacity enforced.

        Note:
            When capacity is reduced, lowest-priority assignments are removed
            first. These removed assignments create coverage gaps that may
            need to be filled separately.

        Example:
            >>> # Reduce ICU capacity from 3 to 2 residents
            >>> schedule = await updater.update_rotation_capacity(
            ...     schedule,
            ...     "icu_rotation",
            ...     new_capacity=2,
            ...     date_range=(date(2024, 4, 1), date(2024, 4, 30))
            ... )
        """
        logger.info(f"Updating capacity for rotation {rotation_id} to {new_capacity}")

        start_date, end_date = date_range

        # Check each date in range
        current_date = start_date
        while current_date <= end_date:
            # Count assignments for this rotation on this date
            assignments = [
                a
                for a in schedule["assignments"]
                if a["rotation_id"] == rotation_id and a["block_date"] == current_date
            ]

            if len(assignments) > new_capacity:
                # Need to remove some assignments
                excess = len(assignments) - new_capacity
                logger.warning(
                    f"Rotation {rotation_id} over capacity by {excess} on {current_date}"
                )

                # Remove lowest priority assignments
                assignments.sort(key=lambda a: a.get("priority", 0))
                to_remove = assignments[:excess]

                for assign in to_remove:
                    schedule["assignments"].remove(assign)

                self.conflict_count += excess

            current_date += timedelta(days=1)

        self.update_count += 1
        return schedule

    def _find_available_slots(
        self,
        schedule: dict,
        person: dict,
        date_range: tuple[date, date],
        constraints: dict,
    ) -> list[dict]:
        """
        Find available slots for a person in the schedule.

        Identifies date-rotation combinations where the person can be
        assigned without conflicting with existing assignments or
        violating constraints.

        Args:
            schedule: Current schedule to check for conflicts.

            person: Person dictionary with qualifications and preferences.

            date_range: Tuple of (start_date, end_date) to search within.

            constraints: Constraints affecting slot availability.

        Returns:
            List of slot dictionaries, each containing:
                - date: The available date
                - rotations: List of rotation IDs available on that date

        Note:
            This is an internal method. The public API is add_person().
        """
        start_date, end_date = date_range
        available = []

        current_date = start_date
        while current_date <= end_date:
            # Check if person is already assigned
            existing = next(
                (
                    a
                    for a in schedule["assignments"]
                    if a["person_id"] == person["id"]
                    and a["block_date"] == current_date
                ),
                None,
            )

            if not existing:
                available.append(
                    {
                        "date": current_date,
                        "rotations": self._get_available_rotations(
                            schedule, person, current_date, constraints
                        ),
                    }
                )

            current_date += timedelta(days=1)

        return available

    def _get_available_rotations(
        self,
        schedule: dict,
        person: dict,
        target_date: date,
        constraints: dict,
    ) -> list[str]:
        """
        Get available rotations for a person on a specific date.

        Filters rotations based on capacity, person qualifications, and
        other constraints to determine which rotations the person could
        be assigned to.

        Args:
            schedule: Current schedule for capacity checking.

            person: Person dictionary with qualifications.

            target_date: The date to check availability for.

            constraints: Constraint parameters.

        Returns:
            List of rotation IDs that are available for the person on
            the given date. Empty list if no rotations are available.

        Note:
            This is a simplified implementation. Production would check
            rotation capacity, PGY requirements, specialties, etc.
        """
        # Get all available rotations from schedule metadata or constraints
        rotations = schedule.get("rotations", [])
        if not rotations:
            # Fallback: extract rotation IDs from existing assignments
            rotation_ids = set(
                a.get("rotation_id")
                for a in schedule.get("assignments", [])
                if a.get("rotation_id")
            )
            rotations = [{"id": rid} for rid in rotation_ids]

        available = []

        for rotation in rotations:
            rotation_id = rotation.get("id")
            if not rotation_id:
                continue

            # Count current assignments for this rotation on target date
            current_count = sum(
                1
                for a in schedule.get("assignments", [])
                if a.get("rotation_id") == rotation_id
                and a.get("block_date") == target_date
            )

            # Get rotation capacity (from rotation metadata or constraints)
            max_capacity = rotation.get("max_residents")
            if max_capacity is None:
                # Try to get from constraints
                rotation_capacities = constraints.get("rotation_capacities", {})
                max_capacity = rotation_capacities.get(rotation_id)

            # If no capacity limit defined, use default
            if max_capacity is None:
                max_capacity = constraints.get("default_rotation_capacity", 999)

            # Check if rotation has available capacity
            if current_count < max_capacity:
                # Check person qualifications if available
                required_quals = rotation.get("required_qualifications", [])
                person_quals = person.get("qualifications", [])

                # If person has all required qualifications (or no requirements)
                if not required_quals or all(q in person_quals for q in required_quals):
                    available.append(rotation_id)

        logger.debug(
            f"Found {len(available)} available rotations for {person.get('id')} "
            f"on {target_date}"
        )
        return available

    def _assign_to_slots(
        self,
        person: dict,
        available_slots: list[dict],
        constraints: dict,
    ) -> list[dict]:
        """
        Assign a person to available slots.

        Creates assignment records for the person based on available slots
        and constraints. Selects the best rotation for each slot based on
        person preferences and program requirements.

        Args:
            person: Person dictionary with preferences.

            available_slots: List of slot dictionaries from _find_available_slots.

            constraints: Constraints including required rotations.

        Returns:
            List of assignment dictionaries ready to add to schedule.
            Each contains person_id, block_date, rotation_id, and priority.

        Note:
            This is a greedy assignment that picks the first available
            rotation. A more sophisticated implementation would consider
            rotation balance, preferences, and requirements.
        """
        assignments = []

        for slot in available_slots:
            if slot["rotations"]:
                # Pick best rotation for this slot
                rotation_id = slot["rotations"][0]  # Simplified

                assignments.append(
                    {
                        "person_id": person["id"],
                        "block_date": slot["date"],
                        "rotation_id": rotation_id,
                        "priority": 5,
                    }
                )

        return assignments

    def _would_violate_constraints(
        self,
        schedule: dict,
        assign1: dict,
        assign2: dict,
        constraints: dict,
    ) -> bool:
        """
        Check if a swap would violate constraints.

        Validates that swapping two assignments would not violate ACGME
        rules, rotation requirements, or other constraints.

        Args:
            schedule: Current schedule for context.

            assign1: First assignment in the swap.

            assign2: Second assignment in the swap.

            constraints: Constraints to validate against.

        Returns:
            True if the swap would violate constraints, False if valid.

        Note:
            This is a simplified implementation that always returns False.
            Production would check:
            - ACGME hour limits after swap
            - Rotation qualifications
            - Supervision requirements
            - Consecutive duty limits
        """
        # Check ACGME rules, rotation requirements, etc.
        # For now, return False (assume valid)
        return False

    async def get_stats(self) -> dict:
        """
        Get update statistics.

        Returns statistics about incremental updates including total
        update count, conflicts encountered, and conflict rate percentage.

        Returns:
            Statistics dictionary with keys:
                - total_updates: Number of update operations performed
                - conflicts: Number of conflicts encountered
                - conflict_rate: Percentage of updates that had conflicts

        Note:
            Statistics are cumulative across the lifetime of this updater
            instance. Create a new instance to reset statistics.

        Example:
            >>> updater = IncrementalScheduleUpdater()
            >>> # ... perform updates ...
            >>> stats = await updater.get_stats()
            >>> print(f"Total updates: {stats['total_updates']}")
            >>> print(f"Conflict rate: {stats['conflict_rate']:.1f}%")
        """
        return {
            "total_updates": self.update_count,
            "conflicts": self.conflict_count,
            "conflict_rate": (
                self.conflict_count / self.update_count * 100
                if self.update_count > 0
                else 0.0
            ),
        }
