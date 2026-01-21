"""
Faculty Assignment Expansion Service.

Ensures every faculty member has exactly 56 half-day assignments per block (28 days × 2).
Creates HalfDayAssignment records with source='template' (lowest priority) for empty slots.

Key differences from resident expansion:
- No BlockAssignment source - uses Person.type='faculty'
- No 1-in-7 day-off rule (ACGME requirement for residents only)
- Existing assignments (preload, manual) are preserved
- Empty slots get admin placeholder (GME/DFM based on faculty.admin_type)
- Weekends always get W activity
- Holidays always get HOL activity
- Absences get LV activity

Source priority (respected):
1. preload - FMIT, call, absences - NEVER overwritten
2. manual - Human override
3. solver - Computed by optimizer
4. template - Default from this service (lowest priority)

PERSEC-compliant logging (no PII).
"""

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
from app.models.person import Person
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


class FacultyAssignmentExpansionService:
    """
    Service to ensure all faculty have 56 half-day assignments per block.

    Workflow:
    1. Load all active faculty members (excluding adjuncts if specified)
    2. Load existing HalfDayAssignment records for the block
    3. For each faculty, for each of 56 slots:
       - If existing assignment → skip (preserve source priority)
       - If blocking absence → LV activity
       - If weekend → W activity
       - If holiday → HOL activity
       - Else → GME or DFM activity (based on faculty.admin_type)
    4. Return count of new HalfDayAssignment records created
    """

    # Activities cache (loaded once)
    _activity_cache: dict[str, Activity] = {}

    def __init__(self, db: Session):
        self.db = db
        self._absence_cache: dict[UUID, list[Absence]] = {}
        self._existing_slots: set[str] = set()  # Keys: "person_id_date_time"
        self._holiday_dates: set[date] = set()

    def fill_faculty_assignments(
        self,
        block_number: int,
        academic_year: int,
        exclude_adjuncts: bool = True,
    ) -> int:
        """
        Fill all 56 slots for each faculty member with HalfDayAssignment records.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            exclude_adjuncts: If True, skip adjunct faculty (default True)

        Returns:
            Count of new HalfDayAssignment records created
        """
        logger.info(
            f"Filling faculty half-day assignments for block {block_number} AY {academic_year}"
        )

        # Get block date range
        block_dates = get_block_dates(block_number, academic_year)
        start_date, end_date = block_dates.start_date, block_dates.end_date
        logger.info(f"Block {block_number} dates: {start_date} to {end_date}")

        # Load all faculty
        faculty = self._load_faculty(exclude_adjuncts)
        logger.info(f"Found {len(faculty)} faculty members")

        if not faculty:
            return 0

        # Pre-load data
        faculty_ids = [f.id for f in faculty]
        self._preload_activities()
        self._preload_absences(faculty_ids, start_date, end_date)
        self._preload_existing_assignments(faculty_ids, start_date, end_date)
        self._preload_holidays(start_date, end_date)

        # Fill assignments for each faculty
        total_created = 0
        for person in faculty:
            created = self._fill_single_faculty(
                person,
                start_date,
                end_date,
            )
            total_created += created

        logger.info(f"Created {total_created} new faculty half-day assignments")
        return total_created

    def _load_faculty(self, exclude_adjuncts: bool) -> list[Person]:
        """Load all faculty members.

        Note: faculty_role can be NULL for some faculty. The filter
        `!= 'adjunct'` in SQLAlchemy returns False for NULL values,
        so we use an explicit OR condition to include NULL rows.
        """
        stmt = select(Person).where(Person.type == "faculty")
        if exclude_adjuncts:
            # Adjuncts have faculty_role='adjunct'
            # Include NULL faculty_role (most faculty) - they are NOT adjuncts
            from sqlalchemy import or_

            stmt = stmt.where(
                or_(Person.faculty_role != "adjunct", Person.faculty_role.is_(None))
            )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def _preload_activities(self) -> None:
        """Pre-load activity records for faculty assignments."""
        if FacultyAssignmentExpansionService._activity_cache:
            return  # Already loaded (class-level cache)

        # Activities needed for faculty gap filling
        # Note: W, HOL, DEP are uppercase (from 20260120 migration)
        # LV-AM, LV-PM for leave (matches SyncPreloadService)
        # gme, dfm, sm_clinic are lowercase (from 20260109 migration)
        # sm_clinic is for Sports Medicine faculty (Tagawa has admin_type='SM')
        activity_codes = [
            "W",
            "HOL",
            "LV-AM",
            "LV-PM",
            "DEP",
            "gme",
            "dfm",
            "sm_clinic",
        ]

        stmt = select(Activity).where(Activity.code.in_(activity_codes))
        for activity in self.db.execute(stmt).scalars():
            FacultyAssignmentExpansionService._activity_cache[activity.code] = activity

        logger.info(
            f"Pre-loaded {len(FacultyAssignmentExpansionService._activity_cache)} "
            f"faculty activities"
        )

        # Warn if any activities missing
        for code in activity_codes:
            if code not in FacultyAssignmentExpansionService._activity_cache:
                logger.warning(f"Missing activity: {code}")

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
        """Pre-load existing HalfDayAssignment records for all faculty."""
        if not person_ids:
            return

        stmt = (
            select(HalfDayAssignment)
            .where(HalfDayAssignment.person_id.in_(person_ids))
            .where(HalfDayAssignment.date >= start_date)
            .where(HalfDayAssignment.date <= end_date)
        )
        result = self.db.execute(stmt)
        for hda in result.scalars().all():
            # Key by (person_id, date, time_of_day) for O(1) lookup
            key = f"{hda.person_id}_{hda.date.isoformat()}_{hda.time_of_day}"
            self._existing_slots.add(key)
        logger.info(
            f"Pre-loaded {len(self._existing_slots)} existing faculty half-day assignments"
        )

    def _preload_holidays(self, start_date: date, end_date: date) -> None:
        """Pre-load federal holidays and non-operational days from Block table.

        Uses Block.is_holiday and Block.operational_intent to identify
        dates that should get HOL activity instead of admin time.
        """
        from app.models.block import Block
        from app.models.day_type import OperationalIntent

        # Query blocks that are holidays or non-operational (DONSA, EO closure)
        stmt = select(Block.date).where(
            Block.date >= start_date,
            Block.date <= end_date,
            # Match holidays OR non-operational days
            (Block.is_holiday == True) | (Block.operational_intent == OperationalIntent.NON_OPERATIONAL),  # noqa: E712
        ).distinct()

        for row in self.db.execute(stmt):
            self._holiday_dates.add(row[0])

        logger.info(f"Pre-loaded {len(self._holiday_dates)} holiday/non-operational dates from blocks")

    def _get_activity(self, code: str) -> Activity | None:
        """Get activity by code (cached)."""
        return FacultyAssignmentExpansionService._activity_cache.get(code)

    def _fill_single_faculty(
        self,
        person: Person,
        start_date: date,
        end_date: date,
    ) -> int:
        """Fill all 56 slots for a single faculty member."""
        created_count = 0
        current_date = start_date

        # Get faculty's admin type (GME or DFM)
        admin_type = getattr(person, "admin_type", "GME") or "GME"

        while current_date <= end_date:
            day_of_week = current_date.isoweekday()  # 1=Mon, 7=Sun
            is_weekend = day_of_week in (6, 7)  # Saturday or Sunday

            # Check if person has blocking absence
            is_absent = self._is_person_absent(person.id, current_date)

            # Check if deployed
            is_deployed = self._is_person_deployed(person.id, current_date)

            # Check if holiday
            is_holiday = current_date in self._holiday_dates

            # Process AM slot
            am_created = self._fill_slot(
                person,
                current_date,
                "AM",
                is_weekend,
                is_absent,
                is_deployed,
                is_holiday,
                admin_type,
            )
            if am_created:
                created_count += 1

            # Process PM slot
            pm_created = self._fill_slot(
                person,
                current_date,
                "PM",
                is_weekend,
                is_absent,
                is_deployed,
                is_holiday,
                admin_type,
            )
            if pm_created:
                created_count += 1

            current_date += timedelta(days=1)

        return created_count

    def _fill_slot(
        self,
        person: Person,
        slot_date: date,
        time_of_day: str,
        is_weekend: bool,
        is_absent: bool,
        is_deployed: bool,
        is_holiday: bool,
        admin_type: str,
    ) -> bool:
        """
        Fill a single slot for a faculty member if empty.

        Returns True if a new HalfDayAssignment was created.
        """
        # Check if slot already has an assignment (any source)
        key = f"{person.id}_{slot_date.isoformat()}_{time_of_day}"
        if key in self._existing_slots:
            return False  # Already assigned, don't overwrite

        # Determine which activity to use (priority order)
        if is_deployed:
            activity_code = "DEP"
        elif is_absent:
            # LV-AM or LV-PM based on time of day
            activity_code = f"LV-{time_of_day}"
        elif is_weekend:
            activity_code = "W"
        elif is_holiday:
            activity_code = "HOL"
        else:
            # Default to admin time (gme, dfm, or sm_clinic based on faculty)
            # admin_type is stored uppercase ("GME", "DFM", "SM")
            # Activity codes: gme, dfm, sm_clinic (SM maps to sm_clinic)
            if admin_type and admin_type.upper() == "SM":
                activity_code = "sm_clinic"
            else:
                activity_code = admin_type.lower() if admin_type else "gme"

        activity = self._get_activity(activity_code)
        if not activity:
            logger.warning(f"Missing activity {activity_code}, skipping slot")
            return False

        # Create HalfDayAssignment with source='template' (lowest priority)
        half_day = HalfDayAssignment(
            person_id=person.id,
            date=slot_date,
            time_of_day=time_of_day,
            activity_id=activity.id,
            source=AssignmentSource.TEMPLATE.value,
        )
        self.db.add(half_day)

        # Add to existing slots to avoid duplicates
        self._existing_slots.add(key)

        return True

    def _is_person_absent(self, person_id: UUID, check_date: date) -> bool:
        """Check if person has a blocking absence for the date.

        Returns True for leave-type absences (vacation, sick, conference).
        Returns False for deployment-type absences (handled by _is_person_deployed).
        """
        # Deployment-type absences are handled separately (use DEP, not LV)
        deployed_absence_types = {"deployment", "tdy", "training", "military_duty"}

        absences = self._absence_cache.get(person_id, [])
        for absence in absences:
            if absence.start_date <= check_date <= absence.end_date:
                # Check if this is a deployment-type (handled separately)
                absence_type = getattr(absence, "absence_type", None)
                if absence_type in deployed_absence_types:
                    continue  # Handle in _is_person_deployed
                if getattr(absence, "should_block_assignment", True):
                    return True
        return False

    def _is_person_deployed(self, person_id: UUID, check_date: date) -> bool:
        """Check if person is deployed on the date.

        Deployment-like absences that should use DEP activity instead of LV:
        - deployment: Actual deployment (e.g., Colgan)
        - tdy: Temporary duty (off-site, e.g., Hilo)
        - training: Training duty
        - military_duty: Other military obligations
        """
        # Absence types that count as "deployed" (use DEP activity)
        deployed_absence_types = {"deployment", "tdy", "training", "military_duty"}

        absences = self._absence_cache.get(person_id, [])
        for absence in absences:
            if absence.start_date <= check_date <= absence.end_date:
                absence_type = getattr(absence, "absence_type", None)
                if absence_type in deployed_absence_types:
                    return True
        return False
