"""
Swap Execution Service.

This module provides the core functionality for executing and rolling back
FMIT (Faculty Managing Inpatient Teaching) schedule swaps between faculty
members.

Key Features:
    - Atomic swap execution with automatic rollback on failure
    - 24-hour rollback window for executed swaps
    - Row-level locking to prevent race conditions
    - Call cascade updates (Friday/Saturday call assignments)
    - Comprehensive audit trail via SwapRecord

Transaction Safety:
    Uses the transactional_with_retry context manager to ensure:
    - Automatic commit on success
    - Automatic rollback on failure
    - Deadlock detection and retry (up to 3 attempts)
    - Row-level locking for concurrent modification prevention

Usage:
    from app.services.swap_executor import SwapExecutor

    executor = SwapExecutor(db)
    result = executor.execute_swap(
        source_faculty_id=source_id,
        source_week=week_start,
        target_faculty_id=target_id,
        target_week=None,  # Absorb swap (one-way)
        swap_type="absorb",
        reason="Faculty on TDY",
    )

    if result.success:
        print(f"Swap {result.swap_id} executed successfully")
    else:
        print(f"Swap failed: {result.error_code}")

See Also:
    - app.models.swap: SwapRecord, SwapStatus, SwapType models
    - app.db.transaction: Transactional context managers
    - app.services.swap_validator: Pre-execution validation
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.db.transaction import transactional, transactional_with_retry
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.swap import SwapRecord, SwapStatus, SwapType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """
    Result of a swap execution operation.

    Attributes:
        success: Whether the swap was executed successfully.
        swap_id: UUID of the created SwapRecord if successful, None otherwise.
        message: Human-readable description of the result.
        error_code: Machine-readable error code if failed. Common codes:
            - EXECUTION_FAILED: General execution failure
            - VALIDATION_FAILED: Pre-execution validation failed

    Example:
        >>> result = executor.execute_swap(...)
        >>> if result.success:
        ...     print(f"Created swap {result.swap_id}")
        ... else:
        ...     log.error(f"Failed: {result.error_code} - {result.message}")
    """

    success: bool
    swap_id: UUID | None = None
    message: str = ""
    error_code: str | None = None


@dataclass
class RollbackResult:
    """
    Result of a swap rollback operation.

    Attributes:
        success: Whether the rollback was completed successfully.
        message: Human-readable description of the result.
        error_code: Machine-readable error code if failed. Common codes:
            - SWAP_NOT_FOUND: No SwapRecord with the given ID
            - INVALID_STATUS: Swap is not in EXECUTED status
            - ROLLBACK_WINDOW_EXPIRED: 24-hour window has passed
            - ROLLBACK_FAILED: General rollback failure

    Example:
        >>> result = executor.rollback_swap(swap_id, reason="User requested")
        >>> if not result.success:
        ...     if result.error_code == "ROLLBACK_WINDOW_EXPIRED":
        ...         print("Rollback window has closed")
    """

    success: bool
    message: str = ""
    error_code: str | None = None


class SwapExecutor:
    """
    Service for executing FMIT (Faculty Managing Inpatient Teaching) swaps.

    This service handles the atomic execution of schedule swaps between faculty
    members, including the updates to:
    - Block assignments (transferring FMIT weeks)
    - Call assignments (Friday/Saturday call cascade)
    - SwapRecord audit trail

    Thread Safety:
        Uses row-level locking (SELECT ... FOR UPDATE) to prevent concurrent
        modifications. Safe for use in multi-threaded environments.

    Rollback Policy:
        Executed swaps can be rolled back within ROLLBACK_WINDOW_HOURS (24 hours).
        After this window, swaps become permanent and require manual intervention
        to reverse.

    Attributes:
        ROLLBACK_WINDOW_HOURS: Number of hours a swap can be rolled back (24).
        db: SQLAlchemy database session.

    Example:
        >>> executor = SwapExecutor(db)
        >>> # Execute an absorb swap (one-way transfer)
        >>> result = executor.execute_swap(
        ...     source_faculty_id=faculty_a.id,
        ...     source_week=date(2025, 1, 6),
        ...     target_faculty_id=faculty_b.id,
        ...     target_week=None,  # Absorb (no reciprocal)
        ...     swap_type="absorb",
        ... )
        >>> # Execute a one-to-one swap (bidirectional)
        >>> result = executor.execute_swap(
        ...     source_faculty_id=faculty_a.id,
        ...     source_week=date(2025, 1, 6),
        ...     target_faculty_id=faculty_b.id,
        ...     target_week=date(2025, 2, 3),  # Reciprocal week
        ...     swap_type="one_to_one",
        ... )
    """

    ROLLBACK_WINDOW_HOURS = 24

    def __init__(self, db: Session):
        """
        Initialize the SwapExecutor with a database session.

        Args:
            db: SQLAlchemy Session for database operations. The session should
                be managed by the caller (typically via FastAPI's Depends).
        """
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

        Atomically transfers FMIT week assignments from source to target faculty,
        optionally performing a reciprocal transfer for one-to-one swaps. Also
        updates the call cascade (Friday/Saturday call assignments).

        Uses transactional context manager with retry logic to handle:
        - Automatic commit on success
        - Automatic rollback on failure
        - Deadlock detection and retry (up to 3 attempts)
        - Row-level locking to prevent race conditions

        Args:
            source_faculty_id: UUID of the faculty giving up their week.
            source_week: Start date (Monday) of the week being transferred.
            target_faculty_id: UUID of the faculty receiving the week.
            target_week: For one-to-one swaps, the start date of the reciprocal
                week. None for absorb swaps.
            swap_type: Type of swap - "one_to_one" or "absorb".
            reason: Optional human-readable reason for the swap.
            executed_by_id: UUID of the user executing the swap (for audit).

        Returns:
            ExecutionResult: Contains success status, swap_id if successful,
                and error details if failed.

        Raises:
            No exceptions are raised - errors are captured in ExecutionResult.

        Example:
            >>> result = executor.execute_swap(
            ...     source_faculty_id=dr_smith.id,
            ...     source_week=date(2025, 1, 6),
            ...     target_faculty_id=dr_jones.id,
            ...     target_week=None,
            ...     swap_type="absorb",
            ...     reason="Dr. Smith on TDY to Walter Reed",
            ...     executed_by_id=scheduler.id,
            ... )
            >>> if result.success:
            ...     notify_faculty(result.swap_id)
        """
        try:
            swap_id = uuid4()

            # Convert swap_type string to enum if needed
            if isinstance(swap_type, str):
                swap_type_enum = SwapType(swap_type)
            else:
                swap_type_enum = swap_type

            # Execute in transactional context with retry on deadlock
            with transactional_with_retry(self.db, max_retries=3, timeout_seconds=30.0):
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

        except (SQLAlchemyError, ValueError, KeyError) as e:
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

        Reverses all changes made by execute_swap, including:
        - Block assignments (restore original faculty)
        - Call cascade (restore original call assignments)
        - SwapRecord status update (EXECUTED -> ROLLED_BACK)

        Rollback is only allowed within ROLLBACK_WINDOW_HOURS (24 hours) of
        execution. After this window, manual intervention is required.

        Uses row-level locking (SELECT ... FOR UPDATE) to prevent concurrent
        rollback attempts on the same swap.

        Args:
            swap_id: UUID of the SwapRecord to rollback.
            reason: Required explanation for the rollback (for audit trail).
            rolled_back_by_id: UUID of the user performing the rollback.

        Returns:
            RollbackResult: Contains success status and error details if failed.
                Possible error codes:
                - SWAP_NOT_FOUND: No swap with the given ID exists
                - INVALID_STATUS: Swap is not in EXECUTED status
                - ROLLBACK_WINDOW_EXPIRED: More than 24 hours since execution
                - ROLLBACK_FAILED: General failure during rollback

        Example:
            >>> # Rollback a swap that was just executed
            >>> result = executor.rollback_swap(
            ...     swap_id=swap_id,
            ...     reason="Faculty requested reversal due to schedule conflict",
            ...     rolled_back_by_id=scheduler.id,
            ... )
            >>> if result.success:
            ...     print("Swap successfully reversed")
            ... elif result.error_code == "ROLLBACK_WINDOW_EXPIRED":
            ...     print("Cannot rollback - 24 hour window has passed")
        """
        logger.info("Rollback requested for swap %s, reason: %s", swap_id, reason)

        try:
            with transactional_with_retry(self.db, max_retries=3, timeout_seconds=30.0):
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

        except (SQLAlchemyError, ValueError, KeyError) as e:
            logger.exception("Rollback failed for swap %s: %s", swap_id, e)
            return RollbackResult(
                success=False,
                message=f"Rollback failed: {str(e)}",
                error_code="ROLLBACK_FAILED",
            )

    def _check_rollback_window(self, swap_record: SwapRecord) -> bool:
        """
        Check if swap is within the rollback window.

        Internal helper extracted for reuse in rollback_swap and can_rollback.

        Args:
            swap_record: The SwapRecord to check.

        Returns:
            bool: True if within ROLLBACK_WINDOW_HOURS of execution,
                False if window has expired or executed_at is None.
        """
        if not swap_record.executed_at:
            return False

        time_since_execution = datetime.utcnow() - swap_record.executed_at
        rollback_window = timedelta(hours=self.ROLLBACK_WINDOW_HOURS)
        return time_since_execution <= rollback_window

    def can_rollback(self, swap_id: UUID) -> bool:
        """
        Check if a swap can still be rolled back.

        Validates that the swap:
        1. Exists in the database
        2. Has status EXECUTED (not already rolled back or pending)
        3. Has an executed_at timestamp
        4. Is within the 24-hour rollback window

        This is a read-only check - use rollback_swap() to perform the rollback.

        Args:
            swap_id: UUID of the SwapRecord to check.

        Returns:
            bool: True if rollback is allowed, False otherwise.

        Example:
            >>> if executor.can_rollback(swap_id):
            ...     show_rollback_button()
            ... else:
            ...     show_rollback_expired_message()
        """
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

        Transfers all block assignments within the specified week(s) from one
        faculty member to another. For one-to-one swaps, performs a bidirectional
        transfer; for absorb swaps, performs a one-way transfer.

        Implementation Details:
            - Uses row-level locking (SELECT ... FOR UPDATE) to prevent race
              conditions during concurrent swap operations.
            - Uses selectinload to eagerly fetch assignments for all blocks in
              the week range, preventing N+1 queries.
            - Assumes weeks start on Monday and span 7 days.

        Args:
            source_faculty_id: UUID of faculty whose assignments are being
                transferred away.
            source_week: Start date (Monday) of the source week.
            target_faculty_id: UUID of faculty receiving the assignments.
            target_week: For one-to-one swaps, the start date of the reciprocal
                week where target's assignments go to source. None for absorb.

        Note:
            This method modifies Assignment objects in place. The caller is
            responsible for committing the transaction.
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
        Update Friday and Saturday call assignments for a week.

        When FMIT weeks are swapped, the associated weekend call responsibilities
        must also transfer. This method updates all CallAssignment records for
        Friday and Saturday within the specified week.

        Call Cascade Logic:
            FMIT faculty are responsible for Friday and Saturday call during
            their FMIT week. When weeks are swapped, call responsibilities
            follow automatically.

        Implementation Details:
            - Uses selectinload to eagerly fetch person relationships
            - Iterates through the week to find Friday (weekday 4) and
              Saturday (weekday 5)
            - Updates all CallAssignment.person_id for those dates

        Args:
            week: Start date (Monday) of the week being processed.
            new_faculty_id: UUID of the faculty now responsible for call.

        Note:
            This method modifies CallAssignment objects in place. The caller
            is responsible for committing the transaction.
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
