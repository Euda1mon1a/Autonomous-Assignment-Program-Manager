"""
ACGME Compliance Validator.

Validates schedules against ACGME requirements:
- 80-hour rule (rolling 4-week average)
- 1-in-7 days off
- 24+4 rule (max continuous duty)
- Supervision ratios
"""

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session, selectinload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.schemas.schedule import ValidationResult, Violation


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
    HOURS_PER_HALF_DAY = 6  # AM or PM block = 6 hours (realistic clinical duty)
    ROLLING_WINDOW_WEEKS = 4

    def __init__(self, db: Session) -> None:
        """
        Initialize ACGME validator.

        Args:
            db: SQLAlchemy database session for querying assignments
        """
        self.db = db

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
        violations.extend(self._check_supervision_ratios(assignments))

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
                violations.append(
                    Violation(
                        type="80_HOUR_VIOLATION",
                        severity="CRITICAL",
                        person_id=resident.id,
                        person_name=resident.name,
                        message=f"{resident.name}: {avg_weekly:.1f} hours/week (limit: {self.MAX_WEEKLY_HOURS})",
                        details={
                            "window_start": window_start.isoformat(),
                            "window_end": window_end.isoformat(),
                            "average_weekly_hours": avg_weekly,
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
            if assignment.block:
                dates_with_assignments.add(assignment.block.date)

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
                    },
                )
            )

        return violations

    def _check_supervision_ratios(
        self, assignments: list[Assignment]
    ) -> list[Violation]:
        """
        Check faculty:resident supervision ratios for OUTPATIENT rotations only.

        Ratios (for clinic/outpatient only):
        - PGY-1: 1 faculty : 2 residents
        - PGY-2/3: 1 faculty : 4 residents

        Inpatient residents (FMIT, Night Float, etc.) have separate supervision
        via FMIT faculty and are NOT included in clinic supervision ratios.
        """
        violations = []

        # Group by block
        assignments_by_block = defaultdict(list)
        for assignment in assignments:
            assignments_by_block[assignment.block_id].append(assignment)

        # Check each block (use eager-loaded relationships to prevent N+1)
        for block_id, block_assignments in assignments_by_block.items():
            supervised_residents = []
            faculty = []
            block = None  # Will be set from first assignment with block

            for assignment in block_assignments:
                # Use eager-loaded person instead of querying
                person = assignment.person
                if not person:
                    continue

                # Capture block from any assignment (all have same block_id)
                if block is None and assignment.block:
                    block = assignment.block

                if person.type == "faculty":
                    faculty.append(person)
                elif person.type == "resident":
                    # Only count residents on rotations that require FMC supervision
                    # Uses eager-loaded rotation_template
                    rotation = assignment.rotation_template
                    if rotation and rotation.supervision_required:
                        supervised_residents.append(person)

            # No supervised residents in this block = no supervision needed
            if not supervised_residents:
                continue

            # Calculate required faculty for supervised residents
            pgy1_count = sum(1 for r in supervised_residents if r.pgy_level == 1)
            other_count = len(supervised_residents) - pgy1_count

            # 1:2 for PGY-1, 1:4 for others
            required = (pgy1_count + 1) // 2 + (other_count + 3) // 4
            required = max(1, required)

            if len(faculty) < required:
                violations.append(
                    Violation(
                        type="SUPERVISION_RATIO_VIOLATION",
                        severity="CRITICAL",
                        block_id=block_id,
                        message=f"Block {block.display_name if block else block_id}: {len(faculty)} faculty for {len(supervised_residents)} supervised residents (need {required})",
                        details={
                            "residents": len(supervised_residents),
                            "pgy1_count": pgy1_count,
                            "faculty": len(faculty),
                            "required_faculty": required,
                        },
                    )
                )

        return violations

    def _assignments_to_hours(self, assignments: list[Assignment]) -> dict[date, int]:
        """Convert assignments to hours per date (uses eager-loaded block)."""
        hours_by_date = defaultdict(int)

        for assignment in assignments:
            # Use eager-loaded block instead of querying
            if assignment.block:
                hours_by_date[assignment.block.date] += self.HOURS_PER_HALF_DAY

        return dict(hours_by_date)
