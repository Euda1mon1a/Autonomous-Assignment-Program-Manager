"""Early constraint pruning for schedule generation optimization.

Prunes infeasible assignments early to reduce solver search space.
"""

import logging
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ConstraintPruner:
    """Prune infeasible assignments before solver runs."""

    def __init__(self) -> None:
        """
        Initialize constraint pruner.

        Creates a new pruner instance with zero counters for tracking
        pruning statistics across prune_assignments calls.
        """
        self.pruned_count = 0
        self.total_evaluated = 0

    def prune_assignments(
        self,
        persons: list[dict],
        rotations: list[dict],
        blocks: list[dict],
        existing_assignments: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Prune infeasible person-rotation-block combinations.

        Args:
            persons: List of person data
            rotations: List of rotation data
            blocks: List of block data
            existing_assignments: Optional existing assignments

        Returns:
            Dictionary with feasible assignments and pruning stats
        """
        self.pruned_count = 0
        self.total_evaluated = 0

        feasible_assignments = []
        pruning_reasons = {}

        # Build lookup tables
        person_by_id = {p["id"]: p for p in persons}
        rotation_by_id = {r["id"]: r for r in rotations}
        block_by_id = {b["id"]: b for b in blocks}

        # Build existing assignment index
        existing_by_person_block = {}
        if existing_assignments:
            for assign in existing_assignments:
                key = (assign["person_id"], assign["block_id"])
                existing_by_person_block[key] = assign

        # Evaluate all combinations
        for person in persons:
            for block in blocks:
                self.total_evaluated += 1

                # Check if already assigned
                if (person["id"], block["id"]) in existing_by_person_block:
                    continue

                # Get feasible rotations for this person-block
                feasible_rotations = self._get_feasible_rotations(
                    person,
                    block,
                    rotations,
                    pruning_reasons,
                )

                for rotation in feasible_rotations:
                    feasible_assignments.append(
                        {
                            "person_id": person["id"],
                            "block_id": block["id"],
                            "rotation_id": rotation["id"],
                        }
                    )

        logger.info(
            f"Constraint pruning: {self.pruned_count}/{self.total_evaluated} "
            f"combinations pruned ({self.pruned_count / self.total_evaluated * 100:.1f}%)"
        )

        return {
            "feasible_assignments": feasible_assignments,
            "total_evaluated": self.total_evaluated,
            "pruned_count": self.pruned_count,
            "pruning_reasons": pruning_reasons,
            "reduction_ratio": self.pruned_count / self.total_evaluated
            if self.total_evaluated > 0
            else 0,
        }

    def _get_feasible_rotations(
        self,
        person: dict,
        block: dict,
        rotations: list[dict],
        pruning_reasons: dict,
    ) -> list[dict]:
        """Get feasible rotations for person-block combination.

        Args:
            person: Person data
            block: Block data
            rotations: List of rotations
            pruning_reasons: Dictionary to track pruning reasons

        Returns:
            List of feasible rotations
        """
        feasible = []

        for rotation in rotations:
            reason = self._check_feasibility(person, rotation, block)

            if reason is None:
                feasible.append(rotation)
            else:
                self.pruned_count += 1
                pruning_reasons[reason] = pruning_reasons.get(reason, 0) + 1

        return feasible

    def _check_feasibility(
        self,
        person: dict,
        rotation: dict,
        block: dict,
    ) -> str | None:
        """Check if person-rotation-block is feasible.

        Args:
            person: Person data
            rotation: Rotation data
            block: Block data

        Returns:
            Reason for infeasibility, or None if feasible
        """
        # Check person type restrictions
        if "allowed_person_types" in rotation:
            if person.get("type") not in rotation["allowed_person_types"]:
                return "person_type_mismatch"

        # Check PGY level restrictions
        if "min_pgy_level" in rotation:
            if person.get("pgy_level", 0) < rotation["min_pgy_level"]:
                return "pgy_level_too_low"

        if "max_pgy_level" in rotation:
            if person.get("pgy_level", 999) > rotation["max_pgy_level"]:
                return "pgy_level_too_high"

        # Check specialty restrictions
        if "required_specialties" in rotation:
            person_specialties = person.get("specialties", [])
            required = rotation["required_specialties"]

            if not any(spec in person_specialties for spec in required):
                return "specialty_mismatch"

        # Check availability (e.g., leave, deployments)
        if person.get("unavailable_dates"):
            block_date = block.get("date")
            if block_date in person["unavailable_dates"]:
                return "person_unavailable"

        # Check rotation capacity
        if rotation.get("max_people"):
            # This would need to check current assignments
            # For now, we just mark it as potentially feasible
            pass

        # Check time-based restrictions
        if rotation.get("time_of_day"):
            block_is_am = block.get("is_am", True)
            if rotation["time_of_day"] == "AM" and not block_is_am:
                return "time_of_day_mismatch"
            if rotation["time_of_day"] == "PM" and block_is_am:
                return "time_of_day_mismatch"

        return None

    def estimate_search_space_reduction(
        self,
        pruning_result: dict,
    ) -> dict:
        """
        Estimate search space reduction from pruning.

        Calculates how much the solver search space was reduced by
        constraint pruning. Uses exponential estimation based on the
        assumption that pruning reduces combinatorial explosion.

        Args:
            pruning_result: Result dictionary from prune_assignments

        Returns:
            Dictionary with reduction statistics including:
                - total_combinations: Total assignments evaluated
                - pruned_combinations: Number pruned as infeasible
                - remaining_combinations: Number still feasible
                - reduction_ratio: Fraction pruned (0.0-1.0)
                - estimated_search_space_reduction_factor: Exponential reduction
                - estimated_solver_speedup: Expected solver speedup multiplier
        """
        total = pruning_result["total_evaluated"]
        pruned = pruning_result["pruned_count"]
        remaining = total - pruned

        # Estimate exponential search space reduction
        # If we prune 50% of assignments, we reduce search space by 2^n
        reduction_factor = 2 ** (pruned / total) if total > 0 else 1

        return {
            "total_combinations": total,
            "pruned_combinations": pruned,
            "remaining_combinations": remaining,
            "reduction_ratio": pruned / total if total > 0 else 0,
            "estimated_search_space_reduction_factor": reduction_factor,
            "estimated_solver_speedup": reduction_factor,
        }


def prune_infeasible_assignments(
    persons: list[dict],
    rotations: list[dict],
    blocks: list[dict],
) -> dict:
    """
    Utility function to prune infeasible assignments.

    Convenience wrapper that creates a ConstraintPruner instance
    and runs pruning on the provided scheduling data.

    Args:
        persons: List of person dictionaries
        rotations: List of rotation dictionaries
        blocks: List of block dictionaries

    Returns:
        Pruning result dictionary with feasible assignments and statistics

    Example:
        >>> result = prune_infeasible_assignments(persons, rotations, blocks)
        >>> print(f"Pruned {result['pruned_count']} infeasible assignments")
        >>> feasible = result['feasible_assignments']
    """
    pruner = ConstraintPruner()
    return pruner.prune_assignments(persons, rotations, blocks)
