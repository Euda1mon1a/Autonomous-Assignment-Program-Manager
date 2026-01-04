"""
FMIT Scheduler Orchestration Service.

Higher-level service that orchestrates FMIT scheduling operations,
including assignment management, conflict detection, and fair schedule generation.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.scheduling.constraints.fmit import get_fmit_week_dates
from app.services.conflict_auto_detector import ConflictAutoDetector, ConflictInfo

if TYPE_CHECKING:
    from app.models.block import Block
    from app.models.person import Person
    from app.models.rotation_template import RotationTemplate


@dataclass
class FMITWeekAssignment:
    """Represents a faculty's FMIT assignment for a week."""

    faculty_id: UUID
    faculty_name: str
    week_start: date
    week_end: date
    assignment_ids: list[UUID] = field(default_factory=list)
    rotation_template_id: UUID | None = None
    is_complete: bool = False  # All blocks for the week assigned


@dataclass
class FMITScheduleResult:
    """Result of getting FMIT schedule."""

    assignments: list[FMITWeekAssignment]
    total_weeks: int
    faculty_count: int
    start_date: date
    end_date: date


@dataclass
class FacultyLoadResult:
    """Result of faculty load calculation."""

    faculty_id: UUID
    faculty_name: str
    year: int
    total_weeks: int
    week_dates: list[date]
    average_load: float  # Weeks per year
    is_balanced: bool  # Within 1 week of average


@dataclass
class AssignmentResult:
    """Result of assignment operation."""

    success: bool
    message: str
    assignment_ids: list[UUID] = field(default_factory=list)
    error_code: str | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class ScheduleValidationResult:
    """Result of schedule validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    conflicts: list[ConflictInfo] = field(default_factory=list)
    coverage_gaps: list[date] = field(default_factory=list)
    back_to_back_issues: list[str] = field(default_factory=list)


@dataclass
class FairScheduleResult:
    """Result of fair schedule generation."""

    success: bool
    message: str
    total_weeks: int
    assignments_created: int
    faculty_loads: dict[UUID, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None


class FMITSchedulerService:
    """
    Higher-level orchestration service for FMIT scheduling.

    Coordinates between assignments, conflicts, validation, and fair distribution
    to provide comprehensive FMIT schedule management.
    """

    # Constants
    BLOCKS_PER_WEEK = 14  # 7 days × 2 blocks (AM/PM)
    FMIT_ROTATION_NAME = "FMIT"

    def __init__(self, db: Session) -> None:
        """
        Initialize the FMIT scheduler service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.conflict_detector = ConflictAutoDetector(db)

    def get_fmit_schedule(
        self,
        start_date: date,
        end_date: date,
    ) -> FMITScheduleResult:
        """
        Get the complete FMIT schedule for a date range.

        Retrieves all FMIT assignments and groups them by week and faculty.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            FMITScheduleResult with all FMIT assignments organized by week
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person

        # Get FMIT rotation template
        fmit_template = self._get_fmit_template()
        if not fmit_template:
            return FMITScheduleResult(
                assignments=[],
                total_weeks=0,
                faculty_count=0,
                start_date=start_date,
                end_date=end_date,
            )

        # Query all FMIT assignments in range
        assignments = (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= start_date,
                Block.date <= end_date,
            )
            .all()
        )

        # Group assignments by faculty and week
        week_assignments_map: dict[tuple, list[Assignment]] = defaultdict(list)
        for assignment in assignments:
            week_start = self._get_week_start(assignment.block.date)
            key = (assignment.person_id, week_start)
            week_assignments_map[key].append(assignment)

        # Build FMITWeekAssignment objects
        week_assignments = []
        faculty_ids = set()
        for (person_id, week_start), assignments_list in week_assignments_map.items():
            person = self.db.query(Person).filter(Person.id == person_id).first()
            if not person:
                continue

            faculty_ids.add(person_id)
            week_end = week_start + timedelta(days=6)

            week_assignments.append(
                FMITWeekAssignment(
                    faculty_id=person_id,
                    faculty_name=person.name,
                    week_start=week_start,
                    week_end=week_end,
                    assignment_ids=[a.id for a in assignments_list],
                    rotation_template_id=fmit_template.id,
                    is_complete=len(assignments_list) >= self.BLOCKS_PER_WEEK,
                )
            )

        # Sort by week start date
        week_assignments.sort(key=lambda x: x.week_start)

        return FMITScheduleResult(
            assignments=week_assignments,
            total_weeks=len(week_assignments),
            faculty_count=len(faculty_ids),
            start_date=start_date,
            end_date=end_date,
        )

    def get_week_assignments(
        self,
        week_date: date,
    ) -> list[FMITWeekAssignment]:
        """
        Get faculty assigned to a specific week.

        Args:
            week_date: Any date within the target week (will be normalized to Friday)

        Returns:
            List of FMITWeekAssignment for that week
        """
        week_start = self._get_week_start(week_date)
        week_end = week_start + timedelta(days=6)

        result = self.get_fmit_schedule(week_start, week_end)
        return result.assignments

    def assign_faculty_to_week(
        self,
        faculty_id: UUID,
        week_date: date,
        created_by: str = "system",
    ) -> AssignmentResult:
        """
        Assign a faculty member to FMIT duty for an entire week.

        Creates assignments for all 14 blocks (AM/PM for 7 days) in the week.

        Args:
            faculty_id: ID of faculty to assign
            week_date: Any date in the target week
            created_by: User creating the assignment

        Returns:
            AssignmentResult with success status and created assignment IDs
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person

        # Validate faculty exists
        faculty = (
            self.db.query(Person)
            .filter(
                Person.id == faculty_id,
                Person.type == "faculty",
            )
            .first()
        )
        if not faculty:
            return AssignmentResult(
                success=False,
                message="Faculty not found",
                error_code="FACULTY_NOT_FOUND",
            )

        # Get FMIT template
        fmit_template = self._get_fmit_template()
        if not fmit_template:
            return AssignmentResult(
                success=False,
                message="FMIT rotation template not found",
                error_code="TEMPLATE_NOT_FOUND",
            )

        # Get week boundaries
        week_start = self._get_week_start(week_date)
        week_end = week_start + timedelta(days=6)

        # Get or create all blocks for the week
        blocks = self._get_or_create_blocks(week_start, week_end)
        if not blocks:
            return AssignmentResult(
                success=False,
                message=f"Failed to create blocks for week {week_start}",
                error_code="BLOCK_CREATION_FAILED",
            )

        # Check for existing assignments
        existing = (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == faculty_id,
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= week_start,
                Block.date <= week_end,
            )
            .count()
        )
        if existing > 0:
            return AssignmentResult(
                success=False,
                message=f"Faculty already has {existing} FMIT assignments this week",
                error_code="ALREADY_ASSIGNED",
            )

        # Create assignments for all blocks
        assignment_ids = []
        warnings = []

        for block in blocks:
            # Check for conflicts with this block
            existing_assignment = (
                self.db.query(Assignment)
                .filter(
                    Assignment.block_id == block.id,
                    Assignment.person_id == faculty_id,
                )
                .first()
            )

            if existing_assignment:
                warnings.append(
                    f"Skipped {block.date} {block.time_of_day} - already assigned"
                )
                continue

            assignment = Assignment(
                block_id=block.id,
                person_id=faculty_id,
                rotation_template_id=fmit_template.id,
                role="primary",
                created_by=created_by,
            )
            self.db.add(assignment)
            self.db.flush()
            assignment_ids.append(assignment.id)

        self.db.commit()

        return AssignmentResult(
            success=True,
            message=f"Assigned {faculty.name} to FMIT week {week_start}",
            assignment_ids=assignment_ids,
            warnings=warnings,
        )

    def remove_faculty_from_week(
        self,
        faculty_id: UUID,
        week_date: date,
    ) -> AssignmentResult:
        """
        Remove a faculty member's FMIT assignments for a week.

        Deletes all FMIT assignments for the specified faculty in the target week.

        Args:
            faculty_id: ID of faculty to remove
            week_date: Any date in the target week

        Returns:
            AssignmentResult with success status
        """
        from app.models.assignment import Assignment
        from app.models.block import Block

        # Get FMIT template
        fmit_template = self._get_fmit_template()
        if not fmit_template:
            return AssignmentResult(
                success=False,
                message="FMIT rotation template not found",
                error_code="TEMPLATE_NOT_FOUND",
            )

        # Get week boundaries
        week_start = self._get_week_start(week_date)
        week_end = week_start + timedelta(days=6)

        # Find and delete assignments
        assignments = (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == faculty_id,
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= week_start,
                Block.date <= week_end,
            )
            .all()
        )

        if not assignments:
            return AssignmentResult(
                success=False,
                message=f"No FMIT assignments found for week {week_start}",
                error_code="NOT_FOUND",
            )

        assignment_ids = [a.id for a in assignments]
        for assignment in assignments:
            self.db.delete(assignment)

        self.db.commit()

        return AssignmentResult(
            success=True,
            message=f"Removed {len(assignments)} FMIT assignments for week {week_start}",
            assignment_ids=assignment_ids,
        )

    def get_upcoming_conflicts(
        self,
        days_ahead: int = 90,
        faculty_id: UUID | None = None,
    ) -> list[ConflictInfo]:
        """
        Get upcoming FMIT conflicts using ConflictAutoDetector.

        Delegates to the conflict detection service to find leave/FMIT overlaps,
        back-to-back issues, and other scheduling conflicts.

        Args:
            days_ahead: Number of days to look ahead (default 90)
            faculty_id: Optional filter by specific faculty

        Returns:
            List of ConflictInfo from the auto-detector
        """
        start_date = date.today()
        end_date = date.today() + timedelta(days=days_ahead)

        return self.conflict_detector.detect_all_conflicts(
            faculty_id=faculty_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_faculty_load(
        self,
        faculty_id: UUID,
        year: int,
    ) -> FacultyLoadResult:
        """
        Calculate FMIT workload for a faculty member in a given year.

        Counts the number of FMIT weeks assigned and compares to average load.

        Args:
            faculty_id: Faculty member to analyze
            year: Calendar year or academic year

        Returns:
            FacultyLoadResult with week count and balance analysis
        """
        from app.models.assignment import Assignment
        from app.models.block import Block
        from app.models.person import Person

        # Get faculty
        faculty = (
            self.db.query(Person)
            .filter(
                Person.id == faculty_id,
                Person.type == "faculty",
            )
            .first()
        )
        if not faculty:
            return FacultyLoadResult(
                faculty_id=faculty_id,
                faculty_name="Unknown",
                year=year,
                total_weeks=0,
                week_dates=[],
                average_load=0.0,
                is_balanced=False,
            )

        # Get FMIT template
        fmit_template = self._get_fmit_template()
        if not fmit_template:
            return FacultyLoadResult(
                faculty_id=faculty_id,
                faculty_name=faculty.name,
                year=year,
                total_weeks=0,
                week_dates=[],
                average_load=0.0,
                is_balanced=True,
            )

        # Define year boundaries
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        # Get all FMIT assignments for this faculty in the year
        assignments = (
            self.db.query(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .filter(
                Assignment.person_id == faculty_id,
                Assignment.rotation_template_id == fmit_template.id,
                Block.date >= year_start,
                Block.date <= year_end,
            )
            .all()
        )

        # Group by week
        weeks_set = set()
        for assignment in assignments:
            week_start = self._get_week_start(assignment.block.date)
            weeks_set.add(week_start)

        week_dates = sorted(weeks_set)
        total_weeks = len(week_dates)

        # Calculate average load across all faculty
        average_load = self._calculate_average_fmit_load(year)

        # Check if balanced (within 1 week of average)
        is_balanced = abs(total_weeks - average_load) <= 1.0

        return FacultyLoadResult(
            faculty_id=faculty_id,
            faculty_name=faculty.name,
            year=year,
            total_weeks=total_weeks,
            week_dates=week_dates,
            average_load=average_load,
            is_balanced=is_balanced,
        )

    def generate_fair_schedule(
        self,
        year: int,
        created_by: str = "system",
    ) -> FairScheduleResult:
        """
        Auto-generate a balanced FMIT schedule for the year.

        Distributes FMIT weeks fairly across all eligible faculty, avoiding
        conflicts and back-to-back assignments.

        Args:
            year: Calendar year to generate schedule for
            created_by: User generating the schedule

        Returns:
            FairScheduleResult with generation status and statistics
        """
        from app.models.person import Person

        # Get all faculty
        faculty = self.db.query(Person).filter(Person.type == "faculty").all()
        if not faculty:
            return FairScheduleResult(
                success=False,
                message="No faculty found",
                total_weeks=0,
                assignments_created=0,
                error_code="NO_FACULTY",
            )

        # Calculate weeks in year (52 weeks)
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        total_weeks = 52

        # Calculate fair distribution
        total_weeks / len(faculty)

        # Get existing loads
        faculty_loads = {}
        for f in faculty:
            load = self.get_faculty_load(f.id, year)
            faculty_loads[f.id] = load.total_weeks

        warnings = []
        assignments_created = 0

        # Generate week by week
        current_week = self._get_week_start(year_start)

        while current_week <= year_end:
            # Check if week already has assignment
            existing = self.get_week_assignments(current_week)
            if existing:
                current_week += timedelta(days=7)
                continue

            # Find faculty with lowest load
            eligible_faculty = self._get_eligible_faculty_for_week(
                faculty,
                current_week,
                faculty_loads,
            )

            if not eligible_faculty:
                warnings.append(f"No eligible faculty for week {current_week}")
                current_week += timedelta(days=7)
                continue

            # Assign to faculty with lowest load
            selected = min(eligible_faculty, key=lambda f: faculty_loads[f.id])

            result = self.assign_faculty_to_week(
                selected.id,
                current_week,
                created_by=created_by,
            )

            if result.success:
                faculty_loads[selected.id] += 1
                assignments_created += len(result.assignment_ids)
            else:
                warnings.append(f"Week {current_week}: {result.message}")

            current_week += timedelta(days=7)

        return FairScheduleResult(
            success=True,
            message=f"Generated schedule for {year} with {assignments_created} assignments",
            total_weeks=total_weeks,
            assignments_created=assignments_created,
            faculty_loads=faculty_loads,
            warnings=warnings,
        )

    def validate_schedule(
        self,
        start_date: date,
        end_date: date,
    ) -> ScheduleValidationResult:
        """
        Validate the entire FMIT schedule for a date range.

        Checks for:
        - Coverage gaps (weeks without assignment)
        - Conflicts with leave/absences
        - Back-to-back assignments
        - Excessive load on any faculty

        Args:
            start_date: Start of validation range
            end_date: End of validation range

        Returns:
            ScheduleValidationResult with all validation findings
        """
        errors = []
        warnings = []
        coverage_gaps = []
        back_to_back_issues = []

        # Get schedule
        schedule_result = self.get_fmit_schedule(start_date, end_date)

        # Check for coverage gaps
        current_week = self._get_week_start(start_date)
        while current_week <= end_date:
            week_assignments = [
                a for a in schedule_result.assignments if a.week_start == current_week
            ]

            if not week_assignments:
                coverage_gaps.append(current_week)
                errors.append(f"No FMIT coverage for week {current_week}")
            elif len(week_assignments) > 1:
                warnings.append(f"Multiple faculty assigned to week {current_week}")
            elif week_assignments and not week_assignments[0].is_complete:
                warnings.append(f"Incomplete assignment for week {current_week}")

            current_week += timedelta(days=7)

        # Check for conflicts
        conflicts = self.get_upcoming_conflicts(
            days_ahead=(end_date - date.today()).days,
        )
        for conflict in conflicts:
            if conflict.severity == "critical":
                errors.append(conflict.description)
            else:
                warnings.append(conflict.description)

        # Check for back-to-back assignments
        faculty_weeks = defaultdict(list)
        for assignment in schedule_result.assignments:
            faculty_weeks[assignment.faculty_id].append(assignment.week_start)

        for faculty_id, weeks in faculty_weeks.items():
            sorted_weeks = sorted(weeks)
            for i in range(len(sorted_weeks) - 1):
                gap_days = (sorted_weeks[i + 1] - sorted_weeks[i]).days
                if gap_days <= 14:  # Less than 2 weeks apart
                    back_to_back_issues.append(
                        f"Faculty {faculty_id} has back-to-back weeks: "
                        f"{sorted_weeks[i]} and {sorted_weeks[i + 1]}"
                    )
                    warnings.append(back_to_back_issues[-1])

        return ScheduleValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            conflicts=conflicts,
            coverage_gaps=coverage_gaps,
            back_to_back_issues=back_to_back_issues,
        )

    # Private helper methods

    def _get_fmit_template(self) -> Optional["RotationTemplate"]:
        """Get the FMIT rotation template."""
        from app.models.rotation_template import RotationTemplate

        return (
            self.db.query(RotationTemplate)
            .filter(RotationTemplate.name == self.FMIT_ROTATION_NAME)
            .first()
        )

    def _get_week_start(self, any_date: date) -> date:
        """
        Get the Friday of the FMIT week containing the given date.

        FMIT weeks run Friday-Thursday, not Monday-Sunday.
        This aligns with the constraint logic in app.scheduling.constraints.fmit.

        Args:
            any_date: Any date in the target week

        Returns:
            Friday of that FMIT week
        """
        friday, _ = get_fmit_week_dates(any_date)
        return friday

    def _get_or_create_blocks(
        self,
        start_date: date,
        end_date: date,
    ) -> list["Block"]:
        """
        Get or create all blocks for a date range.

        Args:
            start_date: Start date
            end_date: End date (inclusive)

        Returns:
            List of Block objects
        """
        from app.models.block import Block

        blocks = []
        current_date = start_date

        while current_date <= end_date:
            for time_of_day in ["AM", "PM"]:
                # Try to get existing block
                block = (
                    self.db.query(Block)
                    .filter(
                        Block.date == current_date,
                        Block.time_of_day == time_of_day,
                    )
                    .first()
                )

                # Create if doesn't exist
                if not block:
                    block = Block(
                        date=current_date,
                        time_of_day=time_of_day,
                        block_number=1,  # Default block number
                        is_weekend=current_date.weekday() >= 5,
                        is_holiday=False,
                    )
                    self.db.add(block)
                    self.db.flush()

                blocks.append(block)

            current_date += timedelta(days=1)

        return blocks

    def _calculate_average_fmit_load(self, year: int) -> float:
        """
        Calculate the average FMIT weeks per faculty for the year.

        Args:
            year: Year to calculate for

        Returns:
            Average weeks per faculty
        """
        from app.models.person import Person

        # Count active faculty
        faculty_count = self.db.query(Person).filter(Person.type == "faculty").count()
        if faculty_count == 0:
            return 0.0

        # 52 weeks in a year
        return 52.0 / faculty_count

    def _get_eligible_faculty_for_week(
        self,
        faculty: list["Person"],
        week_date: date,
        current_loads: dict[UUID, int],
    ) -> list["Person"]:
        """
        Get faculty eligible for assignment to a specific week.

        Filters out faculty with:
        - Blocking absences during the week
        - Back-to-back FMIT assignments

        Args:
            faculty: List of all faculty
            week_date: Week to check
            current_loads: Current load counts

        Returns:
            List of eligible faculty
        """
        from app.models.absence import Absence

        week_start = self._get_week_start(week_date)
        week_end = week_start + timedelta(days=6)

        eligible = []

        for person in faculty:
            # Check for blocking absences
            conflicts = (
                self.db.query(Absence)
                .filter(
                    Absence.person_id == person.id,
                    Absence.is_blocking,
                    Absence.start_date <= week_end,
                    Absence.end_date >= week_start,
                )
                .count()
            )

            if conflicts > 0:
                continue

            # Check for back-to-back assignments
            # Get assignments from 2 weeks before to 2 weeks after
            buffer_start = week_start - timedelta(days=14)
            buffer_end = week_end + timedelta(days=14)

            schedule = self.get_fmit_schedule(buffer_start, buffer_end)
            person_weeks = [
                a.week_start
                for a in schedule.assignments
                if a.faculty_id == person.id and a.week_start != week_start
            ]

            # Check if any existing week is too close
            has_back_to_back = False
            for existing_week in person_weeks:
                gap_days = abs((existing_week - week_start).days)
                if gap_days <= 14:
                    has_back_to_back = True
                    break

            if has_back_to_back:
                continue

            eligible.append(person)

        return eligible
