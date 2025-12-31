"""Swap execution service."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.db.transaction import transactional, transactional_with_retry
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.swap import SwapRecord, SwapStatus, SwapType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of a swap execution operation."""

    success: bool
    swap_id: UUID | None = None
    message: str = ""
    error_code: str | None = None


@dataclass
class RollbackResult:
    """Result of a swap rollback operation."""

    success: bool
    message: str = ""
    error_code: str | None = None


class SwapExecutor:
    """Service for executing FMIT swaps."""

    ROLLBACK_WINDOW_HOURS = 24

    def __init__(self, db: Session):
        self.db = db

    def execute_swap(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: date | None,
        swap_type: str,
        reason: str | None = None,
        executed_by_id: UUID | None = None,
    ) -> ExecutionResult:
        """
        Execute a swap after validation.

        Uses transactional context manager with retry logic to handle:
        - Automatic commit on success
        - Automatic rollback on failure
        - Deadlock detection and retry
        - Row-level locking to prevent race conditions
        """
        try:
            swap_id = uuid4()

            # Convert swap_type string to enum if needed
            if isinstance(swap_type, str):
                swap_type_enum = SwapType(swap_type)
            else:
                swap_type_enum = swap_type

            # Execute in transactional context with retry on deadlock
            with transactional_with_retry(
                self.db, max_retries=3, timeout_seconds=30.0
            ):
                # Persist SwapRecord to database
                swap_record = SwapRecord(
                    id=swap_id,
                    source_faculty_id=source_faculty_id,
                    source_week=source_week,
                    target_faculty_id=target_faculty_id,
                    target_week=target_week,
                    swap_type=swap_type_enum,
                    status=SwapStatus.EXECUTED,
                    reason=reason,
                    executed_at=datetime.utcnow(),
                    executed_by_id=executed_by_id,
                )
                self.db.add(swap_record)
                self.db.flush()

                # Update schedule assignments with row-level locking
                self._update_schedule_assignments(
                    source_faculty_id, source_week, target_faculty_id, target_week
                )

                # Update call cascade (Fri/Sat call assignments)
                self._update_call_cascade(source_week, target_faculty_id)
                if target_week:
                    self._update_call_cascade(target_week, source_faculty_id)

                # Transaction auto-commits on success, rolls back on exception

            logger.info(
                f"Swap executed successfully: {swap_id} "
                f"(source: {source_faculty_id}, target: {target_faculty_id})"
            )

            return ExecutionResult(
                success=True,
                swap_id=swap_id,
                message=f"Swap executed. Week {source_week} transferred.",
            )

        except Exception as e:
            logger.exception(f"Swap execution failed: {e}")
            return ExecutionResult(
                success=False,
                message=f"Swap execution failed: {str(e)}",
                error_code="EXECUTION_FAILED",
            )

    def rollback_swap(
        self,
        swap_id: UUID,
        reason: str,
        rolled_back_by_id: UUID | None = None,
    ) -> RollbackResult:
        """
        Rollback an executed swap within the allowed window.

        Uses row-level locking to prevent concurrent modifications.
        """
        logger.info("Rollback requested for swap %s, reason: %s", swap_id, reason)

        try:
            with transactional_with_retry(
                self.db, max_retries=3, timeout_seconds=30.0
            ):
                # Retrieve swap record with row-level lock to prevent concurrent rollbacks
                swap_record = (
                    self.db.query(SwapRecord)
                    .filter(SwapRecord.id == swap_id)
                    .with_for_update()
                    .first()
                )

                if not swap_record:
                    logger.warning("Rollback failed: swap %s not found", swap_id)
                    return RollbackResult(
                        success=False,
                        message="Swap record not found",
                        error_code="SWAP_NOT_FOUND",
                    )

                # Check if swap is in a state that can be rolled back
                if swap_record.status != SwapStatus.EXECUTED:
                    logger.warning(
                        "Rollback failed: swap %s has invalid status %s",
                        swap_id,
                        swap_record.status,
                    )
                    return RollbackResult(
                        success=False,
                        message=f"Cannot rollback swap with status: {swap_record.status}",
                        error_code="INVALID_STATUS",
                    )

                # Check if rollback is within the allowed time window
                if not self._check_rollback_window(swap_record):
                    time_since = (
                        datetime.utcnow() - swap_record.executed_at
                        if swap_record.executed_at
                        else None
                    )
                    logger.warning(
                        "Rollback failed: swap %s window expired (executed %s ago)",
                        swap_id,
                        time_since,
                    )
                    return RollbackResult(
                        success=False,
                        message=f"Rollback window of {self.ROLLBACK_WINDOW_HOURS} hours has expired",
                        error_code="ROLLBACK_WINDOW_EXPIRED",
                    )

                # Reverse the schedule assignments
                self._update_schedule_assignments(
                    swap_record.target_faculty_id,
                    swap_record.source_week,
                    swap_record.source_faculty_id,
                    swap_record.target_week,
                )

                # Reverse the call cascade
                self._update_call_cascade(
                    swap_record.source_week, swap_record.source_faculty_id
                )
                if swap_record.target_week:
                    self._update_call_cascade(
                        swap_record.target_week, swap_record.target_faculty_id
                    )

                # Update swap record status
                swap_record.status = SwapStatus.ROLLED_BACK
                swap_record.rolled_back_at = datetime.utcnow()
                swap_record.rolled_back_by_id = rolled_back_by_id
                swap_record.rollback_reason = reason

                # Transaction auto-commits

            logger.info(
                "Swap %s successfully rolled back (source: %s, target: %s)",
                swap_id,
                swap_record.source_faculty_id,
                swap_record.target_faculty_id,
            )

            return RollbackResult(
                success=True,
                message="Swap successfully rolled back",
            )

        except Exception as e:
            logger.exception("Rollback failed for swap %s: %s", swap_id, e)
            return RollbackResult(
                success=False,
                message=f"Rollback failed: {str(e)}",
                error_code="ROLLBACK_FAILED",
            )

    def _check_rollback_window(self, swap_record: SwapRecord) -> bool:
        """Check if swap is within rollback window (extracted for reuse)."""
        if not swap_record.executed_at:
            return False

        time_since_execution = datetime.utcnow() - swap_record.executed_at
        rollback_window = timedelta(hours=self.ROLLBACK_WINDOW_HOURS)
        return time_since_execution <= rollback_window

    def can_rollback(self, swap_id: UUID) -> bool:
        """Check if a swap can still be rolled back."""
        swap_record = self.db.query(SwapRecord).filter(SwapRecord.id == swap_id).first()

        if not swap_record:
            logger.debug("can_rollback(%s): swap not found", swap_id)
            return False

        if swap_record.status != SwapStatus.EXECUTED:
            logger.debug(
                "can_rollback(%s): invalid status %s", swap_id, swap_record.status
            )
            return False

        if not swap_record.executed_at:
            logger.debug("can_rollback(%s): no executed_at timestamp", swap_id)
            return False

        # Check if within rollback window
        time_since_execution = datetime.utcnow() - swap_record.executed_at
        rollback_window = timedelta(hours=self.ROLLBACK_WINDOW_HOURS)

        can_rb = time_since_execution <= rollback_window
        logger.debug(
            "can_rollback(%s): %s (executed %s ago, window=%sh)",
            swap_id,
            can_rb,
            time_since_execution,
            self.ROLLBACK_WINDOW_HOURS,
        )
        return can_rb

    def _update_schedule_assignments(
        self,
        source_faculty_id: UUID,
        source_week: date,
        target_faculty_id: UUID,
        target_week: date | None,
    ) -> None:
        """
        Update schedule assignments for the swap.

        Uses row-level locking to prevent race conditions when updating assignments.
        N+1 Optimization: Uses selectinload to eagerly fetch assignments for all
        blocks in the week range, preventing N+1 queries when iterating over blocks
        to find and update assignments.
        """
        # Calculate week end date (assuming week starts on Monday)
        source_week_end = source_week + timedelta(days=6)

        # Get all blocks in the source week with eager-loaded assignments
        # Row-level lock to prevent concurrent modifications
        # N+1 Optimization: Load blocks with their assignments in a single batch query
        source_blocks = (
            self.db.query(Block)
            .options(selectinload(Block.assignments))
            .filter(
                and_(
                    Block.date >= source_week,
                    Block.date <= source_week_end,
                )
            )
            .with_for_update()
            .all()
        )

        # Update assignments for source faculty in source week
        # N+1 Optimization: Assignments are already loaded, no additional queries needed
        for block in source_blocks:
            for assignment in block.assignments:
                if assignment.person_id == source_faculty_id:
                    # Transfer assignment to target faculty
                    assignment.person_id = target_faculty_id
                    assignment.notes = (
                        f"Swapped from faculty {source_faculty_id} via swap execution"
                    )

        # If this is a one-to-one swap, update target week assignments
        if target_week:
            target_week_end = target_week + timedelta(days=6)

            # N+1 Optimization: Eager load assignments for target week blocks
            # Row-level lock to prevent concurrent modifications
            target_blocks = (
                self.db.query(Block)
                .options(selectinload(Block.assignments))
                .filter(
                    and_(
                        Block.date >= target_week,
                        Block.date <= target_week_end,
                    )
                )
                .with_for_update()
                .all()
            )

            # N+1 Optimization: Assignments are already loaded
            for block in target_blocks:
                for assignment in block.assignments:
                    if assignment.person_id == target_faculty_id:
                        # Transfer assignment to source faculty
                        assignment.person_id = source_faculty_id
                        assignment.notes = f"Swapped from faculty {target_faculty_id} via swap execution"

    def _update_call_cascade(self, week: date, new_faculty_id: UUID) -> None:
        """
        Update Fri/Sat call assignments.

        N+1 Optimization: Uses selectinload to eagerly fetch person relationships
        for call assignments, though in this case we're only updating person_id.
        Included for consistency and potential future use.
        """
        # Calculate week end date
        week_end = week + timedelta(days=6)

        # Find Friday and Saturday in the week
        current_date = week
        while current_date <= week_end:
            # Check if this is Friday (weekday 4) or Saturday (weekday 5)
            if current_date.weekday() in [4, 5]:
                # Update call assignments for this date
                # N+1 Optimization: Eager load person relationship
                call_assignments = (
                    self.db.query(CallAssignment)
                    .options(selectinload(CallAssignment.person))
                    .filter(CallAssignment.date == current_date)
                    .all()
                )

                for call_assignment in call_assignments:
                    # Update to new faculty
                    call_assignment.person_id = new_faculty_id

            current_date += timedelta(days=1)
