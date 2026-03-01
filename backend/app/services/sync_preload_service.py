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
8b. Load faculty Wednesday PM LEC (protected didactic, skips 4th Wed)
9. Load conferences (HAFP, USAFP, LEC)
10. Load protected time (SIM, PI, MM)
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
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

# Shared preload logic — extracted to eliminate duplication with async service
from app.services.preload import (
    ActivityCache,
    CLINIC_PATTERN_CODES,
    NIGHT_FLOAT_ROTATIONS,
    OFFSITE_ROTATIONS,
    ROTATION_TO_ACTIVITY,
    TemplateCache,
    canonical_rotation_code,
    get_rotation_codes,
    get_rotation_preload_codes,
    pattern_day_of_week,
    pattern_week_number,
)

logger = get_logger(__name__)


class SyncPreloadService:
    """
    Synchronous service to load preloaded assignments into half_day_assignments.

    All preloaded assignments have source='preload' and are locked
    (cannot be overwritten by solver).
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self._activity_cache = ActivityCache(session)
        self._template_cache = TemplateCache(session)

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

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

        if skip_faculty_call:
            cleared = self._clear_faculty_call_preloads(start_date, end_date)
            if cleared:
                logger.info(f"Cleared {cleared} stale faculty call PCAT/DO preloads")

        total += self._load_absences(start_date, end_date)
        total += self._load_institutional_events(start_date, end_date)
        total += self._load_rotation_protected_preloads(block_number, academic_year)
        total += self._load_inpatient_preloads(start_date, end_date)
        total += self._load_fmit_call(start_date, end_date)
        total += self._load_inpatient_clinic(block_number, academic_year)
        total += self._load_resident_call(start_date, end_date)

        if not skip_faculty_call:
            total += self._load_faculty_call(start_date, end_date)
        else:
            logger.info("Skipping faculty call PCAT/DO (engine creates from NEW call)")

        total += self._load_sm_preloads(start_date, end_date)
        total += self._load_faculty_wednesday_pm_lec(start_date, end_date)

        total += self._load_compound_rotation_weekends(
            block_number, academic_year, start_date, end_date
        )

        self.session.flush()
        logger.info(f"Loaded {total} preload assignments")
        return total

    # ------------------------------------------------------------------
    # Phase loaders (DB-dependent)
    # ------------------------------------------------------------------

    def _clear_faculty_call_preloads(self, start_date: date, end_date: date) -> int:
        pcat_id = self._activity_cache.get("PCAT")
        do_id = self._activity_cache.get("DO")
        if not pcat_id or not do_id:
            return 0

        deleted = (
            self.session.query(HalfDayAssignment)
            .filter(
                HalfDayAssignment.date >= start_date,
                HalfDayAssignment.date <= end_date,
                HalfDayAssignment.source == AssignmentSource.PRELOAD.value,
                HalfDayAssignment.activity_id.in_([pcat_id, do_id]),
            )
            .delete(synchronize_session=False)
        )
        if deleted:
            self.session.flush()
        return deleted

    def _load_absences(self, start_date: date, end_date: date) -> int:
        count = 0
        lv_am_id = self._activity_cache.get("LV-AM")
        lv_pm_id = self._activity_cache.get("LV-PM")

        stmt = select(Absence).where(
            Absence.start_date <= end_date,
            Absence.end_date >= start_date,
        )
        all_absences = self.session.execute(stmt).scalars().all()
        absences = [a for a in all_absences if a.should_block_assignment]
        logger.debug(
            f"Found {len(all_absences)} absences, {len(absences)} are blocking"
        )

        for absence in absences:
            current = max(absence.start_date, start_date)
            end = min(absence.end_date, end_date)
            while current <= end:
                if self._create_preload(absence.person_id, current, "AM", lv_am_id):
                    count += 1
                if self._create_preload(absence.person_id, current, "PM", lv_pm_id):
                    count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} absence preloads")
        return count

    def refresh_leave_preloads(
        self, person_id: UUID, start_date: date, end_date: date
    ) -> int:
        """Delete LV preloads for person in range, re-create from absences.

        Called after Absence CRUD to keep preloads in sync.

        Returns:
            Number of new preloads created.
        """
        lv_am_id = self._activity_cache.get("LV-AM")
        lv_pm_id = self._activity_cache.get("LV-PM")
        lv_ids = [aid for aid in [lv_am_id, lv_pm_id] if aid]

        # Delete existing LV preloads for this person in the date range
        if lv_ids:
            (
                self.session.query(HalfDayAssignment)
                .filter(
                    HalfDayAssignment.person_id == person_id,
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                    HalfDayAssignment.activity_id.in_(lv_ids),
                    HalfDayAssignment.source == AssignmentSource.PRELOAD,
                )
                .delete(synchronize_session=False)
            )

        # Re-create from absences overlapping this range
        absences = (
            self.session.query(Absence)
            .filter(
                Absence.person_id == person_id,
                Absence.start_date <= end_date,
                Absence.end_date >= start_date,
            )
            .all()
        )

        count = 0
        for absence in absences:
            if not getattr(absence, "should_block_assignment", True):
                continue
            current = max(absence.start_date, start_date)
            end = min(absence.end_date, end_date)
            while current <= end:
                if lv_am_id and self._create_preload(
                    person_id, current, "AM", lv_am_id
                ):
                    count += 1
                if lv_pm_id and self._create_preload(
                    person_id, current, "PM", lv_pm_id
                ):
                    count += 1
                current += timedelta(days=1)

        self.session.flush()
        logger.info(
            "Refreshed leave preloads for person %s (%s to %s): %d created",
            person_id,
            start_date,
            end_date,
            count,
        )
        return count

    def _load_institutional_events(self, start_date: date, end_date: date) -> int:
        stmt = (
            select(InstitutionalEvent)
            .options(selectinload(InstitutionalEvent.activity))
            .where(
                InstitutionalEvent.is_active.is_(True),
                InstitutionalEvent.start_date <= end_date,
                InstitutionalEvent.end_date >= start_date,
            )
        )
        events = self.session.execute(stmt).scalars().all()
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
        for start, end in preload_map.get(person_id, []):
            if start <= date_val <= end:
                return True
        return False

    def _load_inpatient_preloads(self, start_date: date, end_date: date) -> int:
        count = 0
        stmt = (
            select(InpatientPreload)
            .options(selectinload(InpatientPreload.person))
            .where(
                InpatientPreload.start_date <= end_date,
                InpatientPreload.end_date >= start_date,
            )
        )
        preloads = self.session.execute(stmt).scalars().all()

        for preload in preloads:
            rotation_type = preload.rotation_type
            person = preload.person
            activity_code = (
                rotation_type.value
                if hasattr(rotation_type, "value")
                else (rotation_type or "FMIT")
            )
            activity_code = ROTATION_TO_ACTIVITY.get(activity_code, activity_code)
            activity_id = self._activity_cache.get(activity_code)

            template = self._template_cache.get(rotation_type, person)
            has_time_off_patterns = self._template_has_time_off_patterns(template)

            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            while current <= end:
                am_code, pm_code = get_rotation_codes(
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

                am_activity_id = self._activity_cache.get(am_code)
                pm_activity_id = self._activity_cache.get(pm_code)

                is_weekend = current.weekday() >= 5
                if (
                    is_weekend
                    and rotation_type
                    not in (
                        InpatientRotationType.FMIT,
                        InpatientRotationType.NF,
                        InpatientRotationType.PEDNF,
                        InpatientRotationType.LDNF,
                        InpatientRotationType.KAP,
                        InpatientRotationType.IM,
                        InpatientRotationType.PEDW,
                    )
                    and not (am_code == "W" and pm_code == "W")
                ):
                    current += timedelta(days=1)
                    continue

                if self._create_preload(
                    preload.person_id, current, "AM", am_activity_id
                ):
                    count += 1
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
        assignments = self.session.execute(stmt).scalars().all()

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
                am_code, pm_code = get_rotation_preload_codes(
                    rotation_code,
                    current,
                    start_date,
                    end_date,
                    pgy,
                    is_outpatient,
                    has_time_off_patterns,
                )

                if am_code:
                    am_activity_id = self._activity_cache.get(am_code)
                    if am_activity_id and self._create_preload(
                        assignment.resident_id, current, "AM", am_activity_id
                    ):
                        count += 1
                if pm_code:
                    pm_activity_id = self._activity_cache.get(pm_code)
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
        template = assignment.rotation_template
        if assignment.secondary_rotation_template_id and current_date >= mid_block_date:
            template = assignment.secondary_rotation_template

        raw_code = self._rotation_label(template)
        code = canonical_rotation_code(raw_code)
        if assignment.secondary_rotation_template_id:
            return code

        if "-1ST-" in code and "-2ND" in code:
            first, second = code.split("-1ST-", 1)
            second = second.replace("-2ND", "")
            first = canonical_rotation_code(first)
            second = canonical_rotation_code(second)
            return second if current_date >= mid_block_date else first

        if "/" in code:
            parts = [p.strip() for p in code.split("/") if p.strip()]
            if len(parts) == 2:
                first = canonical_rotation_code(parts[0])
                second = canonical_rotation_code(parts[1])
                return second if current_date >= mid_block_date else first

        if "+" in code:
            parts = [p.strip() for p in code.split("+") if p.strip()]
            if len(parts) == 2:
                first = canonical_rotation_code(parts[0])
                second = canonical_rotation_code(parts[1])
                return second if current_date >= mid_block_date else first

        return code

    def _rotation_label(self, template: RotationTemplate | None) -> str:
        if not template:
            return ""
        return (
            template.abbreviation
            or template.display_abbreviation
            or template.name
            or ""
        )

    def _apply_inpatient_clinic_patterns(
        self,
        person_id: UUID,
        current_date: date,
        template: RotationTemplate,
        block_start: date,
    ) -> int:
        patterns = list(template.weekly_patterns or [])
        if not patterns:
            return 0

        target_week = pattern_week_number(current_date, block_start)
        target_dow = pattern_day_of_week(current_date)
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
        patterns = list(template.weekly_patterns or [])
        if not patterns:
            return 0

        target_week = pattern_week_number(current_date, block_start)
        target_dow = pattern_day_of_week(current_date)
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
        target_week = pattern_week_number(current_date, block_dates.start_date)
        target_dow = pattern_day_of_week(current_date)

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
        return code in CLINIC_PATTERN_CODES or display in CLINIC_PATTERN_CODES

    def _is_time_off_pattern_activity(self, activity: Activity | None) -> bool:
        if not activity:
            return False
        category = (activity.activity_category or "").strip().lower()
        if category == "time_off":
            return True
        code = (activity.code or "").strip().upper()
        return code in {"OFF", "W"}

    def _load_fmit_call(self, start_date: date, end_date: date) -> int:
        created_calls = 0
        from app.models.call_assignment import CallAssignment

        stmt = (
            select(InpatientPreload)
            .where(
                InpatientPreload.rotation_type == InpatientRotationType.FMIT,
                InpatientPreload.start_date <= end_date,
                InpatientPreload.end_date >= start_date,
            )
            .options(selectinload(InpatientPreload.person))
        )
        preloads = self.session.execute(stmt).scalars().all()

        for preload in preloads:
            if not preload.person or preload.person.type != "faculty":
                continue
            current = max(preload.start_date, start_date)
            end = min(preload.end_date, end_date)

            while current <= end:
                if current.weekday() in (4, 5):
                    existing_call = (
                        self.session.execute(
                            select(CallAssignment).where(
                                CallAssignment.person_id == preload.person_id,
                                CallAssignment.date == current,
                                CallAssignment.call_type == "overnight",
                            )
                        )
                        .scalars()
                        .first()
                    )
                    if not existing_call:
                        self.session.add(
                            CallAssignment(
                                person_id=preload.person_id,
                                date=current,
                                call_type="overnight",
                                is_weekend=current.weekday() >= 5,
                            )
                        )
                        created_calls += 1
                current += timedelta(days=1)

        if created_calls:
            self.session.flush()
        logger.info(f"Created {created_calls} FMIT call assignments")
        return created_calls

    def _load_inpatient_clinic(self, block_number: int, academic_year: int) -> int:
        count = 0
        ci_id = self._activity_cache.get(
            "C-I", required=False
        ) or self._activity_cache.get("C")

        block_dates = get_block_dates(block_number, academic_year)
        start_date = block_dates.start_date
        end_date = block_dates.end_date

        stmt = (
            select(InpatientPreload)
            .options(selectinload(InpatientPreload.person))
            .where(
                InpatientPreload.rotation_type == InpatientRotationType.FMIT,
                InpatientPreload.start_date <= end_date,
                InpatientPreload.end_date >= start_date,
            )
        )
        preloads = self.session.execute(stmt).scalars().all()

        for preload in preloads:
            person = preload.person
            if not person:
                continue
            pgy = person.pgy_level or 0
            if pgy == 0:
                continue

            if pgy == 1:
                target_dow, target_time = 2, "AM"
            elif pgy == 2:
                target_dow, target_time = 1, "PM"
            elif pgy == 3:
                target_dow, target_time = 0, "PM"
            else:
                continue

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
        count = 0
        call_id = self._activity_cache.get("CALL")

        stmt = select(ResidentCallPreload).where(
            ResidentCallPreload.call_date >= start_date,
            ResidentCallPreload.call_date <= end_date,
        )
        preloads = self.session.execute(stmt).scalars().all()

        for preload in preloads:
            if self._create_preload(
                preload.person_id, preload.call_date, "PM", call_id
            ):
                count += 1

        logger.info(f"Loaded {count} resident call preloads")
        return count

    def _load_faculty_call(self, start_date: date, end_date: date) -> int:
        count = 0
        call_id = self._activity_cache.get("CALL")
        pcat_id = self._activity_cache.get("PCAT")
        do_id = self._activity_cache.get("DO")

        stmt = select(CallAssignment).where(
            CallAssignment.date >= start_date,
            CallAssignment.date <= end_date,
        )
        calls = self.session.execute(stmt).scalars().all()

        for call in calls:
            if self._create_preload(call.person_id, call.date, "PM", call_id):
                count += 1

            next_day = call.date + timedelta(days=1)
            if not self._is_on_fmit(call.person_id, next_day):
                if self._create_preload(call.person_id, next_day, "AM", pcat_id):
                    count += 1
                if self._create_preload(call.person_id, next_day, "PM", do_id):
                    count += 1

        logger.info(f"Loaded {count} faculty call preloads")
        return count

    def _load_sm_preloads(self, start_date: date, end_date: date) -> int:
        count = 0
        asm_id = self._activity_cache.get("aSM", required=False)
        if not asm_id:
            return 0

        stmt = (
            select(BlockAssignment)
            .options(selectinload(BlockAssignment.rotation_template))
            .where(
                BlockAssignment.rotation_template.has(abbreviation="SM"),
            )
        )
        sm_assignments = self.session.execute(stmt).scalars().all()

        for assignment in sm_assignments:
            current = start_date
            while current <= end_date:
                if current.weekday() == 2:
                    if self._create_preload(
                        assignment.resident_id, current, "AM", asm_id
                    ):
                        count += 1
                current += timedelta(days=1)

        logger.info(f"Loaded {count} SM preloads")
        return count

    def _load_faculty_wednesday_pm_lec(self, start_date: date, end_date: date) -> int:
        """Preload LEC for all core faculty on regular Wednesday PMs.

        Wednesday PM is protected didactic time at TAMC — residents have LEC
        (injected by rotation_codes.py), and faculty should attend LEC/didactic
        rather than seeing patients. The solver skips preloaded slots, so this
        prevents faculty from being scheduled into clinic on Wednesday PM.

        Skips 4th Wednesdays (day >= 22) — those use an inverted schedule where
        one faculty covers clinic. Also skips faculty on FMIT rotation (they
        follow their own FMIT schedule).
        """
        count = 0
        lec_id = self._activity_cache.get("LEC", required=False)
        if not lec_id:
            logger.warning("LEC activity not found — skipping faculty Wed PM preload")
            return 0

        from app.models.person import FacultyRole

        # Core faculty only (exclude adjuncts — hand-jammed by coordinator)
        core_faculty = (
            self.session.query(Person)
            .filter(
                Person.type == "faculty",
                Person.faculty_role != FacultyRole.ADJUNCT.value,
            )
            .all()
        )
        if not core_faculty:
            return 0

        # Build set of faculty on FMIT rotation (they keep their FMIT schedule)
        fmit_faculty_dates: set[tuple[UUID, date]] = set()
        fmit_stmt = select(InpatientPreload).where(
            InpatientPreload.rotation_type == InpatientRotationType.FMIT,
            InpatientPreload.start_date <= end_date,
            InpatientPreload.end_date >= start_date,
        )
        fmit_preloads = self.session.execute(fmit_stmt).scalars().all()
        for fp in fmit_preloads:
            current = max(fp.start_date, start_date)
            fmit_end = min(fp.end_date, end_date)
            while current <= fmit_end:
                fmit_faculty_dates.add((fp.person_id, current))
                current += timedelta(days=1)

        # Iterate over all dates in range, find regular Wednesdays
        current = start_date
        while current <= end_date:
            if current.weekday() == 2 and current.day < 22:
                # Regular Wednesday (not 4th) — preload LEC for PM
                for faculty in core_faculty:
                    if (faculty.id, current) in fmit_faculty_dates:
                        continue
                    if self._create_preload(faculty.id, current, "PM", lec_id):
                        count += 1
            current += timedelta(days=1)

        logger.info(f"Loaded {count} faculty Wednesday PM LEC preloads")
        return count

    def _load_compound_rotation_weekends(
        self,
        block_number: int,
        academic_year: int,
        start_date: date,
        end_date: date,
    ) -> int:
        count = 0
        w_id = self._activity_cache.get("W")

        stmt = (
            select(BlockAssignment)
            .options(selectinload(BlockAssignment.rotation_template))
            .options(selectinload(BlockAssignment.secondary_rotation_template))
            .where(
                BlockAssignment.block_number == block_number,
                BlockAssignment.academic_year == academic_year,
            )
        )
        assignments = self.session.execute(stmt).scalars().all()

        mid_block_date = start_date + timedelta(days=11)

        for assignment in assignments:
            if not assignment.rotation_template:
                continue

            primary_template = assignment.rotation_template
            secondary_template = assignment.secondary_rotation_template
            primary_code = canonical_rotation_code(
                self._rotation_label(primary_template)
            )
            secondary_code = canonical_rotation_code(
                self._rotation_label(secondary_template)
            )

            first_half_no_weekend = False
            second_half_no_weekend = False

            if secondary_template:
                first_is_night_float = primary_code in NIGHT_FLOAT_ROTATIONS
                second_is_night_float = secondary_code in NIGHT_FLOAT_ROTATIONS

                if not first_is_night_float and not second_is_night_float:
                    continue

                if (
                    not first_is_night_float
                    and not primary_template.includes_weekend_work
                    and primary_code not in OFFSITE_ROTATIONS
                ):
                    first_half_no_weekend = True

                if (
                    not second_is_night_float
                    and not secondary_template.includes_weekend_work
                    and secondary_code not in OFFSITE_ROTATIONS
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

            current = start_date
            while current <= end_date:
                is_weekend = current.weekday() >= 5
                if not is_weekend:
                    current += timedelta(days=1)
                    continue

                is_first_half = current < mid_block_date
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

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

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

        stmt = select(HalfDayAssignment).where(
            HalfDayAssignment.person_id == person_id,
            HalfDayAssignment.date == date_val,
            HalfDayAssignment.time_of_day == time_of_day,
        )
        existing = self.session.execute(stmt).scalars().first()

        if existing:
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
                if (
                    existing.activity_id == activity_id
                    and capacity_flag is not None
                    and existing.counts_toward_fmc_capacity != capacity_flag
                ):
                    existing.counts_toward_fmc_capacity = capacity_flag
                    return True
            return False

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
            pgcode = getattr(e.orig, "pgcode", "unknown")
            logger.error(
                f"Unexpected IntegrityError (pgcode={pgcode}): {e.orig}. "
                f"person_id={person_id}, date={date_val}, time_of_day={time_of_day}, "
                f"activity_id={activity_id}"
            )
            raise

    def _is_on_fmit(self, person_id: UUID, date_val: date) -> bool:
        stmt = select(InpatientPreload).where(
            InpatientPreload.person_id == person_id,
            InpatientPreload.rotation_type == InpatientRotationType.FMIT,
            InpatientPreload.start_date <= date_val,
            InpatientPreload.end_date >= date_val,
        )
        return self.session.execute(stmt).scalars().first() is not None
