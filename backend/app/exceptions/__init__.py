"""Domain-specific exception modules for the Residency Scheduler application.

This package organizes exceptions by domain to provide better error handling
and clearer error messages for different parts of the application.

Import hierarchy:
    from app.exceptions import (
        # Base exceptions
        AppException,
        NotFoundError,
        ValidationError,
        ConflictError,
        UnauthorizedError,
        ForbiddenError,

        # Scheduling exceptions
        SchedulingError,
        ScheduleConflictError,
        ScheduleGenerationError,
        SolverTimeoutError,

        # ACGME compliance exceptions
        ACGMEComplianceError,
        WorkHourViolationError,
        SupervisionViolationError,
        RestRequirementViolationError,

        # Authentication/Authorization exceptions
        AuthenticationError,
        InvalidCredentialsError,
        TokenExpiredError,
        InvalidTokenError,
        PermissionDeniedError,

        # Database exceptions
        DatabaseError,
        RecordNotFoundError,
        DuplicateRecordError,
        IntegrityConstraintError,
        ConcurrentModificationError,

        # Validation exceptions
        InputValidationError,
        DateValidationError,
        SchemaValidationError,
        BusinessRuleViolationError,

        # External service exceptions
        ExternalServiceError,
        ServiceUnavailableError,
        ServiceTimeoutError,
        ExternalAPIError,

        # Rate limiting exceptions
        RateLimitExceededError,
        QuotaExceededError,
    )

Example usage:
    from app.exceptions import ScheduleConflictError, WorkHourViolationError

    # Raise domain-specific exception
    if has_conflict:
        raise ScheduleConflictError(
            message="Assignment conflicts with existing schedule",
            conflicting_assignment_id=existing.id,
            requested_date=assignment.date,
        )

    # ACGME compliance violation
    if total_hours > 80:
        raise WorkHourViolationError(
            resident_id=resident.id,
            period_start=week_start,
            period_end=week_end,
            actual_hours=total_hours,
            limit_hours=80,
        )
"""

# Import base exceptions from core
from app.core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)

# Import domain-specific exceptions
from app.exceptions.authentication import (
    AuthenticationError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    TokenExpiredError,
)
from app.exceptions.compliance import (
    ACGMEComplianceError,
    RestRequirementViolationError,
    SupervisionViolationError,
    WorkHourViolationError,
)
from app.exceptions.database import (
    ConcurrentModificationError,
    DatabaseError,
    DuplicateRecordError,
    IntegrityConstraintError,
    RecordNotFoundError,
)
from app.exceptions.external_service import (
    ExternalAPIError,
    ExternalServiceError,
    ServiceTimeoutError,
    ServiceUnavailableError,
)
from app.exceptions.rate_limit import (
    QuotaExceededError,
    RateLimitExceededError,
)
from app.exceptions.scheduling import (
    ScheduleConflictError,
    ScheduleGenerationError,
    SchedulingError,
    SolverTimeoutError,
)
from app.exceptions.validation import (
    BusinessRuleViolationError,
    DateValidationError,
    InputValidationError,
    SchemaValidationError,
)

__all__ = [
    # Base exceptions (from core)
    "AppException",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    # Scheduling exceptions
    "SchedulingError",
    "ScheduleConflictError",
    "ScheduleGenerationError",
    "SolverTimeoutError",
    # ACGME compliance exceptions
    "ACGMEComplianceError",
    "WorkHourViolationError",
    "SupervisionViolationError",
    "RestRequirementViolationError",
    # Authentication/Authorization exceptions
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "PermissionDeniedError",
    # Database exceptions
    "DatabaseError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "IntegrityConstraintError",
    "ConcurrentModificationError",
    # Validation exceptions
    "InputValidationError",
    "DateValidationError",
    "SchemaValidationError",
    "BusinessRuleViolationError",
    # External service exceptions
    "ExternalServiceError",
    "ServiceUnavailableError",
    "ServiceTimeoutError",
    "ExternalAPIError",
    # Rate limiting exceptions
    "RateLimitExceededError",
    "QuotaExceededError",
]
