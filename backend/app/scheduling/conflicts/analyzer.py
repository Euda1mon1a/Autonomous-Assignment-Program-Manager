"""
Conflict Analysis Engine.

This module provides the main engine for detecting and analyzing schedule conflicts.
It identifies time overlaps, resource contentions, ACGME violations, and other
scheduling issues.
"""

import hashlib
import logging
import math
import re
from collections import defaultdict
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.activity import Activity
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.half_day_assignment import HalfDayAssignment
from app.models.person import Person
from app.utils.fmc_capacity import activity_is_proc_or_vas
from app.utils.supervision import (
    activity_provides_supervision,
    assignment_requires_fmc_supervision,
)
from app.scheduling.conflicts.types import (
    ACGMEViolationConflict,
    Conflict,
    ConflictSeverity,
    ConflictSummary,
    ConflictType,
    ResourceContentionConflict,
    SupervisionConflict,
    TimeOverlapConflict,
)

logger = logging.getLogger(__name__)


class ConflictAnalyzer:
    """
    Main conflict analysis engine.

    Detects and analyzes various types of schedule conflicts including:
    - Time overlaps (double booking)
    - Resource contention (insufficient coverage)
    - ACGME violations (duty hours, consecutive days)
    - Supervision issues (inadequate ratios)
    - Availability conflicts (assignments during absences)
    """

    # ACGME Constants
    MAX_WEEKLY_HOURS = 80.0
    MAX_CONSECUTIVE_DAYS = 6
    HOURS_PER_BLOCK = 6.0
    ROLLING_WEEKS = 4
    ROLLING_WINDOW_DAYS = 27  # 28 days - 1 (inclusive end date for timedelta)

    # Supervision ratios
    PGY1_RATIO = 2  # 1 faculty per 2 PGY-1 residents
    OTHER_RATIO = 4  # 1 faculty per 4 PGY-2/3 residents

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize the conflict analyzer.

        Args:
            db: Async database session
        """
        self.db = db
        self._time_off_slots: set[tuple[str, date, str]] = set()
        self._time_off_codes = {"W", "OFF", "LV-AM", "LV-PM", "PC"}

    async def analyze_schedule(
        self,
        start_date: date,
        end_date: date,
        person_id: UUID | None = None,
    ) -> list[Conflict]:
        """
        Comprehensive schedule conflict analysis.

        Analyzes the schedule for the given date range and detects all
        types of conflicts. If person_id is provided, only analyze conflicts
        affecting that person.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            person_id: Optional person to focus analysis on

        Returns:
            List of detected conflicts, sorted by severity and urgency
        """
        logger.info(
            f"Analyzing schedule for conflicts: {start_date} to {end_date}"
            + (f" for person {person_id}" if person_id else "")
        )

        conflicts: list[Conflict] = []

        # Detect different types of conflicts
        time_overlaps = await self._detect_time_overlaps(
            start_date, end_date, person_id
        )
        conflicts.extend(time_overlaps)

        supervision_issues = await self._detect_supervision_issues(start_date, end_date)
        conflicts.extend(supervision_issues)

        acgme_violations = await self._detect_acgme_violations(
            start_date, end_date, person_id
        )
        conflicts.extend(acgme_violations)

        resource_contentions = await self._detect_resource_contentions(
            start_date, end_date
        )
        conflicts.extend(resource_contentions)

        # Sort by severity and urgency
        conflicts = self._sort_conflicts(conflicts)

        logger.info(f"Detected {len(conflicts)} total conflicts")
        return conflicts

    async def _detect_time_overlaps(
        self,
        start_date: date,
        end_date: date,
        person_id: UUID | None = None,
    ) -> list[TimeOverlapConflict]:
        """
        Detect time overlap conflicts (double booking).

        Finds cases where a person is assigned to multiple blocks at the same time.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            person_id: Optional person to focus on

        Returns:
            List of time overlap conflicts
        """
        conflicts: list[TimeOverlapConflict] = []

        # Build query
        query = (
            select(Assignment)
            .join(Block)
            .options(selectinload(Assignment.person), selectinload(Assignment.block))
            .where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
        )

        if person_id:
            query = query.where(Assignment.person_id == person_id)

        result = await self.db.execute(query)
        assignments = result.scalars().all()

        # Group assignments by person and block
        by_person_and_block: dict[tuple[UUID, UUID], list[Assignment]] = defaultdict(
            list
        )

        for assignment in assignments:
            key = (assignment.person_id, assignment.block_id)
            by_person_and_block[key].append(assignment)

        # Find overlaps (more than one assignment per person per block)
        for (person_id, block_id), person_assignments in by_person_and_block.items():
            if len(person_assignments) <= 1:
                continue

            # Double booking detected
            assignment = person_assignments[0]
            person = assignment.person
            block = assignment.block

            conflict_id = self._generate_conflict_id(
                "overlap", str(person_id), str(block_id)
            )

            conflict = TimeOverlapConflict(
                conflict_id=conflict_id,
                conflict_type=ConflictType.DOUBLE_BOOKING,
                severity=ConflictSeverity.HIGH,
                title=f"Double Booking: {person.name}",
                description=(
                    f"{person.name} has {len(person_assignments)} assignments "
                    f"on {block.date} {block.time_of_day}"
                ),
                start_date=block.date,
                end_date=block.date,
                affected_people=[person_id],
                affected_blocks=[block_id],
                affected_assignments=[a.id for a in person_assignments],
                overlapping_assignment_ids=[a.id for a in person_assignments],
                overlap_duration_hours=self.HOURS_PER_BLOCK,
                impact_score=0.8,
                urgency_score=0.9,
                complexity_score=0.4,
                is_auto_resolvable=True,
                resolution_difficulty="easy",
                estimated_resolution_time_minutes=15,
            )

            conflicts.append(conflict)

        return conflicts

    async def _detect_supervision_issues(
        self,
        start_date: date,
        end_date: date,
    ) -> list[SupervisionConflict]:
        """
        Detect supervision ratio violations.

        Checks each block to ensure adequate faculty-to-resident ratios
        based on PGY levels.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of supervision conflicts
        """
        conflicts: list[SupervisionConflict] = []

        # Load blocks for date/time lookup
        block_result = await self.db.execute(
            select(Block).where(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
        )
        blocks = block_result.scalars().all()
        blocks_by_key = {(b.date, b.time_of_day): b for b in blocks}

        # Get half-day assignments with activity context
        result = await self.db.execute(
            select(HalfDayAssignment)
            .options(
                selectinload(HalfDayAssignment.person),
                selectinload(HalfDayAssignment.activity),
            )
            .where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                )
            )
        )
        assignments = result.scalars().all()

        by_slot: dict[tuple[date, str], dict[str, Any]] = defaultdict(
            lambda: {
                "resident_ids": [],
                "faculty_ids": [],
                "pgy1_count": 0,
                "pgy2_3_count": 0,
                "proc_vas_count": 0,
                "demand_units": 0,
            }
        )

        for assignment in assignments:
            if not assignment.person or not assignment.activity:
                continue
            if assignment.date.weekday() >= 5:
                continue
            slot_key = (assignment.date, assignment.time_of_day)

            if assignment.person.is_resident:
                if not assignment_requires_fmc_supervision(assignment):
                    continue
                pgy_level = assignment.person.pgy_level or 2
                demand_units = 2 if pgy_level == 1 else 1
                if activity_is_proc_or_vas(assignment.activity):
                    demand_units += 4
                    by_slot[slot_key]["proc_vas_count"] += 1
                by_slot[slot_key]["resident_ids"].append(assignment.person_id)
                if pgy_level == 1:
                    by_slot[slot_key]["pgy1_count"] += 1
                else:
                    by_slot[slot_key]["pgy2_3_count"] += 1
                by_slot[slot_key]["demand_units"] += demand_units
                continue

            if assignment.person.is_faculty:
                if not activity_provides_supervision(assignment.activity):
                    continue
                by_slot[slot_key]["faculty_ids"].append(assignment.person_id)

        for slot_key, slot_data in by_slot.items():
            demand_units = slot_data["demand_units"]
            if demand_units <= 0:
                continue
            required_faculty = math.ceil(demand_units / 4)
            faculty_count = len(slot_data["faculty_ids"])
            if faculty_count >= required_faculty:
                continue

            block = blocks_by_key.get(slot_key)
            block_id = block.id if block else None
            slot_date, time_of_day = slot_key

            conflict_id = self._generate_conflict_id(
                "supervision",
                str(block_id) if block_id else f"{slot_date}-{time_of_day}",
            )
            severity = (
                ConflictSeverity.CRITICAL
                if faculty_count == 0
                else ConflictSeverity.HIGH
            )
            title_date = block.date if block else slot_date
            title_time = block.time_of_day if block else time_of_day
            conflict = SupervisionConflict(
                conflict_id=conflict_id,
                conflict_type=ConflictType.SUPERVISION_RATIO_VIOLATION,
                severity=severity,
                title=f"Inadequate Supervision on {title_date}",
                description=(
                    f"Block on {title_date} {title_time} has {len(slot_data['resident_ids'])} residents "
                    f"({slot_data['pgy1_count']} PGY-1, {slot_data['pgy2_3_count']} PGY-2/3"
                    f"{', ' + str(slot_data['proc_vas_count']) + ' PROC/VAS' if slot_data['proc_vas_count'] else ''}) "
                    f"but only {faculty_count} faculty (requires {required_faculty})"
                ),
                start_date=title_date,
                end_date=title_date,
                affected_blocks=[block_id] if block_id else [],
                affected_people=slot_data["resident_ids"],
                resident_ids=slot_data["resident_ids"],
                pgy1_count=slot_data["pgy1_count"],
                pgy2_3_count=slot_data["pgy2_3_count"],
                faculty_ids=slot_data["faculty_ids"],
                faculty_count=faculty_count,
                required_faculty_count=required_faculty,
                impact_score=0.9,
                urgency_score=0.95,
                complexity_score=0.6,
                is_auto_resolvable=False,
                resolution_difficulty="medium",
                estimated_resolution_time_minutes=30,
            )

            conflicts.append(conflict)

        return conflicts

    async def _detect_acgme_violations(
        self,
        start_date: date,
        end_date: date,
        person_id: UUID | None = None,
    ) -> list[ACGMEViolationConflict]:
        """
        Detect ACGME compliance violations.

        Checks for:
        - 80-hour work week violations
        - 1-in-7 day off violations
        - Excessive consecutive days

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            person_id: Optional person to focus on

        Returns:
            List of ACGME violation conflicts
        """
        conflicts: list[ACGMEViolationConflict] = []

        # Preload time-off slots (source of truth for duty hour exclusions)
        self._time_off_slots = await self._load_time_off_slots(
            start_date, end_date, person_id
        )

        # Get residents
        query = select(Person).where(Person.type == "resident")
        if person_id:
            query = query.where(Person.id == person_id)

        result = await self.db.execute(query)
        residents = result.scalars().all()

        for resident in residents:
            # Check 80-hour rule
            hour_violations = await self._check_eighty_hour_rule(
                resident, start_date, end_date
            )
            conflicts.extend(hour_violations)

            # Check 1-in-7 rule
            consecutive_violations = await self._check_one_in_seven_rule(
                resident, start_date, end_date
            )
            conflicts.extend(consecutive_violations)

        return conflicts

    async def _check_eighty_hour_rule(
        self,
        resident: Person,
        start_date: date,
        end_date: date,
    ) -> list[ACGMEViolationConflict]:
        """
        Check for 80-hour work week violations.

        Uses rolling 4-week windows to check average hours.

        Args:
            resident: Resident to check
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of 80-hour violations
        """
        violations: list[ACGMEViolationConflict] = []

        # Get assignments
        result = await self.db.execute(
            select(Assignment)
            .join(Block)
            .where(
                and_(
                    Assignment.person_id == resident.id,
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .options(
                selectinload(Assignment.block),
                selectinload(Assignment.rotation_template),
            )
        )
        assignments = result.scalars().all()

        # Group by date
        blocks_by_date: dict[date, int] = defaultdict(int)
        for assignment in assignments:
            if not self._counts_toward_duty_hours(assignment):
                continue
            blocks_by_date[assignment.block.date] += 1

        fixed_blocks_by_date = await self._fixed_half_day_blocks_by_date(
            resident.id, start_date, end_date
        )

        if not blocks_by_date:
            return violations

        dates = sorted(blocks_by_date.keys())

        # Check rolling 4-week windows
        for window_start in dates:
            window_end = window_start + timedelta(
                days=self.ROLLING_WINDOW_DAYS
            )  # 4 weeks = 28 days

            total_blocks = sum(
                count
                for d, count in blocks_by_date.items()
                if window_start <= d <= window_end
            )

            total_hours = total_blocks * self.HOURS_PER_BLOCK
            avg_weekly = total_hours / self.ROLLING_WEEKS

            if avg_weekly > self.MAX_WEEKLY_HOURS:
                fixed_blocks = sum(
                    count
                    for d, count in fixed_blocks_by_date.items()
                    if window_start <= d <= window_end
                )
                fixed_total_hours = fixed_blocks * self.HOURS_PER_BLOCK
                fixed_avg_weekly = (
                    fixed_total_hours / self.ROLLING_WEEKS
                    if fixed_total_hours
                    else 0.0
                )
                fixed_exempt = fixed_avg_weekly > self.MAX_WEEKLY_HOURS
                conflict_id = self._generate_conflict_id(
                    "80hour",
                    str(resident.id),
                    window_start.isoformat(),
                )

                violation = ACGMEViolationConflict(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.EIGHTY_HOUR_VIOLATION,
                    severity=ConflictSeverity.CRITICAL,
                    title=f"80-Hour Violation: {resident.name}",
                    description=(
                        f"{resident.name} averaged {avg_weekly:.1f} hours/week "
                        f"in 4-week period starting {window_start}"
                    ),
                    start_date=window_start,
                    end_date=window_end,
                    affected_people=[resident.id],
                    acgme_rule="80-hour work week limit",
                    person_id=resident.id,
                    person_name=resident.name,
                    pgy_level=resident.pgy_level,
                    threshold_value=self.MAX_WEEKLY_HOURS,
                    actual_value=avg_weekly,
                    excess_amount=avg_weekly - self.MAX_WEEKLY_HOURS,
                    total_hours=total_hours,
                    average_weekly_hours=avg_weekly,
                    impact_score=0.95,
                    urgency_score=1.0,
                    complexity_score=0.7,
                    is_auto_resolvable=False,
                    resolution_difficulty="hard",
                    estimated_resolution_time_minutes=60,
                    context={
                        "window_start": window_start.isoformat(),
                        "window_end": window_end.isoformat(),
                        "total_blocks": total_blocks,
                        "fixed_workload_exempt": fixed_exempt,
                        "fixed_blocks": fixed_blocks,
                        "fixed_avg_weekly_hours": fixed_avg_weekly,
                    },
                )

                violations.append(violation)
                break  # One violation per resident is enough

        return violations

    async def _check_one_in_seven_rule(
        self,
        resident: Person,
        start_date: date,
        end_date: date,
    ) -> list[ACGMEViolationConflict]:
        """
        Check for 1-in-7 day off violations.

        Ensures resident gets at least one 24-hour period off every 7 days.

        Args:
            resident: Resident to check
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of consecutive day violations
        """
        violations: list[ACGMEViolationConflict] = []

        # Get assignments
        result = await self.db.execute(
            select(Assignment)
            .join(Block)
            .where(
                and_(
                    Assignment.person_id == resident.id,
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .options(
                selectinload(Assignment.block),
                selectinload(Assignment.rotation_template),
            )
        )
        assignments = result.scalars().all()

        # Get unique dates worked
        dates_worked = set(
            assignment.block.date
            for assignment in assignments
            if self._counts_toward_duty_hours(assignment)
        )
        fixed_dates_worked = set(
            (
                await self._fixed_half_day_blocks_by_date(
                    resident.id, start_date, end_date
                )
            ).keys()
        )

        if len(dates_worked) < self.MAX_CONSECUTIVE_DAYS + 1:
            return violations

        dates_sorted = sorted(dates_worked)

        # Find consecutive work days
        consecutive = 1
        max_consecutive = 1
        violation_start = None
        violation_end = None

        for i in range(1, len(dates_sorted)):
            if (dates_sorted[i] - dates_sorted[i - 1]).days == 1:
                consecutive += 1
                if consecutive > max_consecutive:
                    max_consecutive = consecutive
                    violation_start = dates_sorted[i - consecutive + 1]
                    violation_end = dates_sorted[i]
            else:
                consecutive = 1

        fixed_max_consecutive = self._max_consecutive_days(fixed_dates_worked)
        fixed_exempt = fixed_max_consecutive > self.MAX_CONSECUTIVE_DAYS

        if max_consecutive > self.MAX_CONSECUTIVE_DAYS:
            conflict_id = self._generate_conflict_id(
                "1in7",
                str(resident.id),
                violation_start.isoformat() if violation_start else "",
            )

            violation = ACGMEViolationConflict(
                conflict_id=conflict_id,
                conflict_type=ConflictType.ONE_IN_SEVEN_VIOLATION,
                severity=ConflictSeverity.HIGH,
                title=f"1-in-7 Violation: {resident.name}",
                description=(
                    f"{resident.name} worked {max_consecutive} consecutive days "
                    f"(limit: {self.MAX_CONSECUTIVE_DAYS})"
                ),
                start_date=violation_start or start_date,
                end_date=violation_end or end_date,
                affected_people=[resident.id],
                acgme_rule="1-in-7 day off requirement",
                person_id=resident.id,
                person_name=resident.name,
                pgy_level=resident.pgy_level,
                threshold_value=float(self.MAX_CONSECUTIVE_DAYS),
                actual_value=float(max_consecutive),
                excess_amount=float(max_consecutive - self.MAX_CONSECUTIVE_DAYS),
                consecutive_days=max_consecutive,
                impact_score=0.85,
                urgency_score=0.9,
                complexity_score=0.6,
                is_auto_resolvable=False,
                resolution_difficulty="medium",
                estimated_resolution_time_minutes=45,
                context={
                    "fixed_workload_exempt": fixed_exempt,
                    "fixed_consecutive_days": fixed_max_consecutive,
                },
            )

            violations.append(violation)

        return violations

    async def _detect_resource_contentions(
        self,
        start_date: date,
        end_date: date,
    ) -> list[ResourceContentionConflict]:
        """
        Detect resource contention issues.

        Placeholder for future implementation of resource tracking
        (rooms, equipment, etc.)

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            List of resource contention conflicts
        """
        # Placeholder - to be implemented based on resource tracking requirements
        return []

    async def _fixed_half_day_blocks_by_date(
        self, resident_id: UUID, start_date: date, end_date: date
    ) -> dict[date, int]:
        """Return fixed workload blocks per date from preload/manual half-day assignments."""
        from app.models.half_day_assignment import HalfDayAssignment, AssignmentSource
        from app.models.activity import Activity

        result = await self.db.execute(
            select(
                HalfDayAssignment.date,
                Activity.code,
                Activity.display_abbreviation,
                Activity.activity_category,
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .where(
                and_(
                    HalfDayAssignment.person_id == resident_id,
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                    HalfDayAssignment.source.in_(
                        [
                            AssignmentSource.PRELOAD.value,
                            AssignmentSource.MANUAL.value,
                        ]
                    ),
                )
            )
        )
        rows = result.all()
        fixed_prefixes = ("FMIT", "ICU", "NICU", "NIC", "LAD", "NBN", "IM", "PEDW")
        offsite_prefixes = ("HILO", "OKI", "KAP", "KAPI", "TDY")
        fixed_exact = {"TAMC-LD", "TAMC_LD"}
        nf_tokens = {"NF", "PEDNF", "LDNF", "PNF"}

        def is_fixed_code(raw: str | None) -> bool:
            base = (raw or "").strip().upper()
            if not base:
                return False
            if base.endswith("-AM") or base.endswith("-PM"):
                base = base[:-3]
            if base in fixed_exact:
                return True
            if base.startswith(fixed_prefixes) or base.startswith(offsite_prefixes):
                return True
            tokens = [t for t in re.split(r"[^A-Z0-9]+", base) if t]
            return any(t in nf_tokens for t in tokens)
        blocks_by_date: dict[date, int] = defaultdict(int)
        for slot_date, code, abbrev, category in rows:
            if (category or "").lower() == "time_off":
                continue
            if is_fixed_code(code) or is_fixed_code(abbrev):
                blocks_by_date[slot_date] += 1

        return blocks_by_date

    def _counts_toward_duty_hours(self, assignment: Assignment) -> bool:
        """Return True if assignment counts toward duty hours."""
        if assignment.block:
            slot_key = (
                str(assignment.person_id),
                assignment.block.date,
                assignment.block.time_of_day,
            )
            if slot_key in self._time_off_slots:
                return False
        template = assignment.rotation_template
        if not template:
            return True

        rotation_type = (template.rotation_type or "").lower()
        template_category = (template.template_category or "").lower()

        if template_category in {"time_off", "absence"}:
            return False
        if rotation_type in {"off", "absence", "recovery"}:
            return False

        return True

    def _is_fixed_workload(self, assignment: Assignment) -> bool:
        """Return True if assignment is fixed workload (inpatient/offsite)."""
        if not self._counts_toward_duty_hours(assignment):
            return False

        template = assignment.rotation_template
        if not template:
            return False

        rotation_type = (template.rotation_type or "").lower()
        template_category = (template.template_category or "").lower()

        if template_category in {"time_off", "absence"}:
            return False

        return rotation_type in {"inpatient", "off"}

    async def _load_time_off_slots(
        self,
        start_date: date,
        end_date: date,
        person_id: UUID | None = None,
    ) -> set[tuple[str, date, str]]:
        """Load time-off slots from half-day assignments."""
        query = (
            select(
                HalfDayAssignment.person_id,
                HalfDayAssignment.date,
                HalfDayAssignment.time_of_day,
                Activity.code,
                Activity.display_abbreviation,
                Activity.activity_category,
            )
            .join(Activity, HalfDayAssignment.activity_id == Activity.id)
            .where(
                and_(
                    HalfDayAssignment.date >= start_date,
                    HalfDayAssignment.date <= end_date,
                )
            )
        )

        if person_id:
            query = query.where(HalfDayAssignment.person_id == person_id)

        result = await self.db.execute(query)
        rows = result.all()

        slots: set[tuple[str, date, str]] = set()
        for row in rows:
            person_id_val, slot_date, time_of_day, code, display, category = row
            cat = (category or "").lower()
            code_norm = (code or "").strip().upper()
            display_norm = (display or "").strip().upper()
            if cat == "time_off" or code_norm in self._time_off_codes or display_norm in self._time_off_codes:
                slots.add((str(person_id_val), slot_date, time_of_day))

        return slots

    def _max_consecutive_days(self, dates: set[date]) -> int:
        """Return max consecutive day streak for a set of dates."""
        if not dates:
            return 0

        sorted_dates = sorted(dates)
        consecutive = 1
        max_consecutive = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        return max_consecutive

    def _calculate_required_faculty(self, pgy1_count: int, other_count: int) -> int:
        """
        Calculate required faculty for supervision ratios.

        Args:
            pgy1_count: Number of PGY-1 residents
            other_count: Number of PGY-2/3 residents

        Returns:
            Minimum number of faculty required
        """
        from_pgy1 = (pgy1_count + self.PGY1_RATIO - 1) // self.PGY1_RATIO
        from_other = (other_count + self.OTHER_RATIO - 1) // self.OTHER_RATIO
        return max(1, from_pgy1 + from_other) if (pgy1_count + other_count) > 0 else 0

    def _generate_conflict_id(self, *components: str) -> str:
        """
        Generate a unique conflict ID.

        Args:
            *components: Components to hash for ID generation

        Returns:
            Unique conflict ID
        """
        combined = "_".join(str(c) for c in components)
        hash_obj = hashlib.sha256(combined.encode())
        return f"conflict_{hash_obj.hexdigest()[:16]}"

    def _sort_conflicts(self, conflicts: list[Conflict]) -> list[Conflict]:
        """
        Sort conflicts by severity and urgency.

        Args:
            conflicts: List of conflicts to sort

        Returns:
            Sorted list of conflicts
        """
        severity_order = {
            ConflictSeverity.CRITICAL: 0,
            ConflictSeverity.HIGH: 1,
            ConflictSeverity.MEDIUM: 2,
            ConflictSeverity.LOW: 3,
        }

        return sorted(
            conflicts,
            key=lambda c: (
                severity_order.get(c.severity, 999),
                -c.urgency_score,
                -c.impact_score,
            ),
        )

    async def generate_summary(
        self,
        conflicts: list[Conflict],
    ) -> ConflictSummary:
        """
        Generate summary statistics for conflicts.

        Args:
            conflicts: List of conflicts to summarize

        Returns:
            ConflictSummary with statistics
        """
        summary = ConflictSummary(total_conflicts=len(conflicts))

        if not conflicts:
            return summary

        # Count by severity
        for conflict in conflicts:
            if conflict.severity == ConflictSeverity.CRITICAL:
                summary.critical_count += 1
            elif conflict.severity == ConflictSeverity.HIGH:
                summary.high_count += 1
            elif conflict.severity == ConflictSeverity.MEDIUM:
                summary.medium_count += 1
            elif conflict.severity == ConflictSeverity.LOW:
                summary.low_count += 1

        # Count by category and type
        for conflict in conflicts:
            category_key = conflict.category.value
            summary.by_category[category_key] = (
                summary.by_category.get(category_key, 0) + 1
            )

            type_key = conflict.conflict_type.value
            summary.by_type[type_key] = summary.by_type.get(type_key, 0) + 1

        # Count affected entities
        all_people = set()
        all_blocks = set()
        for conflict in conflicts:
            all_people.update(conflict.affected_people)
            all_blocks.update(conflict.affected_blocks)

        summary.affected_people_count = len(all_people)
        summary.affected_blocks_count = len(all_blocks)

        # Resolution metrics
        summary.auto_resolvable_count = sum(
            1 for c in conflicts if c.is_auto_resolvable
        )
        summary.requires_manual_count = len(conflicts) - summary.auto_resolvable_count

        # Average scores
        summary.average_impact_score = sum(c.impact_score for c in conflicts) / len(
            conflicts
        )
        summary.average_urgency_score = sum(c.urgency_score for c in conflicts) / len(
            conflicts
        )
        summary.average_complexity_score = sum(
            c.complexity_score for c in conflicts
        ) / len(conflicts)

        # Timeline
        summary.earliest_date = min(c.start_date for c in conflicts)
        summary.latest_date = max(c.end_date for c in conflicts)

        return summary
