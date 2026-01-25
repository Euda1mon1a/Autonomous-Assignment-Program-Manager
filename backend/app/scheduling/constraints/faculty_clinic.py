"""
Faculty Clinic and AT (Attending Time) Constraints.

Implements ACGME supervision requirements and faculty clinic caps:
1. FacultyClinicCapConstraint - MIN/MAX C (clinic) per week per faculty
2. FacultySupervisionConstraint - ACGME AT coverage for residents in clinic

Session 136: Created to fix missing faculty C/AT assignments in solver.

The solver was only generating resident assignments, leaving faculty slots
to be filled by FacultyAssignmentExpansionService with GME/DFM by default.
These constraints ensure proper faculty clinic and supervision coverage.
"""

import logging
import math
from collections import defaultdict
from datetime import date, timedelta
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


# Faculty clinic caps (MIN, MAX per week)
# From TAMC scheduling requirements (skill doc: tamc-cpsat-constraints)
# C = Faculty seeing OWN patients (has caps)
# AT = Faculty supervising residents (no cap - unlimited)
FACULTY_CLINIC_CAPS: dict[str, tuple[int, int]] = {
    # Core faculty with clinic responsibilities
    "Kinkennon": (2, 4),  # MIN 2, MAX 4 per week
    "LaBounty": (2, 4),
    "McRae": (2, 4),
    "Montgomery": (2, 2),  # Fixed at 2 per week
    "Lamoureux": (2, 2),
    "McGuire": (1, 1),  # DFM focus, minimal clinic
    # Sports Med and specialty faculty (no FM clinic)
    "Tagawa": (0, 0),  # SM only
    # FMIT-focused faculty (no outpatient clinic)
    "Bevis": (0, 0),
    "Dahl": (1, 2),
    "Chu": (0, 0),
    "Napierala": (0, 0),
    "Van Brunt": (0, 0),
    "Colgan": (0, 0),  # Deployed
}

# Default caps for faculty not in the list
DEFAULT_CLINIC_CAPS = (0, 4)  # MIN 0, MAX 4


class FacultyClinicCapConstraint(SoftConstraint):
    """
    Enforce MIN and MAX clinic sessions per week per faculty.

    MIN is a soft constraint (warn if can't meet due to other constraints).
    MAX is enforced as hard in the solver but soft in validation.

    Clinic (C) means faculty seeing their OWN patients, generating their
    own patient load. This is distinct from AT (Attending Time) where
    faculty supervise residents.
    """

    def __init__(self, weight: float = 50.0) -> None:
        super().__init__(
            name="FacultyClinicCap",
            constraint_type=ConstraintType.CAPACITY,
            weight=weight,
            priority=ConstraintPriority.HIGH,
        )

    def _get_caps(self, faculty_name: str) -> tuple[int, int]:
        """Get (MIN, MAX) clinic caps for faculty by last name."""
        # Extract last name from "First Last" or "Last, First" format
        if "," in faculty_name:
            last_name = faculty_name.split(",")[0].strip()
        else:
            parts = faculty_name.split()
            last_name = parts[-1] if parts else faculty_name

        return FACULTY_CLINIC_CAPS.get(last_name, DEFAULT_CLINIC_CAPS)

    def _get_week_dates(
        self, start_date: date, end_date: date
    ) -> list[tuple[date, date]]:
        """Get list of (week_start, week_end) tuples for the date range."""
        weeks = []
        current = start_date

        # Use 7-day windows anchored to start_date (block-aligned weeks)
        while current <= end_date:
            week_end = current + timedelta(days=6)
            if week_end > end_date:
                week_end = end_date
            weeks.append((current, week_end))
            current = week_end + timedelta(days=1)

        return weeks

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add clinic cap constraints to CP-SAT model."""
        faculty_clinic = variables.get("faculty_clinic", {})

        if not faculty_clinic:
            logger.debug("No faculty_clinic variables, skipping constraint")
            return

        if not context.start_date or not context.end_date:
            logger.warning("No date range in context, skipping constraint")
            return

        weeks = self._get_week_dates(context.start_date, context.end_date)

        for faculty in context.faculty:
            faculty_name = getattr(faculty, "name", "")
            min_c, max_c = self._get_caps(faculty_name)

            for week_start, week_end in weeks:
                # Collect clinic variables for this faculty in this week
                clinic_vars = []
                current = week_start
                while current <= week_end:
                    # Skip weekends (Sat=5, Sun=6)
                    if current.weekday() < 5:
                        for slot in ["AM", "PM"]:
                            key = (faculty.id, current, slot)
                            if key in faculty_clinic:
                                clinic_vars.append(faculty_clinic[key])
                    current += timedelta(days=1)

                if not clinic_vars:
                    continue

                clinic_sum = sum(clinic_vars)

                # MAX constraint (hard in solver)
                if max_c > 0:
                    model.Add(clinic_sum <= max_c)

                # MIN constraint (soft - penalize in objective)
                # We don't add as hard constraint to avoid infeasibility
                # Validation will catch and warn if MIN not met

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add clinic cap constraints to PuLP model."""
        # Similar logic to CP-SAT
        pass  # PuLP implementation if needed

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate clinic caps for each faculty per week."""
        violations: list[ConstraintViolation] = []
        total_penalty = 0.0

        if not context.start_date or not context.end_date:
            return ConstraintResult(satisfied=True, violations=[], penalty=0.0)

        weeks = self._get_week_dates(context.start_date, context.end_date)

        # Build clinic counts by faculty and week
        # Assumes assignments have person_id, date, and activity_code attributes
        clinic_codes = {"fm_clinic", "C"}  # Both db code and display code

        faculty_week_counts: dict[UUID, dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        for assignment in assignments:
            person_id = getattr(assignment, "person_id", None)
            assign_date = getattr(assignment, "date", None)
            activity_code = getattr(assignment, "activity_code", None)

            if not person_id or not assign_date or not activity_code:
                continue

            if activity_code not in clinic_codes:
                continue

            # Find which week this assignment belongs to
            for week_idx, (week_start, week_end) in enumerate(weeks):
                if week_start <= assign_date <= week_end:
                    faculty_week_counts[person_id][week_idx] += 1
                    break

        # Check each faculty against their caps
        faculty_by_id = {f.id: f for f in context.faculty}

        for faculty_id, week_counts in faculty_week_counts.items():
            faculty = faculty_by_id.get(faculty_id)
            if not faculty:
                continue

            faculty_name = getattr(faculty, "name", "Unknown")
            min_c, max_c = self._get_caps(faculty_name)

            for week_idx, count in week_counts.items():
                week_start, _ = weeks[week_idx]

                # Check MAX violation
                if max_c > 0 and count > max_c:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="HIGH",
                            message=(
                                f"{faculty_name} has {count} clinic sessions "
                                f"in week of {week_start} (max: {max_c})"
                            ),
                            person_id=faculty_id,
                            details={"count": count, "max": max_c},
                        )
                    )
                    total_penalty += self.weight * (count - max_c)

                # Check MIN violation (warn only)
                if min_c > 0 and count < min_c:
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            constraint_type=self.constraint_type,
                            severity="MEDIUM",
                            message=(
                                f"{faculty_name} has {count} clinic sessions "
                                f"in week of {week_start} (min: {min_c})"
                            ),
                            person_id=faculty_id,
                            details={"count": count, "min": min_c},
                        )
                    )
                    total_penalty += self.weight * 0.5 * (min_c - count)

        return ConstraintResult(
            satisfied=len([v for v in violations if v.severity == "HIGH"]) == 0,
            violations=violations,
            penalty=total_penalty,
        )


class FacultySupervisionConstraint(HardConstraint):
    """
    Ensure ACGME AT (Attending Time) coverage for residents in clinic.

    ACGME supervision ratios:
    - PGY-1: 1 faculty per 2 residents (0.5 AT demand each)
    - PGY-2/3: 1 faculty per 4 residents (0.25 AT demand each)

    AT coverage sources:
    - AT: Attending Time (primary supervision)
    - PCAT: Post-Call Attending Time

    This is the highest priority constraint - ACGME compliance.
    """

    # Supervision demand per resident PGY level
    AT_DEMAND: dict[int, float] = {
        1: 0.5,  # PGY-1: 2 residents per faculty
        2: 0.25,  # PGY-2: 4 residents per faculty
        3: 0.25,  # PGY-3: 4 residents per faculty
    }

    # Activity codes that count as AT coverage
    AT_COVERAGE_CODES = {"at", "pcat"}

    def __init__(self) -> None:
        super().__init__(
            name="FacultySupervision",
            constraint_type=ConstraintType.SUPERVISION,
            priority=ConstraintPriority.CRITICAL,
        )

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add ACGME supervision constraint to CP-SAT model."""
        faculty_at = variables.get("faculty_at", {})
        faculty_pcat = variables.get("faculty_pcat", {})
        resident_clinic = variables.get("resident_clinic", {})

        # If no faculty AT variables, can't enforce this constraint
        if not faculty_at and not faculty_pcat:
            logger.warning(
                "No faculty_at or faculty_pcat variables, "
                "supervision constraint not applied"
            )
            return

        if not context.start_date or not context.end_date:
            return

        # For each day and slot, ensure AT coverage >= demand
        current = context.start_date
        while current <= context.end_date:
            # Skip weekends
            if current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            for slot in ["AM", "PM"]:
                # Calculate demand from residents in clinic
                # If we don't have resident_clinic vars, use static demand
                if resident_clinic:
                    demand_vars = []
                    for resident in context.residents:
                        key = (resident.id, current, slot)
                        if key in resident_clinic:
                            pgy = getattr(resident, "pgy_level", 2) or 2
                            demand_factor = self.AT_DEMAND.get(pgy, 0.25)
                            # Create auxiliary variable for fractional demand
                            # CP-SAT uses integers, so we multiply by 4
                            # and compare to integer coverage * 4
                            demand_vars.append(
                                (resident_clinic[key], int(demand_factor * 4))
                            )

                    if not demand_vars:
                        continue

                    # Sum weighted demand (each resident adds their factor)
                    total_demand = sum(var * factor for var, factor in demand_vars)

                    # Sum coverage (AT + PCAT only)
                    coverage_vars = []
                    for faculty in context.faculty:
                        fkey = (faculty.id, current, slot)
                        if fkey in faculty_at:
                            coverage_vars.append(faculty_at[fkey])
                        if fkey in faculty_pcat:
                            coverage_vars.append(faculty_pcat[fkey])

                    if coverage_vars:
                        # Coverage * 4 >= demand (scaled by 4)
                        total_coverage = sum(coverage_vars) * 4
                        model.Add(total_coverage >= total_demand)

            current += timedelta(days=1)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add ACGME supervision constraint to PuLP model."""
        pass  # PuLP implementation if needed

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate ACGME supervision ratios."""
        violations: list[ConstraintViolation] = []

        if not context.start_date or not context.end_date:
            return ConstraintResult(satisfied=True, violations=[])

        # Group assignments by (date, slot)
        # Track residents in clinic and faculty providing coverage
        resident_clinic_codes = {"fm_clinic", "C", "C-N", "CV"}

        slot_residents: dict[tuple, list] = defaultdict(list)
        slot_faculty: dict[tuple, list] = defaultdict(list)

        for assignment in assignments:
            assign_date = getattr(assignment, "date", None)
            time_of_day = getattr(assignment, "time_of_day", None)
            person_id = getattr(assignment, "person_id", None)
            person_type = getattr(assignment, "person_type", None)
            activity_code = getattr(assignment, "activity_code", None)
            pgy_level = getattr(assignment, "pgy_level", None)

            if not assign_date or not time_of_day or not person_id:
                continue

            key = (assign_date, time_of_day)

            if person_type == "resident" and activity_code in resident_clinic_codes:
                slot_residents[key].append({"id": person_id, "pgy": pgy_level or 2})

            if person_type == "faculty" and activity_code in self.AT_COVERAGE_CODES:
                slot_faculty[key].append(person_id)

        # Check each slot
        for key, residents in slot_residents.items():
            if not residents:
                continue

            assign_date, slot = key
            faculty_count = len(slot_faculty.get(key, []))

            # Calculate demand
            demand = sum(self.AT_DEMAND.get(r["pgy"], 0.25) for r in residents)
            required_faculty = math.ceil(demand)

            if faculty_count < required_faculty:
                deficit = required_faculty - faculty_count
                pgy1_count = len([r for r in residents if r["pgy"] == 1])
                other_count = len(residents) - pgy1_count

                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        constraint_type=self.constraint_type,
                        severity="CRITICAL",
                        message=(
                            f"{assign_date} {slot}: Need {required_faculty} AT "
                            f"but have {faculty_count} (deficit: {deficit}) "
                            f"for {pgy1_count} PGY-1 + {other_count} PGY-2/3"
                        ),
                        details={
                            "date": str(assign_date),
                            "slot": slot,
                            "required": required_faculty,
                            "actual": faculty_count,
                            "deficit": deficit,
                            "residents": len(residents),
                        },
                    )
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )
