"""SyncPreloadService - Synchronous version of PreloadService.

This is a sync wrapper for PreloadService that works with the synchronous
SchedulingEngine. It loads preloaded assignments (FMIT, call, absences, etc.)
into the half_day_assignments table with source='preload'.

Order of Operations (per TAMC skill):
1. Load absences → LV-AM, LV-PM
2. Load inpatient_preloads → FMIT, NF, PedW, KAP, IM, LDNF
3. Load FMIT Fri/Sat call (auto-assigned with FMIT)
4. Load C-I (inpatient clinic): PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
5. Load resident_call_preloads → CALL, PC
6. Load faculty_call → CALL, PCAT, DO
7. Load aSM (Wed AM for SM faculty)
8. Load conferences (HAFP, USAFP, LEC)
9. Load protected time (SIM, PI, MM)
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.activity import Activity
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.inpatient_preload import InpatientPreload, InpatientRotationType
from app.models.person import Person
from app.models.resident_call_preload import ResidentCallPreload
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


class SyncPreloadService:
    """
    Synchronous service to load preloaded assignments into half_day_assignments.

    All preloaded assignments have source='preload' and are locked
    (cannot be overwritten by solver).
    """

    def __init__(self, session: Session):
        self.session = session
        self._activity_cache: dict[str, UUID] = {}

    def load_all_preloads(
        self,
        block_number: int,
        academic_year: int,
        skip_faculty_call: bool = False,
    ) -> int:
        """
        Load all preloads for a block into half_day_assignments.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            skip_faculty_call: If True, skip loading faculty call PCAT/DO from
                              existing CallAssignment table. Use this when the
                              engine will generate NEW call assignments and create
                              PCAT/DO directly (correct order of operations).

        Returns:
            Number of assignments created
        """
        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date

        logger.info(
            f"Loading preloads for Block {block_number} ({academic_year}): "
            f"{start_date} to {end_date}"
        )

        total = 0

        # Order of operations (per TAMC skill)
        total += self._load_absences(start_date, end_date)
        total += self._load_inpatient_preloads(start_date, end_date)
        total += self._load_fmit_call(start_date, end_date)
        total += self._load_inpatient_clinic(block_number, academic_year)
        total += self._load_resident_call(start_date, end_date)

        # Faculty call PCAT/DO - skip if engine will create from NEW call
        # Old behavior: Load PCAT/DO from existing CallAssignment (STALE!)
        # New behavior: Engine runs call solver first, creates PCAT/DO directly
        if not skip_faculty_call:
            total += self._load_faculty_call(start_date, end_date)
        else:
            logger.info("Skipping faculty call PCAT/DO (engine creates from NEW call)")

        total += self._load_sm_preloads(start_date, end_date)
        # Conferences and protected time are stubbed out in async version
        # total += self._load_conferences(start_date, end_date)
        # total += self._load_protected_time(start_date, end_date)

        # Load weekend preloads for compound rotations (NEURO-1ST-NF-2ND, etc.)
        total += self._load_compound_rotation_weekends(
            block_number, academic_year, start_date, end_date
        )

        # Don't commit here - let the engine handle transaction
        self.session.flush()
        logger.info(f"Loaded {total} preload assignments")
        return total

    def _load_absences(self, start_date: date, end_date: date) -> int:
        """Load absence assignments (LV-AM, LV-PM)."""
        count = 0

        # Get LV activities
        lv_am_id = self._get_activity_id("LV-AM")
        lv_pm_id = self._get_activity_id("LV-PM")

        if not lv_am_id or not lv_pm_id:
            logger.warning("Missing LV-AM or LV-PM activity, skipping absences")
            return 0

        # Query absences that block assignments
        stmt = select(Absence).where(
            Absence.start_date <= end_date,
            Absence.end_date >= start_date,
            Absence.should_block_assignment == True,  # noqa: E712
        )
        result = self.session.execute(stmt)
        absences = result.scalars().all()

        for absence in absences:
            # Create preloads for each day of the absence
            current = max(absence.start_date, start_date)
            end = min(absence.end_date, end_date)

            while current <= end:
                # AM slot
                if self._create_preload(absence.person_id, current, "AM", lv_am_id):
                    count += 1
                # PM slot
                if self._create_preload(absence.person_id, current, "PM", lv_pm_id):
                    count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} absence preloads")
        return count

    def _load_inpatient_preloads(self, start_date: date, end_date: date) -> int:
        """Load inpatient rotation preloads (FMIT, NF, PedW, KAP, IM, LDNF)."""
        count = 0

        stmt = select(InpatientPreload).where(
            InpatientPreload.start_date <= end_date,
            InpatientPreload.end_date >= start_date,
        )
        result = self.session.execute(stmt)
        preloads = result.scalars().all()

        # Mapping for rotation types to activity codes
        rotation_to_activity = {
            "FMC": "fm_clinic",  # FM Clinic -> C
            "HILO": "TDY",  # Hilo rotation -> TDY
        }

        for preload in preloads:
            rotation_type = preload.rotation_type
            # Handle both enum and string rotation types
            activity_code = (
                rotation_type.value
                if hasattr(rotation_type, "value")
                else (rotation_type or "FMIT")
            )
            # Apply mapping if needed
            activity_code = rotation_to_activity.get(activity_code, activity_code)

            # Get activity for this rotation
            activity_id = self._get_activity_id(activity_code)
            if not activity_id:
                logger.warning(f"No activity found for rotation type: {activity_code}")
                continue

            # Create preloads for each day
            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            while current <= end:
                # Get day-specific codes for special rotations
                am_code, pm_code = self._get_rotation_codes(rotation_type, current)

                am_activity_id = self._get_activity_id(am_code) or activity_id
                pm_activity_id = self._get_activity_id(pm_code) or activity_id

                # Skip weekends for non-24/7 rotations
                # Note: NF-type rotations still need weekend preloads (with W activity)
                is_weekend = current.weekday() >= 5
                if is_weekend and rotation_type not in (
                    InpatientRotationType.FMIT,
                    InpatientRotationType.NF,
                    InpatientRotationType.PEDNF,  # Peds Night Float - creates W on weekends
                    InpatientRotationType.LDNF,  # L&D Night Float - creates W on weekends
                    InpatientRotationType.KAP,  # Kapiolani - works Thu-Sun
                    InpatientRotationType.IM,
                    InpatientRotationType.PEDW,
                ):
                    current += timedelta(days=1)
                    continue

                # AM slot
                if self._create_preload(
                    preload.person_id, current, "AM", am_activity_id
                ):
                    count += 1
                # PM slot
                if self._create_preload(
                    preload.person_id, current, "PM", pm_activity_id
                ):
                    count += 1

                current += timedelta(days=1)

        logger.info(f"Loaded {count} inpatient preloads")
        return count

    def _get_rotation_codes(
        self, rotation_type: InpatientRotationType | str | None, current_date: date
    ) -> tuple[str, str]:
        """Get AM/PM activity codes for special rotations based on day of week."""
        if rotation_type is None:
            return ("FMIT", "FMIT")

        dow = current_date.weekday()  # 0=Mon, 6=Sun

        # Get string code for comparison
        code = rotation_type.value if hasattr(rotation_type, "value") else rotation_type

        # KAP (Kapiolani L&D - off-site)
        if code == "KAP":
            if dow == 0:  # Monday
                return ("KAP", "OFF")
            elif dow == 1:  # Tuesday
                return ("OFF", "OFF")
            elif dow == 2:  # Wednesday
                return ("C", "LEC")
            else:  # Thu-Sun
                return ("KAP", "KAP")

        # LDNF (L&D Night Float - Friday clinic!)
        if code == "LDNF":
            if dow == 4:  # Friday
                return ("C", "OFF")
            elif dow >= 5:  # Weekend
                return ("W", "W")
            else:  # Mon-Thu
                return ("OFF", "LDNF")

        # NF (Night Float) - off AM (sleeping), NF PM (working), weekends off
        if code == "NF":
            if dow >= 5:  # Weekend (Sat=5, Sun=6)
                return ("W", "W")
            else:  # Mon-Fri
                return ("OFF", "NF")

        # PedNF (Peds Night Float) - same pattern as NF
        if code == "PedNF":
            if dow >= 5:  # Weekend
                return ("W", "W")
            else:  # Mon-Fri
                return ("OFF", "PedNF")

        # Rotations that work all days including weekends:
        # FMIT, PedW, IM - just use rotation code for both slots
        # Default: use rotation type for both slots
        return (code, code)

    def _load_fmit_call(self, start_date: date, end_date: date) -> int:
        """Load FMIT call (Fri/Sat PM during FMIT weeks)."""
        count = 0
        call_id = self._get_activity_id("CALL")
        if not call_id:
            logger.warning("Missing CALL activity")
            return 0

        # Get FMIT preloads
        stmt = select(InpatientPreload).where(
            InpatientPreload.rotation_type == InpatientRotationType.FMIT,
            InpatientPreload.start_date <= end_date,
            InpatientPreload.end_date >= start_date,
        )
        result = self.session.execute(stmt)
        preloads = result.scalars().all()

        for preload in preloads:
            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            while current <= end:
                # Fri=4, Sat=5
                if current.weekday() in (4, 5):
                    if self._create_preload(preload.person_id, current, "PM", call_id):
                        count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} FMIT call preloads")
        return count

    def _load_inpatient_clinic(self, block_number: int, academic_year: int) -> int:
        """Load inpatient clinic (C-I) based on PGY level.

        PGY-1: Wednesday AM
        PGY-2: Tuesday PM
        PGY-3: Monday PM
        """
        count = 0
        ci_id = self._get_activity_id("C-I") or self._get_activity_id("C")
        if not ci_id:
            logger.warning("Missing C-I or C activity")
            return 0

        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date

        # Get FMIT preloads with person info
        stmt = (
            select(InpatientPreload)
            .options(selectinload(InpatientPreload.person))
            .where(
                InpatientPreload.rotation_type == InpatientRotationType.FMIT,
                InpatientPreload.start_date <= end_date,
                InpatientPreload.end_date >= start_date,
            )
        )
        result = self.session.execute(stmt)
        preloads = result.scalars().all()

        for preload in preloads:
            person = preload.person
            if not person:
                continue

            pgy = person.pgy_level or 0
            if pgy == 0:
                continue  # Faculty don't get C-I

            # Determine which day/time based on PGY
            if pgy == 1:
                target_dow, target_time = 2, "AM"  # Wed AM
            elif pgy == 2:
                target_dow, target_time = 1, "PM"  # Tue PM
            elif pgy == 3:
                target_dow, target_time = 0, "PM"  # Mon PM
            else:
                continue

            # Find all matching days in the preload period
            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            while current <= end:
                if current.weekday() == target_dow:
                    if self._create_preload(
                        preload.person_id, current, target_time, ci_id
                    ):
                        count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} inpatient clinic preloads")
        return count

    def _load_resident_call(self, start_date: date, end_date: date) -> int:
        """Load resident call preloads."""
        count = 0
        call_id = self._get_activity_id("CALL")
        if not call_id:
            logger.warning("Missing CALL activity")
            return 0

        stmt = select(ResidentCallPreload).where(
            ResidentCallPreload.call_date >= start_date,
            ResidentCallPreload.call_date <= end_date,
        )
        result = self.session.execute(stmt)
        preloads = result.scalars().all()

        for preload in preloads:
            # Call is typically PM
            if self._create_preload(
                preload.person_id, preload.call_date, "PM", call_id
            ):
                count += 1

        logger.info(f"Loaded {count} resident call preloads")
        return count

    def _load_faculty_call(self, start_date: date, end_date: date) -> int:
        """Load faculty call with PCAT/DO auto-generation."""
        count = 0
        call_id = self._get_activity_id("CALL")
        pcat_id = self._get_activity_id("PCAT")
        do_id = self._get_activity_id("DO")

        if not call_id:
            logger.warning("Missing CALL activity")
            return 0

        stmt = select(CallAssignment).where(
            CallAssignment.date >= start_date,
            CallAssignment.date <= end_date,
        )
        result = self.session.execute(stmt)
        calls = result.scalars().all()

        for call in calls:
            # Call PM slot
            if self._create_preload(call.person_id, call.date, "PM", call_id):
                count += 1

            # Next day: PCAT AM, DO PM (if not on FMIT)
            # Note: Create PCAT/DO even if next_day is in the next block - we use actual
            # dates, and preload source is locked so next block won't overwrite it
            next_day = call.date + timedelta(days=1)
            if not self._is_on_fmit(call.person_id, next_day):
                if pcat_id and self._create_preload(
                    call.person_id, next_day, "AM", pcat_id
                ):
                    count += 1
                if do_id and self._create_preload(
                    call.person_id, next_day, "PM", do_id
                ):
                    count += 1

        logger.info(f"Loaded {count} faculty call preloads")
        return count

    def _load_sm_preloads(self, start_date: date, end_date: date) -> int:
        """Load Sports Medicine preloads (Wed AM for SM faculty)."""
        count = 0
        asm_id = self._get_activity_id("aSM")
        if not asm_id:
            # aSM might not exist in all deployments
            return 0

        # Get SM faculty from block_assignments
        stmt = (
            select(BlockAssignment)
            .options(selectinload(BlockAssignment.rotation_template))
            .where(
                BlockAssignment.rotation_template.has(abbreviation="SM"),
            )
        )
        result = self.session.execute(stmt)
        sm_assignments = result.scalars().all()

        for assignment in sm_assignments:
            # Find Wednesdays in date range
            current = start_date
            while current <= end_date:
                if current.weekday() == 2:  # Wednesday
                    if self._create_preload(
                        assignment.resident_id, current, "AM", asm_id
                    ):
                        count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} SM preloads")
        return count

    def _load_compound_rotation_weekends(
        self,
        block_number: int,
        academic_year: int,
        start_date: date,
        end_date: date,
    ) -> int:
        """Load weekend preloads for compound rotations.

        Compound rotations like NEURO-1ST-NF-2ND have different weekend rules
        for each half:
        - NEURO (first half): No weekend work → needs W preloads
        - NF (second half): Weekend work handled by inpatient_preloads

        Similarly for NF-1ST-ENDO-2ND:
        - NF (first half): Weekend work handled by inpatient_preloads
        - ENDO (second half): No weekend work → needs W preloads
        """
        count = 0
        w_id = self._get_activity_id("W")
        if not w_id:
            logger.warning("Missing W activity, skipping compound rotation weekends")
            return 0

        # Find block assignments with compound rotations
        from app.models.rotation_template import RotationTemplate

        stmt = (
            select(BlockAssignment)
            .options(selectinload(BlockAssignment.rotation_template))
            .where(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
        )
        result = self.session.execute(stmt)
        assignments = result.scalars().all()

        # Mid-block transition point (day 14 = start of week 3)
        mid_block_date = start_date + timedelta(days=14)

        for assignment in assignments:
            if not assignment.rotation_template:
                continue

            abbrev = assignment.rotation_template.abbreviation or ""

            # Detect compound rotation patterns
            # Pattern: *-1ST-NF-2ND → first half is elective (no weekends)
            # Pattern: NF-1ST-*-2ND → second half is elective (no weekends)
            first_half_no_weekend = False
            second_half_no_weekend = False

            if "-1ST-NF-2ND" in abbrev or "-1ST-PEDNF-2ND" in abbrev:
                # First half is elective (NEURO, etc.) - no weekend work
                first_half_no_weekend = True
            elif abbrev.startswith("NF-1ST-") or abbrev.startswith("PEDNF-1ST-"):
                # Second half is elective (ENDO, etc.) - no weekend work
                second_half_no_weekend = True

            if not first_half_no_weekend and not second_half_no_weekend:
                continue

            # Create W preloads for appropriate weekends
            current = start_date
            while current <= end_date:
                is_weekend = current.weekday() >= 5  # Sat=5, Sun=6
                if not is_weekend:
                    current += timedelta(days=1)
                    continue

                # Determine which half this weekend falls in
                is_first_half = current < mid_block_date

                # Create W preload if this half doesn't work weekends
                should_create_w = (
                    (is_first_half and first_half_no_weekend)
                    or (not is_first_half and second_half_no_weekend)
                )

                if should_create_w:
                    if self._create_preload(
                        assignment.resident_id, current, "AM", w_id
                    ):
                        count += 1
                    if self._create_preload(
                        assignment.resident_id, current, "PM", w_id
                    ):
                        count += 1

                current += timedelta(days=1)

        if count > 0:
            logger.info(f"Loaded {count} compound rotation weekend preloads")
        return count

    def _get_activity_id(self, code: str) -> UUID | None:
        """Get activity ID by code (cached)."""
        if code in self._activity_cache:
            return self._activity_cache[code]

        # Try exact code match
        stmt = select(Activity).where(Activity.code == code)
        result = self.session.execute(stmt)
        activity = result.scalars().first()

        if not activity:
            # Try case-insensitive
            stmt = select(Activity).where(Activity.code.ilike(code))
            result = self.session.execute(stmt)
            activity = result.scalars().first()

        if not activity:
            # Try display_abbreviation
            stmt = select(Activity).where(Activity.display_abbreviation == code)
            result = self.session.execute(stmt)
            activity = result.scalars().first()

        if activity:
            self._activity_cache[code] = activity.id
            return activity.id

        return None

    def _create_preload(
        self,
        person_id: UUID,
        date_val: date,
        time_of_day: str,
        activity_id: UUID,
    ) -> bool:
        """
        Create a preload assignment (race-condition safe).

        Returns True if created, False if already exists.
        """
        # Check if exists
        stmt = select(HalfDayAssignment).where(
            HalfDayAssignment.person_id == person_id,
            HalfDayAssignment.date == date_val,
            HalfDayAssignment.time_of_day == time_of_day,
        )
        result = self.session.execute(stmt)
        existing = result.scalars().first()

        if existing:
            # Already exists - update if it's a lower priority source
            if existing.source in (
                AssignmentSource.TEMPLATE.value,
                AssignmentSource.SOLVER.value,
            ):
                existing.activity_id = activity_id
                existing.source = AssignmentSource.PRELOAD.value
                return True
            if (
                existing.source == AssignmentSource.PRELOAD.value
                and existing.activity_id is None
                and activity_id
            ):
                existing.activity_id = activity_id
                return True
            return False

        # Create new
        assignment = HalfDayAssignment(
            person_id=person_id,
            date=date_val,
            time_of_day=time_of_day,
            activity_id=activity_id,
            source=AssignmentSource.PRELOAD.value,
        )
        self.session.add(assignment)

        try:
            self.session.flush()
            return True
        except IntegrityError:
            self.session.rollback()
            return False

    def _is_on_fmit(self, person_id: UUID, date_val: date) -> bool:
        """Check if person is on FMIT on the given date."""
        stmt = select(InpatientPreload).where(
            InpatientPreload.person_id == person_id,
            InpatientPreload.rotation_type == InpatientRotationType.FMIT,
            InpatientPreload.start_date <= date_val,
            InpatientPreload.end_date >= date_val,
        )
        result = self.session.execute(stmt)
        return result.scalars().first() is not None
