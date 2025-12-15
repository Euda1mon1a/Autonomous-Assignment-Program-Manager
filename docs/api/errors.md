# Error Handling

This document describes the error handling patterns, HTTP status codes, and error response formats used by the Residency Scheduler API.

## HTTP Status Codes

### Success Codes

| Code | Name | Description |
|------|------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content returned (DELETE operations) |
| 207 | Multi-Status | Partial success (schedule generation with warnings) |

### Client Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid input, validation error, or malformed request |
| 401 | Unauthorized | Authentication required or credentials invalid |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Requested resource does not exist |
| 409 | Conflict | Resource conflict (optimistic locking, duplicate entry) |
| 422 | Unprocessable Entity | Request understood but cannot be processed |

### Server Error Codes

| Code | Name | Description |
|------|------|-------------|
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Server temporarily unavailable |

## Error Response Format

All errors return a JSON response with a `detail` field:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Errors

Validation errors may include additional details about which fields failed:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    },
    {
      "loc": ["body", "pgy_level"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Common Error Scenarios

### Authentication Errors (401)

#### Missing Authorization Header

```bash
curl http://localhost:8000/api/auth/me

# Response (401):
{
  "detail": "Not authenticated"
}
```

#### Invalid Token

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer invalid_token"

# Response (401):
{
  "detail": "Could not validate credentials"
}
```

#### Expired Token

```bash
# Response (401):
{
  "detail": "Token has expired"
}
```

#### Invalid Credentials

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "wrong"}'

# Response (401):
{
  "detail": "Incorrect username or password"
}
```

### Authorization Errors (403)

#### Insufficient Permissions

```bash
# Non-admin trying to access admin-only endpoint
curl http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <coordinator_token>"

# Response (403):
{
  "detail": "Not authorized to access this resource"
}
```

### Validation Errors (400)

#### Missing Required Field

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Smith", "type": "resident"}'

# Response (400):
{
  "detail": "PGY level required for residents"
}
```

#### Invalid Field Value

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Smith", "type": "invalid"}'

# Response (400):
{
  "detail": "type must be 'resident' or 'faculty'"
}
```

#### Invalid PGY Level

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Smith", "type": "resident", "pgy_level": 5}'

# Response (400):
{
  "detail": "PGY level must be 1, 2, or 3"
}
```

#### Invalid Email Format

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Smith", "type": "faculty", "email": "not-an-email"}'

# Response (422):
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

#### Invalid Date Range

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-06-30", "end_date": "2024-01-01"}'

# Response (400):
{
  "detail": "start_date must be before or equal to end_date"
}
```

### Resource Not Found (404)

#### Person Not Found

```bash
curl http://localhost:8000/api/people/nonexistent-uuid

# Response (404):
{
  "detail": "Person not found"
}
```

#### Block Not Found

```bash
curl http://localhost:8000/api/blocks/nonexistent-uuid

# Response (404):
{
  "detail": "Block not found"
}
```

#### Assignment Not Found

```bash
curl http://localhost:8000/api/assignments/nonexistent-uuid \
  -H "Authorization: Bearer <token>"

# Response (404):
{
  "detail": "Assignment not found"
}
```

#### Rotation Template Not Found

```bash
curl http://localhost:8000/api/rotation-templates/nonexistent-uuid

# Response (404):
{
  "detail": "Rotation template not found"
}
```

#### Absence Not Found

```bash
curl http://localhost:8000/api/absences/nonexistent-uuid

# Response (404):
{
  "detail": "Absence not found"
}
```

### Conflict Errors (409)

#### Duplicate Assignment

```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "existing-block-id",
    "person_id": "already-assigned-person-id",
    "role": "primary"
  }'

# Response (400):
{
  "detail": "Person already assigned to this block"
}
```

#### Duplicate Block

```bash
curl -X POST http://localhost:8000/api/blocks \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-15", "time_of_day": "AM", "block_number": 1}'

# If block already exists:
# Response (400):
{
  "detail": "Block already exists for this date and time"
}
```

#### Optimistic Locking Violation

```bash
# When trying to update an assignment that was modified by another user
curl -X PUT http://localhost:8000/api/assignments/assignment-id \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "backup",
    "updated_at": "2024-01-01T00:00:00Z"
  }'

# Response (409):
{
  "detail": "Assignment has been modified by another user. Please refresh and try again."
}
```

#### Schedule Generation in Progress

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-01-01", "end_date": "2024-06-30"}'

# If generation already in progress for overlapping dates:
# Response (409):
{
  "detail": "Schedule generation already in progress for overlapping date range"
}
```

### Schedule Generation Errors (422)

#### Generation Failed

```bash
# Response (422):
{
  "detail": "Schedule generation failed: No valid assignments could be created"
}
```

### Partial Success (207)

Schedule generation may return partial success:

```bash
# Response (207 Multi-Status):
{
  "status": "partial",
  "message": "Schedule generated with warnings",
  "total_blocks_assigned": 2800,
  "total_blocks": 3650,
  "validation": {
    "valid": false,
    "total_violations": 3,
    "violations": [
      {
        "type": "80_HOUR_VIOLATION",
        "severity": "CRITICAL",
        "person_id": "uuid",
        "person_name": "Dr. Smith",
        "message": "Dr. Smith: 82.5 hours/week (limit: 80)"
      }
    ],
    "coverage_rate": 76.7
  }
}
```

## ACGME Violation Types

The schedule validation endpoint returns specific violation types:

| Type | Severity | Description |
|------|----------|-------------|
| `80_HOUR_VIOLATION` | CRITICAL | Weekly hours exceed 80-hour limit |
| `1_IN_7_VIOLATION` | HIGH | Missing required day off per 7 days |
| `SUPERVISION_RATIO_VIOLATION` | CRITICAL | Insufficient faculty supervision |
| `CONSECUTIVE_DUTY_VIOLATION` | HIGH | Too many consecutive duty days |

### Violation Response Structure

```json
{
  "type": "80_HOUR_VIOLATION",
  "severity": "CRITICAL",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_name": "Dr. Jane Smith",
  "block_id": null,
  "message": "Dr. Jane Smith: 82.5 hours/week average (limit: 80)",
  "details": {
    "window_start": "2024-01-01",
    "window_end": "2024-01-28",
    "average_weekly_hours": 82.5
  }
}
```

## Error Handling Best Practices

### Client-Side Error Handling

```javascript
async function apiRequest(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.json();

    switch (response.status) {
      case 401:
        // Redirect to login or refresh token
        handleAuthError(error);
        break;
      case 403:
        // Show permission denied message
        showError("You don't have permission to perform this action");
        break;
      case 404:
        // Show not found message
        showError("The requested resource was not found");
        break;
      case 409:
        // Handle conflict (e.g., reload and retry)
        handleConflict(error);
        break;
      case 422:
        // Show validation errors
        showValidationErrors(error.detail);
        break;
      default:
        // Generic error handling
        showError(error.detail || "An unexpected error occurred");
    }

    throw new Error(error.detail);
  }

  return response.json();
}
```

### Retry Logic

For transient errors (5xx), implement retry with exponential backoff:

```python
import time
import requests

def api_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 500:
                wait_time = 2 ** attempt  # 1, 2, 4 seconds
                time.sleep(wait_time)
                continue
            raise
    raise Exception("Max retries exceeded")
```

## Debugging Errors

When encountering unexpected errors:

1. **Check the request format**: Ensure headers and body are correct
2. **Verify authentication**: Confirm token is valid and not expired
3. **Review validation rules**: Check field constraints in the schema
4. **Check for conflicts**: Verify resource state hasn't changed
5. **Review server logs**: Check backend logs for detailed error information

## Error Codes Reference

| Status | Common Causes | Resolution |
|--------|---------------|------------|
| 400 | Missing field, invalid value, validation failure | Check request body against schema |
| 401 | Missing token, invalid token, expired token | Re-authenticate and retry |
| 403 | Wrong role, insufficient permissions | Contact admin for access |
| 404 | Invalid ID, deleted resource | Verify resource exists |
| 409 | Concurrent modification, duplicate entry | Refresh data and retry |
| 422 | Invalid request structure | Check request format |
| 500 | Server error | Retry later, report if persistent |

---

*See also: [Authentication](./authentication.md) for auth-specific errors*
