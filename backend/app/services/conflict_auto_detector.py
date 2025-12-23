"""
Conflict auto-detection service.

Detects conflicts between leave records and FMIT schedule assignments,
creating alerts when overlaps are found. Also detects ACGME compliance
violations and supervision ratio issues.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, joinedload, selectinload

if TYPE_CHECKING:
    pass


@dataclass
class ConflictInfo:
    """Information about a detected conflict."""

    faculty_id: UUID
    faculty_name: str
    conflict_type: str  # leave_fmit_overlap, back_to_back, double_booking, etc.
    fmit_week: date | None = None
    leave_id: UUID | None = None
    assignment_id: UUID | None = None
    residency_block_id: UUID | None = None
    severity: str = "medium"  # critical, high, medium, low
    description: str = ""
    start_date: date | None = None
    end_date: date | None = None
    hours_worked: float | None = None
    consecutive_days: int | None = None
    supervision_ratio: float | None = None
    suggested_resolution: str | None = None


class ConflictAutoDetector:
    """
    Service for automatically detecting schedule conflicts.

    Monitors leave changes and detects when they overlap with
    FMIT assignments or create scheduling problems.
    """

    def __init__(self, db: Session):
        self.db = db

    def detect_conflicts_for_absence(
        self,
        absence_id: UUID,
    ) -> list[ConflictInfo]:
        """
        Detect conflicts for a specific absence record.

        Args:
            absence_id: ID of the absence to check

        Returns:
            List of ConflictInfo for any detected conflicts
        """
        from app.models.absence import Absence

        # OPTIMIZATION: Use joinedload to eagerly load person relationship
        absence = (
            self.db.query(Absence)
            .options(joinedload(Absence.person))
            .filter(Absence.id == absence_id)
            .first()
        )
        if not absence:
            return []

        conflicts = []

        # Check for FMIT overlap if absence is blocking
        if absence.should_block_assignment:
            fmit_conflicts = self._find_fmit_overlaps(
                absence.person_id,
                absence.start_date,
                absence.end_date,
            )
            for fmit_week in fmit_conflicts:
                conflicts.append(
                    ConflictInfo(
                        faculty_id=absence.person_id,
                        faculty_name=absence.person.name
                        if absence.person
                        else "Unknown",
                        conflict_type="leave_fmit_overlap",
                        fmit_week=fmit_week,
                        leave_id=absence_id,
                        severity="critical",
                        description=f"{absence.absence_type} conflicts with FMIT week {fmit_week}",
                    )
                )

        return conflicts

    def detect_all_conflicts(
        self,
        faculty_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[ConflictInfo]:
        """
        Scan for all conflicts in a date range.

        Args:
            faculty_id: Optional filter by faculty
            start_date: Start of scan range (default: today)
            end_date: End of scan range (default: 90 days out)

        Returns:
            List of all detected conflicts
        """
        from app.models.absence import Absence

        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date.today() + timedelta(days=90)

        conflicts = []

        # 1. Check absence-based conflicts
        # OPTIMIZATION: Eagerly load person relationship to avoid N+1 queries
        query = (
            self.db.query(Absence)
            .options(joinedload(Absence.person))
            .filter(
                Absence.end_date >= start_date,
                Absence.start_date <= end_date,
            )
        )

        if faculty_id:
            query = query.filter(Absence.person_id == faculty_id)

        absences = query.all()

        # Process absences inline to avoid additional queries
        for absence in absences:
            if absence.should_block_assignment:
                fmit_conflicts = self._find_fmit_overlaps(
                    absence.person_id,
                    absence.start_date,
                    absence.end_date,
                )
                for fmit_week in fmit_conflicts:
                    conflicts.append(
                        ConflictInfo(
                            faculty_id=absence.person_id,
                            faculty_name=absence.person.name
                            if absence.person
                            else "Unknown",
                            conflict_type="leave_fmit_overlap",
                            fmit_week=fmit_week,
                            leave_id=absence.id,
                            severity="critical",
                            description=f"{absence.absence_type} conflicts with FMIT week {fmit_week}",
                        )
                    )

        # 2. Check for double-booking across systems
        conflicts.extend(
            self._detect_cross_system_double_booking(faculty_id, start_date, end_date)
        )

        # 3. Check ACGME compliance violations
        conflicts.extend(
            self._detect_acgme_violations(faculty_id, start_date, end_date)
        )

        # 4. Check supervision ratio violations
        conflicts.extend(
            self._detect_supervision_violations(faculty_id, start_date, end_date)
        )

        return conflicts

    def create_conflict_alerts(
        self,
        conflicts: list[ConflictInfo],
        created_by_id: UUID | None = None,
    ) -> list[UUID]:
        """
        Create ConflictAlert records for detected conflicts.

        Args:
            conflicts: List of conflicts to create alerts for
            created_by_id: User who triggered the scan

        Returns:
            List of created alert IDs
        """
        from app.models.conflict_alert import (
            ConflictAlert,
            ConflictSeverity,
            ConflictType,
        )

        alert_ids = []

        # Map new conflict types to existing enum values (for backward compatibility)
        conflict_type_map = {
            "leave_fmit_overlap": "LEAVE_FMIT_OVERLAP",
            "residency_fmit_double_booking": "LEAVE_FMIT_OVERLAP",  # Map to closest existing
            "back_to_back": "BACK_TO_BACK",
            "excessive_alternating": "EXCESSIVE_ALTERNATING",
            "work_hour_violation": "EXTERNAL_COMMITMENT",  # Map to generic type
            "rest_day_violation": "EXTERNAL_COMMITMENT",  # Map to generic type
            "supervision_ratio_violation": "EXTERNAL_COMMITMENT",  # Map to generic type
            "missing_supervision": "EXTERNAL_COMMITMENT",  # Map to generic type
            "call_cascade": "CALL_CASCADE",
            "external_commitment": "EXTERNAL_COMMITMENT",
        }

        # Map new severity levels to existing enum values
        severity_map = {
            "critical": "CRITICAL",
            "high": "WARNING",
            "medium": "WARNING",
            "low": "INFO",
            "warning": "WARNING",  # Backward compatibility
            "info": "INFO",  # Backward compatibility
        }

        for conflict in conflicts:
            # Map conflict type to existing enum
            conflict_type_key = conflict_type_map.get(conflict.conflict_type.lower())
            if not conflict_type_key:
                # Skip if type not mappable
                continue

            try:
                conflict_type_enum = ConflictType[conflict_type_key]
            except KeyError:
                # Skip if enum value doesn't exist
                continue

            # Map severity to existing enum
            severity_key = severity_map.get(conflict.severity.lower(), "WARNING")
            severity_enum = ConflictSeverity[severity_key]

            # Check if a similar alert already exists
            existing = (
                self.db.query(ConflictAlert)
                .filter(
                    and_(
                        ConflictAlert.faculty_id == conflict.faculty_id,
                        ConflictAlert.conflict_type == conflict_type_enum,
                        ConflictAlert.fmit_week
                        == (conflict.fmit_week or conflict.start_date),
                        ConflictAlert.status.in_(["new", "acknowledged"]),
                    )
                )
                .first()
            )

            if existing:
                # Update existing alert if severity increased
                if self._severity_priority(conflict.severity) > self._severity_priority(
                    existing.severity.value.lower()
                ):
                    existing.severity = severity_enum
                    existing.description = conflict.description
                    self.db.commit()
                alert_ids.append(existing.id)
            else:
                # Create new alert
                alert = ConflictAlert(
                    id=uuid4(),
                    faculty_id=conflict.faculty_id,
                    conflict_type=conflict_type_enum,
                    severity=severity_enum,
                    fmit_week=conflict.fmit_week or conflict.start_date or date.today(),
                    description=conflict.description,
                    leave_id=conflict.leave_id,
                )
                self.db.add(alert)
                self.db.commit()
                self.db.refresh(alert)
                alert_ids.append(alert.id)

        return alert_ids

    def _find_fmit_overlaps(
        self,
        faculty_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[date]:
        """
        Find FMIT weeks that overlap with a date range.

        Args:
            faculty_id: Faculty to check
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List of FMIT week start dates that overlap
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.rotation_template import RotationTemplate

        # Query for FMIT assignments in the date range
        fmit_weeks = []

        # OPTIMIZATION: Use joinedload to eagerly load block relationship
        assignments = (
            self.db.query(Assignment)
            .join(Block)
            .join(RotationTemplate)
            .options(joinedload(Assignment.block))
            .filter(
                and_(
                    Assignment.person_id == faculty_id,
                    Block.date >= start_date,
                    Block.date <= end_date,
                    RotationTemplate.name.ilike("%FMIT%"),
                )
            )
            .all()
        )

        # Group by week start dates
        seen_weeks = set()
        for assignment in assignments:
            block_date = assignment.block.date
            # Get week start (Monday)
            week_start = block_date - timedelta(days=block_date.weekday())
            if week_start not in seen_weeks:
                seen_weeks.add(week_start)
                fmit_weeks.append(week_start)

        return sorted(fmit_weeks)

    def _check_back_to_back(
        self,
        faculty_id: UUID,
        fmit_weeks: list[date],
    ) -> list[ConflictInfo]:
        """Check for back-to-back FMIT conflicts."""
        from app.services.xlsx_import import has_back_to_back_conflict

        if has_back_to_back_conflict(sorted(fmit_weeks)):
            # Find which weeks are back-to-back
            conflicts = []
            sorted_weeks = sorted(fmit_weeks)
            for i in range(len(sorted_weeks) - 1):
                gap = (sorted_weeks[i + 1] - sorted_weeks[i]).days
                if gap <= 14:  # Less than 2 week gap
                    conflicts.append(
                        ConflictInfo(
                            faculty_id=faculty_id,
                            faculty_name="",  # Would be populated from query
                            conflict_type="back_to_back",
                            fmit_week=sorted_weeks[i],
                            severity="high",
                            description=f"Back-to-back FMIT: {sorted_weeks[i]} and {sorted_weeks[i + 1]}",
                            suggested_resolution="Add at least 2 weeks between FMIT rotations",
                        )
                    )
            return conflicts
        return []

    def _detect_cross_system_double_booking(
        self,
        faculty_id: UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[ConflictInfo]:
        """
        Detect double-booking across residency and FMIT systems.

        Checks if a person is assigned to both residency rotation and FMIT
        on the same date/time.
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person
        from app.models.rotation_template import RotationTemplate

        conflicts = []

        # Query for people with assignments in date range
        query = (
            self.db.query(Person.id, Person.name, Block.date, Block.time_of_day)
            .select_from(Assignment)
            .join(Person, Assignment.person_id == Person.id)
            .join(Block, Assignment.block_id == Block.id)
            .join(
                RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id
            )
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
        )

        if faculty_id:
            query = query.filter(Person.id == faculty_id)

        # Group assignments by person and block
        assignments_by_person_block = defaultdict(list)
        for person_id, person_name, block_date, time_of_day in query.all():
            key = (person_id, person_name, block_date, time_of_day)
            assignments_by_person_block[key].append((person_id, person_name))

        # Check for double-booking (person assigned multiple times to same block)
        for (
            person_id,
            person_name,
            block_date,
            time_of_day,
        ), assignments in assignments_by_person_block.items():
            if len(assignments) > 1:
                conflicts.append(
                    ConflictInfo(
                        faculty_id=person_id,
                        faculty_name=person_name,
                        conflict_type="residency_fmit_double_booking",
                        severity="critical",
                        description=f"Double-booked on {block_date} {time_of_day}: multiple concurrent assignments",
                        start_date=block_date,
                        end_date=block_date,
                        suggested_resolution="Remove one of the conflicting assignments",
                    )
                )

        return conflicts

    def _detect_acgme_violations(
        self,
        faculty_id: UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[ConflictInfo]:
        """
        Detect ACGME compliance violations (80-hour work week, 1-in-7 rest day).

        Args:
            faculty_id: Optional filter by specific person
            start_date: Start of check period
            end_date: End of check period

        Returns:
            List of ACGME violation conflicts
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person

        conflicts = []

        # Query all residents (ACGME rules apply to residents)
        # OPTIMIZATION: Eagerly load assignments to reduce queries in violation checks
        query = (
            self.db.query(Person)
            .options(selectinload(Person.assignments))
            .filter(Person.type == "resident")
        )
        if faculty_id:
            query = query.filter(Person.id == faculty_id)

        residents = query.all()

        for person in residents:
            # Check 80-hour work week violations
            week_violations = self._check_80_hour_violations(
                person, start_date, end_date
            )
            conflicts.extend(week_violations)

            # Check 1-in-7 rest day violations
            rest_violations = self._check_1_in_7_violations(
                person, start_date, end_date
            )
            conflicts.extend(rest_violations)

        return conflicts

    def _check_80_hour_violations(
        self,
        person: "Person",
        start_date: date,
        end_date: date,
    ) -> list[ConflictInfo]:
        """Check for 80-hour work week violations."""
        from app.models.assignment import Assignment
        from app.models.block import Block

        conflicts = []

        # Iterate through weeks in the date range
        current_date = start_date
        while current_date <= end_date:
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)

            # Count work blocks in this week (each block = 4 hours)
            work_blocks = (
                self.db.query(Assignment)
                .join(Block)
                .filter(
                    and_(
                        Assignment.person_id == person.id,
                        Block.date >= week_start,
                        Block.date <= week_end,
                        Block.is_weekend == False,
                    )
                )
                .count()
            )

            # Each block is 4 hours (half-day)
            hours_worked = work_blocks * 4.0

            if hours_worked > 80:
                conflicts.append(
                    ConflictInfo(
                        faculty_id=person.id,
                        faculty_name=person.name,
                        conflict_type="work_hour_violation",
                        severity="critical",
                        description=f"ACGME 80-hour violation: {hours_worked:.1f} hours in week of {week_start}",
                        start_date=week_start,
                        end_date=week_end,
                        hours_worked=hours_worked,
                        suggested_resolution="Reduce work hours or redistribute assignments to comply with 80-hour limit",
                    )
                )

            # Move to next week
            current_date = week_end + timedelta(days=1)

        return conflicts

    def _check_1_in_7_violations(
        self,
        person: "Person",
        start_date: date,
        end_date: date,
    ) -> list[ConflictInfo]:
        """Check for 1-in-7 rest day violations (must have 1 day off per week)."""
        from app.models.assignment import Assignment
        from app.models.block import Block

        conflicts = []

        # Get all work days in the date range
        work_days_query = (
            self.db.query(Block.date)
            .select_from(Assignment)
            .join(Block)
            .filter(
                and_(
                    Assignment.person_id == person.id,
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
            .distinct()
            .order_by(Block.date)
        )

        work_days = [row[0] for row in work_days_query.all()]

        if not work_days:
            return conflicts

        # Check for consecutive work days > 6
        consecutive_days = 1
        streak_start = work_days[0]

        for i in range(1, len(work_days)):
            if (work_days[i] - work_days[i - 1]).days == 1:
                consecutive_days += 1
            else:
                # Streak broken
                if consecutive_days > 6:
                    conflicts.append(
                        ConflictInfo(
                            faculty_id=person.id,
                            faculty_name=person.name,
                            conflict_type="rest_day_violation",
                            severity="critical",
                            description=f"ACGME 1-in-7 violation: {consecutive_days} consecutive work days starting {streak_start}",
                            start_date=streak_start,
                            end_date=work_days[i - 1],
                            consecutive_days=consecutive_days,
                            suggested_resolution="Ensure at least 1 day off every 7 days",
                        )
                    )
                consecutive_days = 1
                streak_start = work_days[i]

        # Check final streak
        if consecutive_days > 6:
            conflicts.append(
                ConflictInfo(
                    faculty_id=person.id,
                    faculty_name=person.name,
                    conflict_type="rest_day_violation",
                    severity="critical",
                    description=f"ACGME 1-in-7 violation: {consecutive_days} consecutive work days starting {streak_start}",
                    start_date=streak_start,
                    end_date=work_days[-1],
                    consecutive_days=consecutive_days,
                    suggested_resolution="Ensure at least 1 day off every 7 days",
                )
            )

        return conflicts

    def _detect_supervision_violations(
        self,
        faculty_id: UUID | None,
        start_date: date,
        end_date: date,
    ) -> list[ConflictInfo]:
        """
        Detect supervision ratio violations.

        ACGME requires:
        - PGY-1: 1 faculty per 2 residents (1:2)
        - PGY-2/3: 1 faculty per 4 residents (1:4)
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person
        from app.models.rotation_template import RotationTemplate

        conflicts = []

        # OPTIMIZATION: Load blocks with their assignments and related data in one query
        blocks_query = (
            self.db.query(Block)
            .options(
                selectinload(Block.assignments).joinedload(Assignment.person),
                selectinload(Block.assignments).joinedload(
                    Assignment.rotation_template
                ),
            )
            .filter(
                and_(
                    Block.date >= start_date,
                    Block.date <= end_date,
                )
            )
        )

        blocks = blocks_query.all()

        for block in blocks:
            # Get all assignments for this block (already loaded)
            assignments = block.assignments

            if not assignments:
                continue

            # Count residents by PGY level and faculty
            pgy1_count = 0
            pgy2_3_count = 0
            faculty_count = 0
            rotation_name = None

            for assignment in assignments:
                if assignment.person.is_resident:
                    if assignment.person.pgy_level == 1:
                        pgy1_count += 1
                    elif assignment.person.pgy_level in [2, 3]:
                        pgy2_3_count += 1
                elif assignment.person.is_faculty:
                    faculty_count += 1

                if assignment.rotation_template:
                    rotation_name = assignment.rotation_template.name

            # Check ratios
            if pgy1_count > 0 or pgy2_3_count > 0:
                # Check if supervision required (skip if no residents or already has faculty)
                if faculty_count == 0:
                    conflicts.append(
                        ConflictInfo(
                            faculty_id=faculty_id or assignments[0].person_id,
                            faculty_name=f"Block {block.display_name}",
                            conflict_type="missing_supervision",
                            severity="critical",
                            description=f"No faculty supervision on {block.display_name} with {pgy1_count + pgy2_3_count} residents",
                            start_date=block.date,
                            end_date=block.date,
                            supervision_ratio=0.0,
                            suggested_resolution="Assign at least one supervising faculty member",
                        )
                    )
                else:
                    # Check ratios
                    if pgy1_count > 0:
                        pgy1_ratio = pgy1_count / faculty_count
                        if pgy1_ratio > 2.0:
                            conflicts.append(
                                ConflictInfo(
                                    faculty_id=faculty_id or assignments[0].person_id,
                                    faculty_name=f"Block {block.display_name}",
                                    conflict_type="supervision_ratio_violation",
                                    severity="high",
                                    description=f"PGY-1 supervision ratio violation on {block.display_name}: {pgy1_ratio:.1f}:1 (max 2:1)",
                                    start_date=block.date,
                                    end_date=block.date,
                                    supervision_ratio=pgy1_ratio,
                                    suggested_resolution="Increase faculty supervision or reduce PGY-1 assignments",
                                )
                            )

                    if pgy2_3_count > 0:
                        pgy2_3_ratio = pgy2_3_count / faculty_count
                        if pgy2_3_ratio > 4.0:
                            conflicts.append(
                                ConflictInfo(
                                    faculty_id=faculty_id or assignments[0].person_id,
                                    faculty_name=f"Block {block.display_name}",
                                    conflict_type="supervision_ratio_violation",
                                    severity="medium",
                                    description=f"PGY-2/3 supervision ratio violation on {block.display_name}: {pgy2_3_ratio:.1f}:1 (max 4:1)",
                                    start_date=block.date,
                                    end_date=block.date,
                                    supervision_ratio=pgy2_3_ratio,
                                    suggested_resolution="Increase faculty supervision or reduce PGY-2/3 assignments",
                                )
                            )

        return conflicts

    def group_conflicts(
        self,
        conflicts: list[ConflictInfo],
        group_by: str = "type",
    ) -> dict[str, list[ConflictInfo]]:
        """
        Group conflicts by specified criteria.

        Args:
            conflicts: List of conflicts to group
            group_by: Grouping criteria - "type", "person", "severity", "date"

        Returns:
            Dictionary mapping group key to list of conflicts
        """
        groups = defaultdict(list)

        for conflict in conflicts:
            if group_by == "type":
                key = conflict.conflict_type
            elif group_by == "person":
                key = f"{conflict.faculty_name} ({conflict.faculty_id})"
            elif group_by == "severity":
                key = conflict.severity
            elif group_by == "date":
                key = str(conflict.start_date or conflict.fmit_week or "unknown")
            else:
                key = "ungrouped"

            groups[key].append(conflict)

        return dict(groups)

    def get_conflict_summary(
        self,
        conflicts: list[ConflictInfo],
    ) -> dict:
        """
        Generate summary statistics for conflicts.

        Args:
            conflicts: List of conflicts to summarize

        Returns:
            Dictionary with summary statistics
        """
        if not conflicts:
            return {
                "total_conflicts": 0,
                "by_severity": {},
                "by_type": {},
                "affected_people": [],
            }

        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        affected_people = set()

        for conflict in conflicts:
            severity_counts[conflict.severity] += 1
            type_counts[conflict.conflict_type] += 1
            affected_people.add((conflict.faculty_id, conflict.faculty_name))

        return {
            "total_conflicts": len(conflicts),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "affected_people": [
                {"id": str(pid), "name": name}
                for pid, name in sorted(affected_people, key=lambda x: x[1])
            ],
        }

    @staticmethod
    def _severity_priority(severity: str) -> int:
        """Get numeric priority for severity level (higher = more severe)."""
        priorities = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4,
            "warning": 2,  # Backward compatibility
            "info": 1,  # Backward compatibility
        }
        return priorities.get(severity.lower(), 2)
