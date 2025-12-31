"""Scheduling-specific exceptions for schedule generation and management.

These exceptions are raised during schedule generation, conflict detection,
solver operations, and schedule manipulation.
"""

from typing import Any

from app.core.exceptions import AppException, ConflictError


class SchedulingError(AppException):
    """Base exception for all scheduling-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        **context: Any,
    ):
        """Initialize scheduling error.

        Args:
            message: User-friendly error message
            status_code: HTTP status code
            **context: Additional context (assignment_id, date, etc.)
        """
        super().__init__(message, status_code)
        self.context = context


class ScheduleConflictError(ConflictError):
    """Raised when a schedule assignment conflicts with existing assignments."""

    def __init__(
        self,
        message: str = "Schedule assignment conflicts with existing assignments",
        conflicting_assignment_id: str | None = None,
        requested_date: str | None = None,
        person_id: str | None = None,
        **context: Any,
    ):
        """Initialize schedule conflict error.

        Args:
            message: User-friendly error message
            conflicting_assignment_id: ID of conflicting assignment
            requested_date: Date of requested assignment
            person_id: ID of person being assigned
            **context: Additional context
        """
        super().__init__(message)
        self.conflicting_assignment_id = conflicting_assignment_id
        self.requested_date = requested_date
        self.person_id = person_id
        self.context = context


class ScheduleGenerationError(SchedulingError):
    """Raised when schedule generation fails."""

    def __init__(
        self,
        message: str = "Failed to generate schedule",
        reason: str | None = None,
        block_range: tuple[str, str] | None = None,
        **context: Any,
    ):
        """Initialize schedule generation error.

        Args:
            message: User-friendly error message
            reason: Technical reason for failure
            block_range: Date range of failed generation (start, end)
            **context: Additional context
        """
        super().__init__(message, status_code=422, **context)
        self.reason = reason
        self.block_range = block_range


class SolverTimeoutError(SchedulingError):
    """Raised when the constraint solver times out."""

    def __init__(
        self,
        message: str = "Schedule solver timed out",
        timeout_seconds: int | None = None,
        partial_solution: dict[str, Any] | None = None,
        **context: Any,
    ):
        """Initialize solver timeout error.

        Args:
            message: User-friendly error message
            timeout_seconds: Timeout limit in seconds
            partial_solution: Partial solution if available
            **context: Additional context
        """
        super().__init__(message, status_code=504, **context)
        self.timeout_seconds = timeout_seconds
        self.partial_solution = partial_solution


class ConstraintViolationError(SchedulingError):
    """Raised when a scheduling constraint is violated."""

    def __init__(
        self,
        message: str = "Scheduling constraint violated",
        constraint_name: str | None = None,
        violated_rule: str | None = None,
        **context: Any,
    ):
        """Initialize constraint violation error.

        Args:
            message: User-friendly error message
            constraint_name: Name of violated constraint
            violated_rule: Specific rule that was violated
            **context: Additional context
        """
        super().__init__(message, status_code=422, **context)
        self.constraint_name = constraint_name
        self.violated_rule = violated_rule


class InfeasibleScheduleError(SchedulingError):
    """Raised when schedule requirements are infeasible (no solution exists)."""

    def __init__(
        self,
        message: str = "Schedule requirements cannot be satisfied",
        conflicting_constraints: list[str] | None = None,
        **context: Any,
    ):
        """Initialize infeasible schedule error.

        Args:
            message: User-friendly error message
            conflicting_constraints: List of conflicting constraint names
            **context: Additional context
        """
        super().__init__(message, status_code=422, **context)
        self.conflicting_constraints = conflicting_constraints or []


class RotationTemplateError(SchedulingError):
    """Raised when there's an issue with rotation templates."""

    def __init__(
        self,
        message: str = "Invalid rotation template",
        template_id: str | None = None,
        **context: Any,
    ):
        """Initialize rotation template error.

        Args:
            message: User-friendly error message
            template_id: ID of problematic template
            **context: Additional context
        """
        super().__init__(message, status_code=400, **context)
        self.template_id = template_id


class BlockAssignmentError(SchedulingError):
    """Raised when there's an issue with block assignments."""

    def __init__(
        self,
        message: str = "Invalid block assignment",
        block_id: str | None = None,
        assignment_id: str | None = None,
        **context: Any,
    ):
        """Initialize block assignment error.

        Args:
            message: User-friendly error message
            block_id: ID of block
            assignment_id: ID of assignment
            **context: Additional context
        """
        super().__init__(message, status_code=400, **context)
        self.block_id = block_id
        self.assignment_id = assignment_id
