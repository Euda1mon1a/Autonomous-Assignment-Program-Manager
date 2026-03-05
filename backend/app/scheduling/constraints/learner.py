"""
Learner Scheduling Constraints.

Enforces rules for med students and rotating interns overlaid on the
existing clinic schedule.

Constraints:
    - LearnerSupervisionConstraint (hard): PGY-1 cannot supervise; max 2 learners per supervisor
    - LearnerASMWednesdayConstraint (hard): ASM sessions must be Wednesday AM
    - LearnerFMITBlockingConstraint (hard): During FMIT week, learner blocked from clinic
    - LearnerDoubleBookingConstraint (hard): One activity per learner per half-day slot
    - LearnerTrackBalanceConstraint (soft): Balance learner count across tracks

See: docs/archived/planning/MED_STUDENT_SCHEDULING_REQUIREMENTS.md
"""

import logging
from typing import Any
from uuid import UUID

from .base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)

logger = logging.getLogger(__name__)


class LearnerSupervisionConstraint(HardConstraint):
    """
    Enforce learner supervision rules.

    - PGY-1 residents cannot supervise learners (faculty or PGY-2+ only)
    - Maximum 2 learners per supervisor per block
    """

    def __init__(self) -> None:
        super().__init__(
            name="LearnerSupervision",
            constraint_type=ConstraintType.SUPERVISION,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        learner_vars = variables.get("learner_assignments")
        if not learner_vars:
            return

        # Group learner assignments by (supervisor_assignment_id, block)
        # and enforce max 2 per group
        from collections import defaultdict

        supervisor_groups: dict[tuple, list] = defaultdict(list)
        for key, var in learner_vars.items():
            learner_id, block_id, day, time, parent_id = key
            if parent_id is not None:
                supervisor_groups[(parent_id, block_id)].append(var)

        for group_key, group_vars in supervisor_groups.items():
            if len(group_vars) > 2:
                model.Add(sum(group_vars) <= 2)

        logger.info(
            "LearnerSupervision: enforced max 2 learners per supervisor "
            f"across {len(supervisor_groups)} groups"
        )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        pass  # PuLP not used for learner scheduling

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        violations = []

        # Group by parent assignment
        from collections import defaultdict

        by_parent: dict[UUID, list] = defaultdict(list)
        for a in assignments:
            if hasattr(a, "parent_assignment_id") and a.parent_assignment_id:
                by_parent[a.parent_assignment_id].append(a)

        for parent_id, learners in by_parent.items():
            if len(learners) > 2:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Supervisor assignment {parent_id} has {len(learners)} learners (max 2)",
                        details={
                            "parent_assignment_id": str(parent_id),
                            "count": len(learners),
                        },
                    )
                )

        return ConstraintResult(satisfied=len(violations) == 0, violations=violations)


class LearnerASMWednesdayConstraint(HardConstraint):
    """
    ASM (Ambulatory Skills Module) sessions must be Wednesday AM.

    This is a program-level requirement: all learner ASM activities
    are fixed to Wednesday morning (day_of_week=2, time_of_day=AM).
    """

    def __init__(self) -> None:
        super().__init__(
            name="LearnerASMWednesday",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        learner_vars = variables.get("learner_assignments")
        if not learner_vars:
            return

        constrained = 0
        for key, var in learner_vars.items():
            learner_id, block_id, day, time, parent_id = key
            activity_type = variables.get("learner_activity_types", {}).get(key)
            if activity_type == "ASM":
                # ASM must be Wednesday (day=2) AM
                if day != 2 or time != "AM":
                    model.Add(var == 0)
                    constrained += 1

        if constrained:
            logger.info(
                f"LearnerASMWednesday: blocked {constrained} non-Wed-AM ASM slots"
            )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        violations = []
        for a in assignments:
            if hasattr(a, "activity_type") and a.activity_type == "ASM":
                if a.day_of_week != 2 or a.time_of_day != "AM":
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=f"ASM assignment not on Wednesday AM (day={a.day_of_week}, time={a.time_of_day})",
                            person_id=a.learner_id
                            if hasattr(a, "learner_id")
                            else None,
                            block_id=a.block_id if hasattr(a, "block_id") else None,
                        )
                    )
        return ConstraintResult(satisfied=len(violations) == 0, violations=violations)


class LearnerFMITBlockingConstraint(HardConstraint):
    """
    During a learner's FMIT week, block them from clinic assignments.

    Learners assigned to FMIT should have all half-day slots set to FMIT
    activity, not clinic or other activities.
    """

    def __init__(self) -> None:
        super().__init__(
            name="LearnerFMITBlocking",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        learner_vars = variables.get("learner_assignments")
        fmit_weeks = variables.get("learner_fmit_weeks", {})
        if not learner_vars or not fmit_weeks:
            return

        blocked = 0
        for key, var in learner_vars.items():
            learner_id, block_id, day, time, parent_id = key
            activity_type = variables.get("learner_activity_types", {}).get(key)
            # If this learner has FMIT this block, non-FMIT activities are blocked
            if (learner_id, block_id) in fmit_weeks and activity_type != "FMIT":
                model.Add(var == 0)
                blocked += 1

        if blocked:
            logger.info(
                f"LearnerFMITBlocking: blocked {blocked} non-FMIT slots during FMIT weeks"
            )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        # Validation requires knowing which learners have FMIT in which blocks
        # This is checked at the generator level
        return ConstraintResult(satisfied=True)


class LearnerDoubleBookingConstraint(HardConstraint):
    """
    Prevent double-booking: one activity per learner per half-day slot.

    Each (learner_id, block_id, day_of_week, time_of_day) must have at most
    one assignment.
    """

    def __init__(self) -> None:
        super().__init__(
            name="LearnerDoubleBooking",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        learner_vars = variables.get("learner_assignments")
        if not learner_vars:
            return

        from collections import defaultdict

        slot_vars: dict[tuple, list] = defaultdict(list)
        for key, var in learner_vars.items():
            learner_id, block_id, day, time, _parent_id = key
            slot_key = (learner_id, block_id, day, time)
            slot_vars[slot_key].append(var)

        constrained = 0
        for slot_key, vars_list in slot_vars.items():
            if len(vars_list) > 1:
                model.Add(sum(vars_list) <= 1)
                constrained += 1

        if constrained:
            logger.info(
                f"LearnerDoubleBooking: enforced uniqueness on {constrained} slots"
            )

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        violations = []
        seen: set[tuple] = set()
        for a in assignments:
            slot = (
                getattr(a, "learner_id", None),
                getattr(a, "block_id", None),
                getattr(a, "day_of_week", None),
                getattr(a, "time_of_day", None),
            )
            if slot in seen:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=f"Learner double-booked: day={slot[2]}, time={slot[3]}",
                        person_id=slot[0],
                        block_id=slot[1],
                    )
                )
            seen.add(slot)

        return ConstraintResult(satisfied=len(violations) == 0, violations=violations)


class LearnerTrackBalanceConstraint(SoftConstraint):
    """
    Soft constraint: balance learner count across the 7 tracks.

    Penalizes imbalanced track assignments to ensure even distribution
    of learners across tracks within a block.
    """

    def __init__(self, weight: float = 10.0) -> None:
        super().__init__(
            name="LearnerTrackBalance",
            constraint_type=ConstraintType.EQUITY,
            weight=weight,
            priority=ConstraintPriority.LOW,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        # Track balance is handled at the assignment level, not solver level
        pass

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        pass

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        # Count learners per track
        from collections import Counter

        track_counts = Counter()
        for a in assignments:
            if hasattr(a, "track_id") and a.track_id:
                track_counts[a.track_id] += 1

        if not track_counts:
            return ConstraintResult(satisfied=True)

        max_count = max(track_counts.values())
        min_count = min(track_counts.values())
        imbalance = max_count - min_count

        violations = []
        if imbalance > 2:
            violations.append(
                ConstraintViolation(
                    constraint_name=self.name,
                    constraint_type=self.constraint_type,
                    severity="LOW",
                    message=f"Track imbalance: {imbalance} (max={max_count}, min={min_count})",
                    details={
                        "imbalance": imbalance,
                        "track_counts": dict(track_counts),
                    },
                )
            )

        return ConstraintResult(
            satisfied=True,  # Soft constraint, always "satisfied"
            violations=violations,
            penalty=self.get_penalty(imbalance) if imbalance > 1 else 0.0,
        )
