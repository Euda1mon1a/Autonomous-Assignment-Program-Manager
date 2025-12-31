# Error Handling Guide

> **Last Updated:** 2025-12-31
> **Purpose:** Developer guide for error handling in the Residency Scheduler application

---

## Table of Contents

1. [Overview](#overview)
2. [Backend Error Handling](#backend-error-handling)
3. [Frontend Error Handling](#frontend-error-handling)
4. [Best Practices](#best-practices)
5. [Common Patterns](#common-patterns)
6. [Testing Error Handling](#testing-error-handling)

---

## Overview

The Residency Scheduler uses a comprehensive error handling system based on **RFC 7807 Problem Details for HTTP APIs**. This provides consistent, machine-readable error responses while protecting sensitive information.

### Key Features

- **Domain-specific exceptions**: Organized by domain (scheduling, compliance, auth, etc.)
- **Structured error codes**: Machine-readable codes for all error types
- **RFC 7807 compliant**: Standardized error response format
- **Type-safe**: Full TypeScript support on the frontend
- **User-friendly**: Clear error messages without exposing internals
- **Comprehensive logging**: Error tracking and reporting

---

## Backend Error Handling

### Exception Hierarchy

All application exceptions inherit from `AppException`:

```python
from app.exceptions import (
    # Base exceptions
    AppException,
    NotFoundError,
    ValidationError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,

    # Domain-specific exceptions
    SchedulingError,
    ScheduleConflictError,
    ACGMEComplianceError,
    WorkHourViolationError,
    # ... and many more
)
```

### Using Exceptions

#### Basic Usage

```python
from app.exceptions import NotFoundError, ValidationError

# Raise a not found error
if not person:
    raise NotFoundError(
        message="Person not found",
        # Optional context for logging
        person_id=person_id,
    )

# Raise a validation error
if age < 0:
    raise ValidationError(
        message="Age must be positive",
        field="age",
        value=age,
    )
```

#### Domain-Specific Exceptions

```python
from app.exceptions import ScheduleConflictError, WorkHourViolationError

# Schedule conflict
if has_conflict(assignment):
    raise ScheduleConflictError(
        message="Assignment conflicts with existing schedule",
        conflicting_assignment_id=existing.id,
        requested_date=assignment.date,
        person_id=assignment.person_id,
    )

# ACGME compliance violation
if total_hours > 80:
    raise WorkHourViolationError(
        resident_id=resident.id,
        period_start=week_start,
        period_end=week_end,
        actual_hours=total_hours,
        limit_hours=80.0,
    )
```

### Error Response Format

All errors are automatically formatted according to RFC 7807:

```json
{
  "type": "https://api.residency-scheduler.example.com/errors/work-hour-violation",
  "title": "ACGME Work Hour Violation",
  "status": 422,
  "detail": "Assignment would violate the 80-hour work week limit",
  "instance": "/api/v1/assignments",
  "error_code": "WORK_HOUR_VIOLATION",
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-31T10:30:00Z",
  "violation": {
    "resident_id": "RES-001",
    "period_start": "2025-12-01",
    "period_end": "2025-12-28",
    "actual_hours": 84.5,
    "limit_hours": 80.0,
    "rule_violated": "80-hour work week (averaged over 4 weeks)"
  }
}
```

### Creating Custom Exceptions

```python
# In app/exceptions/your_domain.py
from typing import Any
from app.core.exceptions import AppException

class YourDomainError(AppException):
    """Base exception for your domain."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        **context: Any,
    ):
        super().__init__(message, status_code)
        self.context = context


class SpecificError(YourDomainError):
    """Specific error in your domain."""

    def __init__(
        self,
        message: str = "Default error message",
        custom_field: str | None = None,
        **context: Any,
    ):
        super().__init__(message, status_code=422, **context)
        self.custom_field = custom_field
```

### Error Handling in Routes

```python
from fastapi import APIRouter, Depends
from app.exceptions import NotFoundError, ScheduleConflictError

router = APIRouter()

@router.post("/assignments")
async def create_assignment(
    assignment_data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new assignment.

    The error handling middleware will automatically catch and format
    any exceptions raised by this endpoint.
    """
    # Check if person exists
    person = await get_person(db, assignment_data.person_id)
    if not person:
        raise NotFoundError(
            message=f"Person {assignment_data.person_id} not found",
        )

    # Check for conflicts
    if has_conflict:
        raise ScheduleConflictError(
            message="Assignment conflicts with existing schedule",
            conflicting_assignment_id=existing.id,
            requested_date=assignment_data.date,
            person_id=assignment_data.person_id,
        )

    # Create assignment
    return await create_assignment_service(db, assignment_data)
```

---

## Frontend Error Handling

### TypeScript Types

All backend error responses have corresponding TypeScript types:

```typescript
import {
  ErrorCode,
  ErrorResponse,
  ValidationErrorResponse,
  ACGMEComplianceErrorResponse,
  isRFC7807Error,
  isValidationError,
} from '@/lib/errors'
```

### Error Boundary

Wrap your app with `ErrorBoundary` to catch React errors:

```tsx
import { ErrorBoundary } from '@/lib/errors'

function App() {
  return (
    <ErrorBoundary
      fallback={(error, errorInfo) => (
        <div>
          <h1>Something went wrong</h1>
          <p>{error.message}</p>
        </div>
      )}
      onError={(error, errorInfo) => {
        // Custom error handling
        console.error('Caught by error boundary:', error, errorInfo)
      }}
    >
      <YourApp />
    </ErrorBoundary>
  )
}
```

### Error Toast Notifications

```tsx
import { ErrorToastContainer, showErrorToast } from '@/lib/errors'

// In your app root
function App() {
  return (
    <>
      <ErrorToastContainer position="top-right" />
      <YourApp />
    </>
  )
}

// In a component
async function handleSubmit() {
  try {
    await createAssignment(data)
  } catch (error) {
    showErrorToast(error)
  }
}
```

### Error Handler Hook

```tsx
import { useErrorHandler } from '@/lib/errors'

function MyComponent() {
  const {
    handleError,
    getUserMessage,
    shouldReauthenticate,
    isRetryable,
    getValidationErrors,
  } = useErrorHandler()

  async function doSomething() {
    try {
      await apiCall()
    } catch (error) {
      // Handle the error
      handleError(error, { component: 'MyComponent' })

      // Get user-friendly message
      const message = getUserMessage(error)
      alert(message)

      // Check if we should redirect to login
      if (shouldReauthenticate(error)) {
        router.push('/login')
      }

      // Check if we should retry
      if (isRetryable(error)) {
        setTimeout(() => doSomething(), 1000)
      }

      // Get validation errors for form fields
      const validationErrors = getValidationErrors(error)
      setFieldErrors(validationErrors)
    }
  }
}
```

### Handling Specific Error Types

```tsx
import {
  isValidationError,
  isACGMEComplianceError,
  isScheduleConflictError,
  isRateLimitError,
} from '@/lib/errors'

async function handleSubmit() {
  try {
    await createAssignment(data)
  } catch (error) {
    // Handle validation errors
    if (isValidationError(error)) {
      error.errors.forEach((err) => {
        setFieldError(err.field, err.message)
      })
      return
    }

    // Handle ACGME compliance errors
    if (isACGMEComplianceError(error)) {
      showACGMEViolationDialog(error.violation)
      return
    }

    // Handle schedule conflicts
    if (isScheduleConflictError(error)) {
      showConflictResolutionDialog(error.conflict)
      return
    }

    // Handle rate limits
    if (isRateLimitError(error)) {
      const retryAfter = error.retry_after
      showMessage(`Please wait ${retryAfter} seconds and try again`)
      return
    }

    // Generic error handling
    showErrorToast(error)
  }
}
```

---

## Best Practices

### 1. Use Domain-Specific Exceptions

```python
# ❌ Bad - using generic exceptions
raise ValueError("Schedule conflict")

# ✅ Good - using domain-specific exception
raise ScheduleConflictError(
    message="Assignment conflicts with existing schedule",
    conflicting_assignment_id=existing.id,
)
```

### 2. Provide Context

```python
# ❌ Bad - no context
raise NotFoundError("Person not found")

# ✅ Good - with context for debugging
raise NotFoundError(
    message=f"Person not found: {person_id}",
    person_id=person_id,
    requested_at=datetime.now().isoformat(),
)
```

### 3. Don't Leak Sensitive Information

```python
# ❌ Bad - leaking database details
raise DatabaseError(f"Query failed: {sql_query}")

# ✅ Good - safe error message
raise DatabaseError(
    message="Database operation failed",
    operation="SELECT",
    table="persons",
)
```

### 4. Use Type Guards on Frontend

```typescript
// ❌ Bad - unsafe access
const errorCode = (error as any).error_code

// ✅ Good - type-safe access
if (isRFC7807Error(error)) {
  const errorCode = error.error_code
}
```

### 5. Handle Errors at the Right Level

```python
# ❌ Bad - catching and re-raising without adding value
try:
    do_something()
except Exception as e:
    raise e

# ✅ Good - add context or handle
try:
    do_something()
except DatabaseError as e:
    # Add context
    raise DatabaseError(
        message="Failed to create assignment",
        original_error=str(e),
    ) from e
```

---

## Common Patterns

### Pattern 1: Validation Errors with Field Details

```python
from app.exceptions import InputValidationError

def validate_assignment(assignment_data):
    errors = []

    if not assignment_data.person_id:
        errors.append({"field": "person_id", "message": "Person ID is required"})

    if not assignment_data.date:
        errors.append({"field": "date", "message": "Date is required"})

    if errors:
        # Create validation error with field details
        raise InputValidationError(
            message="Assignment validation failed",
            errors=errors,
        )
```

### Pattern 2: Retrying on Specific Errors

```typescript
async function retryOnTimeout<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  let lastError: unknown

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error

      if (isRFC7807Error(error)) {
        // Retry on timeout errors
        if (
          error.error_code === ErrorCode.SERVICE_TIMEOUT ||
          error.error_code === ErrorCode.DATABASE_TIMEOUT
        ) {
          await delay(Math.pow(2, i) * 1000) // Exponential backoff
          continue
        }
      }

      // Not retryable, rethrow
      throw error
    }
  }

  throw lastError
}
```

### Pattern 3: Error Recovery

```typescript
import { useErrorHandler } from '@/lib/errors'

function useDataWithRecovery<T>(fetchFn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<unknown>(null)
  const { shouldReauthenticate, isRetryable } = useErrorHandler()

  const fetch = useCallback(async () => {
    try {
      const result = await fetchFn()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err)

      // Redirect to login if auth error
      if (shouldReauthenticate(err)) {
        router.push('/login')
        return
      }

      // Retry if retryable
      if (isRetryable(err)) {
        setTimeout(() => fetch(), 5000)
        return
      }

      // Otherwise, show error
      showErrorToast(err)
    }
  }, [fetchFn, shouldReauthenticate, isRetryable])

  return { data, error, refetch: fetch }
}
```

---

## Testing Error Handling

### Backend Tests

```python
import pytest
from app.exceptions import ScheduleConflictError, WorkHourViolationError

async def test_schedule_conflict_error(db):
    """Test that schedule conflicts raise appropriate error."""
    # Create conflicting assignments
    assignment1 = await create_assignment(db, person_id="P1", date="2025-12-31")

    # Attempt to create conflicting assignment
    with pytest.raises(ScheduleConflictError) as exc_info:
        await create_assignment(db, person_id="P1", date="2025-12-31")

    # Verify error details
    error = exc_info.value
    assert error.message == "Assignment conflicts with existing schedule"
    assert error.conflicting_assignment_id == assignment1.id
    assert error.status_code == 409


async def test_acgme_violation_error(db):
    """Test that ACGME violations raise appropriate error."""
    # Create assignments that violate 80-hour rule
    resident = await create_resident(db)

    # Add 80 hours of assignments
    await add_assignments(db, resident.id, hours=80)

    # Attempt to add more hours
    with pytest.raises(WorkHourViolationError) as exc_info:
        await add_assignment(db, resident.id, hours=5)

    # Verify error details
    error = exc_info.value
    assert error.actual_hours == 85
    assert error.limit_hours == 80
    assert error.resident_id == resident.id
```

### Frontend Tests

```typescript
import { render, screen } from '@testing-library/react'
import { ErrorBoundary, ErrorToast, isValidationError } from '@/lib/errors'

describe('Error Handling', () => {
  test('ErrorBoundary catches and displays errors', () => {
    const ThrowError = () => {
      throw new Error('Test error')
    }

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText(/Test error/i)).toBeInTheDocument()
  })

  test('ErrorToast displays error message', () => {
    const error = {
      type: 'https://api.example.com/errors/validation-error',
      title: 'Validation Failed',
      status: 422,
      detail: 'Invalid input',
      error_code: 'VALIDATION_ERROR',
      // ...other fields
    }

    render(<ErrorToast error={error} onClose={() => {}} />)

    expect(screen.getByText('Validation Failed')).toBeInTheDocument()
    expect(screen.getByText('Invalid input')).toBeInTheDocument()
  })

  test('Type guards work correctly', () => {
    const validationError = {
      // RFC 7807 fields
      error_code: 'VALIDATION_ERROR',
      errors: [{ field: 'email', message: 'Invalid email' }],
      // ...other fields
    }

    expect(isValidationError(validationError)).toBe(true)
  })
})
```

---

## Error Code Reference

See [Error Codes Reference](./error-codes-reference.md) for a complete list of all error codes and their meanings.

---

## Troubleshooting

### Q: Error responses don't include stack traces in development

**A:** Make sure `DEBUG=True` in backend settings. Stack traces are only included when `DEBUG=True`.

### Q: Error toasts aren't showing up

**A:** Ensure `<ErrorToastContainer />` is rendered in your app root.

### Q: Type guards aren't working

**A:** Make sure you're importing from `@/lib/errors`, not constructing error objects manually.

### Q: Custom exceptions aren't being caught by error handler

**A:** Verify that custom exceptions inherit from `AppException` and are registered in `backend/app/middleware/errors/mappings.py`.

---

## Additional Resources

- [RFC 7807: Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807)
- [Error Codes Reference](./error-codes-reference.md)
- [ACGME Compliance Rules](../architecture/acgme-compliance.md)
- [API Documentation](./api-reference.md)

---

*This guide is maintained by the development team. If you have questions or suggestions, please open an issue.*
