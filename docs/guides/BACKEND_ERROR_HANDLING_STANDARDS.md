# Backend Error Handling Standards
## SESSION 8 BURN: Standardized Exception Hierarchy & Response Patterns

**Generated:** 2025-12-31
**Based On:** SESSION_1_BACKEND/backend-error-handling.md
**Status:** IMPLEMENTATION GUIDE

---

## Executive Summary

The backend implements RFC 7807 compliant error handling with:
- ✅ **50+ exception classes** across 8 domain modules
- ✅ **110+ predefined error codes** with machine-readable mapping
- ✅ **Global middleware** for consistent error responses
- ✅ **Comprehensive PII filtering** preventing sensitive data leakage

**Key Finding:** 267 error handling blocks need standardization. This guide provides unified patterns for all services.

---

## SECTION 1: EXCEPTION HIERARCHY STANDARDIZATION

### Recommended Exception Structure

```python
# backend/app/core/exceptions.py (EXTENDED)

from typing import Any, Optional
from dataclasses import dataclass

class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        user_message: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "INTERNAL_ERROR"
        self.details = details or {}
        self.user_message = user_message or message
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to error response dict."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "status_code": self.status_code,
        }


# Domain-Specific Exception Classes

class NotFoundError(AppException):
    """404 - Resource not found."""
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} not found",
            status_code=404,
            error_code="NOT_FOUND",
            user_message=f"The {resource_type} you're looking for doesn't exist",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ValidationError(AppException):
    """422 - Validation failed."""
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation failed on {field}: {reason}",
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"field": field, "reason": reason},
        )


class ConflictError(AppException):
    """409 - Resource conflict."""
    def __init__(self, message: str, conflict_details: Optional[dict] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=conflict_details or {},
        )


# Domain Exceptions

class ACGMEComplianceError(AppException):
    """ACGME rule violation."""
    def __init__(
        self,
        violation_type: str,
        resident_id: str,
        current_value: int,
        limit: int,
        period: Optional[dict] = None,
    ):
        super().__init__(
            message=f"ACGME {violation_type} violation",
            status_code=409,
            error_code=f"ACGME_{violation_type.upper()}",
            details={
                "violation_type": violation_type,
                "resident_id": resident_id,
                "current_value": current_value,
                "limit": limit,
                "period": period,
            },
            user_message=f"Schedule violates ACGME {violation_type} rule",
        )


class ScheduleConflictError(AppException):
    """Schedule conflict detected."""
    def __init__(
        self,
        assignment_id: str,
        conflict_type: str,
        conflicting_assignment_id: Optional[str] = None,
    ):
        super().__init__(
            message=f"Schedule conflict: {conflict_type}",
            status_code=409,
            error_code="SCHEDULE_CONFLICT",
            details={
                "assignment_id": assignment_id,
                "conflict_type": conflict_type,
                "conflicting_assignment_id": conflicting_assignment_id,
            },
            user_message="Schedule has conflicting assignments",
        )
```

---

## SECTION 2: ERROR RESPONSE PATTERNS

### Pattern 1: Standard Error Response

**Usage:** Most API endpoints

```python
# Response format (RFC 7807)
{
    "type": "https://api.residency-scheduler.example.com/errors/validation-error",
    "title": "Validation Failed",
    "status": 422,
    "detail": "The request contains invalid data",
    "instance": "/api/v1/assignments",
    "error_code": "VALIDATION_ERROR",
    "error_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-12-31T10:30:00Z",
    "request_id": "req-12345"
}
```

### Pattern 2: Validation Error Response (Multiple Fields)

**Usage:** Batch operations, form submissions

```python
{
    "type": "https://api.residency-scheduler.example.com/errors/validation-error",
    "title": "Validation Failed",
    "status": 422,
    "error_code": "VALIDATION_ERROR",
    "error_id": "...",
    "timestamp": "...",
    "errors": [
        {
            "field": "email",
            "message": "Invalid email format",
            "type": "value_error.email",
            "location": ["body", "email"]
        },
        {
            "field": "pgy_level",
            "message": "Must be between 1 and 5",
            "type": "value_error.number.not_in_range",
            "location": ["body", "pgy_level"]
        }
    ]
}
```

### Pattern 3: ACGME Compliance Error Response

**Usage:** Schedule operations with compliance violations

```python
{
    "type": "https://api.residency-scheduler.example.com/errors/acgme-compliance",
    "title": "ACGME Compliance Violation",
    "status": 409,
    "error_code": "ACGME_WORK_HOUR_VIOLATION",
    "detail": "Schedule exceeds 80-hour rule",
    "violations": [
        {
            "rule": "80_hour_rule",
            "resident_id": "resident-123",
            "current_value": 85,
            "limit": 80,
            "period_start": "2025-12-29",
            "period_end": "2026-01-26",
            "severity": "error"
        }
    ]
}
```

### Pattern 4: Batch Operation Error Response

**Usage:** Bulk imports, multi-record operations

```python
{
    "type": "https://api.residency-scheduler.example.com/errors/batch-operation-error",
    "title": "Batch Operation Partially Failed",
    "status": 207,
    "error_code": "PARTIAL_BATCH_FAILURE",
    "summary": {
        "total": 100,
        "succeeded": 87,
        "failed": 13
    },
    "errors": [
        {
            "record_index": 3,
            "record_id": "record-uuid-123",
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid email format"
        },
        {
            "record_index": 7,
            "record_id": "record-uuid-456",
            "error_code": "DUPLICATE_RECORD",
            "message": "Person already exists"
        }
    ]
}
```

---

## SECTION 3: SERVICE-LEVEL ERROR HANDLING

### Pattern A: Service Returns Result Dict

**Current Pattern (Widespread)**

```python
# Service method
def create_assignment(self, block_id: UUID, person_id: UUID) -> dict:
    """Returns dict with success/error keys."""
    existing = self.assignment_repo.get_by_block_and_person(block_id, person_id)
    if existing:
        return {
            "assignment": None,
            "error": "Person already assigned to this block",
            "acgme_warnings": [],
        }

    assignment = self.assignment_repo.create({...})
    return {
        "assignment": assignment,
        "error": None,
        "acgme_warnings": [...],
    }

# Controller handler
def create_assignment(self, assignment_in: AssignmentCreate) -> dict:
    result = self.service.create_assignment(...)

    if result["error"]:
        raise HTTPException(status_code=409, detail=result["error"])

    return result
```

**Recommendation:** Use typed Result dataclass for clarity

### Pattern B: Service Raises Exception (Recommended)

**Improved Pattern**

```python
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

@dataclass
class ServiceResult(Generic[T]):
    """Type-safe service result."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    warnings: Optional[list[str]] = None

    def unwrap(self) -> T:
        """Raise exception if failed."""
        if not self.success:
            raise ValueError(self.error)
        return self.data

    def unwrap_or(self, default: T) -> T:
        """Return data or default."""
        return self.data if self.success else default


# Service method (improved)
def create_assignment(
    self,
    block_id: UUID,
    person_id: UUID,
) -> ServiceResult[Assignment]:
    """Returns typed result with explicit success/error."""
    existing = self.assignment_repo.get_by_block_and_person(block_id, person_id)

    if existing:
        return ServiceResult(
            success=False,
            error="Person already assigned to this block"
        )

    try:
        assignment = self.assignment_repo.create({...})
        validation_result = self.acgme_validator.validate(...)

        return ServiceResult(
            success=True,
            data=assignment,
            warnings=validation_result.get("warnings", []),
        )
    except ACGMEComplianceError as e:
        return ServiceResult(success=False, error=str(e))

# Controller handler (improved)
def create_assignment(self, assignment_in: AssignmentCreate) -> dict:
    result = self.service.create_assignment(...)

    if not result.success:
        raise HTTPException(
            status_code=409,
            detail=result.error,
        )

    return {
        "assignment": result.data,
        "warnings": result.warnings or [],
    }
```

---

## SECTION 4: ERROR CODE STANDARDIZATION

### Error Code Categories

```python
# backend/app/core/error_codes.py (EXTENDED)

from enum import Enum

class ErrorCode(str, Enum):
    """Machine-readable error codes."""

    # Resource Errors (4xx client errors)
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    DUPLICATE_RECORD = "DUPLICATE_RECORD"

    # Validation Errors (422)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_FORMAT = "INVALID_FORMAT"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"

    # Authentication/Authorization (401/403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Business Logic (409)
    CONFLICT = "CONFLICT"
    SCHEDULE_CONFLICT = "SCHEDULE_CONFLICT"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"

    # ACGME Compliance (409)
    ACGME_COMPLIANCE_ERROR = "ACGME_COMPLIANCE_ERROR"
    WORK_HOUR_VIOLATION = "WORK_HOUR_VIOLATION"
    REST_REQUIREMENT_VIOLATION = "REST_REQUIREMENT_VIOLATION"
    SUPERVISION_VIOLATION = "SUPERVISION_VIOLATION"

    # Database (5xx server errors)
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    TRANSACTION_ERROR = "TRANSACTION_ERROR"

    # External Services (5xx)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    EMAIL_SERVICE_ERROR = "EMAIL_SERVICE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    # Rate Limiting (429)
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Generic
    INTERNAL_ERROR = "INTERNAL_ERROR"


# Mapping to HTTP status codes
ERROR_CODE_TO_STATUS = {
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.CONFLICT: 409,
    ErrorCode.RATE_LIMIT_EXCEEDED: 429,
    ErrorCode.DATABASE_CONNECTION_ERROR: 503,
    ErrorCode.INTERNAL_ERROR: 500,
}

# Human-readable descriptions
ERROR_CODE_DESCRIPTIONS = {
    ErrorCode.NOT_FOUND: "The requested resource could not be found",
    ErrorCode.VALIDATION_ERROR: "The request contains invalid data",
    ErrorCode.UNAUTHORIZED: "Authentication is required",
    ErrorCode.FORBIDDEN: "You do not have permission to access this resource",
    ErrorCode.CONFLICT: "The request conflicts with the current state",
    ErrorCode.ACGME_COMPLIANCE_ERROR: "The schedule violates ACGME regulations",
    ErrorCode.WORK_HOUR_VIOLATION: "Schedule exceeds 80-hour rule",
    ErrorCode.REST_REQUIREMENT_VIOLATION: "Schedule violates 1-in-7 rest requirement",
}
```

---

## SECTION 5: MIDDLEWARE CONFIGURATION

### Global Error Handler Middleware

```python
# backend/app/middleware/error_handler.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    """Global error handling middleware."""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except RequestValidationError as exc:
            # Pydantic validation errors
            return await self._handle_validation_error(request, exc)

        except AppException as exc:
            # Custom application exceptions
            return await self._handle_app_exception(request, exc)

        except Exception as exc:
            # Unexpected errors
            return await self._handle_internal_error(request, exc)

    async def _handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        error_id = str(uuid4())
        errors = []

        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"][1:])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        logger.warning(
            f"Validation error: {error_id}",
            extra={"request_id": request.headers.get("X-Request-ID")}
        )

        return JSONResponse(
            status_code=422,
            content={
                "type": "validation_error",
                "title": "Validation Failed",
                "status": 422,
                "error_code": "VALIDATION_ERROR",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
                "errors": errors,
            },
        )

    async def _handle_app_exception(
        self,
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        error_id = str(uuid4())

        log_level = "warning" if exc.status_code < 500 else "error"
        getattr(logger, log_level)(
            f"Application error: {exc.error_code}",
            exc_info=True,
            extra={
                "error_id": error_id,
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"about:blank#{exc.error_code.lower()}",
                "title": exc.error_code,
                "status": exc.status_code,
                "detail": exc.user_message,
                "error_code": exc.error_code,
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
                "instance": str(request.url.path),
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

    async def _handle_internal_error(
        self,
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected errors."""
        error_id = str(uuid4())

        logger.critical(
            "Unhandled exception",
            exc_info=exc,
            extra={
                "error_id": error_id,
                "request_id": request.headers.get("X-Request-ID"),
            },
        )

        # Return generic message to client (don't leak details)
        return JSONResponse(
            status_code=500,
            content={
                "type": "about:blank#internal_error",
                "title": "Internal Server Error",
                "status": 500,
                "detail": "An unexpected error occurred. Please contact support.",
                "error_code": "INTERNAL_ERROR",
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.headers.get("X-Request-ID"),
            },
        )
```

### Registering Middleware

```python
# backend/app/main.py

from fastapi import FastAPI
from app.middleware.error_handler import ErrorHandlerMiddleware

app = FastAPI()

# Register error handler AFTER other middleware
app.add_middleware(ErrorHandlerMiddleware)
```

---

## SECTION 6: SERVICE ERROR HANDLING CHECKLIST

### Checklist for Every Service Method

```python
# Template: service_method_error_handling.py

class ExampleService:
    def critical_operation(self, **kwargs) -> ServiceResult[ResultType]:
        """
        Example service method with comprehensive error handling.

        Raises:
            ValidationError: If input validation fails
            NotFoundError: If required resource doesn't exist
            ACGMEComplianceError: If compliance check fails
        """
        try:
            # [ ] 1. Validate inputs
            if not kwargs.get("required_field"):
                raise ValidationError("required_field", "is required")

            # [ ] 2. Check prerequisites
            resource = self.repo.get_by_id(kwargs["id"])
            if not resource:
                raise NotFoundError("Resource", kwargs["id"])

            # [ ] 3. Check business rules
            if not self.is_valid_state(resource):
                raise ConflictError("Invalid state for operation")

            # [ ] 4. Check compliance
            if not self.check_compliance(resource):
                raise ACGMEComplianceError(...)

            # [ ] 5. Execute operation
            result = self._perform_operation(resource, **kwargs)

            # [ ] 6. Validate result
            if not self.validate_result(result):
                raise ValueError("Result validation failed")

            # [ ] 7. Return success
            return ServiceResult(success=True, data=result)

        except AppException as e:
            # [ ] 8. Handle expected exceptions
            logger.warning(f"Expected error: {e.error_code}")
            return ServiceResult(success=False, error=str(e))

        except Exception as e:
            # [ ] 9. Log unexpected errors
            logger.error(f"Unexpected error in {self.__class__.__name__}", exc_info=True)
            raise  # Re-raise to middleware
```

---

## SECTION 7: TESTING ERROR HANDLING

### Test Template for Error Cases

```python
# backend/tests/test_error_handling.py

import pytest
from app.core.exceptions import (
    AppException,
    ValidationError,
    NotFoundError,
    ACGMEComplianceError,
)

class TestAssignmentServiceErrors:
    """Test error handling in AssignmentService."""

    def test_create_assignment_duplicate(self, assignment_service):
        """Test: Duplicate assignment returns error."""
        with pytest.raises(ConflictError) as exc_info:
            assignment_service.create_assignment(
                block_id=existing_block_id,
                person_id=assigned_person_id,
            )

        assert exc_info.value.error_code == "CONFLICT"
        assert exc_info.value.status_code == 409

    def test_create_assignment_missing_block(self, assignment_service):
        """Test: Missing block raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            assignment_service.create_assignment(
                block_id=nonexistent_block_id,
                person_id=valid_person_id,
            )

        assert exc_info.value.status_code == 404

    def test_create_assignment_acgme_violation(self, assignment_service):
        """Test: ACGME violation raises ACGMEComplianceError."""
        with pytest.raises(ACGMEComplianceError) as exc_info:
            assignment_service.create_assignment(
                block_id=block_exceeding_80_hours,
                person_id=resident_id,
            )

        assert "80_hour_rule" in exc_info.value.details["violation_type"]

    def test_error_response_format(self, client):
        """Test: Error response follows RFC 7807."""
        response = client.post(
            "/api/v1/assignments",
            json={"block_id": "invalid", "person_id": "invalid"},
        )

        assert response.status_code == 422
        body = response.json()

        # [ ] RFC 7807 fields present
        assert "type" in body
        assert "title" in body
        assert "status" in body
        assert "detail" in body

        # [ ] Custom fields present
        assert "error_code" in body
        assert "error_id" in body
        assert "timestamp" in body
        assert "request_id" in body
```

---

## SECTION 8: PII/SENSITIVE DATA PROTECTION

### Sensitive Fields That Must Be Redacted

```python
# backend/app/core/logging/sanitizers.py

SENSITIVE_FIELDS = {
    # Authentication
    "password", "passwd", "pwd",
    "token", "access_token", "refresh_token",
    "api_key", "apikey", "api_secret",
    "secret", "credentials",

    # Medical Records (PII)
    "ssn", "social_security_number",
    "passport", "driver_license",
    "phone", "phone_number", "mobile",

    # Financial
    "credit_card", "card_number", "cvv", "cvn",
    "routing_number", "account_number",

    # Personal
    "email", "address", "zip_code", "date_of_birth",
}

def sanitize_error_message(message: str) -> str:
    """Remove sensitive data from error messages."""
    for pattern, replacement in SANITIZATION_PATTERNS:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    return message

# Usage in exception handler
def _handle_app_exception(self, request, exc):
    # Sanitize error detail before sending to client
    sanitized_detail = sanitize_error_message(exc.user_message)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": sanitized_detail},
    )
```

---

## SECTION 9: MIGRATION GUIDE

### Step 1: Add New Exception Base

```python
# Add to backend/app/core/exceptions.py
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')

@dataclass
class ServiceResult(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    warnings: Optional[list[str]] = None
```

### Step 2: Update Service Layer (Gradual)

Priority order:
1. `AssignmentService` → Use Result type
2. `SwapExecutor` → Use Result type
3. `ACGMEValidator` → Use exceptions
4. Remaining services → Adopt pattern incrementally

### Step 3: Update Controllers

```python
# Before
result = service.create_assignment(...)
if result["error"]:
    raise HTTPException(...)
return result

# After
result = service.create_assignment(...)
if not result.success:
    raise HTTPException(status_code=409, detail=result.error)
return result.data
```

---

## SECTION 10: SUMMARY CHECKLIST

**For New Exception Classes:**
- [ ] Inherit from `AppException`
- [ ] Define `error_code` constant
- [ ] Provide `user_message` (safe for client)
- [ ] Include domain-specific `details`
- [ ] Add type hints for all fields
- [ ] Document with docstring
- [ ] Add to `ERROR_CODE_DESCRIPTIONS`
- [ ] Add unit tests for exception

**For Service Methods:**
- [ ] Validate inputs
- [ ] Check prerequisites
- [ ] Check business rules
- [ ] Check compliance rules
- [ ] Execute operation
- [ ] Return typed result
- [ ] Handle expected exceptions
- [ ] Log unexpected errors
- [ ] Write error test cases

**For API Endpoints:**
- [ ] Specify response_model
- [ ] Specify status_code
- [ ] Handle HTTPException
- [ ] Document error cases
- [ ] Test error responses
- [ ] Verify error format (RFC 7807)

---

*Generated by SESSION 8 BURN - Backend Improvements*
*Reference: SESSION_1_BACKEND/backend-error-handling.md*
