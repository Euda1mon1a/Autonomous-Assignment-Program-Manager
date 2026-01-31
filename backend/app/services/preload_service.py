"""PreloadService - Load locked assignments before solver runs.

This service loads preloaded assignments (FMIT, call, absences, etc.) into
the half_day_assignments table with source='preload'. These assignments
are locked and cannot be overwritten by the solver.

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

Block 10 FMIT Faculty:
- Week 1 (Mar 13-19): Tagawa (overlaps from Block 9)
- Week 2 (Mar 20-26): Chu
- Week 3 (Mar 27-Apr 2): Bevis
- Week 4 (Apr 3-9): Chu
- (LaBounty overlaps into Block 11)

FMIT Residents: Petrie (R3), Cataquiz (R2)
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, and_, or_, case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


class PreloadService:
    """
    Service to load preloaded assignments into half_day_assignments.

    All preloaded assignments have source='preload' and are locked
    (cannot be overwritten by solver).
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._activity_cache: dict[str, UUID] = {}
        self._template_cache: dict[str, RotationTemplate | None] = {}

    async def load_all_preloads(
        self,
        block_number: int,
        academic_year: int,
    ) -> int:
        """
        Load all preloads for a block into half_day_assignments.

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
        total += await self._load_absences(start_date, end_date)
        total += await self._load_institutional_events(start_date, end_date)
        total += await self._load_rotation_protected_preloads(
            block_number, academic_year
        )
        total += await self._load_inpatient_preloads(start_date, end_date)
        total += await self._load_fmit_call(start_date, end_date)
        total += await self._load_inpatient_clinic(block_number, academic_year)
        total += await self._load_resident_call(start_date, end_date)
        total += await self._load_faculty_call(start_date, end_date)
        total += await self._load_sm_preloads(start_date, end_date)
        total += await self._load_conferences(start_date, end_date)
        total += await self._load_protected_time(start_date, end_date)

        await self.session.commit()
        logger.info(f"Loaded {total} preload assignments")
        return total

    async def _load_absences(self, start_date: date, end_date: date) -> int:
        """Load absences as LV-AM/LV-PM preloads."""
        stmt = (
            select(Absence)
            .where(
                and_(
                    Absence.start_date <= end_date,
                    Absence.end_date >= start_date,
                )
            )
            .options(selectinload(Absence.person))
        )
        result = await self.session.execute(stmt)
        absences = result.scalars().all()

        lv_am_id = await self._get_activity_id("LV-AM")
        lv_pm_id = await self._get_activity_id("LV-PM")

        count = 0
        for absence in absences:
            # Only preload blocking absences (P2 Codex fix)
            if not absence.should_block_assignment:
                logger.debug(
                    f"Skipping non-blocking absence: {absence.absence_type} "
                    f"for person {absence.person_id}"
                )
                continue

            current = max(absence.start_date, start_date)
            end = min(absence.end_date, end_date)

            while current <= end:
                # Create AM and PM assignments
                for time_of_day, activity_id in [("AM", lv_am_id), ("PM", lv_pm_id)]:
                    await self._create_preload(
                        person_id=absence.person_id,
                        date_val=current,
                        time_of_day=time_of_day,
                        activity_id=activity_id,
                    )
                    count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} absence preloads")
        return count

    async def _load_institutional_events(self, start_date: date, end_date: date) -> int:
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
        result = await self.session.execute(stmt)
        events = result.scalars().all()
        if not events:
            return 0

        people_result = await self.session.execute(select(Person))
        people = people_result.scalars().all()
        people_by_scope: dict[InstitutionalEventScope, list[Person]] = {
            InstitutionalEventScope.ALL: people,
            InstitutionalEventScope.FACULTY: [p for p in people if p.type == "faculty"],
            InstitutionalEventScope.RESIDENT: [
                p for p in people if p.type == "resident"
            ],
        }
        inpatient_map = await self._build_inpatient_preload_map(start_date, end_date)

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
                        created = await self._create_preload(
                            person_id=person.id,
                            date_val=current,
                            time_of_day=time_of_day,
                            activity_id=event.activity_id,
                        )
                        if created:
                            count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} institutional event preloads")
        return count

    async def _build_inpatient_preload_map(
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
        result = await self.session.execute(stmt)
        rows = result.all()
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

    async def _load_inpatient_preloads(self, start_date: date, end_date: date) -> int:
        """Load inpatient rotation preloads (FMIT, NF, PedW, etc.)."""
        stmt = (
            select(InpatientPreload)
            .where(
                and_(
                    InpatientPreload.start_date <= end_date,
                    InpatientPreload.end_date >= start_date,
                )
            )
            .options(selectinload(InpatientPreload.person))
        )
        result = await self.session.execute(stmt)
        preloads = result.scalars().all()

        count = 0
        skipped = 0
        for preload in preloads:
            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            # Look up template for GUI day-off patterns
            template = await self._get_template_for_rotation_type(
                preload.rotation_type, preload.person
            )
            has_time_off_patterns = self._template_has_time_off_patterns(template)

            while current <= end:
                # Get AM/PM activity codes based on rotation type and day of week
                am_code, pm_code = self._get_rotation_codes(
                    preload.rotation_type,
                    current.weekday(),
                    person=preload.person,
                    has_time_off_patterns=has_time_off_patterns,
                )
                if has_time_off_patterns:
                    time_off_codes = self._get_time_off_codes_for_date(
                        template, current
                    )
                    am_code = time_off_codes.get("AM", am_code)
                    pm_code = time_off_codes.get("PM", pm_code)

                am_activity = await self._get_activity_id(am_code)
                pm_activity = await self._get_activity_id(pm_code)

                # Validate activity lookup succeeded - CRITICAL for GUI display
                if am_activity is None:
                    logger.error(
                        f"Activity lookup FAILED for AM code '{am_code}' "
                        f"(rotation={preload.rotation_type}, date={current}). "
                        f"Skipping preload - GUI will not display correctly!"
                    )
                    skipped += 1
                else:
                    await self._create_preload(
                        person_id=preload.person_id,
                        date_val=current,
                        time_of_day="AM",
                        activity_id=am_activity,
                    )
                    count += 1

                if pm_activity is None:
                    logger.error(
                        f"Activity lookup FAILED for PM code '{pm_code}' "
                        f"(rotation={preload.rotation_type}, date={current}). "
                        f"Skipping preload - GUI will not display correctly!"
                    )
                    skipped += 1
                else:
                    await self._create_preload(
                        person_id=preload.person_id,
                        date_val=current,
                        time_of_day="PM",
                        activity_id=pm_activity,
                    )
                    count += 1

                current += timedelta(days=1)

                # Handle post-call if applicable
            if preload.includes_post_call:
                pc_date = preload.end_date + timedelta(days=1)
                if pc_date <= end_date:
                    pc_activity = await self._get_activity_id("PC")
                    if pc_activity is None:
                        logger.error(
                            "Activity lookup FAILED for PC "
                            f"(rotation={preload.rotation_type}, date={pc_date}). "
                            "Skipping post-call preload - GUI will not display correctly!"
                        )
                        skipped += 2
                    else:
                        await self._create_preload(
                            person_id=preload.person_id,
                            date_val=pc_date,
                            time_of_day="AM",
                            activity_id=pc_activity,
                        )
                        await self._create_preload(
                            person_id=preload.person_id,
                            date_val=pc_date,
                            time_of_day="PM",
                            activity_id=pc_activity,
                        )
                        count += 2

        if skipped > 0:
            logger.warning(
                f"Loaded {count} inpatient preloads, SKIPPED {skipped} due to "
                f"missing activity codes (check rotation mappings!)"
            )
        else:
            logger.info(f"Loaded {count} inpatient preloads")
        return count

    async def _load_rotation_protected_preloads(
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
        result = await self.session.execute(stmt)
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
                is_outpatient = (
                    (active_template.rotation_type or "").lower() == "outpatient"
                    if active_template
                    else False
                )

                rotation_type = (
                    (active_template.rotation_type or "").lower()
                    if active_template
                    else ""
                )
                is_inpatient = rotation_type == "inpatient"
                is_offsite = rotation_type == "off"

                if is_inpatient and active_template:
                    count += await self._apply_inpatient_clinic_patterns(
                        assignment.resident_id,
                        current,
                        active_template,
                        start_date,
                    )
                if active_template:
                    count += await self._apply_inpatient_time_off_patterns(
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
                    am_activity_id = await self._get_activity_id(am_code)
                    if am_activity_id and await self._create_preload(
                        assignment.resident_id, current, "AM", am_activity_id
                    ):
                        count += 1
                if pm_code:
                    pm_activity_id = await self._get_activity_id(pm_code)
                    if pm_activity_id and await self._create_preload(
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

    async def _apply_inpatient_clinic_patterns(
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
            if pattern.activity_id and await self._create_preload(
                person_id, current_date, pattern.time_of_day, pattern.activity_id
            ):
                count += 1

        return count

    async def _apply_inpatient_time_off_patterns(
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
            if pattern.activity_id:
                await self._create_preload(
                    person_id, current_date, pattern.time_of_day, pattern.activity_id
                )
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

    async def _get_template_for_rotation_type(
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
            result = await self.session.execute(stmt)
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
            if dow == 5:  # Saturday off
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

    async def _load_fmit_call(self, start_date: date, end_date: date) -> int:
        """
        Load FMIT Fri/Sat call (auto-assigned with FMIT).

        FMIT faculty automatically cover Friday and Saturday call during their
        FMIT week. This creates CALL preloads in the PM slot (overnight starts PM).

        Note: Faculty call also triggers PCAT/DO on the following day, but that's
        handled separately in _load_faculty_call since it applies to all call,
        not just FMIT call.
        """
        # FMIT faculty cover Fri/Sat call during their FMIT week
        stmt = (
            select(InpatientPreload)
            .where(
                and_(
                    InpatientPreload.rotation_type == "FMIT",
                    InpatientPreload.start_date <= end_date,
                    InpatientPreload.end_date >= start_date,
                )
            )
            .options(selectinload(InpatientPreload.person))
        )
        result = await self.session.execute(stmt)
        fmit_preloads = result.scalars().all()

        # Get CALL activity ID
        call_activity_id = await self._get_activity_id("CALL")

        count = 0
        for preload in fmit_preloads:
            # Only for faculty (not residents)
            if not preload.person or preload.person.type != "faculty":
                continue

                # Friday and Saturday of FMIT week (within date range)
            current = max(preload.start_date, start_date)
            fmit_end = min(preload.end_date, end_date)

            while current <= fmit_end:
                if current.weekday() in (4, 5):  # Friday=4, Saturday=5
                    # Create call assignment in PM slot (overnight starts PM)
                    created = await self._create_preload(
                        person_id=preload.person_id,
                        date_val=current,
                        time_of_day="PM",
                        activity_id=call_activity_id,
                    )
                    if created:
                        count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} FMIT call preloads")
        return count

    async def _load_inpatient_clinic(
        self, block_number: int, academic_year: int
    ) -> int:
        """
        Load C-I (inpatient clinic) for residents on FMIT.

        Per PGY level:
        - PGY-1: Wednesday AM
        - PGY-2: Tuesday PM
        - PGY-3: Monday PM
        """
        block_dates = get_block_dates(block_number, academic_year)

        # Get FMIT residents from block assignments
        stmt = (
            select(BlockAssignment)
            .join(BlockAssignment.rotation_template)
            .where(
                and_(
                    BlockAssignment.block_number == block_number,
                    BlockAssignment.academic_year == academic_year,
                )
            )
            .options(
                selectinload(BlockAssignment.resident),
                selectinload(BlockAssignment.rotation_template),
            )
        )
        result = await self.session.execute(stmt)
        assignments = result.scalars().all()

        ci_activity = await self._get_activity_id(
            "C-I", required=False
        ) or await self._get_activity_id("C")
        if not ci_activity:
            logger.warning("Missing C-I or C activity, skipping C-I preloads")
            return 0
        count = 0

        for assignment in assignments:
            if not assignment.rotation_template:
                continue

                # Check if FMIT rotation
            rot_name = assignment.rotation_template.name or ""
            if "FMIT" not in rot_name.upper():
                continue

            if not assignment.resident:
                continue

            pgy = assignment.resident.pgy_level
            if not pgy:
                continue

                # Get C-I day based on PGY level
            if pgy == 1:
                day_of_week = 2  # Wednesday
                time_of_day = "AM"
            elif pgy == 2:
                day_of_week = 1  # Tuesday
                time_of_day = "PM"
            elif pgy == 3:
                day_of_week = 0  # Monday
                time_of_day = "PM"
            else:
                continue

                # Create C-I for each week of the block
            current = block_dates.start_date
            while current <= block_dates.end_date:
                if current.weekday() == day_of_week:
                    await self._create_preload(
                        person_id=assignment.resident_id,
                        date_val=current,
                        time_of_day=time_of_day,
                        activity_id=ci_activity,
                    )
                    count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} C-I preloads")
        return count

    async def _load_resident_call(self, start_date: date, end_date: date) -> int:
        """Load resident call preloads."""
        stmt = select(ResidentCallPreload).where(
            and_(
                ResidentCallPreload.call_date >= start_date,
                ResidentCallPreload.call_date <= end_date,
            )
        )
        result = await self.session.execute(stmt)
        preloads = result.scalars().all()

        call_activity = await self._get_activity_id("CALL")
        if not call_activity:
            logger.warning("CALL activity not found, skipping resident call preloads")
            return 0
        count = 0

        for preload in preloads:
            # Mark call date with CALL activity
            await self._create_preload(
                person_id=preload.person_id,
                date_val=preload.call_date,
                time_of_day="PM",  # Call is typically PM assignment
                activity_id=call_activity,
            )
            count += 1

        logger.info(f"Loaded {count} resident call preloads")
        return count

    async def _load_faculty_call(self, start_date: date, end_date: date) -> int:
        """
        Load faculty call with PCAT/DO auto-generation.

        After call night, faculty gets:
        - Next day AM: PCAT (Post-Call Admin Time) - CAN precept
        - Next day PM: DO (Day Off)
        """
        stmt = (
            select(CallAssignment)
            .where(
                and_(
                    CallAssignment.date >= start_date,
                    CallAssignment.date <= end_date,
                )
            )
            .options(selectinload(CallAssignment.person))
        )
        result = await self.session.execute(stmt)
        call_assignments = result.scalars().all()

        pcat_activity = await self._get_activity_id("PCAT")
        do_activity = await self._get_activity_id("DO")
        if not pcat_activity and not do_activity:
            logger.warning("Missing PCAT and DO activities, skipping faculty call")
            return 0
        count = 0

        for ca in call_assignments:
            # Only faculty get PCAT/DO
            if not ca.person or ca.person.type != "faculty":
                continue

                # Check if faculty is on FMIT - FMIT faculty don't get PCAT/DO
            if await self._is_on_fmit(ca.person_id, ca.date):
                continue

                # Post-call day
            post_call_date = ca.date + timedelta(days=1)
            if post_call_date > end_date:
                continue

                # PCAT in AM
            if pcat_activity:
                await self._create_preload(
                    person_id=ca.person_id,
                    date_val=post_call_date,
                    time_of_day="AM",
                    activity_id=pcat_activity,
                )
                count += 1

                # DO in PM
            if do_activity:
                await self._create_preload(
                    person_id=ca.person_id,
                    date_val=post_call_date,
                    time_of_day="PM",
                    activity_id=do_activity,
                )
                count += 1

        logger.info(f"Loaded {count} faculty call preloads (PCAT/DO)")
        return count

    async def _load_sm_preloads(self, start_date: date, end_date: date) -> int:
        """Load aSM (Academic Sports Med) for SM faculty on Wednesday AM."""
        # Find SM faculty (Tagawa)
        stmt = select(Person).where(
            and_(
                Person.type == "faculty",
                Person.admin_type == "SM",
            )
        )
        result = await self.session.execute(stmt)
        sm_faculty = result.scalars().all()

        asm_activity = await self._get_activity_id("aSM")
        if not asm_activity:
            return 0
        count = 0

        for faculty in sm_faculty:
            current = start_date
            while current <= end_date:
                if current.weekday() == 2:  # Wednesday
                    await self._create_preload(
                        person_id=faculty.id,
                        date_val=current,
                        time_of_day="AM",
                        activity_id=asm_activity,
                    )
                    count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} aSM preloads")
        return count

    async def _load_conferences(self, start_date: date, end_date: date) -> int:
        """Load conferences (HAFP, USAFP, LEC)."""
        # LEC on all Wednesday PM for all people
        # This would typically be done at the rotation level
        # For now, we'll skip this as it's handled by templates
        return 0

    async def _load_protected_time(self, start_date: date, end_date: date) -> int:
        """Load protected time (SIM, PI, MM)."""
        # Protected time is typically assigned manually or from templates
        return 0

        # Mapping from rotation types to activity codes
        # Some rotation types don't match activity codes (e.g., HILO → TDY)

    ROTATION_TO_ACTIVITY = {
        "HILO": "TDY",  # Hilo off-island rotation → Temporary Duty
        "FMC": "fm_clinic",  # FM Clinic rotation → fm_clinic activity
    }

    def _get_rotation_codes(
        self,
        rotation_type: str,
        day_of_week: int,
        *,
        person: Person | None = None,
        has_time_off_patterns: bool = False,
    ) -> tuple[str, str]:
        """
        Get AM/PM activity codes for rotation with day-specific patterns.

        P1 Codex fix: KAP and LDNF have day-specific rules that must be applied
        here to avoid locking incorrect values as preloads.

        Args:
            rotation_type: Rotation code (FMIT, KAP, LDNF, etc.)
            day_of_week: 0=Mon, 1=Tue, ..., 6=Sun

        Returns:
            Tuple of (AM_code, PM_code) - activity codes, not rotation types
        """
        code_upper = (rotation_type or "").strip().upper()
        person_type = getattr(person, "type", None)
        pgy_level = (
            getattr(person, "pgy_level", None) if person_type == "resident" else None
        )

        # Resident-only Saturday/Sunday off rules (temporary P6-2 defaults).
        # GUI patterns override these defaults when has_time_off_patterns=True.
        if person_type == "resident" and not has_time_off_patterns:
            if code_upper == "FMIT":
                if day_of_week == 5 and pgy_level in (1, 2):
                    return ("W", "W")
                if day_of_week == 6 and pgy_level == 3:
                    return ("W", "W")
            if day_of_week == 5 and code_upper in _SATURDAY_OFF_ROTATIONS:
                return ("W", "W")

                # Day-specific patterns for KAP (Kapiolani L&D)
                # Mon PM=OFF (travel), Tue=OFF/OFF (recovery), Wed AM=C (continuity)
        if code_upper == "KAP":
            if day_of_week == 0:  # Monday
                return ("KAP", "off")  # Travel back from Kapiolani
            elif day_of_week == 1:  # Tuesday
                return ("off", "off")  # Recovery day
            elif day_of_week == 2:  # Wednesday
                return ("fm_clinic", "lec")  # Continuity clinic + lecture
            else:  # Thu-Sun
                return ("KAP", "KAP")  # On-site at Kapiolani

                # Day-specific patterns for LDNF (L&D Night Float)
                # CRITICAL: Friday clinic, NOT Wednesday!
        if code_upper == "LDNF":
            if day_of_week == 4:  # Friday
                return ("fm_clinic", "off")  # Friday morning clinic!
            elif day_of_week in (5, 6):  # Weekend
                if not has_time_off_patterns:
                    return ("W", "W")
                # GUI patterns exist - skip hardcoded time-off, use normal codes
                return ("off", "LDNF")
            else:  # Mon-Thu
                return ("off", "LDNF")  # Working nights, sleeping days

                # Day-specific patterns for NF (Night Float)
                # AM = off (sleeping), PM = NF (working nights)
        if code_upper == "NF":
            if day_of_week in (5, 6):  # Weekend
                if not has_time_off_patterns:
                    return ("W", "W")
                # GUI patterns exist - skip hardcoded time-off
                return ("off", "NF")
            else:
                return ("off", "NF")

                # Day-specific patterns for PedNF (Peds Night Float)
        if code_upper == "PEDNF":
            if day_of_week == 5:  # Saturday off
                if not has_time_off_patterns:
                    return ("W", "W")
                # GUI patterns exist - skip hardcoded time-off
                return ("off", "PedNF")
            else:
                return ("off", "PedNF")

                # Fixed patterns for other rotations (no day-specific rules)
        codes = {
            "FMIT": ("FMIT", "FMIT"),
            "PEDW": ("PedW", "PedW"),
            "IM": ("IM", "IM"),
            "HILO": ("TDY", "TDY"),  # Hilo = TDY activity
            "FMC": ("fm_clinic", "fm_clinic"),  # FMC = fm_clinic activity
        }

        # Fall back to rotation type as activity code (works for most)
        default = self.ROTATION_TO_ACTIVITY.get(code_upper, rotation_type)
        return codes.get(code_upper, (default, default))

    async def _get_activity_id(
        self,
        code: str,
        *,
        required: bool = True,
    ) -> UUID | None:
        """Get activity ID by code (cached).

        Lookup order:
        1. Exact code match
        2. Case-insensitive code match (CALL -> call)
        3. Display abbreviation match (C-I -> fm_clinic_i)
        """
        if code in self._activity_cache:
            return self._activity_cache[code]

            # Try exact code match first
        stmt = select(Activity).where(Activity.code == code)
        result = await self.session.execute(stmt)
        activity = result.scalar_one_or_none()

        if not activity:
            # Try case-insensitive code match
            from sqlalchemy import func

            stmt = select(Activity).where(func.lower(Activity.code) == code.lower())
            result = await self.session.execute(stmt)
            activity = result.scalar_one_or_none()

        if not activity:
            # Try display abbreviation match
            stmt = select(Activity).where(Activity.display_abbreviation == code)
            result = await self.session.execute(stmt)
            activity = result.scalar_one_or_none()

        if activity:
            self._activity_cache[code] = activity.id
            return activity.id

        if required:
            logger.error(f"Unknown activity code during preload: {code}")
            raise ActivityNotFoundError(code, context="preload_service")

        logger.warning(f"Optional activity not found during preload: {code}")
        return None

    async def _create_preload(
        self,
        person_id: UUID,
        date_val: date,
        time_of_day: str,
        activity_id: UUID | None,
    ) -> HalfDayAssignment | None:
        """
        Create a preload assignment (idempotent - skips if exists).

        Race condition safe: uses check-then-insert with IntegrityError handling
        for the unique constraint on (person_id, date, time_of_day).
        """
        if not activity_id:
            logger.error(
                "Cannot create preload without activity_id "
                f"(person_id={person_id}, date={date_val}, time_of_day={time_of_day})"
            )
            raise ActivityNotFoundError(
                "<missing activity_id>", context="preload_service"
            )
            # Build query for checking existence (reused after IntegrityError)
        stmt = select(HalfDayAssignment).where(
            and_(
                HalfDayAssignment.person_id == person_id,
                HalfDayAssignment.date == date_val,
                HalfDayAssignment.time_of_day == time_of_day,
            )
        )

        # Check if already exists
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Already exists - allow time-off override for existing preloads
            new_activity = await self.session.get(Activity, activity_id)
            existing_activity = (
                await self.session.get(Activity, existing.activity_id)
                if existing.activity_id
                else None
            )
            new_is_time_off = new_activity and (
                (new_activity.activity_category or "").lower() == "time_off"
                or new_activity.counts_toward_clinical_hours is False
            )
            existing_is_time_off = existing_activity and (
                (existing_activity.activity_category or "").lower() == "time_off"
                or existing_activity.counts_toward_clinical_hours is False
            )
            if (
                existing.source == AssignmentSource.PRELOAD.value
                and new_is_time_off
                and not existing_is_time_off
            ):
                existing.activity_id = activity_id
                existing.source = AssignmentSource.PRELOAD.value
                await self.session.flush()
            return existing

            # Create new preload
        assignment = HalfDayAssignment(
            person_id=person_id,
            date=date_val,
            time_of_day=time_of_day,
            activity_id=activity_id,
            source=AssignmentSource.PRELOAD.value,
        )
        self.session.add(assignment)

        try:
            # Flush to trigger constraint check
            await self.session.flush()
        except IntegrityError:
            # Race condition - another process inserted first
            await self.session.rollback()
            # Re-fetch the existing record
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                logger.debug(
                    f"Race condition handled for preload: "
                    f"person={person_id}, date={date_val}, time={time_of_day}"
                )
                return existing
                # Re-raise if still not found (different integrity error)
            raise

        return assignment

    async def _is_on_fmit(self, person_id: UUID, date_val: date) -> bool:
        """Check if person is on FMIT on given date."""
        stmt = select(InpatientPreload).where(
            and_(
                InpatientPreload.person_id == person_id,
                InpatientPreload.rotation_type == "FMIT",
                InpatientPreload.start_date <= date_val,
                InpatientPreload.end_date >= date_val,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


async def load_block_preloads(
    session: AsyncSession,
    block_number: int,
    academic_year: int,
) -> int:
    """
    Convenience function to load all preloads for a block.

    Args:
        session: Database session
        block_number: Block number (1-13)
        academic_year: Academic year

    Returns:
        Number of preload assignments created
    """
    service = PreloadService(session)
    return await service.load_all_preloads(block_number, academic_year)
