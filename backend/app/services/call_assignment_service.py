"""Call assignment service for business logic using async SQLAlchemy 2.0 patterns."""

import logging
import statistics
from collections import defaultdict
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.block import Block
from app.models.assignment import Assignment
from app.schemas.call_assignment import (
    BulkCallAssignmentUpdateInput,
    CallAssignmentCreate,
    CallAssignmentUpdate,
    CallCoverageReport,
    CallEquityReport,
    EquityPreviewResponse,
    FacultyEquityDetail,
    PCATAssignmentResult,
    PCATGenerationResponse,
    SimulatedChange,
)

logger = logging.getLogger(__name__)


class CallAssignmentService:
    """Service for call assignment business logic using async SQLAlchemy 2.0 patterns."""

    def __init__(self, db: AsyncSession) -> None:
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
            CallAssignment.date == assignment_data.call_date,
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
            date=assignment_data.call_date,
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
            f"on {assignment_data.call_date}"
        )

        return {"call_assignment": call_assignment, "error": None}

    async def update_call_assignment(
        self,
        call_id: UUID,
        update_data: CallAssignmentUpdate,
        *,
        commit: bool = True,
    ) -> dict:
        """
        Update an existing call assignment.

        Args:
            call_id: Call assignment ID
            update_data: Updated call assignment data
            commit: Whether to commit the transaction (default True)

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
        if commit:
            await self.db.commit()
        await self.db.refresh(call_assignment)

        logger.info(f"Updated call assignment {call_id}")

        return {"call_assignment": call_assignment, "error": None}

    async def delete_call_assignment(
        self,
        call_id: UUID,
        *,
        commit: bool = True,
    ) -> dict:
        """
        Delete a call assignment.

        Args:
            call_id: Call assignment ID
            commit: Whether to commit the transaction (default True)

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
        if commit:
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
                    f"on {assignment_data.call_date}: {result['error']}"
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

    # =========================================================================
    # Bulk Update Methods
    # =========================================================================

    async def bulk_update_call_assignments(
        self,
        assignment_ids: list[UUID],
        updates: BulkCallAssignmentUpdateInput,
    ) -> dict:
        """
        Bulk update multiple call assignments with the same updates.

        Args:
            assignment_ids: List of call assignment IDs to update
            updates: Fields to update on all selected assignments

        Returns:
            Dict with:
            - updated: Number of assignments successfully updated
            - errors: List of error messages for failed updates
            - assignments: List of updated CallAssignment objects
        """
        updated_assignments = []
        errors = []

        # Validate new person_id if provided
        if updates.person_id:
            person_stmt = select(Person).where(Person.id == updates.person_id)
            person_result = await self.db.execute(person_stmt)
            person = person_result.scalar_one_or_none()

            if not person:
                return {
                    "updated": 0,
                    "errors": [f"Person with ID {updates.person_id} not found"],
                    "assignments": [],
                }

        # Update each assignment
        for assignment_id in assignment_ids:
            stmt = (
                select(CallAssignment)
                .options(selectinload(CallAssignment.person))
                .where(CallAssignment.id == assignment_id)
            )
            result = await self.db.execute(stmt)
            call_assignment = result.scalar_one_or_none()

            if not call_assignment:
                errors.append(f"Call assignment {assignment_id} not found")
                continue

            # Apply updates
            if updates.person_id:
                call_assignment.person_id = updates.person_id

            updated_assignments.append(call_assignment)

        # Commit all changes
        await self.db.flush()
        await self.db.commit()

        # Refresh to get updated relationships
        for assignment in updated_assignments:
            await self.db.refresh(assignment)

        logger.info(
            f"Bulk updated {len(updated_assignments)} call assignments, "
            f"{len(errors)} errors"
        )

        return {
            "updated": len(updated_assignments),
            "errors": errors,
            "assignments": updated_assignments,
        }

    # =========================================================================
    # PCAT/DO Generation Methods
    # =========================================================================

    def _is_sun_thurs(self, d: date) -> bool:
        """Check if date is Sunday through Thursday (valid overnight call days)."""
        # Sunday = 6, Monday = 0, Tuesday = 1, Wednesday = 2, Thursday = 3
        return d.weekday() in (0, 1, 2, 3, 6)

    async def _find_template_by_abbrev(self, abbrev: str) -> RotationTemplate | None:
        """Find rotation template by abbreviation."""
        stmt = select(RotationTemplate).where(
            func.upper(RotationTemplate.abbreviation) == abbrev.upper()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_block_for_date_time(
        self, target_date: date, time_of_day: str
    ) -> Block | None:
        """Find schedule block for a specific date and time of day."""
        stmt = select(Block).where(
            Block.date == target_date,
            Block.time_of_day == time_of_day,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_assignment_if_not_exists(
        self,
        person_id: UUID,
        block_id: UUID,
        template_id: UUID,
    ) -> tuple[UUID | None, bool]:
        """
        Create assignment if it doesn't already exist.

        Returns:
            Tuple of (assignment_id, was_created)
        """
        # Check if assignment already exists
        existing_stmt = select(Assignment).where(
            Assignment.person_id == person_id,
            Assignment.block_id == block_id,
            Assignment.rotation_template_id == template_id,
        )
        existing_result = await self.db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing:
            return existing.id, False

        # Create new assignment - role defaults to 'primary' for PCAT/DO
        new_assignment = Assignment(
            person_id=person_id,
            block_id=block_id,
            rotation_template_id=template_id,
            role="primary",
        )
        self.db.add(new_assignment)
        await self.db.flush()

        return new_assignment.id, True

    async def generate_pcat_for_assignments(
        self,
        assignment_ids: list[UUID],
    ) -> PCATGenerationResponse:
        """
        Generate PCAT (AM) and DO (PM) assignments for the day after overnight call.

        For each call assignment on Sun-Thurs:
        - Creates PCAT assignment for next day AM block
        - Creates DO assignment for next day PM block

        Args:
            assignment_ids: List of call assignment IDs to process

        Returns:
            PCATGenerationResponse with results of the operation
        """
        results: list[PCATAssignmentResult] = []
        errors: list[str] = []
        pcat_created_count = 0
        do_created_count = 0

        # Find PCAT and DO templates
        pcat_template = await self._find_template_by_abbrev("PCAT")
        do_template = await self._find_template_by_abbrev("DO")

        if not pcat_template:
            errors.append("PCAT rotation template not found in database")
        if not do_template:
            errors.append("DO rotation template not found in database")

        if not pcat_template or not do_template:
            return PCATGenerationResponse(
                processed=0,
                pcat_created=0,
                do_created=0,
                errors=errors,
                results=[],
            )

        # Process each call assignment
        for assignment_id in assignment_ids:
            # Fetch call assignment with person
            stmt = (
                select(CallAssignment)
                .options(selectinload(CallAssignment.person))
                .where(CallAssignment.id == assignment_id)
            )
            result = await self.db.execute(stmt)
            call_assignment = result.scalar_one_or_none()

            if not call_assignment:
                errors.append(f"Call assignment {assignment_id} not found")
                continue

            # Skip if not Sun-Thurs (Friday/Saturday handled by FMIT)
            if not self._is_sun_thurs(call_assignment.date):
                results.append(
                    PCATAssignmentResult(
                        call_assignment_id=assignment_id,
                        call_date=call_assignment.date,
                        person_id=call_assignment.person_id,
                        person_name=call_assignment.person.name
                        if call_assignment.person
                        else None,
                        pcat_created=False,
                        do_created=False,
                        error=f"Call on {call_assignment.date} is Fri/Sat - use FMIT rules",
                    )
                )
                continue

            next_day = call_assignment.date + timedelta(days=1)
            pcat_created = False
            do_created = False
            pcat_assignment_id = None
            do_assignment_id = None
            error_msg = None

            # Find AM block for PCAT
            am_block = await self._find_block_for_date_time(next_day, "AM")
            if am_block:
                pcat_id, was_created = await self._create_assignment_if_not_exists(
                    person_id=call_assignment.person_id,
                    block_id=am_block.id,
                    template_id=pcat_template.id,
                )
                pcat_assignment_id = pcat_id
                pcat_created = was_created
                if was_created:
                    pcat_created_count += 1
            else:
                error_msg = f"No AM block found for {next_day}"

            # Find PM block for DO
            pm_block = await self._find_block_for_date_time(next_day, "PM")
            if pm_block:
                do_id, was_created = await self._create_assignment_if_not_exists(
                    person_id=call_assignment.person_id,
                    block_id=pm_block.id,
                    template_id=do_template.id,
                )
                do_assignment_id = do_id
                do_created = was_created
                if was_created:
                    do_created_count += 1
            else:
                if error_msg:
                    error_msg += f"; No PM block found for {next_day}"
                else:
                    error_msg = f"No PM block found for {next_day}"

            results.append(
                PCATAssignmentResult(
                    call_assignment_id=assignment_id,
                    call_date=call_assignment.date,
                    person_id=call_assignment.person_id,
                    person_name=call_assignment.person.name
                    if call_assignment.person
                    else None,
                    pcat_created=pcat_created,
                    do_created=do_created,
                    pcat_assignment_id=pcat_assignment_id,
                    do_assignment_id=do_assignment_id,
                    error=error_msg,
                )
            )

        # Commit all changes
        await self.db.commit()

        logger.info(
            f"PCAT generation: processed {len(results)} call assignments, "
            f"created {pcat_created_count} PCAT and {do_created_count} DO assignments"
        )

        return PCATGenerationResponse(
            processed=len(results),
            pcat_created=pcat_created_count,
            do_created=do_created_count,
            errors=errors,
            results=results,
        )

    # =========================================================================
    # Equity Preview Methods
    # =========================================================================

    async def get_equity_preview(
        self,
        start_date: date,
        end_date: date,
        simulated_changes: list[SimulatedChange],
    ) -> EquityPreviewResponse:
        """
        Preview equity distribution with simulated changes applied.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            simulated_changes: List of simulated changes to apply

        Returns:
            EquityPreviewResponse with current vs projected equity
        """
        # Get current equity
        current_equity = await self.get_equity_report(start_date, end_date)

        # Get all assignments in range
        assignments = await self.get_call_assignments_by_date_range(
            start_date, end_date
        )

        # Build current counts
        current_sunday: dict[UUID, int] = defaultdict(int)
        current_weekday: dict[UUID, int] = defaultdict(int)
        names: dict[UUID, str] = {}

        for a in assignments:
            if a.call_type == "overnight":
                if a.date.weekday() == 6:  # Sunday
                    current_sunday[a.person_id] += 1
                else:
                    current_weekday[a.person_id] += 1
                if a.person:
                    names[a.person_id] = a.person.name

        # Start with current counts for projected
        projected_sunday = dict(current_sunday)
        projected_weekday = dict(current_weekday)

        # Apply simulated changes
        for change in simulated_changes:
            # Decrement old person if specified
            if change.old_person_id:
                if change.call_date and change.call_date.weekday() == 6:
                    projected_sunday[change.old_person_id] = max(
                        0, projected_sunday.get(change.old_person_id, 0) - 1
                    )
                else:
                    projected_weekday[change.old_person_id] = max(
                        0, projected_weekday.get(change.old_person_id, 0) - 1
                    )

            # Increment new person
            if change.call_date and change.call_date.weekday() == 6:
                projected_sunday[change.new_person_id] = (
                    projected_sunday.get(change.new_person_id, 0) + 1
                )
            else:
                projected_weekday[change.new_person_id] = (
                    projected_weekday.get(change.new_person_id, 0) + 1
                )

            # Fetch name if not known
            if change.new_person_id not in names:
                person_stmt = select(Person).where(Person.id == change.new_person_id)
                person_result = await self.db.execute(person_stmt)
                person = person_result.scalar_one_or_none()
                if person:
                    names[change.new_person_id] = person.name

        # Calculate projected equity statistics
        all_person_ids = set(current_sunday.keys()) | set(current_weekday.keys())
        all_person_ids |= set(projected_sunday.keys()) | set(projected_weekday.keys())

        projected_sunday_values = [projected_sunday.get(pid, 0) for pid in all_person_ids]
        projected_weekday_values = [projected_weekday.get(pid, 0) for pid in all_person_ids]
        projected_total_values = [
            projected_sunday.get(pid, 0) + projected_weekday.get(pid, 0)
            for pid in all_person_ids
        ]

        # Build projected distribution
        projected_distribution = []
        for pid in all_person_ids:
            projected_distribution.append({
                "person_id": str(pid),
                "name": names.get(pid, "Unknown"),
                "sunday_calls": projected_sunday.get(pid, 0),
                "weekday_calls": projected_weekday.get(pid, 0),
                "total_calls": projected_sunday.get(pid, 0) + projected_weekday.get(pid, 0),
            })
        projected_distribution.sort(key=lambda x: x["total_calls"], reverse=True)

        projected_equity = CallEquityReport(
            start_date=start_date,
            end_date=end_date,
            faculty_count=len(all_person_ids),
            total_overnight_calls=sum(projected_total_values),
            sunday_call_stats={
                "min": min(projected_sunday_values) if projected_sunday_values else 0,
                "max": max(projected_sunday_values) if projected_sunday_values else 0,
                "mean": round(statistics.mean(projected_sunday_values), 2)
                if projected_sunday_values
                else 0,
                "stdev": round(statistics.stdev(projected_sunday_values), 2)
                if len(projected_sunday_values) > 1
                else 0,
            },
            weekday_call_stats={
                "min": min(projected_weekday_values) if projected_weekday_values else 0,
                "max": max(projected_weekday_values) if projected_weekday_values else 0,
                "mean": round(statistics.mean(projected_weekday_values), 2)
                if projected_weekday_values
                else 0,
                "stdev": round(statistics.stdev(projected_weekday_values), 2)
                if len(projected_weekday_values) > 1
                else 0,
            },
            distribution=projected_distribution,
        )

        # Build faculty details
        faculty_details = []
        for pid in all_person_ids:
            current_total = current_sunday.get(pid, 0) + current_weekday.get(pid, 0)
            projected_total = projected_sunday.get(pid, 0) + projected_weekday.get(pid, 0)

            faculty_details.append(
                FacultyEquityDetail(
                    person_id=pid,
                    name=names.get(pid, "Unknown"),
                    current_sunday_calls=current_sunday.get(pid, 0),
                    current_weekday_calls=current_weekday.get(pid, 0),
                    current_total_calls=current_total,
                    projected_sunday_calls=projected_sunday.get(pid, 0),
                    projected_weekday_calls=projected_weekday.get(pid, 0),
                    projected_total_calls=projected_total,
                    delta=projected_total - current_total,
                )
            )

        # Calculate improvement score based on standard deviation reduction
        current_stdev = current_equity.weekday_call_stats.get("stdev", 0)
        projected_stdev = projected_equity.weekday_call_stats.get("stdev", 0)

        # Improvement score: positive = more equitable, negative = less equitable
        if current_stdev > 0:
            improvement_score = (current_stdev - projected_stdev) / current_stdev
        else:
            improvement_score = 0.0

        # Clamp to -1 to 1
        improvement_score = max(-1.0, min(1.0, improvement_score))

        return EquityPreviewResponse(
            start_date=start_date,
            end_date=end_date,
            current_equity=current_equity,
            projected_equity=projected_equity,
            faculty_details=faculty_details,
            improvement_score=round(improvement_score, 3),
        )
