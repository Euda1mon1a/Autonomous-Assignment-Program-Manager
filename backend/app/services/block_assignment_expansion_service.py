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
from app.models.activity import Activity
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.block_assignment import BlockAssignment
from app.models.half_day_assignment import AssignmentSource, HalfDayAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.utils.academic_blocks import get_block_dates

logger = get_logger(__name__)


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  TAMC SCHEDULING CONSTANTS - from coworker's TAMC_SCHEDULING_CONTEXT.md      ║
# ║  These align with the Excel Block Template2 patterns.                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Night Float rotations: AM is OFF (or specific activity), PM is night float work
# These residents work nights, not days
NIGHT_FLOAT_PATTERNS: dict[str, tuple[str, str]] = {
    "NF": ("OFF-AM", "NF"),  # Night Float: OFF morning, NF evening
    "NF-ENDO": ("OFF-AM", "NF"),  # Night Float + Endo: same pattern
    "NEURO-NF": (
        "NEURO",
        "NF",
    ),  # Neurology mornings, NF evenings (first half of block)
    "PNF": ("OFF-AM", "PNF"),  # Peds Night Float
    # NOTE: LDNF and KAPI-LD removed - they have special patterns handled separately
}

# Kapiolani L&D rotations - special off-site pattern
KAPIOLANI_ROTATIONS = frozenset(["KAP", "KAPI-LD", "Kapiolani L and D"])

# L&D Night Float rotations - Friday AM clinic pattern (NOT Wednesday!)
LDNF_ROTATIONS = frozenset(["LDNF", "L and D night float", "L&D Night Float"])

# Internal Medicine rotations - inpatient, works weekends
IM_ROTATIONS = frozenset(["IM", "Internal Medicine", "IM-INT"])

# Pediatrics Ward rotations - inpatient, works weekends
PEDW_ROTATIONS = frozenset(["PedW", "Peds Ward", "Pediatrics Ward", "PEDS-W"])

# FM Inpatient Team rotations - inpatient, works weekends
FMIT_ROTATIONS = frozenset(["FMIT", "FMIT 2", "FM Inpatient Team"])

# Rotations exempt from Wednesday PM LEC (they work nights or are off-site)
LEC_EXEMPT_ROTATIONS = frozenset(
    [
        "NF",
        "NF-ENDO",
        "NEURO-NF",
        "PNF",
        "LDNF",
        "KAPI-LD",
        "HILO",
        "TDY",
    ]
)

# Wednesday constants
WEDNESDAY_DOW = 3  # ISO weekday: 1=Mon, ..., 3=Wed
LEC_TEMPLATE_ABBREV = "LEC-PM"
ADV_TEMPLATE_ABBREV = "ADV"  # Advising (last Wednesday PM)

# Mid-block transition (28-day block, switch at day 11 = start of Week 3)
# TAMC weeks: Week 1 (Thu-Sun, days 0-3), Week 2 (Mon-Sun, days 4-10),
#             Week 3 (Mon-Sun, days 11-17), Week 4 (Mon-Sun, days 18-24)
# Column 28 in Excel = day 11 = start of second-half rotations
MID_BLOCK_DAY = 11

# Intern continuity rule: PGY-1 gets clinic on Wednesday AM (except exempt rotations)
# These rotations are exempt because they work nights, are off-site, or have special scheduling
# NOTE: FMIT removed - PGY-1 on FMIT now gets Wed AM = C (handled by explicit pattern method)
INTERN_CONTINUITY_EXEMPT = frozenset(
    [
        "NF",
        "PNF",
        "LDNF",
        "TDY",
        "HILO",
        "KAPI-LD",
        "PedNF",
        "Peds NF",
    ]
)

# Clinic template abbreviation for intern continuity
CLINIC_TEMPLATE_ABBREV = "C"


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
        self._activity_cache: dict[str, Activity | None] = {}

    def expand_block_assignments(
        self,
        block_number: int,
        academic_year: int,
        schedule_run_id: UUID | None = None,
        created_by: str = "expansion_service",
        apply_one_in_seven: bool = True,
        persist_half_day: bool = False,
    ) -> list[Assignment]:
        """
        Expand all BlockAssignments for a block into daily Assignments.

        Args:
            block_number: Academic block number (1-13)
            academic_year: Academic year (e.g., 2025 for AY 2025-2026)
            schedule_run_id: Optional provenance tracking ID
            created_by: Audit field for who created assignments
            apply_one_in_seven: Whether to enforce 1-in-7 day off rule
            persist_half_day: If True, also persist HalfDayAssignment records (dual-write)

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
        all_half_day_assignments: list[HalfDayAssignment] = []
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

            # Dual-write: Also create HalfDayAssignment records
            if persist_half_day:
                half_day_records = self._persist_to_half_day_assignments(
                    assignments, block_assignment
                )
                all_half_day_assignments.extend(half_day_records)

        logger.info(f"Expanded to {len(all_assignments)} daily assignments")
        if persist_half_day:
            logger.info(
                f"Created {len(all_half_day_assignments)} half-day assignment records"
            )
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
                # Also load secondary rotation for mid-block transitions
                selectinload(BlockAssignment.secondary_rotation_template).selectinload(
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
        """Pre-load absence/placeholder rotation templates for 56-slot expansion.

        These templates (W-AM, W-PM, LV-AM, LV-PM, OFF-AM, OFF-PM, LEC-PM) are used to
        create placeholder assignments for weekends, absences, days off, and protected time.
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
                    "LEC-PM",  # Protected lecture time (Wednesday PM)
                    "LEC",  # Last Wednesday AM (all residents attend)
                    "ADV",  # Last Wednesday PM (advising for all)
                    "C",  # Clinic (for intern continuity rule)
                ]
            )
        )
        for rt in self.db.execute(stmt).scalars():
            self._absence_templates[rt.abbreviation] = rt
        logger.info(f"Pre-loaded {len(self._absence_templates)} placeholder templates")

    def _get_absence_template(self, abbrev: str) -> RotationTemplate | None:
        """Get absence rotation template by abbreviation (cached)."""
        if not hasattr(self, "_absence_templates"):
            self._preload_absence_templates()
        return self._absence_templates.get(abbrev)

    def _lookup_activity_by_abbreviation(self, abbreviation: str) -> Activity | None:
        """Lookup Activity by display_abbreviation or code (cached).

        Handles absence template suffixes (-AM/-PM) by stripping them for lookup.
        E.g., "W-AM" -> looks up "W-AM" first, then "W" as fallback.

        Args:
            abbreviation: Activity display_abbreviation (e.g., 'C', 'LEC', 'FMIT', 'W-AM')

        Returns:
            Activity if found, None otherwise
        """
        if abbreviation not in self._activity_cache:
            # Try display_abbreviation first, then code
            stmt = select(Activity).where(
                (Activity.display_abbreviation == abbreviation)
                | (Activity.code == abbreviation)
            )
            result = self.db.execute(stmt)
            activity = result.scalars().first()

            # Fallback: strip -AM/-PM suffix for absence templates
            # (e.g., "W-AM" -> "W", "LV-PM" -> "LV", "HOL-AM" -> "HOL")
            if activity is None and abbreviation.endswith(("-AM", "-PM")):
                base_code = abbreviation.rsplit("-", 1)[0]
                stmt = select(Activity).where(
                    (Activity.display_abbreviation == base_code)
                    | (Activity.code == base_code)
                )
                result = self.db.execute(stmt)
                activity = result.scalars().first()

            self._activity_cache[abbreviation] = activity
        return self._activity_cache.get(abbreviation)

    def _get_active_rotation(
        self,
        block_assignment: BlockAssignment,
        day_index: int,
    ) -> RotationTemplate | None:
        """Get the active rotation for a given day (handles mid-block transitions).

        Mid-block transitions: Some residents switch rotations at day 14.
        - Days 0-13: Use primary rotation_template
        - Days 14-27: Use secondary_rotation_template (if set)
        """
        if (
            block_assignment.secondary_rotation_template_id
            and day_index >= MID_BLOCK_DAY
        ):
            return block_assignment.secondary_rotation_template
        return block_assignment.rotation_template

    def _is_wednesday(self, current_date: date) -> bool:
        """Check if date is Wednesday (for LEC assignment)."""
        return current_date.isoweekday() == WEDNESDAY_DOW

    def _is_last_wednesday_of_block(
        self,
        current_date: date,
        end_date: date,
    ) -> bool:
        """Check if this is the last Wednesday of the block.

        Last Wednesday has special rules:
        - AM = LEC (for ALL residents, including exempt rotations)
        - PM = ADV (advising, for ALL residents)

        Args:
            current_date: The date to check
            end_date: The last day of the block

        Returns:
            True if this is the last Wednesday of the block
        """
        if not self._is_wednesday(current_date):
            return False
        # Check if there are any more Wednesdays before end_date
        next_wed = current_date + timedelta(days=7)
        return next_wed > end_date

    def _should_apply_intern_continuity(
        self,
        block_assignment: BlockAssignment,
        rotation: RotationTemplate,
        current_date: date,
    ) -> bool:
        """Check if intern continuity rule applies (PGY-1 Wed AM = Clinic).

        Intern continuity rule:
        - PGY-1 interns get Clinic on Wednesday AM
        - This applies REGARDLESS of their rotation
        - EXCEPT for exempt rotations (NF, LDNF, FMIT, TDY, off-site)

        Args:
            block_assignment: The block assignment (to get PGY level)
            rotation: The active rotation for this day
            current_date: The date to check

        Returns:
            True if intern continuity should apply
        """
        if not self._is_wednesday(current_date):
            return False

        # Check if PGY-1 (intern)
        resident = block_assignment.resident
        if not resident or resident.pgy_level != 1:
            return False

        # Check if rotation is exempt
        if rotation.abbreviation in INTERN_CONTINUITY_EXEMPT:
            return False

        return True

    def _should_use_lec(self, rotation: RotationTemplate, current_date: date) -> bool:
        """Check if this slot should use LEC template (Wednesday PM, non-exempt rotation)."""
        if not self._is_wednesday(current_date):
            return False
        if rotation.abbreviation in LEC_EXEMPT_ROTATIONS:
            return False
        return True

    def _get_kapiolani_assignment(
        self,
        current_date: date,
        time_of_day: str,
        is_last_wed: bool,
    ) -> str:
        """
        Get assignment code for Kapiolani L&D rotation (off-site).

        Pattern:
        - Mon: KAP / OFF (travel back from Kapiolani)
        - Tue: OFF / OFF (recovery day)
        - Wed: C / LEC (continuity clinic + lecture)
        - Thu-Sun: KAP / KAP (on-site at Kapiolani)

        Last Wednesday overrides: LEC / ADV
        """
        dow = current_date.isoweekday()  # 1=Mon, 2=Tue, 3=Wed, ...
        is_am = time_of_day == "AM"

        # Last Wednesday rule takes priority
        if is_last_wed:
            return "LEC" if is_am else "ADV"

        if dow == 1:  # Monday
            return "KAP" if is_am else "OFF"
        elif dow == 2:  # Tuesday
            return "OFF"  # Both AM and PM
        elif dow == 3:  # Wednesday
            return "C" if is_am else "LEC"
        else:  # Thu-Sun (4, 5, 6, 7)
            return "KAP"

    def _get_ldnf_assignment(
        self,
        current_date: date,
        time_of_day: str,
        is_last_wed: bool,
    ) -> str:
        """
        Get assignment code for L&D Night Float rotation.

        CRITICAL: Friday MORNING clinic (not Wednesday!)

        Pattern:
        - Mon-Thu: OFF / LDNF (sleeping days, working nights)
        - Fri: C / OFF (Friday AM clinic!)
        - Sat-Sun: W / W (weekend off)

        Last Wednesday overrides: LEC / ADV
        """
        dow = current_date.isoweekday()  # 1=Mon...5=Fri, 6=Sat, 7=Sun
        is_am = time_of_day == "AM"

        # Last Wednesday rule takes priority
        if is_last_wed:
            return "LEC" if is_am else "ADV"

        if dow == 5:  # Friday
            return "C" if is_am else "OFF"  # FRIDAY clinic!
        elif dow in (6, 7):  # Weekend
            return "W"
        else:  # Mon-Thu
            return "OFF" if is_am else "LDNF"

    def _get_im_assignment(
        self,
        current_date: date,
        time_of_day: str,
        is_last_wed: bool,
        pgy_level: int,
    ) -> str:
        """
        Internal Medicine rotation - inpatient, works weekends.

        Pattern:
        - All days: IM / IM (works including weekends)
        - Continuity clinic: PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
        - Last Wednesday: LEC / ADV
        """
        # Last Wednesday rule takes priority
        if is_last_wed:
            return "LEC" if time_of_day == "AM" else "ADV"

        # Continuity clinic based on PGY level
        if self._should_have_continuity_clinic(current_date, time_of_day, pgy_level):
            return "C"

        # All other times: IM
        return "IM"

    def _get_pedw_assignment(
        self,
        current_date: date,
        time_of_day: str,
        is_last_wed: bool,
        pgy_level: int,
    ) -> str:
        """
        Peds Ward rotation - inpatient, works weekends.

        Pattern:
        - All days: PedW / PedW (works including weekends)
        - Continuity clinic: PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
        - Last Wednesday: LEC / ADV
        """
        # Last Wednesday rule takes priority
        if is_last_wed:
            return "LEC" if time_of_day == "AM" else "ADV"

        # Continuity clinic based on PGY level
        if self._should_have_continuity_clinic(current_date, time_of_day, pgy_level):
            return "C"

        # All other times: PedW
        return "PedW"

    def _is_pgy1(self, block_assignment: BlockAssignment) -> bool:
        """Check if resident is PGY-1 (intern)."""
        if block_assignment.resident and hasattr(
            block_assignment.resident, "pgy_level"
        ):
            return block_assignment.resident.pgy_level == 1
        return False

    def _get_pgy_level(self, block_assignment: BlockAssignment) -> int:
        """Get resident's PGY level (1, 2, or 3)."""
        if block_assignment.resident and hasattr(
            block_assignment.resident, "pgy_level"
        ):
            return block_assignment.resident.pgy_level or 0
        return 0

    def _should_have_continuity_clinic(
        self,
        current_date: date,
        time_of_day: str,
        pgy_level: int,
    ) -> bool:
        """
        Check if this slot should be continuity clinic based on PGY level.

        Continuity clinic schedule for inpatient rotations:
        - PGY-1: Wednesday AM
        - PGY-2: Tuesday PM
        - PGY-3: Monday PM
        """
        dow = current_date.isoweekday()  # 1=Mon, 2=Tue, 3=Wed, ...
        is_am = time_of_day == "AM"

        if pgy_level == 1:
            return dow == 3 and is_am  # Wed AM
        elif pgy_level == 2:
            return dow == 2 and not is_am  # Tue PM
        elif pgy_level == 3:
            return dow == 1 and not is_am  # Mon PM
        return False

    def _get_fmit_assignment(
        self,
        current_date: date,
        time_of_day: str,
        is_last_wed: bool,
        pgy_level: int,
    ) -> str:
        """
        FM Inpatient Team rotation - inpatient, works weekends.

        Pattern:
        - All days: FMIT / FMIT (works including weekends)
        - Continuity clinic: PGY-1 Wed AM, PGY-2 Tue PM, PGY-3 Mon PM
        - Last Wednesday: LEC / ADV
        """
        # Last Wednesday rule takes priority
        if is_last_wed:
            return "LEC" if time_of_day == "AM" else "ADV"

        # Continuity clinic based on PGY level
        if self._should_have_continuity_clinic(current_date, time_of_day, pgy_level):
            return "C"

        # All other times: FMIT
        return "FMIT"

    def _get_night_float_template_abbrev(
        self,
        rotation: RotationTemplate,
        time_of_day: str,
    ) -> str | None:
        """Get the template abbreviation for night float rotations.

        Night float rotations have special AM/PM patterns:
        - NF: OFF-AM / NF
        - Peds NF: OFF-AM / PNF
        - L&D NF: L&D / L&D (works both)
        """
        if rotation.abbreviation in NIGHT_FLOAT_PATTERNS:
            am_abbrev, pm_abbrev = NIGHT_FLOAT_PATTERNS[rotation.abbreviation]
            return am_abbrev if time_of_day == "AM" else pm_abbrev
        return None

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

        # Initial rotation (may change mid-block)
        initial_rotation = block_assignment.rotation_template
        if not initial_rotation:
            logger.warning(
                f"BlockAssignment {block_assignment.id} has no rotation template"
            )
            return []

        # Pre-load placeholder templates for LEC, OFF, etc.
        self._preload_absence_templates()

        # Cache weekly patterns for both rotations (if mid-block transition)
        patterns_cache: dict[UUID, dict] = {}
        patterns_cache[initial_rotation.id] = self._get_weekly_patterns(
            initial_rotation
        )
        if block_assignment.secondary_rotation_template:
            patterns_cache[block_assignment.secondary_rotation_template.id] = (
                self._get_weekly_patterns(block_assignment.secondary_rotation_template)
            )

        # Track consecutive work days for 1-in-7 rule
        consecutive_days = 0
        last_day_off = None

        current_date = start_date
        day_index = 0

        while current_date <= end_date:
            # ╔══════════════════════════════════════════════════════════════════╗
            # ║  MID-BLOCK ROTATION TRANSITION (Session 095e)                    ║
            # ║  Get active rotation based on day_index (switches at day 14)     ║
            # ╚══════════════════════════════════════════════════════════════════╝
            rotation = self._get_active_rotation(block_assignment, day_index)
            if not rotation:
                current_date += timedelta(days=1)
                day_index += 1
                continue

            patterns = patterns_cache.get(rotation.id, {})
            includes_weekends = rotation.includes_weekend_work
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

            # Check if non-operational day (DONSA, EO closure)
            # Non-operational = only essential personnel work (same as weekend rule)
            is_non_operational = am_block.is_non_operational if am_block else False
            skip_non_operational = is_non_operational and not includes_weekends

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
            should_skip = (
                is_absent
                or skip_weekend
                or skip_holiday
                or skip_non_operational
                or force_day_off
            )
            if should_skip:
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
                    is_non_operational=skip_non_operational,
                    is_day_off=force_day_off,
                )

                if (
                    not is_absent and not skip_holiday and not skip_non_operational
                ):  # PAUSE: Only reset for SCHEDULED day off
                    consecutive_days = 0
                    last_day_off = current_date
                # Absence: counter HOLDS (no reset) - correct ACGME interpretation
                current_date += timedelta(days=1)
                day_index += 1
                continue

            # ╔══════════════════════════════════════════════════════════════════╗
            # ║  ROTATION-SPECIFIC PATTERNS (KAP, LDNF)                            ║
            # ║  These rotations have special day-of-week patterns that override   ║
            # ║  the default rotation template. Handle them BEFORE default logic.  ║
            # ╚══════════════════════════════════════════════════════════════════╝
            is_last_wed = self._is_last_wednesday_of_block(current_date, end_date)

            # Kapiolani L&D rotation - special off-site pattern
            if rotation.abbreviation in KAPIOLANI_ROTATIONS:
                am_block = self._block_cache.get((current_date, "AM"))
                pm_block = self._block_cache.get((current_date, "PM"))

                if am_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "AM"
                ):
                    kap_am_code = self._get_kapiolani_assignment(
                        current_date, "AM", is_last_wed
                    )
                    kap_am_template = self._get_absence_template(kap_am_code)
                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                kap_am_template.id if kap_am_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                if pm_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "PM"
                ):
                    kap_pm_code = self._get_kapiolani_assignment(
                        current_date, "PM", is_last_wed
                    )
                    kap_pm_template = self._get_absence_template(kap_pm_code)
                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                kap_pm_template.id if kap_pm_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                consecutive_days += 1
                current_date += timedelta(days=1)
                day_index += 1
                continue  # Skip default AM/PM processing

            # L&D Night Float rotation - Friday AM clinic pattern
            if rotation.abbreviation in LDNF_ROTATIONS:
                am_block = self._block_cache.get((current_date, "AM"))
                pm_block = self._block_cache.get((current_date, "PM"))

                if am_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "AM"
                ):
                    ldnf_am_code = self._get_ldnf_assignment(
                        current_date, "AM", is_last_wed
                    )
                    ldnf_am_template = self._get_absence_template(ldnf_am_code)
                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                ldnf_am_template.id if ldnf_am_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                if pm_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "PM"
                ):
                    ldnf_pm_code = self._get_ldnf_assignment(
                        current_date, "PM", is_last_wed
                    )
                    ldnf_pm_template = self._get_absence_template(ldnf_pm_code)
                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                ldnf_pm_template.id if ldnf_pm_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                consecutive_days += 1
                current_date += timedelta(days=1)
                day_index += 1
                continue  # Skip default AM/PM processing

            # Internal Medicine rotation - inpatient, works weekends
            if rotation.abbreviation in IM_ROTATIONS:
                am_block = self._block_cache.get((current_date, "AM"))
                pm_block = self._block_cache.get((current_date, "PM"))
                pgy_level = self._get_pgy_level(block_assignment)

                if am_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "AM"
                ):
                    im_am_code = self._get_im_assignment(
                        current_date, "AM", is_last_wed, pgy_level
                    )
                    im_am_template = self._get_absence_template(im_am_code)
                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                im_am_template.id if im_am_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                if pm_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "PM"
                ):
                    im_pm_code = self._get_im_assignment(
                        current_date, "PM", is_last_wed, pgy_level
                    )
                    im_pm_template = self._get_absence_template(im_pm_code)
                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                im_pm_template.id if im_pm_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                consecutive_days += 1
                current_date += timedelta(days=1)
                day_index += 1
                continue  # Skip default AM/PM processing

            # Peds Ward rotation - inpatient, works weekends
            if rotation.abbreviation in PEDW_ROTATIONS:
                am_block = self._block_cache.get((current_date, "AM"))
                pm_block = self._block_cache.get((current_date, "PM"))
                pgy_level = self._get_pgy_level(block_assignment)

                if am_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "AM"
                ):
                    pedw_am_code = self._get_pedw_assignment(
                        current_date, "AM", is_last_wed, pgy_level
                    )
                    pedw_am_template = self._get_absence_template(pedw_am_code)
                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                pedw_am_template.id if pedw_am_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                if pm_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "PM"
                ):
                    pedw_pm_code = self._get_pedw_assignment(
                        current_date, "PM", is_last_wed, pgy_level
                    )
                    pedw_pm_template = self._get_absence_template(pedw_pm_code)
                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                pedw_pm_template.id if pedw_pm_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                consecutive_days += 1
                current_date += timedelta(days=1)
                day_index += 1
                continue  # Skip default AM/PM processing

            # FM Inpatient Team rotation - inpatient, works weekends
            if rotation.abbreviation in FMIT_ROTATIONS:
                am_block = self._block_cache.get((current_date, "AM"))
                pm_block = self._block_cache.get((current_date, "PM"))
                pgy_level = self._get_pgy_level(block_assignment)

                if am_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "AM"
                ):
                    fmit_am_code = self._get_fmit_assignment(
                        current_date, "AM", is_last_wed, pgy_level
                    )
                    fmit_am_template = self._get_absence_template(fmit_am_code)
                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                fmit_am_template.id if fmit_am_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                if pm_block and not self._is_person_absent_slot(
                    block_assignment.resident_id, current_date, "PM"
                ):
                    fmit_pm_code = self._get_fmit_assignment(
                        current_date, "PM", is_last_wed, pgy_level
                    )
                    fmit_pm_template = self._get_absence_template(fmit_pm_code)
                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=(
                                fmit_pm_template.id if fmit_pm_template else rotation.id
                            ),
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

                consecutive_days += 1
                current_date += timedelta(days=1)
                day_index += 1
                continue  # Skip default AM/PM processing

            # ╔══════════════════════════════════════════════════════════════════╗
            # ║  AM SLOT ASSIGNMENT                                                 ║
            # ║  Priority: Last Wed LEC > Intern Continuity C > Night Float > Default ║
            # ╚══════════════════════════════════════════════════════════════════╝
            am_activity = self._get_slot_activity(
                patterns, day_of_week, "AM", week_number
            )
            if am_activity and not self._is_person_absent_slot(
                block_assignment.resident_id, current_date, "AM"
            ):
                am_block = self._block_cache.get((current_date, "AM"))
                if am_block:
                    am_template_id = rotation.id  # Default to rotation

                    # Rule 1: Last Wednesday AM = LEC for ALL residents
                    if self._is_last_wednesday_of_block(current_date, end_date):
                        lec_template = self._get_absence_template("LEC")
                        if lec_template:
                            am_template_id = lec_template.id

                    # Rule 2: Intern Continuity - PGY-1 Wed AM = Clinic
                    # (only if not last Wednesday, which takes precedence)
                    elif self._should_apply_intern_continuity(
                        block_assignment, rotation, current_date
                    ):
                        clinic_template = self._get_absence_template(
                            CLINIC_TEMPLATE_ABBREV
                        )
                        if clinic_template:
                            am_template_id = clinic_template.id

                    # Rule 3: Night float AM pattern (OFF-AM for NF rotations)
                    else:
                        nf_am_abbrev = self._get_night_float_template_abbrev(
                            rotation, "AM"
                        )
                        if nf_am_abbrev and nf_am_abbrev.startswith("OFF"):
                            off_template = self._get_absence_template("OFF-AM")
                            if off_template:
                                am_template_id = off_template.id

                    assignments.append(
                        Assignment(
                            block_id=am_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=am_template_id,
                            role="primary",
                            schedule_run_id=schedule_run_id,
                            created_by=created_by,
                        )
                    )

            # ╔══════════════════════════════════════════════════════════════════╗
            # ║  PM SLOT ASSIGNMENT                                                 ║
            # ║  Priority: Last Wed ADV > Regular Wed LEC > Default                ║
            # ╚══════════════════════════════════════════════════════════════════╝
            pm_activity = self._get_slot_activity(
                patterns, day_of_week, "PM", week_number
            )
            if pm_activity and not self._is_person_absent_slot(
                block_assignment.resident_id, current_date, "PM"
            ):
                pm_block = self._block_cache.get((current_date, "PM"))
                if pm_block:
                    pm_template_id = rotation.id  # Default to rotation

                    # Rule 1: Last Wednesday PM = ADV for ALL residents
                    if self._is_last_wednesday_of_block(current_date, end_date):
                        adv_template = self._get_absence_template(ADV_TEMPLATE_ABBREV)
                        if adv_template:
                            pm_template_id = adv_template.id

                    # Rule 2: Regular Wednesday PM = LEC (except exempt rotations)
                    elif self._should_use_lec(rotation, current_date):
                        lec_template = self._get_absence_template(LEC_TEMPLATE_ABBREV)
                        if lec_template:
                            pm_template_id = lec_template.id

                    assignments.append(
                        Assignment(
                            block_id=pm_block.id,
                            person_id=block_assignment.resident_id,
                            rotation_template_id=pm_template_id,
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
        is_non_operational: bool = False,
        is_day_off: bool = False,
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
        - NOP-AM, NOP-PM: Non-operational day (DONSA, EO closure)
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
            is_non_operational: True if non-operational day (DONSA, EO closure)
            is_day_off: True if 1-in-7 rule forces day off
        """
        # Determine which absence template to use (priority order)
        if is_absent:
            am_abbrev, pm_abbrev = "LV-AM", "LV-PM"
        elif is_weekend:
            am_abbrev, pm_abbrev = "W-AM", "W-PM"
        elif is_holiday:
            am_abbrev, pm_abbrev = "HOL-AM", "HOL-PM"
        elif is_non_operational:
            # Use HOL templates as fallback until NOP templates are created
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

    # ╔══════════════════════════════════════════════════════════════════════════════╗
    # ║  DUAL-WRITE: Assignment → HalfDayAssignment                                  ║
    # ║  Persists half-day records for the new data model (Session 104)              ║
    # ╚══════════════════════════════════════════════════════════════════════════════╝

    def _persist_to_half_day_assignments(
        self,
        assignments: list[Assignment],
        block_assignment: BlockAssignment,
    ) -> list[HalfDayAssignment]:
        """
        Dual-write: Convert Assignment → HalfDayAssignment with source priority.

        For each Assignment, create or update corresponding HalfDayAssignment record
        respecting the source priority system:
        - preload: Never overwritten (locked by preload service)
        - manual: Never overwritten (locked by manual override)
        - solver: Overwrites template, skipped if preload/manual exists
        - template: Lowest priority, overwritten by all others

        This enables the transition from compute-on-read (Assignment via expansion)
        to persisted half-day slots (HalfDayAssignment table).

        Args:
            assignments: Expanded Assignment records for a single BlockAssignment
            block_assignment: Parent BlockAssignment for provenance tracking

        Returns:
            List of HalfDayAssignment records (added/updated in session, not committed)
        """
        half_day_records: list[HalfDayAssignment] = []

        # Cache rotation template lookups to avoid N+1 queries
        rotation_cache: dict[UUID, RotationTemplate] = {}

        for assignment in assignments:
            # Get Block to extract date and time_of_day
            block = None

            # First try to find block by ID from cache
            for cache_key, cached_block in self._block_cache.items():
                if cached_block.id == assignment.block_id:
                    block = cached_block
                    break

            if not block:
                logger.warning(
                    f"Cannot find block for assignment block_id={assignment.block_id}"
                )
                continue

            # Get rotation template (cached)
            rotation_id = assignment.rotation_template_id
            if rotation_id not in rotation_cache:
                rotation_stmt = select(RotationTemplate).where(
                    RotationTemplate.id == rotation_id
                )
                rotation_cache[rotation_id] = (
                    self.db.execute(rotation_stmt).scalars().first()
                )

            rotation = rotation_cache.get(rotation_id)

            # Lookup activity by rotation abbreviation
            activity = None
            if rotation:
                abbrev = rotation.display_abbreviation or rotation.abbreviation
                if abbrev:
                    activity = self._lookup_activity_by_abbreviation(abbrev)

            # Determine source: time_off activities (W, LV, HOL, OFF) should be preload
            # so activity solver won't overwrite them
            is_time_off = activity and activity.activity_category == "time_off"
            source = (
                AssignmentSource.PRELOAD.value
                if is_time_off
                else AssignmentSource.SOLVER.value
            )

            # Check if slot already has an assignment (source priority check)
            existing_stmt = select(HalfDayAssignment).where(
                HalfDayAssignment.person_id == assignment.person_id,
                HalfDayAssignment.date == block.date,
                HalfDayAssignment.time_of_day == block.time_of_day,
            )
            existing = self.db.execute(existing_stmt).scalars().first()

            if existing:
                # Check source priority - skip if locked (preload/manual)
                if existing.is_locked:
                    logger.debug(
                        f"Skipping solver assignment: slot locked by "
                        f"source={existing.source} for person={assignment.person_id} "
                        f"date={block.date} time={block.time_of_day}"
                    )
                    continue

                # Can overwrite template source
                if existing.source == AssignmentSource.TEMPLATE.value:
                    # Update existing record
                    existing.activity_id = activity.id if activity else None
                    existing.source = source
                    existing.block_assignment_id = block_assignment.id
                    half_day_records.append(existing)
                    continue

                # Existing is also solver - can update (but not if new source is preload)
                if existing.source == AssignmentSource.SOLVER.value:
                    existing.activity_id = activity.id if activity else None
                    existing.source = source  # Upgrade to preload if time_off
                    existing.block_assignment_id = block_assignment.id
                    half_day_records.append(existing)
                    continue

            # Create new HalfDayAssignment record
            half_day = HalfDayAssignment(
                person_id=assignment.person_id,
                date=block.date,
                time_of_day=block.time_of_day,
                activity_id=activity.id if activity else None,
                source=source,
                block_assignment_id=block_assignment.id,
            )
            self.db.add(half_day)
            half_day_records.append(half_day)

        return half_day_records
