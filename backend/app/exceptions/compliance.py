"""ACGME compliance-specific exceptions.

These exceptions are raised when ACGME (Accreditation Council for Graduate
Medical Education) work hour rules, supervision ratios, or rest requirements
are violated.

ACGME Rules:
- 80-hour work week (averaged over 4 weeks)
- 1-in-7 day off (24 hours free from clinical duties)
- Supervision ratios (PGY-1: 1:2, PGY-2/3: 1:4)
- Maximum shift length (varies by program)
"""

from datetime import date
from typing import Any

from app.core.exceptions import AppException


class ACGMEComplianceError(AppException):
    """Base exception for ACGME compliance violations."""

    def __init__(
        self,
        message: str,
        resident_id: str | None = None,
        violation_date: date | str | None = None,
        status_code: int = 422,
        **context: Any,
    ) -> None:
        """Initialize ACGME compliance error.

        Args:
            message: User-friendly error message
            resident_id: ID of affected resident
            violation_date: Date of violation
            status_code: HTTP status code
            **context: Additional context
        """
        super().__init__(message, status_code)
        self.resident_id = resident_id
        self.violation_date = violation_date
        self.context = context


class WorkHourViolationError(ACGMEComplianceError):
    """Raised when 80-hour work week rule is violated."""

    def __init__(
        self,
        message: str = "80-hour work week limit violated",
        resident_id: str | None = None,
        period_start: date | str | None = None,
        period_end: date | str | None = None,
        actual_hours: float | None = None,
        limit_hours: float = 80.0,
        **context: Any,
    ) -> None:
        """Initialize work hour violation error.

        Args:
            message: User-friendly error message
            resident_id: ID of affected resident
            period_start: Start of evaluation period
            period_end: End of evaluation period
            actual_hours: Actual hours worked
            limit_hours: Hour limit (default 80)
            **context: Additional context
        """
        super().__init__(
            message=message,
            resident_id=resident_id,
            violation_date=period_end,
            **context,
        )
        self.period_start = period_start
        self.period_end = period_end
        self.actual_hours = actual_hours
        self.limit_hours = limit_hours


class RestRequirementViolationError(ACGMEComplianceError):
    """Raised when 1-in-7 rest day requirement is violated."""

    def __init__(
        self,
        message: str = "1-in-7 day rest requirement violated",
        resident_id: str | None = None,
        period_start: date | str | None = None,
        period_end: date | str | None = None,
        consecutive_days: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize rest requirement violation error.

        Args:
            message: User-friendly error message
            resident_id: ID of affected resident
            period_start: Start of evaluation period
            period_end: End of evaluation period
            consecutive_days: Number of consecutive work days
            **context: Additional context
        """
        super().__init__(
            message=message,
            resident_id=resident_id,
            violation_date=period_end,
            **context,
        )
        self.period_start = period_start
        self.period_end = period_end
        self.consecutive_days = consecutive_days


class SupervisionViolationError(ACGMEComplianceError):
    """Raised when supervision ratio requirements are violated."""

    def __init__(
        self,
        message: str = "Supervision ratio requirement violated",
        violation_date: date | str | None = None,
        pgy_level: str | None = None,
        actual_ratio: str | None = None,
        required_ratio: str | None = None,
        **context: Any,
    ) -> None:
        """Initialize supervision violation error.

        Args:
            message: User-friendly error message
            violation_date: Date of violation
            pgy_level: PGY level (PGY-1, PGY-2, PGY-3)
            actual_ratio: Actual faculty:resident ratio
            required_ratio: Required faculty:resident ratio
            **context: Additional context
        """
        super().__init__(
            message=message,
            violation_date=violation_date,
            **context,
        )
        self.pgy_level = pgy_level
        self.actual_ratio = actual_ratio
        self.required_ratio = required_ratio


class ShiftLengthViolationError(ACGMEComplianceError):
    """Raised when maximum shift length is exceeded."""

    def __init__(
        self,
        message: str = "Maximum shift length exceeded",
        resident_id: str | None = None,
        shift_date: date | str | None = None,
        actual_hours: float | None = None,
        max_hours: float | None = None,
        **context: Any,
    ) -> None:
        """Initialize shift length violation error.

        Args:
            message: User-friendly error message
            resident_id: ID of affected resident
            shift_date: Date of shift
            actual_hours: Actual shift length
            max_hours: Maximum allowed shift length
            **context: Additional context
        """
        super().__init__(
            message=message,
            resident_id=resident_id,
            violation_date=shift_date,
            **context,
        )
        self.actual_hours = actual_hours
        self.max_hours = max_hours


class CallFrequencyViolationError(ACGMEComplianceError):
    """Raised when call frequency limits are exceeded."""

    def __init__(
        self,
        message: str = "Call frequency limit exceeded",
        resident_id: str | None = None,
        period_start: date | str | None = None,
        period_end: date | str | None = None,
        actual_frequency: int | None = None,
        max_frequency: int | None = None,
        **context: Any,
    ) -> None:
        """Initialize call frequency violation error.

        Args:
            message: User-friendly error message
            resident_id: ID of affected resident
            period_start: Start of evaluation period
            period_end: End of evaluation period
            actual_frequency: Actual call frequency
            max_frequency: Maximum allowed call frequency
            **context: Additional context
        """
        super().__init__(
            message=message,
            resident_id=resident_id,
            violation_date=period_end,
            **context,
        )
        self.period_start = period_start
        self.period_end = period_end
        self.actual_frequency = actual_frequency
        self.max_frequency = max_frequency
