"""Call assignment service for overnight and weekend call management."""

import logging
import statistics
from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.schemas.call_assignment import (
    CallAssignmentCreate,
    CallCoverageReport,
    CallEquityReport,
)

logger = logging.getLogger(__name__)


class CallAssignmentService:
    """Service for call assignment business logic."""

    def __init__(self, db: Session):
        self.db = db

    def get_call_assignment(self, assignment_id: UUID) -> CallAssignment | None:
        """Get a single call assignment by ID with person relationship."""
        stmt = (
            select(CallAssignment)
            .options(joinedload(CallAssignment.person))
            .where(CallAssignment.id == assignment_id)
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def list_call_assignments(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        person_id: UUID | None = None,
        call_type: str | None = None,
    ) -> list[CallAssignment]:
        """
        List call assignments with optional filters.

        Args:
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            person_id: Filter by person
            call_type: Filter by call type (overnight, weekend, backup)

        Returns:
            List of CallAssignment objects with person relationship loaded
        """
        stmt = select(CallAssignment).options(joinedload(CallAssignment.person))

        filters = []
        if start_date:
            filters.append(CallAssignment.date >= start_date)
        if end_date:
            filters.append(CallAssignment.date <= end_date)
        if person_id:
            filters.append(CallAssignment.person_id == person_id)
        if call_type:
            filters.append(CallAssignment.call_type == call_type)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(CallAssignment.date)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def create_call_assignment(
        self,
        data: CallAssignmentCreate,
    ) -> CallAssignment:
        """
        Create a new call assignment.

        Used for manual assignment (e.g., adjunct faculty).
        """
        # Check for existing assignment on same date/person/type
        existing = self.db.execute(
            select(CallAssignment).where(
                and_(
                    CallAssignment.date == data.date,
                    CallAssignment.person_id == data.person_id,
                    CallAssignment.call_type == data.call_type,
                )
            )
        ).scalar_one_or_none()

        if existing:
            raise ValueError(
                f"Call assignment already exists for {data.date} with type {data.call_type}"
            )

        assignment = CallAssignment(
            date=data.date,
            person_id=data.person_id,
            call_type=data.call_type,
            is_weekend=data.is_weekend,
            is_holiday=data.is_holiday,
        )
        self.db.add(assignment)
        self.db.flush()

        logger.info(
            f"Created call assignment: {assignment.id} for {data.date} "
            f"person={data.person_id} type={data.call_type}"
        )
        return assignment

    def bulk_create_call_assignments(
        self,
        assignments: list[CallAssignmentCreate],
        replace_existing: bool = True,
    ) -> list[CallAssignment]:
        """
        Bulk create call assignments from solver output.

        Args:
            assignments: List of call assignments to create
            replace_existing: If True, delete existing assignments in date range first

        Returns:
            List of created CallAssignment objects
        """
        if not assignments:
            return []

        # Get date range from assignments
        dates = [a.date for a in assignments]
        start_date = min(dates)
        end_date = max(dates)

        if replace_existing:
            # Delete existing call assignments in range
            deleted = self.delete_call_assignments_in_range(
                start_date, end_date, call_type="overnight"
            )
            logger.info(f"Deleted {deleted} existing call assignments in range")

        created = []
        for data in assignments:
            assignment = CallAssignment(
                date=data.date,
                person_id=data.person_id,
                call_type=data.call_type,
                is_weekend=data.is_weekend,
                is_holiday=data.is_holiday,
            )
            self.db.add(assignment)
            created.append(assignment)

        self.db.flush()
        logger.info(f"Created {len(created)} call assignments")
        return created

    def delete_call_assignment(self, assignment_id: UUID) -> bool:
        """Delete a call assignment by ID."""
        assignment = self.get_call_assignment(assignment_id)
        if not assignment:
            return False

        self.db.delete(assignment)
        logger.info(f"Deleted call assignment: {assignment_id}")
        return True

    def delete_call_assignments_in_range(
        self,
        start_date: date,
        end_date: date,
        call_type: str | None = None,
    ) -> int:
        """
        Delete call assignments in a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            call_type: Optional filter by call type

        Returns:
            Number of assignments deleted
        """
        stmt = select(CallAssignment).where(
            and_(
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
        )
        if call_type:
            stmt = stmt.where(CallAssignment.call_type == call_type)

        result = self.db.execute(stmt)
        assignments = list(result.scalars().all())

        for assignment in assignments:
            self.db.delete(assignment)

        return len(assignments)

    def get_coverage_report(
        self,
        start_date: date,
        end_date: date,
    ) -> CallCoverageReport:
        """
        Get call coverage report for a date range.

        Calculates coverage percentage and identifies gaps.
        Only checks Sun-Thurs nights (Fri-Sat handled by FMIT).
        """
        # Count expected nights (Sun-Thurs = weekday 0,1,2,3,6)
        current = start_date
        expected_nights = []
        while current <= end_date:
            if current.weekday() in (0, 1, 2, 3, 6):  # Mon-Thurs, Sun
                expected_nights.append(current)
            current = (
                current.replace(day=current.day + 1)
                if current.day < 28
                else date(
                    current.year, current.month + 1 if current.month < 12 else 1, 1
                )
            )
            # Safer date iteration
            from datetime import timedelta

            current = start_date
            expected_nights = []
            while current <= end_date:
                if current.weekday() in (0, 1, 2, 3, 6):
                    expected_nights.append(current)
                current = current + timedelta(days=1)
            break

        # Get covered nights
        stmt = (
            select(CallAssignment.date)
            .where(
                and_(
                    CallAssignment.date >= start_date,
                    CallAssignment.date <= end_date,
                    CallAssignment.call_type == "overnight",
                )
            )
            .distinct()
        )
        result = self.db.execute(stmt)
        covered_dates = set(row[0] for row in result.all())

        # Find gaps
        gaps = [d for d in expected_nights if d not in covered_dates]

        total = len(expected_nights)
        covered = len([d for d in expected_nights if d in covered_dates])

        return CallCoverageReport(
            start_date=start_date,
            end_date=end_date,
            total_nights=total,
            covered_nights=covered,
            uncovered_nights=total - covered,
            coverage_percentage=covered / total * 100 if total > 0 else 100.0,
            gaps=gaps,
        )

    def get_equity_report(self, year: int) -> CallEquityReport:
        """
        Get call equity report for a year.

        Shows call distribution across faculty with statistics.
        """
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)

        # Get all overnight call assignments for the year
        stmt = (
            select(
                CallAssignment.person_id,
                CallAssignment.date,
                Person.name,
            )
            .join(Person, CallAssignment.person_id == Person.id)
            .where(
                and_(
                    CallAssignment.date >= start_date,
                    CallAssignment.date <= end_date,
                    CallAssignment.call_type == "overnight",
                )
            )
        )
        result = self.db.execute(stmt)
        rows = result.all()

        # Aggregate by person
        faculty_data: dict = {}
        for person_id, call_date, name in rows:
            if person_id not in faculty_data:
                faculty_data[person_id] = {
                    "person_id": str(person_id),
                    "name": name,
                    "sunday_calls": 0,
                    "weekday_calls": 0,
                    "total_calls": 0,
                }

            # Sunday is weekday 6
            if call_date.weekday() == 6:
                faculty_data[person_id]["sunday_calls"] += 1
            else:
                faculty_data[person_id]["weekday_calls"] += 1
            faculty_data[person_id]["total_calls"] += 1

        faculty_counts = list(faculty_data.values())

        # Calculate statistics
        sunday_counts = [f["sunday_calls"] for f in faculty_counts] or [0]
        weekday_counts = [f["weekday_calls"] for f in faculty_counts] or [0]

        def calc_stats(counts: list[int]) -> dict:
            if not counts or len(counts) == 1:
                return {
                    "min": counts[0] if counts else 0,
                    "max": counts[0] if counts else 0,
                    "mean": counts[0] if counts else 0,
                    "stddev": 0,
                }
            return {
                "min": min(counts),
                "max": max(counts),
                "mean": statistics.mean(counts),
                "stddev": statistics.stdev(counts),
            }

        sunday_stats = calc_stats(sunday_counts)
        weekday_stats = calc_stats(weekday_counts)

        # Calculate equity score (1 = perfect equity, 0 = very unequal)
        # Based on coefficient of variation (lower is better)
        total_counts = [f["total_calls"] for f in faculty_counts] or [0]
        if len(total_counts) > 1 and statistics.mean(total_counts) > 0:
            cv = statistics.stdev(total_counts) / statistics.mean(total_counts)
            equity_score = max(0, 1 - cv)  # Clamp to 0-1
        else:
            equity_score = 1.0

        return CallEquityReport(
            year=year,
            faculty_counts=faculty_counts,
            sunday_stats=sunday_stats,
            weekday_stats=weekday_stats,
            equity_score=equity_score,
        )

    def get_faculty_call_counts(
        self,
        faculty_ids: list[UUID],
        start_date: date,
        end_date: date,
    ) -> dict[UUID, dict[str, int]]:
        """
        Get call counts for specific faculty in date range.

        Returns:
            {faculty_id: {"sunday": count, "weekday": count, "total": count}}
        """
        stmt = select(
            CallAssignment.person_id,
            CallAssignment.date,
        ).where(
            and_(
                CallAssignment.person_id.in_(faculty_ids),
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
                CallAssignment.call_type == "overnight",
            )
        )
        result = self.db.execute(stmt)

        counts: dict[UUID, dict[str, int]] = {
            fid: {"sunday": 0, "weekday": 0, "total": 0} for fid in faculty_ids
        }

        for person_id, call_date in result.all():
            if call_date.weekday() == 6:
                counts[person_id]["sunday"] += 1
            else:
                counts[person_id]["weekday"] += 1
            counts[person_id]["total"] += 1

        return counts
