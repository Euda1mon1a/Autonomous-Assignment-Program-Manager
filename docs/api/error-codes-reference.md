***REMOVED*** Error Codes Reference

> **Last Updated:** 2025-12-31
> **Purpose:** Complete reference of all error codes in the Residency Scheduler API

---

***REMOVED******REMOVED*** Overview

This document provides a comprehensive reference of all error codes used in the Residency Scheduler application. Each error code is associated with a specific HTTP status code and provides structured information about the error.

All error responses follow the [RFC 7807 Problem Details](https://tools.ietf.org/html/rfc7807) specification.

---

***REMOVED******REMOVED*** Error Response Format

```json
{
  "type": "https://api.residency-scheduler.example.com/errors/{error-code}",
  "title": "Human-readable error title",
  "status": 400,
  "detail": "Specific error details",
  "instance": "/api/v1/resource",
  "error_code": "ERROR_CODE",
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-31T10:30:00Z"
}
```

---

***REMOVED******REMOVED*** Error Code Categories

- [Resource Errors](***REMOVED***resource-errors)
- [Validation Errors](***REMOVED***validation-errors)
- [Date Validation Errors](***REMOVED***date-validation-errors)
- [Concurrency Errors](***REMOVED***concurrency-errors)
- [Authorization Errors](***REMOVED***authorization-errors)
- [Business Logic Errors](***REMOVED***business-logic-errors)
- [Scheduling Errors](***REMOVED***scheduling-errors)
- [ACGME Compliance Errors](***REMOVED***acgme-compliance-errors)
- [Database Errors](***REMOVED***database-errors)
- [External Service Errors](***REMOVED***external-service-errors)
- [Rate Limiting Errors](***REMOVED***rate-limiting-errors)
- [Generic Errors](***REMOVED***generic-errors)

---

***REMOVED******REMOVED*** Resource Errors

***REMOVED******REMOVED******REMOVED*** NOT_FOUND

- **HTTP Status:** 404
- **Description:** The requested resource was not found
- **User Message:** "The requested resource was not found."
- **Typical Causes:**
  - Invalid ID in URL path
  - Resource was deleted
  - User doesn't have access to the resource

**Example:**
```json
{
  "type": "https://api.residency-scheduler.example.com/errors/not-found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Person with ID 'PER-123' not found",
  "instance": "/api/v1/persons/PER-123",
  "error_code": "NOT_FOUND"
}
```

***REMOVED******REMOVED******REMOVED*** ALREADY_EXISTS

- **HTTP Status:** 409
- **Description:** A resource with this information already exists
- **User Message:** "A resource with this information already exists."
- **Typical Causes:**
  - Duplicate email address
  - Duplicate username
  - Attempting to create a resource that already exists

***REMOVED******REMOVED******REMOVED*** RECORD_NOT_FOUND

- **HTTP Status:** 404
- **Description:** The requested database record was not found
- **User Message:** "The requested database record was not found."
- **Typical Causes:**
  - Invalid database ID
  - Record was deleted
  - Data inconsistency

***REMOVED******REMOVED******REMOVED*** DUPLICATE_RECORD

- **HTTP Status:** 409
- **Description:** A record with this information already exists
- **User Message:** "A record with this information already exists."
- **Typical Causes:**
  - Unique constraint violation
  - Attempting to insert duplicate data

---

***REMOVED******REMOVED*** Validation Errors

***REMOVED******REMOVED******REMOVED*** VALIDATION_ERROR

- **HTTP Status:** 422
- **Description:** The provided data failed validation
- **User Message:** "Please check your input and try again."
- **Additional Fields:** May include `errors` array with field-specific errors

***REMOVED******REMOVED******REMOVED*** INPUT_VALIDATION_ERROR

- **HTTP Status:** 422
- **Description:** The input data is invalid
- **User Message:** "The input data is invalid."

***REMOVED******REMOVED******REMOVED*** SCHEMA_VALIDATION_ERROR

- **HTTP Status:** 422
- **Description:** The data does not match the required schema
- **User Message:** "The data does not match the required format."
- **Additional Fields:** `errors` array with validation errors

***REMOVED******REMOVED******REMOVED*** REQUIRED_FIELD

- **HTTP Status:** 422
- **Description:** A required field is missing
- **User Message:** "A required field is missing."

***REMOVED******REMOVED******REMOVED*** INVALID_FORMAT

- **HTTP Status:** 422
- **Description:** The data format is invalid
- **User Message:** "The data format is invalid."

***REMOVED******REMOVED******REMOVED*** VALUE_OUT_OF_RANGE

- **HTTP Status:** 422
- **Description:** The value is outside the allowed range
- **User Message:** "The value is outside the allowed range."

---

***REMOVED******REMOVED*** Date Validation Errors

***REMOVED******REMOVED******REMOVED*** DATE_VALIDATION_ERROR

- **HTTP Status:** 422
- **Description:** The provided date is invalid
- **User Message:** "The provided date is invalid."

***REMOVED******REMOVED******REMOVED*** DATE_OUT_OF_RANGE

- **HTTP Status:** 422
- **Description:** The date is outside the allowed range
- **User Message:** "The date is outside the allowed range."

***REMOVED******REMOVED******REMOVED*** FUTURE_DATE_NOT_ALLOWED

- **HTTP Status:** 422
- **Description:** Future dates are not allowed for this field
- **User Message:** "Future dates are not allowed for this field."

***REMOVED******REMOVED******REMOVED*** PAST_DATE_NOT_ALLOWED

- **HTTP Status:** 422
- **Description:** Past dates are not allowed for this field
- **User Message:** "Past dates are not allowed for this field."

---

***REMOVED******REMOVED*** Concurrency Errors

***REMOVED******REMOVED******REMOVED*** CONFLICT

- **HTTP Status:** 409
- **Description:** The request conflicts with existing data
- **User Message:** "The request conflicts with existing data."

***REMOVED******REMOVED******REMOVED*** CONCURRENT_MODIFICATION

- **HTTP Status:** 409
- **Description:** The record was modified by another user
- **User Message:** "This record was modified by another user. Please refresh and try again."
- **Resolution:** Refresh the data and retry the operation

---

***REMOVED******REMOVED*** Authorization Errors

***REMOVED******REMOVED******REMOVED*** UNAUTHORIZED

- **HTTP Status:** 401
- **Description:** Authentication is required
- **User Message:** "Your session has expired. Please log in again."
- **Resolution:** Redirect user to login page

***REMOVED******REMOVED******REMOVED*** FORBIDDEN

- **HTTP Status:** 403
- **Description:** You do not have permission for this action
- **User Message:** "You do not have permission to perform this action."

***REMOVED******REMOVED******REMOVED*** INVALID_CREDENTIALS

- **HTTP Status:** 401
- **Description:** The provided credentials are invalid
- **User Message:** "Invalid email or password."

***REMOVED******REMOVED******REMOVED*** TOKEN_EXPIRED

- **HTTP Status:** 401
- **Description:** Your authentication token has expired
- **User Message:** "Your session has expired. Please log in again."
- **Resolution:** Redirect user to login page

***REMOVED******REMOVED******REMOVED*** INVALID_TOKEN

- **HTTP Status:** 401
- **Description:** The authentication token is invalid
- **User Message:** "Your session is invalid. Please log in again."
- **Resolution:** Redirect user to login page

***REMOVED******REMOVED******REMOVED*** TOKEN_REVOKED

- **HTTP Status:** 401
- **Description:** The authentication token has been revoked
- **User Message:** "Your session has been revoked. Please log in again."
- **Resolution:** Redirect user to login page

***REMOVED******REMOVED******REMOVED*** PERMISSION_DENIED

- **HTTP Status:** 403
- **Description:** You do not have permission for this action
- **User Message:** "You do not have permission to perform this action."

***REMOVED******REMOVED******REMOVED*** INSUFFICIENT_ROLE

- **HTTP Status:** 403
- **Description:** Your role does not allow this action
- **User Message:** "Your role does not allow this action."

***REMOVED******REMOVED******REMOVED*** ACCOUNT_DISABLED

- **HTTP Status:** 401
- **Description:** This account has been disabled
- **User Message:** "This account has been disabled. Please contact support."

***REMOVED******REMOVED******REMOVED*** MFA_REQUIRED

- **HTTP Status:** 401
- **Description:** Multi-factor authentication is required
- **User Message:** "Multi-factor authentication is required."

***REMOVED******REMOVED******REMOVED*** MFA_INVALID

- **HTTP Status:** 401
- **Description:** The multi-factor authentication code is invalid
- **User Message:** "The multi-factor authentication code is invalid."

---

***REMOVED******REMOVED*** Business Logic Errors

***REMOVED******REMOVED******REMOVED*** BUSINESS_RULE_VIOLATION

- **HTTP Status:** 422
- **Description:** A business rule was violated
- **User Message:** "A business rule was violated."

***REMOVED******REMOVED******REMOVED*** CONSTRAINT_VIOLATION

- **HTTP Status:** 422
- **Description:** A constraint was violated
- **User Message:** "A constraint was violated."

***REMOVED******REMOVED******REMOVED*** INVALID_STATE_TRANSITION

- **HTTP Status:** 422
- **Description:** The requested state transition is not allowed
- **User Message:** "The requested state transition is not allowed."

---

***REMOVED******REMOVED*** Scheduling Errors

***REMOVED******REMOVED******REMOVED*** SCHEDULING_ERROR

- **HTTP Status:** 400
- **Description:** A scheduling error occurred
- **User Message:** "A scheduling error occurred. Please try again."

***REMOVED******REMOVED******REMOVED*** SCHEDULE_CONFLICT

- **HTTP Status:** 409
- **Description:** The assignment conflicts with existing schedules
- **User Message:** "The assignment conflicts with existing schedules. Please choose a different time."
- **Additional Fields:** `conflict` object with conflict details

**Example:**
```json
{
  "error_code": "SCHEDULE_CONFLICT",
  "status": 409,
  "detail": "Assignment conflicts with existing schedule",
  "conflict": {
    "conflicting_assignment_id": "ASGN-123",
    "requested_date": "2025-12-31",
    "person_id": "PER-456",
    "conflict_type": "time"
  }
}
```

***REMOVED******REMOVED******REMOVED*** SCHEDULE_GENERATION_FAILED

- **HTTP Status:** 422
- **Description:** Schedule generation failed
- **User Message:** "Schedule generation failed. Please adjust your requirements and try again."

***REMOVED******REMOVED******REMOVED*** SOLVER_TIMEOUT

- **HTTP Status:** 504
- **Description:** Schedule solver timed out
- **User Message:** "Schedule generation is taking longer than expected. Please simplify your requirements or try again later."

***REMOVED******REMOVED******REMOVED*** CONSTRAINT_VIOLATION_SCHEDULING

- **HTTP Status:** 422
- **Description:** A scheduling constraint was violated
- **User Message:** "A scheduling constraint was violated."

***REMOVED******REMOVED******REMOVED*** INFEASIBLE_SCHEDULE

- **HTTP Status:** 422
- **Description:** The schedule requirements cannot be satisfied
- **User Message:** "The schedule requirements cannot be satisfied. Please adjust your constraints."

***REMOVED******REMOVED******REMOVED*** ROTATION_TEMPLATE_ERROR

- **HTTP Status:** 400
- **Description:** The rotation template is invalid
- **User Message:** "The rotation template is invalid."

***REMOVED******REMOVED******REMOVED*** BLOCK_ASSIGNMENT_ERROR

- **HTTP Status:** 400
- **Description:** The block assignment is invalid
- **User Message:** "The block assignment is invalid."

---

***REMOVED******REMOVED*** ACGME Compliance Errors

***REMOVED******REMOVED******REMOVED*** ACGME_COMPLIANCE_ERROR

- **HTTP Status:** 422
- **Description:** ACGME compliance requirements were violated
- **User Message:** "ACGME compliance requirements were violated. Please review the details."

***REMOVED******REMOVED******REMOVED*** WORK_HOUR_VIOLATION

- **HTTP Status:** 422
- **Description:** The 80-hour work week limit was violated
- **User Message:** "This assignment would violate the 80-hour work week limit."
- **Additional Fields:** `violation` object with details

**Example:**
```json
{
  "error_code": "WORK_HOUR_VIOLATION",
  "status": 422,
  "detail": "Assignment would violate the 80-hour work week limit",
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

***REMOVED******REMOVED******REMOVED*** REST_REQUIREMENT_VIOLATION

- **HTTP Status:** 422
- **Description:** The 1-in-7 rest day requirement was violated
- **User Message:** "This assignment would violate the 1-in-7 rest day requirement."

***REMOVED******REMOVED******REMOVED*** SUPERVISION_VIOLATION

- **HTTP Status:** 422
- **Description:** Supervision ratio requirements were violated
- **User Message:** "This assignment would violate supervision ratio requirements."

***REMOVED******REMOVED******REMOVED*** SHIFT_LENGTH_VIOLATION

- **HTTP Status:** 422
- **Description:** Maximum shift length was exceeded
- **User Message:** "This assignment would exceed the maximum shift length."

***REMOVED******REMOVED******REMOVED*** CALL_FREQUENCY_VIOLATION

- **HTTP Status:** 422
- **Description:** Call frequency limit was exceeded
- **User Message:** "This assignment would violate call frequency limits."

---

***REMOVED******REMOVED*** Database Errors

***REMOVED******REMOVED******REMOVED*** DATABASE_ERROR

- **HTTP Status:** 500
- **Description:** A database error occurred
- **User Message:** "A database error occurred. Please try again later or contact support."

***REMOVED******REMOVED******REMOVED*** DATABASE_CONNECTION_ERROR

- **HTTP Status:** 503
- **Description:** Unable to connect to the database
- **User Message:** "Unable to connect to the database. Please check your connection and try again."

***REMOVED******REMOVED******REMOVED*** DATABASE_TIMEOUT

- **HTTP Status:** 504
- **Description:** Database operation timed out
- **User Message:** "The database operation timed out. Please try again."

***REMOVED******REMOVED******REMOVED*** INTEGRITY_CONSTRAINT_ERROR

- **HTTP Status:** 409
- **Description:** A database constraint was violated
- **User Message:** "A database constraint was violated. Please check your data."

***REMOVED******REMOVED******REMOVED*** FOREIGN_KEY_VIOLATION

- **HTTP Status:** 409
- **Description:** The referenced record does not exist
- **User Message:** "The referenced record does not exist."

***REMOVED******REMOVED******REMOVED*** TRANSACTION_ERROR

- **HTTP Status:** 500
- **Description:** Database transaction failed
- **User Message:** "The database transaction failed. Please try again."

---

***REMOVED******REMOVED*** External Service Errors

***REMOVED******REMOVED******REMOVED*** EXTERNAL_SERVICE_ERROR

- **HTTP Status:** 502
- **Description:** An external service error occurred
- **User Message:** "An external service error occurred. Please try again later."

***REMOVED******REMOVED******REMOVED*** SERVICE_UNAVAILABLE

- **HTTP Status:** 503
- **Description:** The service is temporarily unavailable
- **User Message:** "The service is temporarily unavailable. Please try again later."

***REMOVED******REMOVED******REMOVED*** SERVICE_TIMEOUT

- **HTTP Status:** 504
- **Description:** The service request timed out
- **User Message:** "The service request timed out. Please try again."

***REMOVED******REMOVED******REMOVED*** EXTERNAL_API_ERROR

- **HTTP Status:** 502
- **Description:** An error occurred while communicating with an external service
- **User Message:** "An error occurred while communicating with an external service."

***REMOVED******REMOVED******REMOVED*** EMAIL_SERVICE_ERROR

- **HTTP Status:** 502
- **Description:** Failed to send email
- **User Message:** "Failed to send email. Please try again or contact support."

***REMOVED******REMOVED******REMOVED*** SMS_SERVICE_ERROR

- **HTTP Status:** 502
- **Description:** Failed to send SMS
- **User Message:** "Failed to send SMS. Please try again or contact support."

***REMOVED******REMOVED******REMOVED*** NOTIFICATION_SERVICE_ERROR

- **HTTP Status:** 502
- **Description:** Failed to send notification
- **User Message:** "Failed to send notification. Please try again or contact support."

---

***REMOVED******REMOVED*** Rate Limiting Errors

***REMOVED******REMOVED******REMOVED*** RATE_LIMIT_EXCEEDED

- **HTTP Status:** 429
- **Description:** Rate limit exceeded
- **User Message:** "You have made too many requests. Please wait a moment and try again."
- **Additional Fields:** `retry_after` (seconds until rate limit resets)
- **Headers:** `Retry-After` header with retry delay

**Example:**
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "status": 429,
  "detail": "Rate limit exceeded. Please try again later.",
  "limit": 100,
  "window_seconds": 60,
  "retry_after": 45
}
```

***REMOVED******REMOVED******REMOVED*** QUOTA_EXCEEDED

- **HTTP Status:** 429
- **Description:** Usage quota exceeded
- **User Message:** "Your usage quota has been exceeded. Please upgrade your plan or wait for the quota to reset."

***REMOVED******REMOVED******REMOVED*** CONCURRENCY_LIMIT_EXCEEDED

- **HTTP Status:** 429
- **Description:** Too many concurrent operations
- **User Message:** "Too many concurrent operations. Please wait and try again."

---

***REMOVED******REMOVED*** Generic Errors

***REMOVED******REMOVED******REMOVED*** INTERNAL_ERROR

- **HTTP Status:** 500
- **Description:** An internal server error occurred
- **User Message:** "An internal server error occurred. Please try again later or contact support."

---

***REMOVED******REMOVED*** HTTP Status Code Summary

| Status Code | Category | Error Codes |
|-------------|----------|-------------|
| 400 | Bad Request | SCHEDULING_ERROR, ROTATION_TEMPLATE_ERROR, BLOCK_ASSIGNMENT_ERROR |
| 401 | Unauthorized | UNAUTHORIZED, INVALID_CREDENTIALS, TOKEN_EXPIRED, INVALID_TOKEN, TOKEN_REVOKED, ACCOUNT_DISABLED, MFA_REQUIRED, MFA_INVALID |
| 403 | Forbidden | FORBIDDEN, PERMISSION_DENIED, INSUFFICIENT_ROLE |
| 404 | Not Found | NOT_FOUND, RECORD_NOT_FOUND |
| 409 | Conflict | ALREADY_EXISTS, DUPLICATE_RECORD, CONFLICT, CONCURRENT_MODIFICATION, SCHEDULE_CONFLICT, INTEGRITY_CONSTRAINT_ERROR, FOREIGN_KEY_VIOLATION |
| 422 | Unprocessable Entity | All validation errors, ACGME compliance errors, scheduling errors |
| 429 | Too Many Requests | RATE_LIMIT_EXCEEDED, QUOTA_EXCEEDED, CONCURRENCY_LIMIT_EXCEEDED |
| 500 | Internal Server Error | DATABASE_ERROR, TRANSACTION_ERROR, INTERNAL_ERROR |
| 502 | Bad Gateway | EXTERNAL_SERVICE_ERROR, EXTERNAL_API_ERROR, EMAIL_SERVICE_ERROR, SMS_SERVICE_ERROR, NOTIFICATION_SERVICE_ERROR |
| 503 | Service Unavailable | SERVICE_UNAVAILABLE, DATABASE_CONNECTION_ERROR |
| 504 | Gateway Timeout | SERVICE_TIMEOUT, DATABASE_TIMEOUT, SOLVER_TIMEOUT |

---

***REMOVED******REMOVED*** Related Documentation

- [Error Handling Guide](./error-handling-guide.md) - Developer guide for implementing error handling
- [API Reference](./api-reference.md) - Complete API documentation
- [ACGME Compliance](../architecture/acgme-compliance.md) - ACGME compliance rules

---

*This reference is automatically generated from the error code enumeration. Last updated: 2025-12-31*
