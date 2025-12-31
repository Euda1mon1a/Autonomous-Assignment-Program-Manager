"""Incremental schedule updates for efficient modifications.

Updates schedules incrementally instead of regenerating from scratch.
"""

import logging
from datetime import date, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)


class IncrementalScheduleUpdater:
    """Update schedules incrementally without full regeneration."""

    def __init__(self):
        """Initialize incremental updater."""
        self.update_count = 0
        self.conflict_count = 0

    async def add_person(
        self,
        schedule: dict,
        person: dict,
        date_range: tuple[date, date],
        constraints: dict,
    ) -> dict:
        """Add a new person to existing schedule.

        Args:
            schedule: Current schedule
            person: Person to add
            date_range: Date range to schedule
            constraints: Scheduling constraints

        Returns:
            Updated schedule with new person
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
        """Remove person from schedule.

        Args:
            schedule: Current schedule
            person_id: Person ID to remove
            date_range: Optional date range (None = remove all)

        Returns:
            Updated schedule
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
        """Swap assignments between two persons.

        Args:
            schedule: Current schedule
            person1_id: First person ID
            person2_id: Second person ID
            date1: First date
            date2: Second date
            constraints: Scheduling constraints

        Returns:
            Updated schedule if swap is valid
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
        """Update rotation capacity and rebalance if needed.

        Args:
            schedule: Current schedule
            rotation_id: Rotation ID
            new_capacity: New capacity
            date_range: Date range affected

        Returns:
            Updated schedule
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
        """Find available slots for person.

        Args:
            schedule: Current schedule
            person: Person data
            date_range: Date range
            constraints: Constraints

        Returns:
            List of available slots
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
        """Get available rotations for person on date.

        Args:
            schedule: Current schedule
            person: Person data
            target_date: Target date
            constraints: Constraints

        Returns:
            List of available rotation IDs
        """
        # This would check rotation capacity, person qualifications, etc.
        # For now, return placeholder
        return []

    def _assign_to_slots(
        self,
        person: dict,
        available_slots: list[dict],
        constraints: dict,
    ) -> list[dict]:
        """Assign person to available slots.

        Args:
            person: Person data
            available_slots: Available slots
            constraints: Constraints

        Returns:
            List of new assignments
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
        """Check if swap would violate constraints.

        Args:
            schedule: Current schedule
            assign1: First assignment
            assign2: Second assignment
            constraints: Constraints

        Returns:
            True if would violate constraints
        """
        # Check ACGME rules, rotation requirements, etc.
        # For now, return False (assume valid)
        return False

    async def get_stats(self) -> dict:
        """Get update statistics.

        Returns:
            Statistics dictionary
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
