"""
Block Assignment Expansion Service.

Expands block-level rotation assignments (28-day periods) into
daily AM/PM slot assignments. This bridges the gap between:
- BlockAssignment: "Resident X is on FMIT for Block 10"
- Assignment: "Resident X works FMIT on March 15 AM"

Key features:
- Uses rotation template's weekly_patterns for slot activities
- Respects absences via availability matrix
- Applies 1-in-7 day-off rule
- Handles inpatient vs outpatient differently
- PERSEC-compliant logging (no PII)
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


class BlockAssignmentExpansionService:
    """
    Service to expand BlockAssignments into daily Assignment records.

    Workflow:
    1. Load BlockAssignments for a given block number
    2. For each BlockAssignment:
       a. Get rotation template and its weekly patterns
       b. For each day in the 28-day block:
          - Skip if person is unavailable (absence)
          - Skip if weekend and rotation doesn't include weekends
          - Apply 1-in-7 day-off rule
          - Create Assignment for AM and PM slots
    3. Return list of Assignment objects (not committed)
    """

    def __init__(self, db: Session):
        self.db = db
        self._absence_cache: dict[UUID, list[Absence]] = {}
        self._block_cache: dict[tuple[date, str], Block] = {}

    def expand_block_assignments(
        self,
        block_number: int,
        academic_year: int,
        schedule_run_id: UUID | None = None,
        created_by: str = "expansion_service",
        apply_one_in_seven: bool = True,
    ) -> list[Assignment]:
        """
        Expand all BlockAssignments for a block into daily Assignments.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            schedule_run_id: Optional provenance tracking ID
            created_by: Audit field for who created assignments
            apply_one_in_seven: Whether to enforce 1-in-7 day off rule

        Returns:
            List of Assignment objects (not yet committed to DB)
        """
        logger.info(f"Expanding block {block_number} AY {academic_year}")

        # Load block assignments with relationships
        block_assignments = self._load_block_assignments(block_number, academic_year)
        logger.info(f"Found {len(block_assignments)} block assignments to expand")

        # Get block date range
        block_dates = get_block_dates(block_number, academic_year)
        start_date, end_date = block_dates.start_date, block_dates.end_date
        logger.info(f"Block {block_number} dates: {start_date} to {end_date}")

        # Pre-load blocks for the date range
        self._preload_blocks(start_date, end_date)

        # Pre-load absences for all people
        person_ids = [ba.resident_id for ba in block_assignments]
        self._preload_absences(person_ids, start_date, end_date)

        # Expand each block assignment
        all_assignments: list[Assignment] = []
        for block_assignment in block_assignments:
            assignments = self._expand_single_block_assignment(
                block_assignment,
                start_date,
                end_date,
                schedule_run_id,
                created_by,
                apply_one_in_seven,
            )
            all_assignments.extend(assignments)

        logger.info(f"Expanded to {len(all_assignments)} daily assignments")
        return all_assignments

    def _load_block_assignments(
        self,
        block_number: int,
        academic_year: int,
    ) -> list[BlockAssignment]:
        """Load BlockAssignments with rotation templates and weekly patterns."""
        stmt = (
            select(BlockAssignment)
            .options(
                selectinload(BlockAssignment.rotation_template).selectinload(
                    RotationTemplate.weekly_patterns
                ),
                selectinload(BlockAssignment.resident),
            )
            .where(BlockAssignment.block_number == block_number)
            .where(BlockAssignment.academic_year == academic_year)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def _preload_blocks(self, start_date: date, end_date: date) -> None:
        """Pre-load all Block records for the date range."""
        stmt = select(Block).where(
            Block.date >= start_date,
            Block.date <= end_date,
        )
        result = self.db.execute(stmt)
        for block in result.scalars().all():
            self._block_cache[(block.date, block.time_of_day)] = block
        logger.info(f"Pre-loaded {len(self._block_cache)} blocks")

    def _preload_absences(
        self,
        person_ids: list[UUID],
        start_date: date,
        end_date: date,
    ) -> None:
        """Pre-load absences for all people in the date range."""
        stmt = (
            select(Absence)
            .where(Absence.person_id.in_(person_ids))
            .where(Absence.start_date <= end_date)
            .where(Absence.end_date >= start_date)
        )
        result = self.db.execute(stmt)
        for absence in result.scalars().all():
            if absence.person_id not in self._absence_cache:
                self._absence_cache[absence.person_id] = []
            self._absence_cache[absence.person_id].append(absence)
        logger.info(f"Pre-loaded absences for {len(self._absence_cache)} people")

    def _preload_absence_templates(self) -> None:
        """Pre-load absence rotation templates for 56-slot expansion.

        These templates (W-AM, W-PM, LV-AM, LV-PM, OFF-AM, OFF-PM) are used to
        create placeholder assignments for weekends, absences, and days off.
        This enables the 56-assignment rule: every person gets 56 assignments
        per block (28 days × 2 half-days), making gap detection trivial.
        """
        if hasattr(self, "_absence_templates"):
            return  # Already loaded

        self._absence_templates: dict[str, RotationTemplate] = {}
        stmt = select(RotationTemplate).where(
            RotationTemplate.abbreviation.in_(
                [
                    "W-AM",
                    "W-PM",
                    "LV-AM",
                    "LV-PM",
                    "OFF-AM",
                    "OFF-PM",
                    "HOL-AM",
                    "HOL-PM",
                ]
            )
        )
        for rt in self.db.execute(stmt).scalars():
            self._absence_templates[rt.abbreviation] = rt
        logger.info(f"Pre-loaded {len(self._absence_templates)} absence templates")

    def _get_absence_template(self, abbrev: str) -> RotationTemplate | None:
        """Get absence rotation template by abbreviation (cached)."""
        if not hasattr(self, "_absence_templates"):
            self._preload_absence_templates()
        return self._absence_templates.get(abbrev)

    def _expand_single_block_assignment(
        self,
        block_assignment: BlockAssignment,
        start_date: date,
        end_date: date,
        schedule_run_id: UUID | None,
        created_by: str,
        apply_one_in_seven: bool,
    ) -> list[Assignment]:
        """Expand a single BlockAssignment into daily Assignments.

        ACGME 1-in-7 RULE IMPLEMENTATION - DO NOT MODIFY WITHOUT PHYSICIAN APPROVAL
        ============================================================================

        This method implements the "PAUSE" interpretation for absences:
        - Scheduled day off (weekend, forced 1-in-7): RESETS consecutive_days to 0
        - Absence (leave, TDY, etc.): HOLDS consecutive_days (no change)

        WHY PAUSE (not RESET on absence):
        1. Leave is SEPARATE from ACGME-required rest days
        2. Schedule must be compliant INDEPENDENT of leave status
        3. Absence ≠ "day off" for 1-in-7 purposes
        4. Prevents gaming: can't work 6→leave→work 6→leave→work 6...
        5. Ensures 1-in-7 distribution throughout block (not crammed at end)

        APPROVED BY: Dr. Montgomery (2026-01-11)
        MEDCOM ADVISORY: Confirms PAUSE is correct ACGME interpretation
        CODEX P2 REJECTED: "Reset on absence" suggestion is INCORRECT

        See: .claude/plans/virtual-snacking-summit.md for full rationale
        """
        assignments: list[Assignment] = []
        rotation = block_assignment.rotation_template

        if not rotation:
            logger.warning(
                f"BlockAssignment {block_assignment.id} has no rotation template"
            )
            return []

        # Get weekly patterns (keyed by day_of_week, time_of_day, week_number)
        patterns = self._get_weekly_patterns(rotation)

        # Determine if this rotation includes weekends
        includes_weekends = rotation.includes_weekend_work

        # Track consecutive work days for 1-in-7 rule
        consecutive_days = 0
        last_day_off = None

        current_date = start_date
        day_index = 0

        while current_date <= end_date:
            day_of_week = current_date.isoweekday() % 7  # 0=Sun, 1=Mon, ..., 6=Sat
            week_number = (day_index // 7) + 1  # 1-4

            # Check if person is absent this day
            is_absent = self._is_person_absent(
                block_assignment.resident_id,
                current_date,
            )

            # Check if weekend and rotation doesn't include weekends
            is_weekend = day_of_week in (0, 6)  # Sunday or Saturday
            skip_weekend = is_weekend and not includes_weekends

            # Check if holiday and rotation doesn't include weekend/holiday work
            # Rotations that include weekends (FMIT, NF) also cover holidays
            am_block = self._block_cache.get((current_date, "AM"))
            is_holiday = am_block.is_holiday if am_block else False
            skip_holiday = is_holiday and not includes_weekends

            # Apply 1-in-7 rule: force day off if 6 consecutive days worked
            force_day_off = False
            if apply_one_in_seven and consecutive_days >= 6:
                force_day_off = True
                last_day_off = current_date

            # ╔══════════════════════════════════════════════════════════════════╗
            # ║  ACGME 1-in-7 RULE - PAUSE BEHAVIOR (DO NOT MODIFY)              ║
            # ║                                                                  ║
            # ║  Absence: Counter HOLDS (doesn't reset) - this is INTENTIONAL    ║
            # ║  Scheduled off: Counter RESETS to 0                              ║
            # ║                                                                  ║
            # ║  Rationale: Leave ≠ day off. Schedule must provide 1-in-7       ║
            # ║  independent of leave. Approved by physician 2026-01-11.         ║
            # ║                                                                  ║
            # ║  CODEX P2 REJECTED: "Reset on absence" is WRONG.                 ║
            # ╚══════════════════════════════════════════════════════════════════╝
            if is_absent or skip_weekend or skip_holiday or force_day_off:
                # 56-ASSIGNMENT RULE: Create placeholder assignments instead of skipping
                self._create_absence_assignments(
                    assignments,
                    block_assignment,
                    current_date,
                    schedule_run_id,
                    created_by,
                    is_absent=is_absent,
                    is_weekend=skip_weekend,
                    is_holiday=skip_holiday,
                    is_day_off=force_day_off,
                )

                if (
                    not is_absent and not skip_holiday
                ):  # PAUSE: Only reset for SCHEDULED day off
                    consecutive_days = 0
                    last_day_off = current_date
                # Absence: counter HOLDS (no reset) - correct ACGME interpretation
                current_date += timedelta(days=1)
                day_index += 1
                continue

            # Get activity for AM slot
            am_activity = self._get_slot_activity(
                patterns, day_of_week, "AM", week_number
            )
            if am_activity and not self._is_person_absent_slot(
                block_assignment.resident_id, current_date, "AM"
            ):
                am_block = self._block_cache.get((current_date, "AM"))
                if am_block:
                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=rotation.id,
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

            # Get activity for PM slot
            pm_activity = self._get_slot_activity(
                patterns, day_of_week, "PM", week_number
            )
            if pm_activity and not self._is_person_absent_slot(
                block_assignment.resident_id, current_date, "PM"
            ):
                pm_block = self._block_cache.get((current_date, "PM"))
                if pm_block:
                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=rotation.id,
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

            # Increment consecutive days if any slot assigned
            if am_activity or pm_activity:
                consecutive_days += 1
            else:
                consecutive_days = 0

            current_date += timedelta(days=1)
            day_index += 1

        return assignments

    def _get_weekly_patterns(
        self,
        rotation: RotationTemplate,
    ) -> dict[tuple[int, str, int | None], WeeklyPattern]:
        """
        Get weekly patterns indexed by (day_of_week, time_of_day, week_number).

        Weekly patterns define EXCEPTIONS to the default rotation activity.
        For example, FMIT-R is "inpatient" by default, with "lecture" on Wed PM.

        Returns a dict where:
        - Explicit patterns from weekly_patterns table override defaults
        - Missing slots use the rotation's activity_type as default
        """
        patterns: dict[tuple[int, str, int | None], WeeklyPattern] = {}

        # First, generate defaults for ALL weekday slots based on activity_type
        # The rotation's main activity applies unless overridden
        default_activity = rotation.activity_type or "clinic"

        # Determine which days to include
        if rotation.includes_weekend_work:
            days_to_include = range(0, 7)  # Sun-Sat
        else:
            days_to_include = range(1, 6)  # Mon-Fri

        for day in days_to_include:
            for time in ["AM", "PM"]:
                patterns[(day, time, None)] = self._create_default_pattern(
                    rotation, day, time, default_activity
                )

        # Now overlay any explicit patterns from the database
        # These override the defaults for specific slots
        if rotation.weekly_patterns:
            for pattern in rotation.weekly_patterns:
                key = (pattern.day_of_week, pattern.time_of_day, pattern.week_number)
                patterns[key] = pattern

        return patterns

    def _create_default_pattern(
        self,
        rotation: RotationTemplate,
        day_of_week: int,
        time_of_day: str,
        activity_type: str,
    ) -> WeeklyPattern:
        """Create a default WeeklyPattern for rotations without explicit patterns."""
        # Note: This creates an in-memory pattern, not saved to DB
        pattern = WeeklyPattern()
        pattern.rotation_template_id = rotation.id
        pattern.day_of_week = day_of_week
        pattern.time_of_day = time_of_day
        pattern.week_number = None  # Applies to all weeks
        pattern.activity_type = activity_type
        pattern.is_protected = False
        return pattern

    def _get_slot_activity(
        self,
        patterns: dict[tuple[int, str, int | None], WeeklyPattern],
        day_of_week: int,
        time_of_day: str,
        week_number: int,
    ) -> WeeklyPattern | None:
        """
        Get the activity for a specific slot.

        Checks week-specific pattern first, then falls back to all-weeks pattern.
        """
        # First try week-specific pattern
        key = (day_of_week, time_of_day, week_number)
        if key in patterns:
            return patterns[key]

        # Fall back to all-weeks pattern (week_number=None)
        key = (day_of_week, time_of_day, None)
        return patterns.get(key)

    def _is_person_absent(self, person_id: UUID, check_date: date) -> bool:
        """Check if person is absent for the entire day."""
        absences = self._absence_cache.get(person_id, [])
        for absence in absences:
            if absence.start_date <= check_date <= absence.end_date:
                if absence.should_block_assignment:
                    return True
        return False

    def _is_person_absent_slot(
        self,
        person_id: UUID,
        check_date: date,
        time_of_day: str,
    ) -> bool:
        """Check if person is absent for a specific slot (partial absence)."""
        absences = self._absence_cache.get(person_id, [])
        for absence in absences:
            if absence.start_date <= check_date <= absence.end_date:
                # Check for partial absence (AM only or PM only)
                if hasattr(absence, "time_of_day") and absence.time_of_day:
                    if absence.time_of_day == time_of_day:
                        return True
                elif absence.should_block_assignment:
                    return True
        return False

    def _create_absence_assignments(
        self,
        assignments: list[Assignment],
        block_assignment: BlockAssignment,
        current_date: date,
        schedule_run_id: UUID | None,
        created_by: str,
        is_absent: bool,
        is_weekend: bool,
        is_holiday: bool,
        is_day_off: bool,
    ) -> None:
        """Create AM and PM assignments for absence/weekend/holiday/day-off days.

        56-ASSIGNMENT RULE IMPLEMENTATION
        =================================
        Instead of skipping days (which creates gaps), we now create placeholder
        assignments using absence rotation templates. This ensures every person
        has exactly 56 assignments per block, making gap detection trivial:
        - 56 assignments = complete schedule
        - <56 assignments = gap detected

        The placeholder templates are:
        - W-AM, W-PM: Weekend (rotation doesn't include weekend work)
        - LV-AM, LV-PM: Leave/absence (blocking absence)
        - HOL-AM, HOL-PM: Federal holiday (rotation doesn't include holiday work)
        - OFF-AM, OFF-PM: Day off (1-in-7 rule forced day)

        Args:
            assignments: List to append new assignments to
            block_assignment: The BlockAssignment being expanded
            current_date: The date for these assignments
            schedule_run_id: Provenance tracking ID
            created_by: Audit field
            is_absent: True if person has blocking absence
            is_weekend: True if weekend and rotation excludes weekends
            is_holiday: True if holiday and rotation excludes holidays
            is_day_off: True if 1-in-7 rule forces day off
        """
        # Determine which absence template to use (priority order)
        if is_absent:
            am_abbrev, pm_abbrev = "LV-AM", "LV-PM"
        elif is_weekend:
            am_abbrev, pm_abbrev = "W-AM", "W-PM"
        elif is_holiday:
            am_abbrev, pm_abbrev = "HOL-AM", "HOL-PM"
        elif is_day_off:
            am_abbrev, pm_abbrev = "OFF-AM", "OFF-PM"
        else:
            return  # Should never happen

        # Create AM assignment
        am_template = self._get_absence_template(am_abbrev)
        am_block = self._block_cache.get((current_date, "AM"))
        if am_template and am_block:
            assignments.append(
                Assignment(
                    block_id=am_block.id,
                    person_id=block_assignment.resident_id,
                    rotation_template_id=am_template.id,
                    role="primary",
                    schedule_run_id=schedule_run_id,
                    created_by=created_by,
                )
            )
        elif not am_template:
            logger.warning(f"Missing absence template: {am_abbrev}")

        # Create PM assignment
        pm_template = self._get_absence_template(pm_abbrev)
        pm_block = self._block_cache.get((current_date, "PM"))
        if pm_template and pm_block:
            assignments.append(
                Assignment(
                    block_id=pm_block.id,
                    person_id=block_assignment.resident_id,
                    rotation_template_id=pm_template.id,
                    role="primary",
                    schedule_run_id=schedule_run_id,
                    created_by=created_by,
                )
            )
        elif not pm_template:
            logger.warning(f"Missing absence template: {pm_abbrev}")
