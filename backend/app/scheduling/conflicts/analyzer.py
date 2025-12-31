"""
Conflict Analysis Engine.

This module provides the main engine for detecting and analyzing schedule conflicts.
It identifies time overlaps, resource contentions, ACGME violations, and other
scheduling issues.
"""

import hashlib
import logging
from collections import defaultdict
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
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

        # Get all assignments in date range
        result = await self.db.execute(
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
        assignments = result.scalars().all()

        # Group by block
        by_block: dict[UUID, list[Assignment]] = defaultdict(list)
        for assignment in assignments:
            by_block[assignment.block_id].append(assignment)

        # Check each block
        for block_id, block_assignments in by_block.items():
            if not block_assignments:
                continue

            # Separate residents and faculty
            residents = [
                a for a in block_assignments if a.person and a.person.is_resident
            ]
            faculty = [a for a in block_assignments if a.person and a.person.is_faculty]

            if not residents:
                continue

            # Count PGY levels
            pgy1_count = sum(
                1 for a in residents if a.person and a.person.pgy_level == 1
            )
            pgy2_3_count = len(residents) - pgy1_count

            # Calculate required faculty
            required_faculty = self._calculate_required_faculty(
                pgy1_count, pgy2_3_count
            )

            if len(faculty) < required_faculty:
                # Supervision violation
                block = block_assignments[0].block

                conflict_id = self._generate_conflict_id("supervision", str(block_id))

                severity = (
                    ConflictSeverity.CRITICAL
                    if len(faculty) == 0
                    else ConflictSeverity.HIGH
                )

                conflict = SupervisionConflict(
                    conflict_id=conflict_id,
                    conflict_type=ConflictType.SUPERVISION_RATIO_VIOLATION,
                    severity=severity,
                    title=f"Inadequate Supervision on {block.date}",
                    description=(
                        f"Block on {block.date} {block.time_of_day} has {len(residents)} residents "
                        f"({pgy1_count} PGY-1, {pgy2_3_count} PGY-2/3) but only {len(faculty)} faculty "
                        f"(requires {required_faculty})"
                    ),
                    start_date=block.date,
                    end_date=block.date,
                    affected_blocks=[block_id],
                    affected_people=[a.person_id for a in residents],
                    resident_ids=[a.person_id for a in residents],
                    pgy1_count=pgy1_count,
                    pgy2_3_count=pgy2_3_count,
                    faculty_ids=[a.person_id for a in faculty],
                    faculty_count=len(faculty),
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
            .options(selectinload(Assignment.block))
        )
        assignments = result.scalars().all()

        # Group by date
        blocks_by_date: dict[date, int] = defaultdict(int)
        for assignment in assignments:
            blocks_by_date[assignment.block.date] += 1

        if not blocks_by_date:
            return violations

        dates = sorted(blocks_by_date.keys())

        # Check rolling 4-week windows
        for window_start in dates:
            window_end = window_start + timedelta(days=self.ROLLING_WINDOW_DAYS)  # 4 weeks = 28 days

            total_blocks = sum(
                count
                for d, count in blocks_by_date.items()
                if window_start <= d <= window_end
            )

            total_hours = total_blocks * self.HOURS_PER_BLOCK
            avg_weekly = total_hours / self.ROLLING_WEEKS

            if avg_weekly > self.MAX_WEEKLY_HOURS:
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
            .options(selectinload(Assignment.block))
        )
        assignments = result.scalars().all()

        # Get unique dates worked
        dates_worked = set(assignment.block.date for assignment in assignments)

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
