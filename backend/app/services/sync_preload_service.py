"""SyncPreloadService - Synchronous version of PreloadService.

This is a sync wrapper for PreloadService that works with the synchronous
SchedulingEngine. It loads preloaded assignments (FMIT, call, absences, etc.)
into the half_day_assignments table with source='preload'.

Order of Operations (per TAMC skill):
1. Load absences → LV-AM, LV-PM
2. Load institutional events → USAFP, holidays, retreats
3. Load inpatient_preloads → FMIT, NF, PedW, KAP, IM, LDNF
4. Load FMIT Fri/Sat call (auto-assigned with FMIT)
5. Load C-I (inpatient clinic): PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
6. Load resident_call_preloads → CALL, PC
7. Load faculty_call → CALL, PCAT, DO
8. Load aSM (Wed AM for SM faculty)
9. Load conferences (HAFP, USAFP, LEC)
10. Load protected time (SIM, PI, MM)
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, and_, or_, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ActivityNotFoundError
from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.activity import Activity
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.inpatient_preload import InpatientPreload, InpatientRotationType
from app.models.institutional_event import InstitutionalEvent, InstitutionalEventScope
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.models.resident_call_preload import ResidentCallPreload
from app.utils.academic_blocks import get_block_dates, get_block_number_for_date
from app.utils.fmc_capacity import activity_counts_toward_fmc_capacity

logger = get_logger(__name__)

# Rotation normalization and protected slot rules
_ROTATION_ALIASES = {
    "PNF": "PEDNF",
    "PEDS NF": "PEDNF",
    "PEDS NIGHT FLOAT": "PEDNF",
    "PEDIATRICS NIGHT FLOAT": "PEDNF",
    "L&D NIGHT FLOAT": "LDNF",
    "L AND D NIGHT FLOAT": "LDNF",
    "KAPI": "KAP",
    "KAPI-LD": "KAP",
    "KAPI_LD": "KAP",
    "KAPIOLANI": "KAP",
    "KAPIOLANI L AND D": "KAP",
    "OKINAWA": "OKI",
}

_NIGHT_FLOAT_ROTATIONS = {"NF", "PEDNF", "LDNF"}
_LEC_EXEMPT_ROTATIONS = {"NF", "PEDNF", "LDNF", "TDY", "HILO", "OKI"}
_INTERN_CONTINUITY_EXEMPT_ROTATIONS = {
    "NF",
    "PEDNF",
    "LDNF",
    "TDY",
    "HILO",
    "OKI",
    "KAP",
}
_OFFSITE_ROTATIONS = {"TDY", "HILO", "OKI"}
_KAP_ROTATIONS = {"KAP"}
_CLINIC_PATTERN_CODES = {"C", "C-I", "C-N", "FM_CLINIC"}
# Temporary Saturday-off rules for external/inpatient rotations (P6-2).
# Refine later with rotation-specific rules.
_SATURDAY_OFF_ROTATIONS = {
    "IM",
    "IMW",
    "PEDW",
    "PEDNF",
    "ICU",
    "CCU",
    "NICU",
    "NIC",
    "NBN",
    "LAD",
    "LND",
    "LD",
    "L&D",
    "KAP",
    "HILO",
    "OKI",
    "TDY",
}

# Rotation types that require translation to activity codes
_ROTATION_TO_ACTIVITY = {
    "HILO": "TDY",
    "FMC": "fm_clinic",
}


class SyncPreloadService:
    """
    Synchronous service to load preloaded assignments into half_day_assignments.

    All preloaded assignments have source='preload' and are locked
    (cannot be overwritten by solver).
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._activity_cache: dict[str, UUID] = {}
        self._template_cache: dict[str, RotationTemplate | None] = {}

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
        total += self._load_institutional_events(start_date, end_date)
        total += self._load_rotation_protected_preloads(block_number, academic_year)
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

        # Query all absences in date range, then filter in Python
        # NOTE: should_block_assignment is a @property, not a SQL column,
        # so we cannot filter on it in SQL - must load and filter in Python
        stmt = select(Absence).where(
            Absence.start_date <= end_date,
            Absence.end_date >= start_date,
        )
        result = self.session.execute(stmt)
        all_absences = result.scalars().all()

        # Filter for blocking absences in Python (uses @property logic)
        absences = [a for a in all_absences if a.should_block_assignment]
        logger.debug(
            f"Found {len(all_absences)} absences, {len(absences)} are blocking"
        )

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

    def _load_institutional_events(self, start_date: date, end_date: date) -> int:
        """Load institutional events (USAFP, holidays, retreats) as preloads."""
        stmt = (
            select(InstitutionalEvent)
            .options(selectinload(InstitutionalEvent.activity))
            .where(
                InstitutionalEvent.is_active.is_(True),
                InstitutionalEvent.start_date <= end_date,
                InstitutionalEvent.end_date >= start_date,
            )
        )
        result = self.session.execute(stmt)
        events = result.scalars().all()
        if not events:
            return 0

        people = self.session.execute(select(Person)).scalars().all()
        people_by_scope: dict[InstitutionalEventScope, list[Person]] = {
            InstitutionalEventScope.ALL: people,
            InstitutionalEventScope.FACULTY: [p for p in people if p.type == "faculty"],
            InstitutionalEventScope.RESIDENT: [
                p for p in people if p.type == "resident"
            ],
        }
        inpatient_map = self._build_inpatient_preload_map(start_date, end_date)

        count = 0
        for event in events:
            if not event.activity_id:
                logger.warning(
                    "Institutional event missing activity_id; skipping "
                    f"event_id={event.id} name={event.name}"
                )
                continue

            scope = event.applies_to or InstitutionalEventScope.ALL
            if isinstance(scope, str):
                scope = InstitutionalEventScope(scope)
            targets = people_by_scope.get(scope, people)
            time_slots = [event.time_of_day] if event.time_of_day else ["AM", "PM"]
            current = max(event.start_date, start_date)
            end = min(event.end_date, end_date)

            while current <= end:
                for time_of_day in time_slots:
                    for person in targets:
                        if (
                            person.type == "resident"
                            and not event.applies_to_inpatient
                            and self._is_on_inpatient_preload(
                                person.id, current, inpatient_map
                            )
                        ):
                            continue
                        if self._create_preload(
                            person.id, current, time_of_day, event.activity_id
                        ):
                            count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} institutional event preloads")
        return count

    def _build_inpatient_preload_map(
        self, start_date: date, end_date: date
    ) -> dict[UUID, list[tuple[date, date]]]:
        """Build a map of inpatient preload date ranges by person."""
        stmt = select(
            InpatientPreload.person_id,
            InpatientPreload.start_date,
            InpatientPreload.end_date,
        ).where(
            InpatientPreload.start_date <= end_date,
            InpatientPreload.end_date >= start_date,
        )
        rows = self.session.execute(stmt).all()
        preload_map: dict[UUID, list[tuple[date, date]]] = {}
        for person_id, start, end in rows:
            preload_map.setdefault(person_id, []).append((start, end))
        return preload_map

    def _is_on_inpatient_preload(
        self,
        person_id: UUID,
        date_val: date,
        preload_map: dict[UUID, list[tuple[date, date]]],
    ) -> bool:
        """Check if person is on any inpatient preload for the date."""
        for start, end in preload_map.get(person_id, []):
            if start <= date_val <= end:
                return True
        return False

    def _load_inpatient_preloads(self, start_date: date, end_date: date) -> int:
        """Load inpatient rotation preloads (FMIT, NF, PedW, KAP, IM, LDNF)."""
        count = 0

        stmt = (
            select(InpatientPreload)
            .options(selectinload(InpatientPreload.person))
            .where(
                InpatientPreload.start_date <= end_date,
                InpatientPreload.end_date >= start_date,
            )
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
            person = preload.person
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

            # Look up template for GUI day-off patterns
            template = self._get_template_for_rotation_type(rotation_type, person)
            has_time_off_patterns = self._template_has_time_off_patterns(template)

            # Create preloads for each day
            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            while current <= end:
                # Get day-specific codes for special rotations
                am_code, pm_code = self._get_rotation_codes(
                    rotation_type,
                    current,
                    person=person,
                    has_time_off_patterns=has_time_off_patterns,
                )
                if has_time_off_patterns:
                    time_off_codes = self._get_time_off_codes_for_date(
                        template, current
                    )
                    am_code = time_off_codes.get("AM", am_code)
                    pm_code = time_off_codes.get("PM", pm_code)

                am_activity_id = self._get_activity_id(am_code)
                pm_activity_id = self._get_activity_id(pm_code)

                # Skip weekends for non-24/7 rotations
                # Note: NF-type rotations still need weekend preloads (with W activity)
                is_weekend = current.weekday() >= 5
                if (
                    is_weekend
                    and rotation_type
                    not in (
                        InpatientRotationType.FMIT,
                        InpatientRotationType.NF,
                        InpatientRotationType.PEDNF,  # Peds Night Float - creates W on weekends
                        InpatientRotationType.LDNF,  # L&D Night Float - creates W on weekends
                        InpatientRotationType.KAP,  # Kapiolani - works Thu-Sun
                        InpatientRotationType.IM,
                        InpatientRotationType.PEDW,
                    )
                    and not (am_code == "W" and pm_code == "W")
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

    def _load_rotation_protected_preloads(
        self, block_number: int, academic_year: int
    ) -> int:
        """
        Load protected patterns from rotation assignments.

        Applies:
        - LEC/ADV (last Wednesday)
        - Wednesday PM LEC (non-exempt rotations)
        - Intern continuity clinic (PGY-1 Wed AM, non-exempt)
        - Fixed off-site/night-float patterns when not covered by inpatient_preloads
        - Hilo pre/post clinic pattern
        """
        count = 0
        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date
        mid_block_date = start_date + timedelta(days=11)

        stmt = (
            select(BlockAssignment)
            .options(
                selectinload(BlockAssignment.rotation_template)
                .selectinload(RotationTemplate.weekly_patterns)
                .selectinload(WeeklyPattern.activity),
                selectinload(BlockAssignment.secondary_rotation_template)
                .selectinload(RotationTemplate.weekly_patterns)
                .selectinload(WeeklyPattern.activity),
                selectinload(BlockAssignment.resident),
            )
            .where(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
        )
        result = self.session.execute(stmt)
        assignments = result.scalars().all()

        for assignment in assignments:
            resident = assignment.resident
            if not resident or resident.type != "resident":
                continue

            pgy = resident.pgy_level or 0
            current = start_date
            while current <= end_date:
                rotation_code = self._resolve_rotation_code_for_date(
                    assignment, current, mid_block_date
                )
                if not rotation_code:
                    current += timedelta(days=1)
                    continue

                active_template = assignment.rotation_template
                if (
                    assignment.secondary_rotation_template_id
                    and current >= mid_block_date
                ):
                    active_template = assignment.secondary_rotation_template
                rotation_type = (
                    (active_template.rotation_type or "").lower()
                    if active_template
                    else ""
                )
                is_outpatient = rotation_type == "outpatient"
                is_inpatient = rotation_type == "inpatient"
                is_offsite = rotation_type == "off"

                if is_inpatient and active_template:
                    count += self._apply_inpatient_clinic_patterns(
                        assignment.resident_id,
                        current,
                        active_template,
                        start_date,
                    )
                if active_template:
                    count += self._apply_inpatient_time_off_patterns(
                        assignment.resident_id,
                        current,
                        active_template,
                        start_date,
                    )

                has_time_off_patterns = self._template_has_time_off_patterns(
                    active_template
                )
                am_code, pm_code = self._get_rotation_preload_codes(
                    rotation_code,
                    current,
                    start_date,
                    end_date,
                    pgy,
                    is_outpatient,
                    has_time_off_patterns,
                )

                if am_code:
                    am_activity_id = self._get_activity_id(am_code)
                    if am_activity_id and self._create_preload(
                        assignment.resident_id, current, "AM", am_activity_id
                    ):
                        count += 1
                if pm_code:
                    pm_activity_id = self._get_activity_id(pm_code)
                    if pm_activity_id and self._create_preload(
                        assignment.resident_id, current, "PM", pm_activity_id
                    ):
                        count += 1

                current += timedelta(days=1)

        if count:
            logger.info(f"Loaded {count} rotation protected preloads")
        return count

    def _resolve_rotation_code_for_date(
        self,
        assignment: BlockAssignment,
        current_date: date,
        mid_block_date: date,
    ) -> str:
        """Resolve active rotation code for a date (supports mid-block transitions)."""
        template = assignment.rotation_template
        if assignment.secondary_rotation_template_id and current_date >= mid_block_date:
            template = assignment.secondary_rotation_template

        raw_code = self._rotation_label(template)
        code = self._canonical_rotation_code(raw_code)
        if assignment.secondary_rotation_template_id:
            return code

            # Fallback: parse compound codes like NEURO-1ST-NF-2ND or NEURO/NF
        if "-1ST-" in code and "-2ND" in code:
            first, second = code.split("-1ST-", 1)
            second = second.replace("-2ND", "")
            first = self._canonical_rotation_code(first)
            second = self._canonical_rotation_code(second)
            return second if current_date >= mid_block_date else first

        if "/" in code:
            parts = [p.strip() for p in code.split("/") if p.strip()]
            if len(parts) == 2:
                first = self._canonical_rotation_code(parts[0])
                second = self._canonical_rotation_code(parts[1])
                return second if current_date >= mid_block_date else first

        if "+" in code:
            parts = [p.strip() for p in code.split("+") if p.strip()]
            if len(parts) == 2:
                first = self._canonical_rotation_code(parts[0])
                second = self._canonical_rotation_code(parts[1])
                return second if current_date >= mid_block_date else first

        return code

    def _rotation_label(self, template: RotationTemplate | None) -> str:
        """Get the best available label for a rotation template."""
        if not template:
            return ""
        return (
            template.abbreviation
            or template.display_abbreviation
            or template.name
            or ""
        )

    def _canonical_rotation_code(self, raw_code: str | None) -> str:
        """Normalize a rotation code for matching."""
        code = (raw_code or "").strip().upper()
        if not code:
            return ""
        if code.startswith("HILO"):
            return "HILO"
        if code.startswith("OKI"):
            return "OKI"
        if code.startswith("KAPI"):
            return "KAP"
        return _ROTATION_ALIASES.get(code, code)

    def _get_rotation_preload_codes(
        self,
        rotation_code: str,
        current_date: date,
        block_start: date,
        block_end: date,
        pgy_level: int,
        is_outpatient: bool,
        has_time_off_patterns: bool = False,
    ) -> tuple[str | None, str | None]:
        """Return AM/PM activity codes that should be preloaded for this slot."""
        if not rotation_code:
            return (None, None)

        if self._is_last_wednesday(current_date, block_end):
            return ("LEC", "ADV")

        if (
            current_date.weekday() == 5
            and rotation_code in _SATURDAY_OFF_ROTATIONS
            and not has_time_off_patterns
        ):
            return ("W", "W")

        if rotation_code in _OFFSITE_ROTATIONS:
            if rotation_code in {"HILO", "OKI"}:
                return self._get_hilo_codes(current_date, block_start)
            return ("TDY", "TDY")

        if rotation_code in _KAP_ROTATIONS:
            return self._get_kap_codes(current_date)

        if rotation_code == "LDNF":
            return self._get_ldnf_codes(current_date)

        if rotation_code in ("NF", "PEDNF"):
            return self._get_nf_codes(rotation_code, current_date)

            # Wednesday protected patterns (intern continuity only for outpatient rotations)
        if current_date.weekday() == 2:  # Wednesday
            am_code = None
            if (
                is_outpatient
                and pgy_level == 1
                and not self._is_intern_continuity_exempt(rotation_code)
            ):
                am_code = "C"

            pm_code = None
            if not self._is_lec_exempt(rotation_code):
                pm_code = "LEC"

            return (am_code, pm_code)

        return (None, None)

    def _apply_inpatient_clinic_patterns(
        self,
        person_id: UUID,
        current_date: date,
        template: RotationTemplate,
        block_start: date,
    ) -> int:
        """Preload clinic activities from weekly patterns for inpatient rotations."""
        patterns = list(template.weekly_patterns or [])
        if not patterns:
            return 0

        target_week = self._pattern_week_number(current_date, block_start)
        target_dow = self._pattern_day_of_week(current_date)
        count = 0

        for pattern in patterns:
            if pattern.day_of_week != target_dow:
                continue
            if pattern.week_number is not None and pattern.week_number != target_week:
                continue
            if not self._is_clinic_pattern_activity(pattern.activity):
                continue
            if pattern.activity_id and self._create_preload(
                person_id, current_date, pattern.time_of_day, pattern.activity_id
            ):
                count += 1

        return count

    def _apply_inpatient_time_off_patterns(
        self,
        person_id: UUID,
        current_date: date,
        template: RotationTemplate,
        block_start: date,
    ) -> int:
        """Preload time-off activities from weekly patterns for inpatient/off rotations."""
        patterns = list(template.weekly_patterns or [])
        if not patterns:
            return 0

        target_week = self._pattern_week_number(current_date, block_start)
        target_dow = self._pattern_day_of_week(current_date)
        count = 0

        for pattern in patterns:
            if pattern.day_of_week != target_dow:
                continue
            if pattern.week_number is not None and pattern.week_number != target_week:
                continue
            if not self._is_time_off_pattern_activity(pattern.activity):
                continue
            if pattern.activity_id and self._create_preload(
                person_id, current_date, pattern.time_of_day, pattern.activity_id
            ):
                count += 1

        return count

    def _pattern_week_number(self, current_date: date, block_start: date) -> int:
        return ((current_date - block_start).days // 7) + 1

    def _pattern_day_of_week(self, current_date: date) -> int:
        """Convert Python weekday (Mon=0..Sun=6) to weekly_pattern (Sun=0..Sat=6)."""
        return (current_date.weekday() + 1) % 7

    def _template_has_time_off_patterns(
        self, template: RotationTemplate | None
    ) -> bool:
        if not template:
            return False
        patterns = template.weekly_patterns or []
        return any(
            self._is_time_off_pattern_activity(pattern.activity) for pattern in patterns
        )

    def _get_time_off_codes_for_date(
        self, template: RotationTemplate | None, current_date: date
    ) -> dict[str, str]:
        if not template:
            return {}

        block_number, academic_year = get_block_number_for_date(current_date)
        block_dates = get_block_dates(block_number, academic_year)
        target_week = self._pattern_week_number(current_date, block_dates.start_date)
        target_dow = self._pattern_day_of_week(current_date)

        codes: dict[str, str] = {}
        for pattern in template.weekly_patterns or []:
            if pattern.day_of_week != target_dow:
                continue
            if pattern.week_number is not None and pattern.week_number != target_week:
                continue
            if not self._is_time_off_pattern_activity(pattern.activity):
                continue
            activity = pattern.activity
            if not activity:
                continue
            code = (activity.code or activity.display_abbreviation or "").strip()
            if not code:
                continue
            codes[pattern.time_of_day.upper()] = code

        return codes

    def _is_clinic_pattern_activity(self, activity: Activity | None) -> bool:
        if not activity:
            return False
        code = (activity.code or "").strip().upper()
        display = (activity.display_abbreviation or "").strip().upper()
        return code in _CLINIC_PATTERN_CODES or display in _CLINIC_PATTERN_CODES

    def _is_time_off_pattern_activity(self, activity: Activity | None) -> bool:
        if not activity:
            return False
        category = (activity.activity_category or "").strip().lower()
        if category == "time_off":
            return True
        code = (activity.code or "").strip().upper()
        return code in {"OFF", "W"}

    def _get_template_for_rotation_type(
        self, rotation_type: InpatientRotationType | str | None, person: Person | None
    ) -> RotationTemplate | None:
        """Look up RotationTemplate by rotation_type abbreviation (cached)."""
        if rotation_type is None:
            return None
        # Get string abbreviation
        abbrev = (
            (
                rotation_type.value
                if hasattr(rotation_type, "value")
                else (rotation_type or "")
            )
            .strip()
            .upper()
        )
        if not abbrev:
            return None
        pgy_level = (
            getattr(person, "pgy_level", None)
            if getattr(person, "type", None) == "resident"
            else None
        )
        cache_key = f"{abbrev}:{pgy_level}"
        # Check cache
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        candidates: list[str] = []
        if pgy_level:
            if abbrev == "FMIT":
                candidates.append(f"FMIT-PGY{pgy_level}")
            if abbrev == "IM":
                candidates.append(f"IM-PGY{pgy_level}")
            if abbrev == "PEDW":
                candidates.append(f"PEDS-WARD-PGY{pgy_level}")
            if abbrev == "PEDNF":
                candidates.append(f"NF-PEDS-PGY{pgy_level}")
            if abbrev == "KAP" and pgy_level == 1:
                candidates.append("KAPI-LD-PGY1")

        alias_map = {
            "PEDW": ["PEDSW", "PEDS-W"],
            "PEDNF": ["PNF"],
            "LDNF": ["NF-LD"],
            "KAP": ["KAP-LD"],
        }
        candidates.extend(alias_map.get(abbrev, []))
        candidates.append(abbrev)

        wildcard_map = {
            "FMIT": "FMIT-%",
            "IM": "IM-PGY%",
            "PEDW": "PEDS-WARD-%",
            "PEDNF": "NF-PEDS-%",
            "KAP": "KAPI-LD-%",
        }
        if abbrev in wildcard_map:
            candidates.append(wildcard_map[abbrev])

        template = None
        for candidate in candidates:
            stmt = (
                select(RotationTemplate)
                .options(selectinload(RotationTemplate.weekly_patterns))
                .where(
                    or_(
                        RotationTemplate.abbreviation.ilike(candidate),
                        RotationTemplate.display_abbreviation.ilike(candidate),
                    )
                )
                .order_by(
                    # Prefer exact abbreviation match over display_abbreviation
                    case(
                        (RotationTemplate.abbreviation.ilike(candidate), 0),
                        else_=1,
                    )
                )
                .limit(1)
            )
            result = self.session.execute(stmt)
            template = result.scalars().first()
            if template:
                break

        self._template_cache[cache_key] = template
        return template

    def _is_last_wednesday(self, current_date: date, block_end: date) -> bool:
        """Return True if the date is the last Wednesday of the block."""
        if current_date.weekday() != 2:
            return False
        return current_date + timedelta(days=7) > block_end

    def _is_lec_exempt(self, rotation_code: str) -> bool:
        return rotation_code in _LEC_EXEMPT_ROTATIONS

    def _is_intern_continuity_exempt(self, rotation_code: str) -> bool:
        return rotation_code in _INTERN_CONTINUITY_EXEMPT_ROTATIONS

    def _get_kap_codes(self, current_date: date) -> tuple[str, str]:
        """Kapiolani L&D pattern."""
        dow = current_date.weekday()
        if dow == 0:  # Monday
            return ("KAP", "OFF")
        if dow == 1:  # Tuesday
            return ("OFF", "OFF")
        if dow == 2:  # Wednesday
            return ("C", "LEC")
        return ("KAP", "KAP")

    def _get_ldnf_codes(self, current_date: date) -> tuple[str, str]:
        """L&D Night Float pattern with Friday clinic."""
        dow = current_date.weekday()
        if dow == 4:  # Friday
            return ("C", "OFF")
        if dow >= 5:  # Weekend
            return ("W", "W")
        return ("OFF", "LDNF")

    def _get_nf_codes(self, rotation_code: str, current_date: date) -> tuple[str, str]:
        """Night Float pattern (NF/PedNF)."""
        dow = current_date.weekday()
        if rotation_code == "PEDNF":
            if dow == 5:  # Saturday off only
                return ("W", "W")
            return ("OFF", "PedNF")
        if dow >= 5:
            return ("W", "W")
        return ("OFF", "NF")

    def _get_hilo_codes(self, current_date: date, block_start: date) -> tuple[str, str]:
        """Hilo/Okinawa TDY pattern with pre/post clinic days."""
        day_index = (current_date - block_start).days
        if day_index in (0, 1):  # Thu/Fri before leaving
            return ("C", "C")
        if day_index == 19:  # Return Tuesday (4th Tuesday)
            return ("C", "C")
        return ("TDY", "TDY")

    def _get_rotation_codes(
        self,
        rotation_type: InpatientRotationType | str | None,
        current_date: date,
        *,
        person: Person | None = None,
        has_time_off_patterns: bool = False,
    ) -> tuple[str, str]:
        """Get AM/PM activity codes for special rotations based on day of week."""
        if rotation_type is None:
            return ("FMIT", "FMIT")

        dow = current_date.weekday()  # 0=Mon, 6=Sun

        # Get string code for comparison
        code_raw = (
            rotation_type.value if hasattr(rotation_type, "value") else rotation_type
        )
        code_upper = (code_raw or "").strip().upper()

        person_type = getattr(person, "type", None)
        pgy_level = (
            getattr(person, "pgy_level", None) if person_type == "resident" else None
        )

        # Resident-only Saturday/Sunday off rules (temporary P6-2 defaults).
        # GUI patterns override these defaults when has_time_off_patterns=True.
        if person_type == "resident" and not has_time_off_patterns:
            if code_upper == "FMIT":
                if dow == 5 and pgy_level in (1, 2):
                    return ("W", "W")
                if dow == 6 and pgy_level == 3:
                    return ("W", "W")
            if dow == 5 and code_upper in _SATURDAY_OFF_ROTATIONS:
                return ("W", "W")

                # KAP (Kapiolani L&D - off-site)
        if code_upper == "KAP":
            if dow == 0:  # Monday
                return ("KAP", "OFF")
            elif dow == 1:  # Tuesday
                return ("OFF", "OFF")
            elif dow == 2:  # Wednesday
                return ("C", "LEC")
            else:  # Thu-Sun
                return ("KAP", "KAP")

                # LDNF (L&D Night Float - Friday clinic!)
        if code_upper == "LDNF":
            if dow == 4:  # Friday
                return ("C", "OFF")
            elif dow >= 5:  # Weekend
                if not has_time_off_patterns:
                    return ("W", "W")
                # GUI patterns exist - skip hardcoded time-off
                return ("OFF", "LDNF")
            else:  # Mon-Thu
                return ("OFF", "LDNF")

                # NF (Night Float) - off AM (sleeping), NF PM (working), weekends off
        if code_upper == "NF":
            if dow >= 5:  # Weekend (Sat=5, Sun=6)
                if not has_time_off_patterns:
                    return ("W", "W")
                # GUI patterns exist - skip hardcoded time-off
                return ("OFF", "NF")
            else:  # Mon-Fri
                return ("OFF", "NF")

                # PedNF (Peds Night Float) - Saturday off only
        if code_upper == "PEDNF":
            if dow == 5:  # Saturday
                if not has_time_off_patterns:
                    return ("W", "W")
                # GUI patterns exist - skip hardcoded time-off
                return ("OFF", "PedNF")
            return ("OFF", "PedNF")

            # Rotations that work all days including weekends:
            # FMIT, PedW, IM - just use rotation code for both slots
            # Default: use rotation type for both slots (after mapping to activity code)
        mapped = _ROTATION_TO_ACTIVITY.get(code_upper, code_raw)
        return (mapped, mapped)

    def _load_fmit_call(self, start_date: date, end_date: date) -> int:
        """Load FMIT call (Fri/Sat PM during FMIT weeks)."""
        count = 0
        call_id = self._get_activity_id("CALL")

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
        ci_id = self._get_activity_id("C-I", required=False) or self._get_activity_id(
            "C"
        )

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
                if self._create_preload(call.person_id, next_day, "AM", pcat_id):
                    count += 1
                if self._create_preload(call.person_id, next_day, "PM", do_id):
                    count += 1

        logger.info(f"Loaded {count} faculty call preloads")
        return count

    def _load_sm_preloads(self, start_date: date, end_date: date) -> int:
        """Load Sports Medicine preloads (Wed AM for SM faculty)."""
        count = 0
        asm_id = self._get_activity_id("aSM", required=False)
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

        # Find block assignments with compound rotations
        from app.models.rotation_template import RotationTemplate

        stmt = (
            select(BlockAssignment)
            .options(selectinload(BlockAssignment.rotation_template))
            .options(selectinload(BlockAssignment.secondary_rotation_template))
            .where(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
        )
        result = self.session.execute(stmt)
        assignments = result.scalars().all()

        # Mid-block transition point (day 11 = Excel column 28 = Monday of week 2)
        # This matches TAMC Excel format where column 28 is the transition point
        mid_block_date = start_date + timedelta(days=11)

        for assignment in assignments:
            if not assignment.rotation_template:
                continue

            primary_template = assignment.rotation_template
            secondary_template = assignment.secondary_rotation_template
            primary_code = self._canonical_rotation_code(
                self._rotation_label(primary_template)
            )
            secondary_code = self._canonical_rotation_code(
                self._rotation_label(secondary_template)
            )

            # Detect compound rotation patterns
            # One half is night float, the other half should be weekend-off.
            first_half_no_weekend = False
            second_half_no_weekend = False

            if secondary_template:
                first_is_night_float = primary_code in _NIGHT_FLOAT_ROTATIONS
                second_is_night_float = secondary_code in _NIGHT_FLOAT_ROTATIONS

                if not first_is_night_float and not second_is_night_float:
                    continue

                if (
                    not first_is_night_float
                    and not primary_template.includes_weekend_work
                    and primary_code not in _OFFSITE_ROTATIONS
                ):
                    first_half_no_weekend = True

                if (
                    not second_is_night_float
                    and not secondary_template.includes_weekend_work
                    and secondary_code not in _OFFSITE_ROTATIONS
                ):
                    second_half_no_weekend = True
            else:
                abbrev = primary_code
                if "-1ST-NF-2ND" in abbrev or "-1ST-PEDNF-2ND" in abbrev:
                    first_half_no_weekend = True
                elif abbrev.startswith("NF-1ST-") or abbrev.startswith("PEDNF-1ST-"):
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
                should_create_w = (is_first_half and first_half_no_weekend) or (
                    not is_first_half and second_half_no_weekend
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

    def _get_activity_id(
        self,
        code: str,
        *,
        required: bool = True,
    ) -> UUID | None:
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

        if required:
            logger.error(f"Unknown activity code during preload: {code}")
            raise ActivityNotFoundError(code, context="sync_preload_service")

        logger.warning(f"Optional activity not found during preload: {code}")
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
        if not activity_id:
            logger.error(
                "Cannot create preload without activity_id "
                f"(person_id={person_id}, date={date_val}, time_of_day={time_of_day})"
            )
            raise ActivityNotFoundError(
                "<missing activity_id>", context="sync_preload_service"
            )
        activity = self.session.get(Activity, activity_id) if activity_id else None
        capacity_flag = (
            activity_counts_toward_fmc_capacity(activity) if activity else None
        )

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
                existing.counts_toward_fmc_capacity = capacity_flag
                return True
            if (
                existing.source == AssignmentSource.PRELOAD.value
                and existing.activity_id is None
                and activity_id
            ):
                existing.activity_id = activity_id
                existing.counts_toward_fmc_capacity = capacity_flag
                return True
            if existing.source == AssignmentSource.PRELOAD.value:
                existing_activity = (
                    self.session.get(Activity, existing.activity_id)
                    if existing.activity_id
                    else None
                )
                new_is_time_off = (
                    (activity.activity_category or "").lower() == "time_off"
                    or activity.counts_toward_clinical_hours is False
                )
                existing_is_time_off = existing_activity and (
                    (existing_activity.activity_category or "").lower() == "time_off"
                    or existing_activity.counts_toward_clinical_hours is False
                )
                if new_is_time_off and not existing_is_time_off:
                    existing.activity_id = activity_id
                    existing.counts_toward_fmc_capacity = capacity_flag
                    return True
            if existing.source == AssignmentSource.PRELOAD.value:
                # Keep counts_toward_fmc_capacity in sync with activity
                if (
                    existing.activity_id == activity_id
                    and capacity_flag is not None
                    and existing.counts_toward_fmc_capacity != capacity_flag
                ):
                    existing.counts_toward_fmc_capacity = capacity_flag
                    return True
            return False

            # Create new
        assignment = HalfDayAssignment(
            person_id=person_id,
            date=date_val,
            time_of_day=time_of_day,
            activity_id=activity_id,
            counts_toward_fmc_capacity=capacity_flag,
            source=AssignmentSource.PRELOAD.value,
        )
        self.session.add(assignment)

        try:
            self.session.flush()
            return True
        except IntegrityError as e:
            self.session.rollback()
            # Use SQLSTATE for reliable duplicate detection across drivers/locales
            # 23505 = unique_violation in PostgreSQL
            # Fallback to string matching for sqlite (used in tests)
            error_str = str(e.orig).lower() if e.orig else str(e).lower()
            is_duplicate = (
                (hasattr(e.orig, "pgcode") and e.orig.pgcode == "23505")
                or "unique constraint" in error_str
                or "uq_half_day_assignment_person_date_time" in error_str
            )
            if is_duplicate:
                logger.debug(
                    f"Preload already exists for person_id={person_id}, "
                    f"date={date_val}, time_of_day={time_of_day}"
                )
                return False
                # FK violation or other constraint error - fail loudly
            pgcode = getattr(e.orig, "pgcode", "unknown")
            logger.error(
                f"Unexpected IntegrityError (pgcode={pgcode}): {e.orig}. "
                f"person_id={person_id}, date={date_val}, time_of_day={time_of_day}, "
                f"activity_id={activity_id}"
            )
            raise

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
