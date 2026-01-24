"""
Faculty Assignment Expansion Service.

Ensures every faculty member has exactly 56 half-day assignments per block (28 days × 2).
Creates HalfDayAssignment records with source='solver' for empty slots.

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

import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.activity import Activity
from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
from app.models.person import Person
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


# Faculty clinic caps (MIN, MAX per week) - Session 136
# C = Faculty seeing OWN patients (has caps)
# AT = Faculty supervising residents (no cap)
FACULTY_CLINIC_CAPS: dict[str, tuple[int, int]] = {
    "Kinkennon": (2, 4),
    "LaBounty": (2, 4),
    "McRae": (2, 4),
    "Montgomery": (2, 2),
    "Lamoureux": (2, 2),
    "McGuire": (1, 1),
    "Tagawa": (0, 0),  # SM only
    "Bevis": (0, 0),
    "Dahl": (0, 0),
    "Chu": (0, 0),
    "Napierala": (0, 0),
    "Van Brunt": (0, 0),
    "Colgan": (0, 0),
}

# ACGME supervision demand per PGY level
AT_DEMAND_BY_PGY: dict[int, float] = {
    1: 0.5,  # PGY-1: 2 residents per faculty
    2: 0.25,  # PGY-2/3: 4 residents per faculty
    3: 0.25,
}

# Physical capacity: max people in clinic per slot
# AT doesn't count - supervision doesn't take exam room space
MAX_PHYSICAL_CAPACITY = 6

# Activity codes that count against physical capacity
# fm_clinic, C, C-N = taking up exam rooms
# AT, pcat, do = supervision only, no room needed
PHYSICAL_CAPACITY_CODES = ["fm_clinic", "C", "C-N", "CV"]


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
        self._holiday_slots: set[tuple[date, str]] = set()  # Keys: (date, time_of_day)

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

        # =====================================================================
        # ACGME-Aware Faculty Assignment (Session 136)
        # =====================================================================
        # Step 1: Calculate AT demand from resident clinic assignments
        at_demand = self._calculate_at_demand(start_date, end_date)

        # Step 2: Assign AT slots to meet ACGME supervision ratios
        at_created = self._assign_at_slots(faculty, at_demand, start_date, end_date)

        # Step 3: Assign clinic (C) slots to faculty with caps
        clinic_created = self._assign_clinic_slots(faculty, start_date, end_date)

        # Step 4: Fill remaining slots with GME/DFM (original behavior)
        total_created = 0
        for person in faculty:
            created = self._fill_single_faculty(
                person,
                start_date,
                end_date,
            )
            total_created += created

        total_all = at_created + clinic_created + total_created
        logger.info(
            f"Faculty assignments complete: {at_created} AT + {clinic_created} C "
            f"+ {total_created} admin = {total_all} total"
        )
        return total_all

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
        # at, pcat, do, fm_clinic for ACGME supervision and clinic (Session 136)
        activity_codes = [
            "W",
            "HOL",
            "LV-AM",
            "LV-PM",
            "DEP",
            "gme",
            "dfm",
            "sm_clinic",
            # Faculty clinic and supervision activities (NEW - Session 136)
            "at",  # Attending Time - ACGME supervision
            "fm_clinic",  # Faculty clinic - their own patients
            "pcat",  # Post-Call Attending Time
            "do",  # Direct Observation
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
        slots that should get HOL activity instead of admin time.

        NOTE: Holidays are tracked per-slot (date + time_of_day), not per-date.
        This supports partial-day holidays if ever needed (rare but possible).
        """
        from app.models.block import Block
        from app.models.day_type import OperationalIntent

        # Query blocks that are holidays or non-operational (DONSA, EO closure)
        # Include time_of_day for per-slot holiday detection
        stmt = select(Block.date, Block.time_of_day).where(
            Block.date >= start_date,
            Block.date <= end_date,
            # Match holidays OR non-operational days
            (Block.is_holiday == True)
            | (Block.operational_intent == OperationalIntent.NON_OPERATIONAL),  # noqa: E712
        )

        for row in self.db.execute(stmt):
            # Store as (date, time_of_day) tuple for per-slot detection
            self._holiday_slots.add((row[0], row[1]))

        logger.info(
            f"Pre-loaded {len(self._holiday_slots)} holiday/non-operational slots from blocks"
        )

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

            # Process AM slot (check holiday per-slot)
            is_holiday_am = (current_date, "AM") in self._holiday_slots
            am_created = self._fill_slot(
                person,
                current_date,
                "AM",
                is_weekend,
                is_absent,
                is_deployed,
                is_holiday_am,
                admin_type,
            )
            if am_created:
                created_count += 1

            # Process PM slot (check holiday per-slot)
            is_holiday_pm = (current_date, "PM") in self._holiday_slots
            pm_created = self._fill_slot(
                person,
                current_date,
                "PM",
                is_weekend,
                is_absent,
                is_deployed,
                is_holiday_pm,
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

        # Create HalfDayAssignment with source='solver'
        half_day = HalfDayAssignment(
            person_id=person.id,
            date=slot_date,
            time_of_day=time_of_day,
            activity_id=activity.id,
            source=AssignmentSource.SOLVER.value,
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

    # =========================================================================
    # ACGME AT Assignment Logic (Session 136)
    # =========================================================================

    def _calculate_at_demand(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[tuple[date, str], int]:
        """
        Calculate ACGME AT (Attending Time) demand per slot.

        Queries resident clinic assignments and calculates how many faculty
        AT slots are needed per (date, time_of_day) to meet ACGME ratios.

        Returns:
            Dict mapping (date, time_of_day) -> required_faculty_count
        """
        # Query resident clinic assignments
        clinic_codes = ["fm_clinic", "C", "C-N", "CV"]

        stmt = (
            select(
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                Person.pgy_level,
                func.count().label("count"),
            )
            .join(Person, HalfDayAssignment.person_id == Person.id)
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .where(Person.type == "resident")
            .where(Activity.code.in_(clinic_codes))
            .where(HalfDayAssignment.date >= start_date)
            .where(HalfDayAssignment.date <= end_date)
            .group_by(
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                Person.pgy_level,
            )
        )

        # Calculate demand per slot
        demand_by_slot: dict[tuple[date, str], float] = defaultdict(float)

        for row in self.db.execute(stmt):
            slot_date = row[0]
            time_of_day = row[1]
            pgy_level = row[2] or 2  # Default to PGY-2 if unknown
            count = row[3]

            key = (slot_date, time_of_day)
            demand_factor = AT_DEMAND_BY_PGY.get(pgy_level, 0.25)
            demand_by_slot[key] += count * demand_factor

        # Round up each slot's demand
        result = {k: math.ceil(v) for k, v in demand_by_slot.items()}

        total_demand = sum(result.values())
        logger.info(
            f"Calculated AT demand: {total_demand} faculty slots needed "
            f"across {len(result)} clinic slots"
        )

        return result

    def _get_faculty_clinic_cap(self, faculty_name: str) -> tuple[int, int]:
        """Get (MIN, MAX) clinic cap for faculty by name."""
        # Extract last name
        if "," in faculty_name:
            last_name = faculty_name.split(",")[0].strip()
        else:
            parts = faculty_name.split()
            last_name = parts[-1] if parts else faculty_name

        return FACULTY_CLINIC_CAPS.get(last_name, (0, 4))

    def _assign_at_slots(
        self,
        faculty: list[Person],
        at_demand: dict[tuple[date, str], int],
        start_date: date,
        end_date: date,
    ) -> int:
        """
        Assign AT (Attending Time) to faculty slots to meet ACGME demand.

        Returns count of AT assignments created.
        """
        at_activity = self._get_activity("at")
        if not at_activity:
            logger.warning("Missing 'at' activity, skipping AT assignments")
            return 0

        at_created = 0

        # Track existing AT coverage per slot (from PCAT, etc.)
        at_coverage: dict[tuple[date, str], int] = defaultdict(int)

        # Query existing AT-type assignments
        at_codes = ["at", "pcat", "do"]
        stmt = (
            select(
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                func.count().label("count"),
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .join(Person, HalfDayAssignment.person_id == Person.id)
            .where(Person.type == "faculty")
            .where(Activity.code.in_(at_codes))
            .where(HalfDayAssignment.date >= start_date)
            .where(HalfDayAssignment.date <= end_date)
            .group_by(
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
            )
        )

        for row in self.db.execute(stmt):
            key = (row[0], row[1])
            at_coverage[key] = row[2]

        # For each slot with demand, assign AT to available faculty
        for (slot_date, time_of_day), required in at_demand.items():
            existing = at_coverage.get((slot_date, time_of_day), 0)
            needed = max(0, required - existing)

            if needed == 0:
                continue

            # Skip weekends
            if slot_date.weekday() >= 5:
                continue

            # Find available faculty for this slot
            for person in faculty:
                if needed <= 0:
                    break

                key = f"{person.id}_{slot_date.isoformat()}_{time_of_day}"
                if key in self._existing_slots:
                    continue  # Already assigned

                # Check if faculty is available (not absent, not deployed)
                is_absent = self._is_person_absent(person.id, slot_date)
                is_deployed = self._is_person_deployed(person.id, slot_date)
                is_holiday = (slot_date, time_of_day) in self._holiday_slots

                if is_absent or is_deployed or is_holiday:
                    continue

                # Assign AT
                half_day = HalfDayAssignment(
                    person_id=person.id,
                    date=slot_date,
                    time_of_day=time_of_day,
                    activity_id=at_activity.id,
                    source=AssignmentSource.SOLVER.value,
                )
                self.db.add(half_day)
                self._existing_slots.add(key)
                at_created += 1
                needed -= 1

        logger.info(f"Created {at_created} AT assignments for ACGME coverage")
        return at_created

    def _calculate_physical_capacity(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[tuple[date, str], int]:
        """
        Calculate current physical capacity usage per slot.

        Physical capacity = residents + faculty with C/fm_clinic activity.
        AT, pcat, do don't count (supervision doesn't take exam rooms).

        Returns:
            Dict mapping (date, time_of_day) -> current_occupancy
        """
        stmt = (
            select(
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                func.count().label("count"),
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .where(Activity.code.in_(PHYSICAL_CAPACITY_CODES))
            .where(HalfDayAssignment.date >= start_date)
            .where(HalfDayAssignment.date <= end_date)
            .group_by(
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
            )
        )

        capacity_by_slot: dict[tuple[date, str], int] = defaultdict(int)
        for row in self.db.execute(stmt):
            key = (row[0], row[1])
            capacity_by_slot[key] = row[2]

        return capacity_by_slot

    def _assign_clinic_slots(
        self,
        faculty: list[Person],
        start_date: date,
        end_date: date,
    ) -> int:
        """
        Assign fm_clinic (C) to faculty based on their weekly caps.

        Respects physical capacity limit (MAX_PHYSICAL_CAPACITY per slot).
        AT doesn't count against physical capacity.

        Returns count of clinic assignments created.
        """
        clinic_activity = self._get_activity("fm_clinic")
        if not clinic_activity:
            logger.warning("Missing 'fm_clinic' activity, skipping C assignments")
            return 0

        clinic_created = 0
        capacity_blocked = 0

        # Get current physical capacity usage per slot
        slot_capacity = self._calculate_physical_capacity(start_date, end_date)

        # Group dates by week (Mon-Sun)
        weeks: list[list[date]] = []
        current_week: list[date] = []
        current = start_date

        while current <= end_date:
            if current.weekday() == 0 and current_week:
                weeks.append(current_week)
                current_week = []
            current_week.append(current)
            current += timedelta(days=1)

        if current_week:
            weeks.append(current_week)

        # For each faculty with clinic caps, assign C slots
        for person in faculty:
            faculty_name = getattr(person, "name", "")
            min_c, max_c = self._get_faculty_clinic_cap(faculty_name)

            if max_c == 0:
                continue  # No clinic for this faculty

            for week_dates in weeks:
                # Count existing clinic in this week
                existing_c = 0
                available_slots: list[tuple[date, str]] = []

                for day in week_dates:
                    if day.weekday() >= 5:  # Skip weekends
                        continue

                    for slot in ["AM", "PM"]:
                        key = f"{person.id}_{day.isoformat()}_{slot}"
                        if key in self._existing_slots:
                            # Check if it's already a clinic
                            # (we'd need to query, simplified: just skip)
                            continue

                        # Check physical capacity - skip if at limit
                        capacity_key = (day, slot)
                        current_occupancy = slot_capacity.get(capacity_key, 0)
                        if current_occupancy >= MAX_PHYSICAL_CAPACITY:
                            capacity_blocked += 1
                            continue

                        # Check availability
                        is_absent = self._is_person_absent(person.id, day)
                        is_deployed = self._is_person_deployed(person.id, day)
                        is_holiday = (day, slot) in self._holiday_slots

                        if not is_absent and not is_deployed and not is_holiday:
                            available_slots.append((day, slot))

                # Assign up to min_c clinic slots (prefer full days)
                to_assign = min(min_c - existing_c, len(available_slots))

                # Sort to prefer AM slots (for full days)
                available_slots.sort(key=lambda x: (x[0], x[1]))

                for day, slot in available_slots[:to_assign]:
                    key = f"{person.id}_{day.isoformat()}_{slot}"
                    if key in self._existing_slots:
                        continue

                    # Double-check capacity before assignment
                    capacity_key = (day, slot)
                    if slot_capacity.get(capacity_key, 0) >= MAX_PHYSICAL_CAPACITY:
                        capacity_blocked += 1
                        continue

                    half_day = HalfDayAssignment(
                        person_id=person.id,
                        date=day,
                        time_of_day=slot,
                        activity_id=clinic_activity.id,
                        source=AssignmentSource.SOLVER.value,
                    )
                    self.db.add(half_day)
                    self._existing_slots.add(key)
                    # Update capacity tracking
                    slot_capacity[capacity_key] = slot_capacity.get(capacity_key, 0) + 1
                    clinic_created += 1

        if capacity_blocked > 0:
            logger.warning(
                f"Blocked {capacity_blocked} faculty clinic assignments due to "
                f"physical capacity limit ({MAX_PHYSICAL_CAPACITY} per slot)"
            )
        logger.info(f"Created {clinic_created} faculty clinic (C) assignments")
        return clinic_created
