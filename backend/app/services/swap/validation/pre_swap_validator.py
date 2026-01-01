"""
Pre-swap validation.

Validates swap requests before execution to ensure they
meet all requirements and won't cause issues.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.swap import SwapRecord, SwapStatus
from app.models.person import Person
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.absence import Absence


logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of pre-swap validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    checks_performed: list[str]
    metadata: dict[str, Any]


class PreSwapValidator:
    """
    Validates swap requests before execution.

    Performs comprehensive checks to ensure swaps can be
    safely executed without causing schedule problems.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize pre-swap validator.

        Args:
            db: Async database session
        """
        self.db = db

    async def validate(self, swap: SwapRecord) -> ValidationResult:
        """
        Perform comprehensive pre-swap validation.

        Args:
            swap: Swap request to validate

        Returns:
            ValidationResult with validation details
        """
        errors = []
        warnings = []
        checks_performed = []

        # Check 1: Faculty existence
        checks_performed.append("faculty_existence")
        source_faculty = await self._get_faculty(swap.source_faculty_id)
        if not source_faculty:
            errors.append(f"Source faculty {swap.source_faculty_id} not found")

        target_faculty = await self._get_faculty(swap.target_faculty_id)
        if not target_faculty:
            errors.append(f"Target faculty {swap.target_faculty_id} not found")

        # Check 2: Week validity
        checks_performed.append("week_validity")
        if swap.source_week < datetime.utcnow().date():
            errors.append("Cannot swap weeks in the past")

        if swap.target_week and swap.target_week < datetime.utcnow().date():
            errors.append("Target week is in the past")

        # Check 3: Freeze horizon
        checks_performed.append("freeze_horizon")
        days_until_swap = (swap.source_week - datetime.utcnow().date()).days
        if days_until_swap < 7:
            warnings.append(
                f"Swap is only {days_until_swap} days away - very short notice"
            )

        # Check 4: Assignment existence
        checks_performed.append("assignment_existence")
        source_assignments = await self._get_week_assignments(
            swap.source_faculty_id,
            swap.source_week,
        )

        if not source_assignments:
            errors.append(
                f"No assignments found for source faculty on week {swap.source_week}"
            )

        # Check 5: No conflicting swaps
        checks_performed.append("conflicting_swaps")
        conflicting = await self._check_conflicting_swaps(swap)
        if conflicting:
            errors.append(f"Conflicting swap exists: {conflicting[0].id}")

        # Check 6: Faculty availability
        checks_performed.append("faculty_availability")
        # Check if target faculty has leave/TDY during source week
        if target_faculty:
            target_available = await self._check_availability(
                swap.target_faculty_id,
                swap.source_week,
            )
            if not target_available:
                errors.append(
                    f"Target faculty not available for week {swap.source_week}"
                )

        # Check 7: Reciprocal availability (for one-to-one swaps)
        if swap.target_week:
            checks_performed.append("reciprocal_availability")
            if source_faculty:
                source_available = await self._check_availability(
                    swap.source_faculty_id,
                    swap.target_week,
                )
                if not source_available:
                    errors.append(
                        f"Source faculty not available for week {swap.target_week}"
                    )

        metadata = {
            "total_checks": len(checks_performed),
            "validation_timestamp": datetime.utcnow().isoformat(),
            "swap_id": str(swap.id),
        }

        valid = len(errors) == 0

        logger.info(
            f"Pre-swap validation for {swap.id}: "
            f"{'PASSED' if valid else 'FAILED'} "
            f"({len(errors)} errors, {len(warnings)} warnings)"
        )

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            checks_performed=checks_performed,
            metadata=metadata,
        )

    async def quick_validate(self, swap: SwapRecord) -> bool:
        """
        Quick validation check (only critical errors).

        Args:
            swap: Swap request to validate

        Returns:
            True if valid
        """
        # Check faculty existence
        source_exists = await self._faculty_exists(swap.source_faculty_id)
        target_exists = await self._faculty_exists(swap.target_faculty_id)

        if not (source_exists and target_exists):
            return False

        # Check week not in past
        if swap.source_week < datetime.utcnow().date():
            return False

        return True

    # ===== Private Helper Methods =====

    async def _get_faculty(self, faculty_id: UUID) -> Person | None:
        """Get faculty member by ID."""
        result = await self.db.execute(
            select(Person).where(
                and_(
                    Person.id == faculty_id,
                    Person.type == "faculty",
                )
            )
        )
        return result.scalar_one_or_none()

    async def _faculty_exists(self, faculty_id: UUID) -> bool:
        """Check if faculty exists."""
        faculty = await self._get_faculty(faculty_id)
        return faculty is not None

    async def _get_week_assignments(
        self,
        faculty_id: UUID,
        week_start: date,
    ) -> list[Assignment]:
        """Get assignments for a faculty member in a given week."""
        week_end = week_start + timedelta(days=6)

        result = await self.db.execute(
            select(Assignment)
            .join(Block, Assignment.block_id == Block.id)
            .where(
                and_(
                    Assignment.person_id == faculty_id,
                    Block.date >= week_start,
                    Block.date <= week_end,
                )
            )
        )

        return list(result.scalars().all())

    async def _check_conflicting_swaps(
        self,
        swap: SwapRecord,
    ) -> list[SwapRecord]:
        """Check for conflicting swap requests."""
        result = await self.db.execute(
            select(SwapRecord).where(
                and_(
                    SwapRecord.id != swap.id,
                    SwapRecord.status.in_([SwapStatus.PENDING, SwapStatus.EXECUTED]),
                    SwapRecord.source_faculty_id == swap.source_faculty_id,
                    SwapRecord.source_week == swap.source_week,
                )
            )
        )

        return list(result.scalars().all())

    async def _check_availability(
        self,
        faculty_id: UUID,
        week: date,
    ) -> bool:
        """
        Check if faculty is available for a week.

        Checks absence/leave records including deployments, TDY, and other blocking absences.

        Args:
            faculty_id: Faculty member's UUID
            week: Week start date to check

        Returns:
            True if available, False if blocked by absence
        """
        # Calculate week boundaries
        week_end = week + timedelta(days=6)

        # Query for blocking absences that overlap with the week
        result = await self.db.execute(
            select(Absence).where(
                and_(
                    Absence.person_id == faculty_id,
                    Absence.is_blocking == True,
                    # Absence overlaps with week if:
                    # absence.start_date <= week_end AND absence.end_date >= week_start
                    Absence.start_date <= week_end,
                    Absence.end_date >= week,
                )
            )
        )

        blocking_absences = result.scalars().all()

        if blocking_absences:
            # Log which absences are blocking
            absence_types = [a.absence_type for a in blocking_absences]
            logger.info(
                f"Faculty {faculty_id} unavailable for week {week}: "
                f"blocked by {len(blocking_absences)} absence(s) ({', '.join(absence_types)})"
            )
            return False

        return True
