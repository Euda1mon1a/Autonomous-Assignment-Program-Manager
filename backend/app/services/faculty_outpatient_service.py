"""
Faculty Outpatient Assignment Service.

Generates faculty PRIMARY clinic assignments and SUPERVISION assignments
for a specified block. This service handles the generation of:

1. Faculty clinic sessions - Based on role limits (PD=0, APD=2, Core=4/week)
2. Faculty supervision - ACGME-compliant supervision of resident assignments

Flow:
    1. Load faculty available for the block (not on FMIT, leave, etc.)
    2. Load faculty constraints (role limits, day availability, primary duty)
    3. Get outpatient templates available for faculty
    4. Assign faculty to clinic slots respecting constraints
    5. Assign faculty supervision based on resident assignments
    6. Validate and return results

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for full details.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from math import ceil
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import FacultyRole, Person
from app.models.rotation_template import RotationTemplate

if TYPE_CHECKING:
    pass


@dataclass
class FacultyAssignmentSummary:
    """Summary of assignments for a single faculty member."""

    faculty_id: UUID
    faculty_name: str
    faculty_role: str
    clinic_sessions: int
    supervision_sessions: int
    total_sessions: int
    by_week: dict[str, int] = field(default_factory=dict)


@dataclass
class FacultyOutpatientResult:
    """Result of faculty outpatient generation."""

    success: bool
    message: str
    block_number: int
    block_start: date
    block_end: date
    total_clinic_assignments: int
    total_supervision_assignments: int
    cleared_count: int
    faculty_summaries: list[FacultyAssignmentSummary] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class FacultyOutpatientAssignmentService:
    """
    Generate faculty PRIMARY clinic and SUPERVISION assignments for a block.

    This service is distinct from the main scheduling engine:
    - Engine: Optimizes RESIDENT outpatient assignments via solver
    - This service: Assigns FACULTY clinic sessions and supervision

    Role-based clinic limits (per week):
        - PD: 0 (full admin)
        - Dept Chief: 1
        - APD/OIC: 2 (flexible within block)
        - Sports Med: 0 regular (4 SM clinic instead)
        - Core: 4 (16/block max)

    ACGME Supervision Ratios:
        - PGY-1: 1 faculty : 2 residents
        - PGY-2/3: 1 faculty : 4 residents
    """

    def __init__(self, db: Session):
        """Initialize the faculty outpatient service."""
        self.db = db

    def generate_faculty_outpatient_assignments(
        self,
        block_number: int,
        regenerate: bool = True,
        include_clinic: bool = True,
        include_supervision: bool = True,
    ) -> FacultyOutpatientResult:
        """
        Generate faculty outpatient assignments for a block.

        Args:
            block_number: Block number (1-13 for academic year)
            regenerate: If True, clear existing faculty outpatient first
            include_clinic: Generate faculty primary clinic assignments
            include_supervision: Generate faculty supervision assignments

        Returns:
            FacultyOutpatientResult with assignment details and metrics
        """
        warnings: list[str] = []
        errors: list[str] = []

        # Step 1: Get block date range
        block_start, block_end = self._get_block_dates(block_number)
        if not block_start:
            return FacultyOutpatientResult(
                success=False,
                message=f"Could not determine dates for block {block_number}",
                block_number=block_number,
                block_start=date.today(),
                block_end=date.today(),
                total_clinic_assignments=0,
                total_supervision_assignments=0,
                cleared_count=0,
                errors=["Invalid block number or no blocks found"],
            )

        # Step 2: Get blocks for this period
        blocks = self._get_blocks_for_period(block_start, block_end)
        if not blocks:
            return FacultyOutpatientResult(
                success=False,
                message=f"No blocks found for block {block_number}",
                block_number=block_number,
                block_start=block_start,
                block_end=block_end,
                total_clinic_assignments=0,
                total_supervision_assignments=0,
                cleared_count=0,
                errors=["No blocks exist for this period"],
            )

        # Step 3: Clear existing faculty outpatient assignments if regenerating
        cleared_count = 0
        if regenerate:
            cleared_count = self._clear_existing_faculty_outpatient(
                block_start, block_end
            )

        # Step 4: Get available faculty (not on FMIT, leave, etc.)
        available_faculty = self._get_available_faculty(block_start, block_end)
        if not available_faculty:
            warnings.append("No available faculty found for this block")

        # Step 5: Get outpatient templates
        outpatient_templates = self._get_outpatient_templates()
        if not outpatient_templates:
            warnings.append("No outpatient templates found")

        # Step 6: Generate clinic assignments
        clinic_assignments = []
        if include_clinic and available_faculty and outpatient_templates:
            clinic_assignments = self._generate_clinic_assignments(
                available_faculty, blocks, outpatient_templates
            )

        # Step 7: Generate supervision assignments
        supervision_assignments = []
        if include_supervision and available_faculty:
            supervision_assignments = self._generate_supervision_assignments(
                available_faculty, blocks, clinic_assignments
            )

        # Step 8: Commit all assignments
        all_assignments = clinic_assignments + supervision_assignments
        for assignment in all_assignments:
            self.db.add(assignment)
        self.db.commit()

        # Step 9: Build faculty summaries
        faculty_summaries = self._build_faculty_summaries(
            available_faculty, clinic_assignments, supervision_assignments
        )

        total_clinic = len(clinic_assignments)
        total_supervision = len(supervision_assignments)

        return FacultyOutpatientResult(
            success=True,
            message=f"Generated {total_clinic} clinic + {total_supervision} supervision assignments",
            block_number=block_number,
            block_start=block_start,
            block_end=block_end,
            total_clinic_assignments=total_clinic,
            total_supervision_assignments=total_supervision,
            cleared_count=cleared_count,
            faculty_summaries=faculty_summaries,
            warnings=warnings,
            errors=errors,
        )

    def _get_block_dates(self, block_number: int) -> tuple[date | None, date | None]:
        """
        Get start and end dates for a block number.

        Academic year starts first Thursday on or after July 1.
        Each block is 28 days.
        """
        # Query the database for blocks with this block_number
        block = (
            self.db.query(Block)
            .filter(Block.block_number == block_number)
            .order_by(Block.date.asc())
            .first()
        )

        if not block:
            return None, None

        block_start = block.date

        # Find last block with this block_number
        last_block = (
            self.db.query(Block)
            .filter(Block.block_number == block_number)
            .order_by(Block.date.desc())
            .first()
        )

        block_end = last_block.date if last_block else block_start + timedelta(days=27)

        return block_start, block_end

    def _get_blocks_for_period(
        self, start_date: date, end_date: date
    ) -> list[Block]:
        """Get all blocks in the date range."""
        return (
            self.db.query(Block)
            .filter(
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .order_by(Block.date, Block.time_of_day)
            .all()
        )

    def _clear_existing_faculty_outpatient(
        self, block_start: date, block_end: date
    ) -> int:
        """
        Clear existing faculty outpatient assignments for the block.

        Only clears:
        - Faculty assignments (not resident)
        - Outpatient/clinic activity types
        - Primary role (not supervision - that will be regenerated anyway)
        """
        # Get faculty IDs
        faculty_ids = [
            f.id
            for f in self.db.query(Person.id).filter(Person.type == "faculty").all()
        ]

        # Get outpatient template IDs
        outpatient_template_ids = [
            t.id
            for t in self.db.query(RotationTemplate.id)
            .filter(RotationTemplate.activity_type.in_(["clinic", "outpatient"]))
            .all()
        ]

        if not faculty_ids or not outpatient_template_ids:
            return 0

        # Get block IDs in range
        block_ids = [
            b.id
            for b in self.db.query(Block.id)
            .filter(Block.date >= block_start, Block.date <= block_end)
            .all()
        ]

        if not block_ids:
            return 0

        # Delete matching assignments
        deleted = (
            self.db.query(Assignment)
            .filter(
                Assignment.person_id.in_(faculty_ids),
                Assignment.block_id.in_(block_ids),
                Assignment.rotation_template_id.in_(outpatient_template_ids),
            )
            .delete(synchronize_session="fetch")
        )

        return deleted

    def _get_available_faculty(
        self, block_start: date, block_end: date
    ) -> list[Person]:
        """
        Get faculty available for outpatient during the block.

        Excludes faculty who have:
        - FMIT assignments during this period
        - Blocking absences (leave, TDY, etc.)
        - ADJUNCT role (not auto-scheduled, can be pre-loaded to FMIT manually)
        """
        all_faculty = (
            self.db.query(Person)
            .filter(Person.type == "faculty")
            .all()
        )

        # Get faculty with FMIT during this period
        fmit_templates = (
            self.db.query(RotationTemplate)
            .filter(
                or_(
                    RotationTemplate.name.ilike("%FMIT%"),
                    RotationTemplate.activity_type == "inpatient",
                )
            )
            .all()
        )
        fmit_template_ids = [t.id for t in fmit_templates]

        fmit_faculty_ids = set()
        if fmit_template_ids:
            fmit_assignments = (
                self.db.query(Assignment)
                .join(Block, Assignment.block_id == Block.id)
                .filter(
                    Block.date >= block_start,
                    Block.date <= block_end,
                    Assignment.rotation_template_id.in_(fmit_template_ids),
                )
                .all()
            )
            fmit_faculty_ids = {a.person_id for a in fmit_assignments}

        # Get faculty with blocking absences
        absent_faculty_ids = set()
        absences = (
            self.db.query(Absence)
            .filter(
                Absence.start_date <= block_end,
                Absence.end_date >= block_start,
                Absence.is_blocking == True,  # noqa: E712
            )
            .all()
        )
        absent_faculty_ids = {a.person_id for a in absences}

        # Filter to available faculty
        # Exclude faculty on FMIT/absences AND adjunct faculty (not auto-scheduled)
        excluded = fmit_faculty_ids | absent_faculty_ids
        available = [
            f for f in all_faculty
            if f.id not in excluded and f.role_enum != FacultyRole.ADJUNCT
        ]

        return available

    def _get_outpatient_templates(self) -> list[RotationTemplate]:
        """Get rotation templates for outpatient/clinic activities."""
        return (
            self.db.query(RotationTemplate)
            .filter(RotationTemplate.activity_type.in_(["clinic", "outpatient"]))
            .all()
        )

    def _generate_clinic_assignments(
        self,
        faculty: list[Person],
        blocks: list[Block],
        templates: list[RotationTemplate],
    ) -> list[Assignment]:
        """
        Generate faculty PRIMARY clinic assignments.

        Assigns faculty to clinic blocks respecting:
        - Role-based weekly limits (PD=0, APD=2, Core=4)
        - Day availability
        - Load balancing across faculty
        """
        assignments = []
        faculty_weekly_counts: dict[UUID, dict[date, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Filter to workday blocks only (no weekends)
        workday_blocks = [b for b in blocks if not b.is_weekend]

        # Get FM Clinic template (primary clinic assignment target)
        fm_clinic_template = next(
            (t for t in templates if "FM" in t.name.upper() or "CLINIC" in t.name.upper()),
            templates[0] if templates else None,
        )

        if not fm_clinic_template:
            return []

        # Sort blocks by date/time
        workday_blocks.sort(key=lambda b: (b.date, 0 if b.time_of_day == "AM" else 1))

        for block in workday_blocks:
            week_start = self._get_week_start(block.date)

            # Find faculty who can work this block
            candidates = []
            for f in faculty:
                weekly_limit = getattr(f, "weekly_clinic_limit", 4)
                current_count = faculty_weekly_counts[f.id][week_start]

                # Skip if at weekly limit
                if current_count >= weekly_limit:
                    continue

                # Skip Sports Med faculty for regular clinic
                if hasattr(f, "faculty_role") and f.faculty_role == FacultyRole.SPORTS_MED:
                    continue

                # Score by load (fewer = higher priority)
                total_load = sum(faculty_weekly_counts[f.id].values())
                candidates.append((f, total_load))

            if not candidates:
                continue

            # Sort by load (least-loaded first)
            candidates.sort(key=lambda x: x[1])

            # Assign one faculty to this block
            selected_faculty, _ = candidates[0]

            assignment = Assignment(
                block_id=block.id,
                person_id=selected_faculty.id,
                rotation_template_id=fm_clinic_template.id,
                role="primary",
            )
            assignments.append(assignment)
            faculty_weekly_counts[selected_faculty.id][week_start] += 1

        return assignments

    def _generate_supervision_assignments(
        self,
        faculty: list[Person],
        blocks: list[Block],
        clinic_assignments: list[Assignment] | None = None,
    ) -> list[Assignment]:
        """
        Generate faculty SUPERVISION assignments for resident blocks.

        ACGME Supervision Ratios:
        - PGY-1: 1 faculty : 2 residents
        - PGY-2/3: 1 faculty : 4 residents

        Algorithm:
        1. Find all resident assignments in this block range
        2. Group by block
        3. Calculate required faculty count
        4. Assign least-loaded available faculty (excluding those already assigned)
        """
        assignments = []
        faculty_load: dict[UUID, int] = {f.id: 0 for f in faculty}

        # Build set of (block_id, person_id) from new clinic assignments
        # These faculty are already assigned to these blocks
        new_assignments_set: set[tuple[UUID, UUID]] = set()
        if clinic_assignments:
            for ca in clinic_assignments:
                new_assignments_set.add((ca.block_id, ca.person_id))

        # Get all resident assignments in this period
        block_ids = [b.id for b in blocks]

        if not block_ids:
            return []

        # Get outpatient templates (what residents are assigned to)
        outpatient_templates = self._get_outpatient_templates()
        outpatient_template_ids = [t.id for t in outpatient_templates]

        if not outpatient_template_ids:
            return []

        resident_assignments = (
            self.db.query(Assignment)
            .join(Person, Assignment.person_id == Person.id)
            .filter(
                Assignment.block_id.in_(block_ids),
                Assignment.rotation_template_id.in_(outpatient_template_ids),
                Person.type == "resident",
            )
            .all()
        )

        if not resident_assignments:
            return []

        # Group by block
        assignments_by_block: dict[UUID, list[Assignment]] = defaultdict(list)
        for a in resident_assignments:
            assignments_by_block[a.block_id].append(a)

        # Get person lookup for PGY levels
        resident_ids = [a.person_id for a in resident_assignments]
        residents = (
            self.db.query(Person)
            .filter(Person.id.in_(resident_ids))
            .all()
        )
        resident_lookup = {r.id: r for r in residents}

        # For each block with residents, assign supervising faculty
        for block_id, block_assignments in assignments_by_block.items():
            # Count PGY levels
            pgy1_count = sum(
                1
                for a in block_assignments
                if resident_lookup.get(a.person_id)
                and resident_lookup[a.person_id].pgy_level == 1
            )
            other_count = len(block_assignments) - pgy1_count

            # Calculate required faculty using fractional supervision load
            # PGY-1: 0.5 supervision load each (1:2 ratio)
            # PGY-2/3: 0.25 supervision load each (1:4 ratio)
            # Sum loads THEN ceiling to avoid overcounting in mixed PGY scenarios
            supervision_load = (pgy1_count * 0.5) + (other_count * 0.25)
            required = ceil(supervision_load) if supervision_load > 0 else 0
            required = max(1, required) if block_assignments else 0

            if required == 0:
                continue

            # Get a rotation template from the resident assignments
            template_id = block_assignments[0].rotation_template_id

            # Find available faculty (not already assigned to this block)
            existing_faculty_in_block = set()
            existing_assignments = (
                self.db.query(Assignment)
                .filter(Assignment.block_id == block_id)
                .all()
            )
            for ea in existing_assignments:
                existing_faculty_in_block.add(ea.person_id)

            # Also exclude faculty assigned via new clinic assignments (not yet committed)
            for fid in [
                pid for bid, pid in new_assignments_set if bid == block_id
            ]:
                existing_faculty_in_block.add(fid)

            available = [
                f for f in faculty
                if f.id not in existing_faculty_in_block
            ]

            if not available:
                continue

            # Sort by load
            available.sort(key=lambda f: faculty_load.get(f.id, 0))

            # Assign required number of faculty
            for i in range(min(required, len(available))):
                selected = available[i]
                assignment = Assignment(
                    block_id=block_id,
                    person_id=selected.id,
                    rotation_template_id=template_id,
                    role="supervising",
                )
                assignments.append(assignment)
                faculty_load[selected.id] = faculty_load.get(selected.id, 0) + 1

        return assignments

    def _get_week_start(self, d: date) -> date:
        """Get Monday of the week containing the given date."""
        return d - timedelta(days=d.weekday())

    def _build_faculty_summaries(
        self,
        faculty: list[Person],
        clinic_assignments: list[Assignment],
        supervision_assignments: list[Assignment],
    ) -> list[FacultyAssignmentSummary]:
        """Build summary statistics for each faculty member."""
        summaries = []

        # Build lookup
        clinic_by_faculty: dict[UUID, int] = defaultdict(int)
        supervision_by_faculty: dict[UUID, int] = defaultdict(int)

        for a in clinic_assignments:
            clinic_by_faculty[a.person_id] += 1

        for a in supervision_assignments:
            supervision_by_faculty[a.person_id] += 1

        for f in faculty:
            clinic_count = clinic_by_faculty.get(f.id, 0)
            supervision_count = supervision_by_faculty.get(f.id, 0)

            if clinic_count > 0 or supervision_count > 0:
                summaries.append(
                    FacultyAssignmentSummary(
                        faculty_id=f.id,
                        faculty_name=f.name,
                        faculty_role=str(f.faculty_role) if hasattr(f, "faculty_role") and f.faculty_role else "unknown",
                        clinic_sessions=clinic_count,
                        supervision_sessions=supervision_count,
                        total_sessions=clinic_count + supervision_count,
                    )
                )

        # Sort by total sessions descending
        summaries.sort(key=lambda s: s.total_sessions, reverse=True)

        return summaries
