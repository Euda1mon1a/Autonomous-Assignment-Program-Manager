"""Call assignment service for business logic using async SQLAlchemy 2.0 patterns."""

import logging
import statistics
from collections import defaultdict
from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.schemas.call_assignment import (
    CallAssignmentCreate,
    CallAssignmentUpdate,
    CallCoverageReport,
    CallEquityReport,
)

logger = logging.getLogger(__name__)


class CallAssignmentService:
    """Service for call assignment business logic using async SQLAlchemy 2.0 patterns."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the call assignment service.

        Args:
            db: Async database session
        """
        self.db = db

    async def get_call_assignment(self, call_id: UUID) -> CallAssignment | None:
        """
        Get a single call assignment by ID with eager loading.

        Args:
            call_id: Call assignment ID

        Returns:
            CallAssignment or None if not found

        N+1 Optimization: Uses selectinload to eagerly fetch related Person entity,
        preventing N+1 queries when accessing call_assignment.person.
        """
        stmt = (
            select(CallAssignment)
            .options(selectinload(CallAssignment.person))
            .where(CallAssignment.id == call_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_call_assignments(
        self,
        skip: int = 0,
        limit: int = 100,
        person_id: UUID | None = None,
        call_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get paginated list of call assignments with optional filters.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            person_id: Filter by person ID
            call_type: Filter by call type ('overnight', 'weekend', 'backup')
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)

        Returns:
            Dict with 'items' (list of CallAssignments) and 'total' (count)

        N+1 Optimization: Uses selectinload to eagerly fetch Person relationships.
        """
        # Build base query
        stmt = select(CallAssignment).options(selectinload(CallAssignment.person))

        # Apply filters
        if person_id:
            stmt = stmt.where(CallAssignment.person_id == person_id)
        if call_type:
            stmt = stmt.where(CallAssignment.call_type == call_type)
        if start_date:
            stmt = stmt.where(CallAssignment.date >= start_date)
        if end_date:
            stmt = stmt.where(CallAssignment.date <= end_date)

        # Get total count
        count_stmt = select(func.count(CallAssignment.id))
        if person_id:
            count_stmt = count_stmt.where(CallAssignment.person_id == person_id)
        if call_type:
            count_stmt = count_stmt.where(CallAssignment.call_type == call_type)
        if start_date:
            count_stmt = count_stmt.where(CallAssignment.date >= start_date)
        if end_date:
            count_stmt = count_stmt.where(CallAssignment.date <= end_date)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Apply pagination and execute
        stmt = stmt.order_by(CallAssignment.date.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        call_assignments = result.scalars().all()

        return {"items": list(call_assignments), "total": total}

    async def get_call_assignments_by_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CallAssignment]:
        """
        Get all call assignments within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of CallAssignments in the date range

        N+1 Optimization: Eagerly loads Person relationships.
        """
        stmt = (
            select(CallAssignment)
            .options(selectinload(CallAssignment.person))
            .where(
                CallAssignment.date >= start_date,
                CallAssignment.date <= end_date,
            )
            .order_by(CallAssignment.date)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_call_assignments_by_person(
        self,
        person_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CallAssignment]:
        """
        Get all call assignments for a specific person, optionally filtered by date range.

        Args:
            person_id: Person ID
            start_date: Optional start date filter (inclusive)
            end_date: Optional end date filter (inclusive)

        Returns:
            List of CallAssignments for the person
        """
        stmt = (
            select(CallAssignment)
            .options(selectinload(CallAssignment.person))
            .where(CallAssignment.person_id == person_id)
        )

        if start_date:
            stmt = stmt.where(CallAssignment.date >= start_date)
        if end_date:
            stmt = stmt.where(CallAssignment.date <= end_date)

        stmt = stmt.order_by(CallAssignment.date)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_call_assignment(
        self,
        assignment_data: CallAssignmentCreate,
        *,
        commit: bool = True,
    ) -> dict:
        """
        Create a new call assignment.

        Args:
            assignment_data: Validated call assignment data

        Returns:
            Dict with:
            - call_assignment: The created CallAssignment
            - error: Error message if creation failed
        """
        # Check if person exists
        person_stmt = select(Person).where(Person.id == assignment_data.person_id)
        person_result = await self.db.execute(person_stmt)
        person = person_result.scalar_one_or_none()

        if not person:
            return {
                "call_assignment": None,
                "error": f"Person with ID {assignment_data.person_id} not found",
            }

        # Check for duplicate (same person, date, and call_type)
        duplicate_stmt = select(CallAssignment).where(
            CallAssignment.date == assignment_data.date,
            CallAssignment.person_id == assignment_data.person_id,
            CallAssignment.call_type == assignment_data.call_type,
        )
        duplicate_result = await self.db.execute(duplicate_stmt)
        existing = duplicate_result.scalar_one_or_none()

        if existing:
            return {
                "call_assignment": None,
                "error": "Call assignment already exists for this person, date, and type",
            }

        # Create the call assignment
        call_assignment = CallAssignment(
            date=assignment_data.date,
            person_id=assignment_data.person_id,
            call_type=assignment_data.call_type,
            is_weekend=assignment_data.is_weekend,
            is_holiday=assignment_data.is_holiday,
        )

        self.db.add(call_assignment)
        await self.db.flush()
        if commit:
            await self.db.commit()
        await self.db.refresh(call_assignment)

        logger.info(
            f"Created call assignment {call_assignment.id} for person {person.name} "
            f"on {assignment_data.date}"
        )

        return {"call_assignment": call_assignment, "error": None}

    async def update_call_assignment(
        self,
        call_id: UUID,
        update_data: CallAssignmentUpdate,
    ) -> dict:
        """
        Update an existing call assignment.

        Args:
            call_id: Call assignment ID
            update_data: Updated call assignment data

        Returns:
            Dict with:
            - call_assignment: The updated CallAssignment
            - error: Error message if update failed
        """
        # Get existing call assignment
        stmt = select(CallAssignment).where(CallAssignment.id == call_id)
        result = await self.db.execute(stmt)
        call_assignment = result.scalar_one_or_none()

        if not call_assignment:
            return {"call_assignment": None, "error": "Call assignment not found"}

        # Check if person exists if being updated
        if update_data.person_id:
            person_stmt = select(Person).where(Person.id == update_data.person_id)
            person_result = await self.db.execute(person_stmt)
            person = person_result.scalar_one_or_none()

            if not person:
                return {
                    "call_assignment": None,
                    "error": f"Person with ID {update_data.person_id} not found",
                }

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if value is not None:
                setattr(call_assignment, field, value)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(call_assignment)

        logger.info(f"Updated call assignment {call_id}")

        return {"call_assignment": call_assignment, "error": None}

    async def delete_call_assignment(self, call_id: UUID) -> dict:
        """
        Delete a call assignment.

        Args:
            call_id: Call assignment ID

        Returns:
            Dict with:
            - success: True if deleted, False otherwise
            - error: Error message if deletion failed
        """
        # Check if exists
        stmt = select(CallAssignment).where(CallAssignment.id == call_id)
        result = await self.db.execute(stmt)
        call_assignment = result.scalar_one_or_none()

        if not call_assignment:
            return {"success": False, "error": "Call assignment not found"}

        # Delete
        await self.db.delete(call_assignment)
        await self.db.flush()
        await self.db.commit()

        logger.info(f"Deleted call assignment {call_id}")

        return {"success": True, "error": None}

    async def bulk_create_call_assignments(
        self,
        assignments: list[CallAssignmentCreate],
        replace_existing: bool = False,
    ) -> dict:
        """
        Bulk create multiple call assignments (used by solver).

        Args:
            assignments: List of call assignment data to create
            replace_existing: If True, delete existing assignments in date range first

        Returns:
            Dict with:
            - created: List of created CallAssignments
            - errors: List of error messages for failed creations
            - count: Number of successfully created assignments
        """
        if replace_existing and assignments:
            # Find date range from assignments
            dates = [a.date for a in assignments]
            min_date = min(dates)
            max_date = max(dates)
            await self.clear_call_assignments_in_range(
                min_date,
                max_date,
                commit=False,
            )

        created = []
        errors = []

        for assignment_data in assignments:
            result = await self.create_call_assignment(assignment_data, commit=False)

            if result["error"]:
                errors.append(
                    f"Failed to create assignment for {assignment_data.person_id} "
                    f"on {assignment_data.date}: {result['error']}"
                )
            else:
                created.append(result["call_assignment"])

        # Commit all at once
        await self.db.flush()
        await self.db.commit()
        for assignment in created:
            await self.db.refresh(assignment)

        logger.info(
            f"Bulk created {len(created)} call assignments with {len(errors)} errors"
        )

        return {
            "created": created,
            "errors": errors,
            "count": len(created),
        }

    async def clear_call_assignments_in_range(
        self,
        start_date: date,
        end_date: date,
        *,
        commit: bool = True,
    ) -> dict:
        """
        Clear all call assignments within a date range (for schedule regeneration).

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dict with:
            - deleted: Number of call assignments deleted
            - error: Error message if deletion failed
        """
        # Delete all call assignments in range
        stmt = delete(CallAssignment).where(
            CallAssignment.date >= start_date,
            CallAssignment.date <= end_date,
        )

        result = await self.db.execute(stmt)
        deleted_count = result.rowcount

        await self.db.flush()
        if commit:
            await self.db.commit()

        logger.info(
            f"Cleared {deleted_count} call assignments from {start_date} to {end_date}"
        )

        return {"deleted": deleted_count, "error": None}

    async def get_coverage_report(
        self,
        start_date: date,
        end_date: date,
    ) -> CallCoverageReport:
        """
        Generate a coverage report for a date range.

        Identifies coverage gaps where no overnight call is assigned.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            CallCoverageReport with coverage statistics and gaps
        """
        # Get all call assignments in range
        assignments = await self.get_call_assignments_by_date_range(
            start_date, end_date
        )

        # Build set of covered dates
        covered_dates = set()
        for a in assignments:
            if a.call_type == "overnight":
                covered_dates.add(a.date)

        # Find expected overnight call dates (Sun-Thu, weekday 0,1,2,3,6)
        expected_dates = []
        current = start_date
        while current <= end_date:
            if current.weekday() in (0, 1, 2, 3, 6):  # Sun-Thu
                expected_dates.append(current)
            current = current + date.resolution

        # Calculate gaps
        gaps = [d for d in expected_dates if d not in covered_dates]

        coverage_pct = (
            (len(expected_dates) - len(gaps)) / len(expected_dates) * 100
            if expected_dates
            else 100.0
        )

        return CallCoverageReport(
            start_date=start_date,
            end_date=end_date,
            total_expected_nights=len(expected_dates),
            covered_nights=len(expected_dates) - len(gaps),
            coverage_percentage=round(coverage_pct, 2),
            gaps=gaps,
        )

    async def get_equity_report(
        self,
        start_date: date,
        end_date: date,
    ) -> CallEquityReport:
        """
        Generate an equity report showing call distribution across faculty.

        Tracks Sunday calls separately from weekday calls since Sunday
        is considered the worst call day.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            CallEquityReport with distribution statistics
        """
        # Get all call assignments in range
        assignments = await self.get_call_assignments_by_date_range(
            start_date, end_date
        )

        # Count calls per person, separated by Sunday vs weekday
        sunday_counts: dict[UUID, int] = defaultdict(int)
        weekday_counts: dict[UUID, int] = defaultdict(int)
        total_counts: dict[UUID, int] = defaultdict(int)
        names: dict[UUID, str] = {}

        for a in assignments:
            if a.call_type == "overnight":
                total_counts[a.person_id] += 1
                if a.date.weekday() == 6:  # Sunday
                    sunday_counts[a.person_id] += 1
                else:
                    weekday_counts[a.person_id] += 1

                if a.person:
                    names[a.person_id] = a.person.name

        # Calculate statistics
        sunday_values = list(sunday_counts.values()) if sunday_counts else [0]
        weekday_values = list(weekday_counts.values()) if weekday_counts else [0]
        total_values = list(total_counts.values()) if total_counts else [0]

        # Build distribution details
        distribution = []
        for person_id in total_counts:
            distribution.append(
                {
                    "person_id": str(person_id),
                    "name": names.get(person_id, "Unknown"),
                    "sunday_calls": sunday_counts.get(person_id, 0),
                    "weekday_calls": weekday_counts.get(person_id, 0),
                    "total_calls": total_counts.get(person_id, 0),
                }
            )

        # Sort by total calls descending
        distribution.sort(key=lambda x: x["total_calls"], reverse=True)

        return CallEquityReport(
            start_date=start_date,
            end_date=end_date,
            faculty_count=len(total_counts),
            total_overnight_calls=sum(total_values),
            sunday_call_stats={
                "min": min(sunday_values) if sunday_values else 0,
                "max": max(sunday_values) if sunday_values else 0,
                "mean": round(statistics.mean(sunday_values), 2)
                if sunday_values
                else 0,
                "stdev": round(statistics.stdev(sunday_values), 2)
                if len(sunday_values) > 1
                else 0,
            },
            weekday_call_stats={
                "min": min(weekday_values) if weekday_values else 0,
                "max": max(weekday_values) if weekday_values else 0,
                "mean": round(statistics.mean(weekday_values), 2)
                if weekday_values
                else 0,
                "stdev": round(statistics.stdev(weekday_values), 2)
                if len(weekday_values) > 1
                else 0,
            },
            distribution=distribution,
        )
