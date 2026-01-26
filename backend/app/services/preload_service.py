"""PreloadService - Load locked assignments before solver runs.

This service loads preloaded assignments (FMIT, call, absences, etc.) into
the half_day_assignments table with source='preload'. These assignments
are locked and cannot be overwritten by the solver.

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

Block 10 FMIT Faculty:
- Week 1 (Mar 13-19): Tagawa (overlaps from Block 9)
- Week 2 (Mar 20-26): Chu
- Week 3 (Mar 27-Apr 2): Bevis
- Week 4 (Apr 3-9): Chu
- (LaBounty overlaps into Block 11)

FMIT Residents: Petrie (R3), Cataquiz (R2)
"""

from datetime import date, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.absence import Absence
from app.models.activity import Activity
from app.models.block_assignment import BlockAssignment
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.inpatient_preload import InpatientPreload, InpatientRotationType
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.resident_call_preload import ResidentCallPreload
from app.utils.academic_blocks import get_block_dates

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


class PreloadService:
    """
    Service to load preloaded assignments into half_day_assignments.

    All preloaded assignments have source='preload' and are locked
    (cannot be overwritten by solver).
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._activity_cache: dict[str, UUID] = {}

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

            while current <= end:
                # Get AM/PM activity codes based on rotation type and day of week
                am_code, pm_code = self._get_rotation_codes(
                    preload.rotation_type, current.weekday()
                )

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
                selectinload(BlockAssignment.rotation_template),
                selectinload(BlockAssignment.secondary_rotation_template),
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

                am_code, pm_code = self._get_rotation_preload_codes(
                    rotation_code, current, start_date, end_date, pgy
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
    ) -> tuple[str | None, str | None]:
        """Return AM/PM activity codes that should be preloaded for this slot."""
        if not rotation_code:
            return (None, None)

        if self._is_last_wednesday(current_date, block_end):
            return ("LEC", "ADV")

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

        # Wednesday protected patterns for outpatient rotations
        if current_date.weekday() == 2:  # Wednesday
            am_code = None
            if pgy_level == 1 and not self._is_intern_continuity_exempt(rotation_code):
                am_code = "C"

            pm_code = None
            if not self._is_lec_exempt(rotation_code):
                pm_code = "LEC"

            return (am_code, pm_code)

        return (None, None)

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
        if current_date.weekday() >= 5:
            return ("W", "W")
        if rotation_code == "PEDNF":
            return ("OFF", "PedNF")
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
        if not call_activity_id:
            logger.warning("CALL activity not found, skipping FMIT call preload")
            return 0

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

        ci_activity = await self._get_activity_id("C-I") or await self._get_activity_id(
            "C"
        )
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
        self, rotation_type: str, day_of_week: int
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
        # Day-specific patterns for KAP (Kapiolani L&D)
        # Mon PM=OFF (travel), Tue=OFF/OFF (recovery), Wed AM=C (continuity)
        if rotation_type == "KAP":
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
        if rotation_type == "LDNF":
            if day_of_week == 4:  # Friday
                return ("fm_clinic", "off")  # Friday morning clinic!
            elif day_of_week in (5, 6):  # Weekend
                return ("W", "W")
            else:  # Mon-Thu
                return ("off", "LDNF")  # Working nights, sleeping days

        # Day-specific patterns for NF (Night Float)
        # AM = off (sleeping), PM = NF (working nights)
        if rotation_type == "NF":
            if day_of_week in (5, 6):  # Weekend
                return ("W", "W")
            else:
                return ("off", "NF")

        # Day-specific patterns for PedNF (Peds Night Float)
        if rotation_type == "PedNF":
            if day_of_week in (5, 6):  # Weekend
                return ("W", "W")
            else:
                return ("off", "PedNF")

        # Fixed patterns for other rotations (no day-specific rules)
        codes = {
            "FMIT": ("FMIT", "FMIT"),
            "PedW": ("PedW", "PedW"),
            "IM": ("IM", "IM"),
            "HILO": ("TDY", "TDY"),  # Hilo = TDY activity
            "FMC": ("fm_clinic", "fm_clinic"),  # FMC = fm_clinic activity
        }

        # Fall back to rotation type as activity code (works for most)
        default = self.ROTATION_TO_ACTIVITY.get(rotation_type, rotation_type)
        return codes.get(rotation_type, (default, default))

    async def _get_activity_id(self, code: str) -> UUID | None:
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

        logger.warning(f"Activity not found: {code}")
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
            return None
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
            # Already exists - skip (preload priority already set)
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
