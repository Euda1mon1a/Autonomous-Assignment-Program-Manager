"""
ACGME Compliance Validator.

Validates schedules against ACGME requirements:
- 80-hour rule (rolling 4-week average)
- 1-in-7 days off
- 24+4 rule (max continuous duty)
- Supervision ratios
"""

from collections import defaultdict
import math
import re
from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models.activity import Activity
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.schemas.schedule import ValidationResult, Violation
from app.utils.fmc_capacity import activity_is_proc_or_vas
from app.utils.supervision import (
    activity_provides_supervision,
    assignment_requires_fmc_supervision,
)


class ACGMEValidator:
    """
    ACGME compliance validator for residency schedules.

    Validates schedules against ACGME (Accreditation Council for Graduate
    Medical Education) requirements, ensuring resident safety and educational
    quality through duty hour limits and supervision standards.

    ACGME Requirements Enforced:
        - 80-hour rule: Max 80 hours/week averaged over 4 weeks
        - 1-in-7 rule: At least one 24-hour period off every 7 days
        - Supervision ratios: Adequate faculty supervision based on PGY level

    Clinical Context:
        ACGME violations can result in:
        - Program citations and warnings
        - Loss of accreditation
        - Patient safety concerns
        - Resident burnout and fatigue

    Constants:
        MAX_WEEKLY_HOURS (int): Maximum hours per week (80)
        HOURS_PER_HALF_DAY (int): Hours per AM/PM block (6)
        ROLLING_WINDOW_WEEKS (int): Window for averaging hours (4 weeks)

    Example:
        >>> validator = ACGMEValidator(db)
        >>> result = validator.validate_all(start_date, end_date)
        >>> if not result.valid:
        ...     for violation in result.violations:
        ...         print(f"VIOLATION: {violation.message}")
    """

    # Constants
    MAX_WEEKLY_HOURS = 80
    MAX_CONSECUTIVE_DAYS = 6
    HOURS_PER_HALF_DAY = 6  # AM or PM block = 6 hours (realistic clinical duty)
    ROLLING_WINDOW_WEEKS = 4

    def __init__(self, db: Session) -> None:
        """
        Initialize ACGME validator.

        Args:
            db: SQLAlchemy database session for querying assignments
        """
        self.db = db
        self._time_off_slots: set[tuple[str, date, str]] = set()
        self._time_off_codes = {"W", "OFF", "LV-AM", "LV-PM", "PC"}

    def validate_all(self, start_date: date, end_date: date) -> ValidationResult:
        """
        Run all ACGME validation checks for a schedule period.

        Performs comprehensive validation of all residents in the schedule,
        checking 80-hour rule, 1-in-7 rule, and supervision ratios.

        Args:
            start_date: Start date of validation period
            end_date: End date of validation period (inclusive)

        Returns:
            ValidationResult with:
                - valid (bool): True if no critical violations found
                - total_violations (int): Count of all violations
                - violations (list): List of Violation objects with details
                - coverage_rate (float): Percentage of blocks assigned (0-100)
                - statistics (dict): Summary statistics

        Validation Process:
            1. Query all residents and assignments in date range
            2. For each resident:
               - Check 80-hour rule compliance (rolling 4-week windows)
               - Check 1-in-7 rule compliance (max consecutive days)
            3. Check supervision ratios for all blocks
            4. Calculate coverage rate
            5. Aggregate results into ValidationResult

        Example:
            >>> validator = ACGMEValidator(db)
            >>> result = validator.validate_all(
            ...     start_date=date(2025, 1, 1),
            ...     end_date=date(2025, 1, 31)
            ... )
            >>> print(f"Valid: {result.valid}")
            >>> print(f"Coverage: {result.coverage_rate:.1f}%")
            >>> print(f"Violations: {result.total_violations}")
            >>>
            >>> if result.total_violations > 0:
            ...     critical = [v for v in result.violations if v.severity == "CRITICAL"]
            ...     print(f"Critical violations: {len(critical)}")

        Note:
            Violations are categorized by severity:
            - CRITICAL: ACGME compliance violations (must fix immediately)
            - HIGH: Serious issues (should fix soon)
            - MEDIUM: Minor issues (good to address)
        """
        violations = []

        # Get all residents
        residents = self.db.query(Person).filter(Person.type == "resident").all()
        resident_ids = [r.id for r in residents]

        # Preload time-off slots from half-day assignments (source of truth)
        self._time_off_slots = self._load_time_off_slots(
            start_date,
            end_date,
            resident_ids,
        )

        # Get all assignments in range with eager loading to prevent N+1 queries
        assignments = (
            self.db.query(Assignment)
            .options(
                selectinload(Assignment.block),
                selectinload(Assignment.person),
                selectinload(Assignment.rotation_template),
            )
            .join(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .all()
        )

        # Check each resident
        for resident in residents:
            resident_assignments = [
                a for a in assignments if a.person_id == resident.id
            ]

            # 80-hour rule
            violations.extend(self._check_80_hour_rule(resident, resident_assignments))

            # 1-in-7 rule
            violations.extend(self._check_1_in_7_rule(resident, resident_assignments))

        # Check supervision ratios
        violations.extend(
            self._check_supervision_ratios(start_date, end_date)
        )

        # Calculate coverage rate
        total_blocks = (
            self.db.query(Block)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
                Block.is_weekend == False,  # noqa: E712 - SQLAlchemy requires == for filter
            )
            .count()
        )
        assigned_blocks = len(
            {
                a.block_id
                for a in assignments
                if a.block is not None and not a.block.is_weekend
            }
        )
        coverage_rate = assigned_blocks / total_blocks if total_blocks > 0 else 0.0

        return ValidationResult(
            valid=len(violations) == 0,
            total_violations=len(violations),
            violations=violations,
            coverage_rate=coverage_rate * 100,
            statistics={
                "total_assignments": len(assignments),
                "total_blocks": total_blocks,
                "residents_scheduled": len(
                    {
                        a.person_id
                        for a in assignments
                        if a.person and a.person.type == "resident"
                    }
                ),
            },
        )

    def _check_80_hour_rule(
        self, resident: Person, assignments: list[Assignment]
    ) -> list[Violation]:
        """
        Check 80-hour rule.

        Max 80 hours/week averaged over 4 weeks.
        Uses rolling window approach.
        """
        violations = []

        if not assignments:
            return violations

        # Get hours per date
        hours_by_date = self._assignments_to_hours(assignments)
        if not hours_by_date:
            return violations

        fixed_hours_by_date = self._fixed_half_day_hours_by_date(
            resident.id,
            min(hours_by_date.keys()),
            max(hours_by_date.keys()),
        )

        dates = sorted(hours_by_date.keys())
        window_days = self.ROLLING_WINDOW_WEEKS * 7

        # Check all possible 28-day windows
        for i in range(len(dates)):
            window_start = dates[i]
            window_end = window_start + timedelta(days=window_days - 1)

            # Sum hours in window
            total_hours = sum(
                hours
                for d, hours in hours_by_date.items()
                if window_start <= d <= window_end
            )

            avg_weekly = total_hours / self.ROLLING_WINDOW_WEEKS

            if avg_weekly > self.MAX_WEEKLY_HOURS:
                fixed_total_hours = sum(
                    hours
                    for d, hours in fixed_hours_by_date.items()
                    if window_start <= d <= window_end
                )
                fixed_avg_weekly = (
                    fixed_total_hours / self.ROLLING_WINDOW_WEEKS
                    if fixed_total_hours
                    else 0.0
                )
                fixed_exempt = fixed_avg_weekly > self.MAX_WEEKLY_HOURS
                violations.append(
                    Violation(
                        type="80_HOUR_VIOLATION",
                        severity="CRITICAL",
                        person_id=resident.id,
                        person_name=resident.name,
                        message=(
                            f"{resident.name}: {avg_weekly:.1f} hours/week "
                            f"(limit: {self.MAX_WEEKLY_HOURS})"
                        ),
                        details={
                            "window_start": window_start.isoformat(),
                            "window_end": window_end.isoformat(),
                            "average_weekly_hours": avg_weekly,
                            "fixed_workload_exempt": fixed_exempt,
                            "fixed_total_hours": fixed_total_hours,
                            "fixed_avg_weekly_hours": fixed_avg_weekly,
                        },
                    )
                )
                # Only report first violation per resident
                break

        return violations

    def _check_1_in_7_rule(
        self, resident: Person, assignments: list[Assignment]
    ) -> list[Violation]:
        """
        Check 1-in-7 rule.

        One 24-hour period off every 7 days (averaged over 4 weeks).
        Simplified: Check for consecutive duty days > 6.
        """
        violations = []

        if not assignments:
            return violations

        # Get unique dates with assignments (use eager-loaded block)
        dates_with_assignments = set()
        for assignment in assignments:
            if not self._counts_toward_duty_hours(assignment):
                continue
            if assignment.block:
                dates_with_assignments.add(assignment.block.date)

        if dates_with_assignments:
            fixed_dates_with_assignments = set(
                self._fixed_half_day_hours_by_date(
                    resident.id,
                    min(dates_with_assignments),
                    max(dates_with_assignments),
                ).keys()
            )
        else:
            fixed_dates_with_assignments = set()

        if not dates_with_assignments:
            return violations

        sorted_dates = sorted(dates_with_assignments)

        # Check for consecutive days > 6
        consecutive = 1
        max_consecutive = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        fixed_max_consecutive = self._max_consecutive_days(
            fixed_dates_with_assignments
        )
        fixed_exempt = fixed_max_consecutive > self.MAX_CONSECUTIVE_DAYS

        if max_consecutive > 6:
            violations.append(
                Violation(
                    type="1_IN_7_VIOLATION",
                    severity="HIGH",
                    person_id=resident.id,
                    person_name=resident.name,
                    message=f"{resident.name}: {max_consecutive} consecutive duty days (limit: 6)",
                    details={
                        "consecutive_days": max_consecutive,
                        "fixed_workload_exempt": fixed_exempt,
                        "fixed_consecutive_days": fixed_max_consecutive,
                    },
                )
            )

        return violations

    def _check_supervision_ratios(
        self, start_date: date, end_date: date
    ) -> list[Violation]:
        """
        Check faculty:resident supervision ratios using half-day assignments.

        Ratios (for clinic/outpatient only):
        - PGY-1: 1 faculty : 2 residents
        - PGY-2/3: 1 faculty : 4 residents

        Inpatient residents (FMIT, Night Float, etc.) have separate supervision
        via FMIT faculty and are NOT included in clinic supervision ratios.
        """
        violations = []

        # Load blocks for date/time lookup
        blocks = (
            self.db.query(Block)
            .filter(Block.date >= start_date, Block.date <= end_date)
            .all()
        )
        blocks_by_key = {(b.date, b.time_of_day): b for b in blocks}

        # Pull half-day assignments with activity/person context
        half_day_assignments = (
            self.db.query(HalfDayAssignment)
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
            .filter(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
            .all()
        )

        by_slot: dict[tuple[date, str], dict[str, int | list]] = defaultdict(
            lambda: {
                "resident_ids": [],
                "faculty_ids": [],
                "pgy1_count": 0,
                "pgy2_3_count": 0,
                "proc_vas_count": 0,
                "demand_units": 0,
            }
        )

        for assignment in half_day_assignments:
            if not assignment.person or not assignment.activity:
                continue
            if assignment.date.weekday() >= 5:
                continue

            slot_key = (assignment.date, assignment.time_of_day)

            if assignment.person.is_resident:
                if not assignment_requires_fmc_supervision(assignment):
                    continue
                pgy_level = assignment.person.pgy_level or 2
                demand_units = 2 if pgy_level == 1 else 1
                if activity_is_proc_or_vas(assignment.activity):
                    demand_units += 4
                    by_slot[slot_key]["proc_vas_count"] += 1
                by_slot[slot_key]["resident_ids"].append(assignment.person_id)
                if pgy_level == 1:
                    by_slot[slot_key]["pgy1_count"] += 1
                else:
                    by_slot[slot_key]["pgy2_3_count"] += 1
                by_slot[slot_key]["demand_units"] += demand_units
                continue

            if assignment.person.is_faculty:
                if not activity_provides_supervision(assignment.activity):
                    continue
                by_slot[slot_key]["faculty_ids"].append(assignment.person_id)

        for slot_key, slot_data in by_slot.items():
            demand_units = slot_data["demand_units"]
            if demand_units <= 0:
                continue
            required = math.ceil(demand_units / 4)
            faculty_count = len(slot_data["faculty_ids"])
            if faculty_count >= required:
                continue

            block = blocks_by_key.get(slot_key)
            block_id = block.id if block else None
            slot_date, time_of_day = slot_key

            violations.append(
                Violation(
                    type="SUPERVISION_RATIO_VIOLATION",
                    severity="CRITICAL",
                    block_id=block_id,
                    message=(
                        f"Block {block.display_name if block else f'{slot_date} {time_of_day}'}: "
                        f"{faculty_count} faculty for {len(slot_data['resident_ids'])} supervised residents "
                        f"(need {required})"
                    ),
                    details={
                        "residents": len(slot_data["resident_ids"]),
                        "pgy1_count": slot_data["pgy1_count"],
                        "faculty": faculty_count,
                        "required_faculty": required,
                        "proc_vas_count": slot_data["proc_vas_count"],
                    },
                )
            )

        return violations

    def _assignments_to_hours(
        self, assignments: list[Assignment], fixed_only: bool = False
    ) -> dict[date, int]:
        """Convert assignments to hours per date (uses eager-loaded block)."""
        hours_by_date = defaultdict(int)

        for assignment in assignments:
            if not self._counts_toward_duty_hours(assignment):
                continue
            if fixed_only and not self._is_fixed_workload(assignment):
                continue
            # Use eager-loaded block instead of querying
            if assignment.block:
                hours_by_date[assignment.block.date] += self.HOURS_PER_HALF_DAY

        return dict(hours_by_date)

    def _fixed_half_day_hours_by_date(
        self, resident_id, start_date: date, end_date: date
    ) -> dict[date, int]:
        """Return fixed workload hours per date from preload/manual half-day assignments."""
        from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
        from app.models.activity import Activity

        hours_by_date = defaultdict(int)

        fixed_prefixes = ("FMIT", "ICU", "NICU", "NIC", "LAD", "NBN", "IM", "PEDW")
        offsite_prefixes = ("HILO", "OKI", "KAP", "KAPI", "TDY")
        fixed_exact = {"TAMC-LD", "TAMC_LD"}
        nf_tokens = {"NF", "PEDNF", "LDNF", "PNF"}

        def is_fixed_code(raw: str | None) -> bool:
            base = (raw or "").strip().upper()
            if not base:
                return False
            if base.endswith("-AM") or base.endswith("-PM"):
                base = base[:-3]
            if base in fixed_exact:
                return True
            if base.startswith(fixed_prefixes) or base.startswith(offsite_prefixes):
                return True
            tokens = [t for t in re.split(r"[^A-Z0-9]+", base) if t]
            return any(t in nf_tokens for t in tokens)

        rows = (
            self.db.query(
                HalfDayAssignment.date,
                Activity.code,
                Activity.display_abbreviation,
                Activity.activity_category,
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .filter(
                HalfDayAssignment.person_id == resident_id,
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
                HalfDayAssignment.source.in_(
                    [AssignmentSource.PRELOAD.value, AssignmentSource.MANUAL.value]
                ),
            )
            .all()
        )

        for slot_date, code, abbrev, category in rows:
            if (category or "").lower() == "time_off":
                continue
            if is_fixed_code(code) or is_fixed_code(abbrev):
                hours_by_date[slot_date] += self.HOURS_PER_HALF_DAY

        return dict(hours_by_date)

    def _max_consecutive_days(self, dates: set[date]) -> int:
        """Return max consecutive day streak for a set of dates."""
        if not dates:
            return 0

        sorted_dates = sorted(dates)
        consecutive = 1
        max_consecutive = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        return max_consecutive

    def _counts_toward_duty_hours(self, assignment: Assignment) -> bool:
        """
        Return True if this assignment should count toward duty hour rules.

        Excludes time-off and absence rotations. Educational/admin rotations
        still count toward duty hours per ACGME.
        """
        if assignment.block:
            slot_key = (
                str(assignment.person_id),
                assignment.block.date,
                assignment.block.time_of_day,
            )
            if slot_key in self._time_off_slots:
                return False
        template = assignment.rotation_template
        if not template:
            return True

        rotation_type = (template.rotation_type or "").lower()
        template_category = (template.template_category or "").lower()

        if template_category in {"time_off", "absence"}:
            return False
        if rotation_type in {"off", "absence", "recovery"}:
            return False

        return True

    def _is_fixed_workload(self, assignment: Assignment) -> bool:
        """
        Return True if this assignment is fixed workload (inpatient/offsite).

        Fixed workload is used to exempt violations that the solver cannot
        change. Offsite and inpatient are treated synonymously for current
        rotations.
        """
        if not self._counts_toward_duty_hours(assignment):
            return False

        template = assignment.rotation_template
        if not template:
            return False

        rotation_type = (template.rotation_type or "").lower()
        template_category = (template.template_category or "").lower()

        if template_category in {"time_off", "absence"}:
            return False

        return rotation_type in {"inpatient", "off"}

    def _load_time_off_slots(
        self,
        start_date: date,
        end_date: date,
        resident_ids: list[str],
    ) -> set[tuple[str, date, str]]:
        """Load time-off slots from half-day assignments."""
        if not resident_ids:
            return set()

        rows = (
            self.db.query(
                HalfDayAssignment.person_id,
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                Activity.code,
                Activity.display_abbreviation,
                Activity.activity_category,
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .filter(
                HalfDayAssignment.person_id.in_(resident_ids),
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
            )
            .all()
        )

        slots: set[tuple[str, date, str]] = set()
        for person_id, slot_date, time_of_day, code, display, category in rows:
            cat = (category or "").lower()
            code_norm = (code or "").strip().upper()
            display_norm = (display or "").strip().upper()
            if cat == "time_off" or code_norm in self._time_off_codes or display_norm in self._time_off_codes:
                slots.add((str(person_id), slot_date, time_of_day))

        return slots
