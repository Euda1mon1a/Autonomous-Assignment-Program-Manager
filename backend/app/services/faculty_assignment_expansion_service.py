"""
Faculty Assignment Expansion Service.

Ensures every faculty member has exactly 56 assignments per block (28 days × 2 half-days).
Unlike residents who have BlockAssignments expanded, faculty assignments are created post-hoc
based on ACGME supervision ratios. This service fills remaining empty slots with placeholders.

Key differences from resident expansion:
- No BlockAssignment source - uses Person.type='faculty'
- No 1-in-7 day-off rule (ACGME requirement for residents only)
- Existing assignments (FMIT, clinic, supervision) are preserved
- Empty slots get GME (admin time) placeholder, not rotation activity
- Weekends always get W-AM/W-PM (faculty don't work weekends)
- Absences get LV-AM/LV-PM

PERSEC-compliant logging (no PII).
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


class FacultyAssignmentExpansionService:
    """
    Service to ensure all faculty have 56 assignments per block.

    Workflow:
    1. Load all faculty members
    2. Load existing assignments for the block
    3. For each faculty, for each of 56 slots:
       - If existing assignment → skip
       - If blocking absence → LV-AM/LV-PM
       - If weekend → W-AM/W-PM
       - Else → GME-AM/GME-PM (admin placeholder)
    4. Return list of new Assignment objects (not committed)
    """

    def __init__(self, db: Session):
        self.db = db
        self._absence_cache: dict[UUID, list[Absence]] = {}
        self._block_cache: dict[tuple[date, str], Block] = {}
        self._existing_assignments: dict[tuple[UUID, UUID], Assignment] = {}
        self._placeholder_templates: dict[str, RotationTemplate] = {}

    def fill_faculty_assignments(
        self,
        block_number: int,
        academic_year: int,
        schedule_run_id: UUID | None = None,
        created_by: str = "faculty_expansion_service",
    ) -> list[Assignment]:
        """
        Fill all 56 slots for each faculty member.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            schedule_run_id: Optional provenance tracking ID
            created_by: Audit field for who created assignments

        Returns:
            List of new Assignment objects to fill gaps (not yet committed to DB)
        """
        logger.info(
            f"Filling faculty assignments for block {block_number} AY {academic_year}"
        )

        # Get block date range
        block_dates = get_block_dates(block_number, academic_year)
        start_date, end_date = block_dates.start_date, block_dates.end_date
        logger.info(f"Block {block_number} dates: {start_date} to {end_date}")

        # Load all faculty
        faculty = self._load_faculty()
        logger.info(f"Found {len(faculty)} faculty members")

        if not faculty:
            return []

        # Pre-load data
        faculty_ids = [f.id for f in faculty]
        self._preload_blocks(start_date, end_date)
        self._preload_absences(faculty_ids, start_date, end_date)
        self._preload_existing_assignments(faculty_ids, start_date, end_date)
        self._preload_placeholder_templates()

        # Fill assignments for each faculty
        all_new_assignments: list[Assignment] = []
        for person in faculty:
            new_assignments = self._fill_single_faculty(
                person,
                start_date,
                end_date,
                schedule_run_id,
                created_by,
            )
            all_new_assignments.extend(new_assignments)

        logger.info(f"Created {len(all_new_assignments)} new faculty assignments")
        return all_new_assignments

    def _load_faculty(self) -> list[Person]:
        """Load all active faculty members."""
        stmt = (
            select(Person)
            .where(Person.type == "faculty")
            .where(Person.is_active == True)  # noqa: E712
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
        """Pre-load absences for all faculty in the date range."""
        if not person_ids:
            return

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
        logger.info(f"Pre-loaded absences for {len(self._absence_cache)} faculty")

    def _preload_existing_assignments(
        self,
        person_ids: list[UUID],
        start_date: date,
        end_date: date,
    ) -> None:
        """Pre-load existing assignments for all faculty in the date range."""
        if not person_ids:
            return

        stmt = (
            select(Assignment)
            .join(Block)
            .where(Assignment.person_id.in_(person_ids))
            .where(Block.date >= start_date)
            .where(Block.date <= end_date)
            .options(selectinload(Assignment.block))
        )
        result = self.db.execute(stmt)
        for assignment in result.scalars().all():
            # Key by (person_id, block_id) for O(1) lookup
            key = (assignment.person_id, assignment.block_id)
            self._existing_assignments[key] = assignment
        logger.info(
            f"Pre-loaded {len(self._existing_assignments)} existing faculty assignments"
        )

    def _preload_placeholder_templates(self) -> None:
        """Pre-load placeholder rotation templates (W, LV, GME)."""
        if self._placeholder_templates:
            return  # Already loaded

        # Templates needed for faculty gap filling
        template_abbrevs = [
            "W-AM",
            "W-PM",  # Weekend
            "LV-AM",
            "LV-PM",  # Leave/absence
            "GME-AM",
            "GME-PM",  # Admin time (default for empty slots)
        ]

        stmt = select(RotationTemplate).where(
            RotationTemplate.abbreviation.in_(template_abbrevs)
        )
        for rt in self.db.execute(stmt).scalars():
            self._placeholder_templates[rt.abbreviation] = rt

        logger.info(
            f"Pre-loaded {len(self._placeholder_templates)} placeholder templates"
        )

        # Warn if any templates missing
        for abbrev in template_abbrevs:
            if abbrev not in self._placeholder_templates:
                logger.warning(f"Missing placeholder template: {abbrev}")

    def _get_placeholder_template(self, abbrev: str) -> RotationTemplate | None:
        """Get placeholder rotation template by abbreviation (cached)."""
        return self._placeholder_templates.get(abbrev)

    def _fill_single_faculty(
        self,
        person: Person,
        start_date: date,
        end_date: date,
        schedule_run_id: UUID | None,
        created_by: str,
    ) -> list[Assignment]:
        """Fill all 56 slots for a single faculty member."""
        new_assignments: list[Assignment] = []
        current_date = start_date

        while current_date <= end_date:
            day_of_week = current_date.isoweekday() % 7  # 0=Sun, 1=Mon, ..., 6=Sat
            is_weekend = day_of_week in (0, 6)  # Sunday or Saturday

            # Check if person has blocking absence
            is_absent = self._is_person_absent(person.id, current_date)

            # Process AM slot
            am_assignment = self._fill_slot(
                person,
                current_date,
                "AM",
                is_weekend,
                is_absent,
                schedule_run_id,
                created_by,
            )
            if am_assignment:
                new_assignments.append(am_assignment)

            # Process PM slot
            pm_assignment = self._fill_slot(
                person,
                current_date,
                "PM",
                is_weekend,
                is_absent,
                schedule_run_id,
                created_by,
            )
            if pm_assignment:
                new_assignments.append(pm_assignment)

            current_date += timedelta(days=1)

        return new_assignments

    def _fill_slot(
        self,
        person: Person,
        slot_date: date,
        time_of_day: str,
        is_weekend: bool,
        is_absent: bool,
        schedule_run_id: UUID | None,
        created_by: str,
    ) -> Assignment | None:
        """
        Fill a single slot for a faculty member if empty.

        Returns None if slot already has an assignment.
        """
        block = self._block_cache.get((slot_date, time_of_day))
        if not block:
            return None

        # Check if slot already has an assignment
        key = (person.id, block.id)
        if key in self._existing_assignments:
            return None  # Already assigned, don't overwrite

        # Check for slot-specific absence (partial day)
        slot_absent = self._is_person_absent_slot(person.id, slot_date, time_of_day)

        # Determine which template to use
        if is_absent or slot_absent:
            template_abbrev = f"LV-{time_of_day}"
        elif is_weekend:
            template_abbrev = f"W-{time_of_day}"
        else:
            template_abbrev = f"GME-{time_of_day}"

        template = self._get_placeholder_template(template_abbrev)
        if not template:
            logger.warning(f"Missing template {template_abbrev}, skipping slot")
            return None

        return Assignment(
            block_id=block.id,
            person_id=person.id,
            rotation_template_id=template.id,
            role="primary",
            schedule_run_id=schedule_run_id,
            created_by=created_by,
        )

    def _is_person_absent(self, person_id: UUID, check_date: date) -> bool:
        """Check if person has a blocking absence for the entire day."""
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
