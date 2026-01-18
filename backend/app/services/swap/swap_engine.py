"""
Core swap orchestration engine.

Coordinates all swap operations including request creation, matching,
validation, execution, and rollback across the system.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.person import Person
from app.models.assignment import Assignment


logger = logging.getLogger(__name__)


@dataclass
class SwapEngineResult:
    """Result of a swap engine operation."""

    success: bool
    swap_id: UUID | None = None
    message: str = ""
    error_code: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class SwapExecutionPlan:
    """Plan for executing a swap operation."""

    swap_id: UUID
    source_faculty_id: UUID
    target_faculty_id: UUID
    source_week: date
    target_week: date | None
    swap_type: SwapType
    validation_passed: bool
    execution_steps: list[str]
    rollback_plan: list[str]
    estimated_duration_seconds: float


class SwapEngine:
    """
    Core swap orchestration engine.

    Provides a unified interface for all swap operations and coordinates
    the various swap subsystems (matching, validation, execution, etc.).
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize swap engine.

        Args:
            db: Async database session
        """
        self.db = db
        self._validators: list[Any] = []
        self._matchers: list[Any] = []
        self._notifiers: list[Any] = []

    async def create_swap_request(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID | None,
        target_week: date | None,
        swap_type: SwapType,
        reason: str | None = None,
        requested_by_id: UUID | None = None,
        auto_match: bool = True,
    ) -> SwapEngineResult:
        """
        Create a new swap request.

        Args:
            source_faculty_id: Faculty requesting the swap
            source_week: Week to swap away
            target_faculty_id: Target faculty (optional for auto-match)
            target_week: Target week (optional for absorb)
            swap_type: Type of swap (one_to_one or absorb)
            reason: Reason for swap request
            requested_by_id: User making the request
            auto_match: Whether to automatically find matches

        Returns:
            SwapEngineResult with operation details
        """
        try:
            # Validate source faculty exists
            source_faculty = await self._get_faculty(source_faculty_id)
            if not source_faculty:
                return SwapEngineResult(
                    success=False,
                    message="Source faculty not found",
                    error_code="FACULTY_NOT_FOUND",
                )

            # Validate target faculty if specified
            if target_faculty_id:
                target_faculty = await self._get_faculty(target_faculty_id)
                if not target_faculty:
                    return SwapEngineResult(
                        success=False,
                        message="Target faculty not found",
                        error_code="FACULTY_NOT_FOUND",
                    )

            # Create swap record
            swap_record = SwapRecord(
                source_faculty_id=source_faculty_id,
                source_week=source_week,
                target_faculty_id=target_faculty_id,
                target_week=target_week,
                swap_type=swap_type,
                status=SwapStatus.PENDING,
                reason=reason,
                requested_at=datetime.utcnow(),
                requested_by_id=requested_by_id,
            )

            self.db.add(swap_record)
            await self.db.flush()

            metadata = {
                "swap_id": str(swap_record.id),
                "auto_match_enabled": auto_match,
            }

            # If auto-match is enabled and no target specified, find matches
            if auto_match and not target_faculty_id:
                match_result = await self._find_auto_matches(swap_record.id)
                metadata["matches_found"] = match_result.get("count", 0)
                metadata["best_match"] = match_result.get("best_match")

            await self.db.commit()

            logger.info(
                f"Created swap request {swap_record.id} for faculty {source_faculty_id}"
            )

            return SwapEngineResult(
                success=True,
                swap_id=swap_record.id,
                message="Swap request created successfully",
                metadata=metadata,
            )

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Failed to create swap request: {e}")
            return SwapEngineResult(
                success=False,
                message=f"Failed to create swap request: {str(e)}",
                error_code="CREATION_FAILED",
            )

    async def validate_swap(
        self,
        swap_id: UUID,
        comprehensive: bool = True,
    ) -> SwapEngineResult:
        """
        Validate a swap request.

        Args:
            swap_id: Swap request ID
            comprehensive: Run all validators (vs quick check)

        Returns:
            SwapEngineResult with validation details
        """
        try:
            swap = await self._get_swap(swap_id)
            if not swap:
                return SwapEngineResult(
                    success=False,
                    message="Swap not found",
                    error_code="SWAP_NOT_FOUND",
                )

            validation_results = []

            # Run all registered validators
            for validator in self._validators:
                try:
                    result = await validator.validate(swap)
                    validation_results.append(result)

                    if not result["valid"] and not comprehensive:
                        # Fast fail on first error
                        break
                except Exception as e:
                    logger.warning(
                        f"Validator {validator.__class__.__name__} failed: {e}"
                    )
                    validation_results.append(
                        {
                            "validator": validator.__class__.__name__,
                            "valid": False,
                            "error": str(e),
                        }
                    )

            all_valid = all(r.get("valid", False) for r in validation_results)

            return SwapEngineResult(
                success=all_valid,
                swap_id=swap_id,
                message="Validation passed" if all_valid else "Validation failed",
                metadata={
                    "validation_results": validation_results,
                    "total_validators": len(self._validators),
                    "passed": sum(1 for r in validation_results if r.get("valid")),
                },
            )

        except Exception as e:
            logger.exception(f"Validation error for swap {swap_id}: {e}")
            return SwapEngineResult(
                success=False,
                message=f"Validation error: {str(e)}",
                error_code="VALIDATION_ERROR",
            )

    async def execute_swap(
        self,
        swap_id: UUID,
        executed_by_id: UUID | None = None,
        dry_run: bool = False,
    ) -> SwapEngineResult:
        """
        Execute a validated swap.

        Args:
            swap_id: Swap request ID
            executed_by_id: User executing the swap
            dry_run: If True, validate but don't execute

        Returns:
            SwapEngineResult with execution details
        """
        try:
            swap = await self._get_swap(swap_id)
            if not swap:
                return SwapEngineResult(
                    success=False,
                    message="Swap not found",
                    error_code="SWAP_NOT_FOUND",
                )

            # Check status
            if swap.status != SwapStatus.PENDING:
                return SwapEngineResult(
                    success=False,
                    message=f"Cannot execute swap with status {swap.status}",
                    error_code="INVALID_STATUS",
                )

            # Validate before execution
            validation_result = await self.validate_swap(swap_id, comprehensive=True)
            if not validation_result.success:
                return SwapEngineResult(
                    success=False,
                    message="Pre-execution validation failed",
                    error_code="VALIDATION_FAILED",
                    metadata=validation_result.metadata,
                )

            if dry_run:
                return SwapEngineResult(
                    success=True,
                    swap_id=swap_id,
                    message="Dry run successful - swap would be executed",
                    metadata={"dry_run": True},
                )

            # Execute the swap
            execution_time = datetime.utcnow()

            # Update assignments
            await self._update_assignments(swap)

            # Update swap status
            swap.status = SwapStatus.EXECUTED
            swap.executed_at = execution_time
            swap.executed_by_id = executed_by_id

            await self.db.commit()

            # Send notifications
            await self._notify_swap_executed(swap)

            logger.info(f"Successfully executed swap {swap_id}")

            return SwapEngineResult(
                success=True,
                swap_id=swap_id,
                message="Swap executed successfully",
                metadata={
                    "executed_at": execution_time.isoformat(),
                    "source_week": swap.source_week.isoformat(),
                    "target_week": swap.target_week.isoformat()
                    if swap.target_week
                    else None,
                },
            )

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Failed to execute swap {swap_id}: {e}")
            return SwapEngineResult(
                success=False,
                message=f"Execution failed: {str(e)}",
                error_code="EXECUTION_FAILED",
            )

    async def rollback_swap(
        self,
        swap_id: UUID,
        reason: str,
        rolled_back_by_id: UUID | None = None,
    ) -> SwapEngineResult:
        """
        Rollback an executed swap.

        Args:
            swap_id: Swap ID to rollback
            reason: Reason for rollback
            rolled_back_by_id: User performing rollback

        Returns:
            SwapEngineResult with rollback details
        """
        try:
            swap = await self._get_swap(swap_id)
            if not swap:
                return SwapEngineResult(
                    success=False,
                    message="Swap not found",
                    error_code="SWAP_NOT_FOUND",
                )

            if swap.status != SwapStatus.EXECUTED:
                return SwapEngineResult(
                    success=False,
                    message=f"Cannot rollback swap with status {swap.status}",
                    error_code="INVALID_STATUS",
                )

            # Check rollback window
            if not await self._can_rollback(swap):
                return SwapEngineResult(
                    success=False,
                    message="Rollback window expired",
                    error_code="ROLLBACK_WINDOW_EXPIRED",
                )

            # Reverse the assignments
            await self._reverse_assignments(swap)

            # Update swap status
            swap.status = SwapStatus.ROLLED_BACK
            swap.rolled_back_at = datetime.utcnow()
            swap.rolled_back_by_id = rolled_back_by_id
            swap.rollback_reason = reason

            await self.db.commit()

            # Send notifications
            await self._notify_swap_rolled_back(swap)

            logger.info(f"Successfully rolled back swap {swap_id}")

            return SwapEngineResult(
                success=True,
                swap_id=swap_id,
                message="Swap rolled back successfully",
            )

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Failed to rollback swap {swap_id}: {e}")
            return SwapEngineResult(
                success=False,
                message=f"Rollback failed: {str(e)}",
                error_code="ROLLBACK_FAILED",
            )

    async def create_execution_plan(self, swap_id: UUID) -> SwapExecutionPlan | None:
        """
        Create a detailed execution plan for a swap.

        Args:
            swap_id: Swap request ID

        Returns:
            SwapExecutionPlan or None if swap not found
        """
        swap = await self._get_swap(swap_id)
        if not swap:
            return None

        execution_steps = [
            "Validate ACGME compliance",
            "Check coverage requirements",
            "Verify skill/credential requirements",
            f"Transfer assignments for week {swap.source_week}",
        ]

        if swap.target_week:
            execution_steps.append(f"Transfer assignments for week {swap.target_week}")

        execution_steps.extend(
            [
                "Update call cascades",
                "Update swap record status",
                "Send confirmation notifications",
            ]
        )

        rollback_steps = [
            f"Reverse assignments for week {swap.source_week}",
        ]

        if swap.target_week:
            rollback_steps.append(f"Reverse assignments for week {swap.target_week}")

        rollback_steps.extend(
            [
                "Reverse call cascades",
                "Update swap record to rolled_back",
                "Send rollback notifications",
            ]
        )

        return SwapExecutionPlan(
            swap_id=swap.id,
            source_faculty_id=swap.source_faculty_id,
            target_faculty_id=swap.target_faculty_id,
            source_week=swap.source_week,
            target_week=swap.target_week,
            swap_type=swap.swap_type,
            validation_passed=False,  # Would need to run validation
            execution_steps=execution_steps,
            rollback_plan=rollback_steps,
            estimated_duration_seconds=2.5,  # Estimated
        )

    # ===== Private Helper Methods =====

    async def _get_swap(self, swap_id: UUID) -> SwapRecord | None:
        """Get swap record by ID."""
        result = await self.db.execute(
            select(SwapRecord)
            .where(SwapRecord.id == swap_id)
            .options(
                selectinload(SwapRecord.source_faculty),
                selectinload(SwapRecord.target_faculty),
            )
        )
        return result.scalar_one_or_none()

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

    async def _find_auto_matches(self, swap_id: UUID) -> dict[str, Any]:
        """Find automatic matches for a swap request."""
        # This would integrate with the matching subsystem
        # For now, return a placeholder
        return {
            "count": 0,
            "best_match": None,
        }

    async def _update_assignments(self, swap: SwapRecord) -> None:
        """Update schedule assignments for the swap."""
        # This would integrate with the assignment service
        # Implementation would transfer assignments between faculty
        pass

    async def _reverse_assignments(self, swap: SwapRecord) -> None:
        """Reverse assignments for a rollback."""
        # Reverse the swap assignment changes
        pass

    async def _can_rollback(self, swap: SwapRecord) -> bool:
        """Check if swap can still be rolled back."""
        if not swap.executed_at:
            return False

        from datetime import timedelta

        rollback_window = timedelta(hours=24)
        time_since_execution = datetime.utcnow() - swap.executed_at

        return time_since_execution <= rollback_window

    async def _notify_swap_executed(self, swap: SwapRecord) -> None:
        """Send notifications for executed swap."""
        for notifier in self._notifiers:
            try:
                await notifier.notify_executed(swap)
            except Exception as e:
                logger.warning(f"Notifier {notifier.__class__.__name__} failed: {e}")

    async def _notify_swap_rolled_back(self, swap: SwapRecord) -> None:
        """Send notifications for rolled back swap."""
        for notifier in self._notifiers:
            try:
                await notifier.notify_rolled_back(swap)
            except Exception as e:
                logger.warning(f"Notifier {notifier.__class__.__name__} failed: {e}")

    def register_validator(self, validator: Any) -> None:
        """Register a swap validator."""
        self._validators.append(validator)

    def register_matcher(self, matcher: Any) -> None:
        """Register a swap matcher."""
        self._matchers.append(matcher)

    def register_notifier(self, notifier: Any) -> None:
        """Register a swap notifier."""
        self._notifiers.append(notifier)
