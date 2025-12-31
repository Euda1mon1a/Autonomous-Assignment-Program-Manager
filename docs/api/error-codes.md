# Error Codes Reference

Complete reference for API error codes and error handling.

---

## Overview

The Residency Scheduler API uses standard HTTP status codes and provides detailed error messages in a consistent JSON format.

---

## HTTP Status Codes

### Success Codes (2xx)

| Code | Name | Description |
|------|------|-------------|
| **200** | OK | Request succeeded |
| **201** | Created | Resource created successfully |
| **204** | No Content | Request succeeded, no response body |
| **207** | Multi-Status | Partial success (used for schedule generation with violations) |

### Client Error Codes (4xx)

| Code | Name | Description |
|------|------|-------------|
| **400** | Bad Request | Invalid request format or parameters |
| **401** | Unauthorized | Authentication required or token invalid |
| **403** | Forbidden | Insufficient permissions for this operation |
| **404** | Not Found | Requested resource does not exist |
| **409** | Conflict | Request conflicts with current state (e.g., concurrent update, idempotency) |
| **422** | Unprocessable Entity | Validation error, request format valid but semantics invalid |
| **429** | Too Many Requests | Rate limit exceeded |

### Server Error Codes (5xx)

| Code | Name | Description |
|------|------|-------------|
| **500** | Internal Server Error | Unexpected server error |
| **503** | Service Unavailable | Server temporarily unavailable (maintenance, overload) |

---

## Error Response Format

All errors return a consistent JSON structure:

### Simple Error

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Invalid email format",
      "type": "value_error"
    },
    {
      "loc": ["body", "pgy_level"],
      "msg": "PGY level must be 1, 2, or 3",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## Authentication Errors (401)

### Invalid Credentials

```json
{
  "detail": "Incorrect email or password"
}
```

**Cause**: Username or password is incorrect.

**Solution**: Verify credentials and retry.

---

### Token Expired

```json
{
  "detail": "Token has expired"
}
```

**Cause**: Access token has exceeded its 15-minute lifetime.

**Solution**: Use refresh token to obtain new access token.

---

### Invalid Token

```json
{
  "detail": "Could not validate credentials"
}
```

**Cause**: Token is malformed, invalid signature, or blacklisted.

**Solution**: Re-authenticate to obtain fresh tokens.

---

### Token Blacklisted

```json
{
  "detail": "Token has been revoked"
}
```

**Cause**: Token was logged out or refresh token was rotated.

**Solution**: Re-authenticate.

---

## Authorization Errors (403)

### Insufficient Permissions

```json
{
  "detail": "Insufficient permissions. Admin role required."
}
```

**Cause**: User lacks required role for the operation.

**Solution**: Request access from administrator or use account with appropriate role.

---

### Scheduler Role Required

```json
{
  "detail": "Scheduler role required (admin or coordinator)"
}
```

**Cause**: Operation requires scheduler privileges (admin or coordinator role).

**Solution**: Use admin or coordinator account.

---

## Validation Errors (422)

### Invalid Date Format

```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

**Cause**: Date parameter not in ISO 8601 format.

**Solution**: Use YYYY-MM-DD format (e.g., "2024-07-15").

---

### Invalid Date Range

```json
{
  "detail": "start_date must be before or equal to end_date"
}
```

**Cause**: Start date is after end date.

**Solution**: Ensure start_date <= end_date.

---

### Invalid PGY Level

```json
{
  "detail": "PGY level must be 1, 2, or 3"
}
```

**Cause**: PGY level outside valid range.

**Solution**: Use 1, 2, or 3 for PGY level.

---

### Email Already Exists

```json
{
  "detail": "Email address already registered"
}
```

**Cause**: Email is already in use by another user/person.

**Solution**: Use different email or update existing record.

---

### Schedule Generation Failed

```json
{
  "detail": "Schedule generation failed: insufficient residents for date range"
}
```

**Cause**: Not enough residents available to cover all blocks.

**Solution**: Add more residents, reduce date range, or adjust rotation templates.

---

## Conflict Errors (409)

### Concurrent Modification

```json
{
  "detail": "Assignment has been modified by another user. Please refresh and try again."
}
```

**Cause**: Optimistic locking detected concurrent update.

**Solution**: Refresh the resource, get latest version number, and retry update.

---

### Schedule In Progress

```json
{
  "detail": "Schedule generation already in progress for overlapping date range. Please wait for the current run to complete."
}
```

**Cause**: Another schedule generation is running for same/overlapping dates.

**Solution**: Wait for current generation to complete (check status via run_id).

---

### Idempotency Conflict

```json
{
  "detail": "Idempotency key was already used with different request parameters. Use a new key for different requests."
}
```

**Cause**: Same idempotency key used with different request body.

**Solution**: Generate new idempotency key for different requests, or reuse same key with identical request.

---

### Idempotency Pending

```json
{
  "detail": "A request with this idempotency key is currently being processed. Please wait for it to complete."
}
```

**Cause**: Request with same idempotency key is still processing.

**Solution**: Wait for original request to complete, or check its status.

---

### Crisis Already Active

```json
{
  "detail": "Crisis mode is already activated"
}
```

**Cause**: Attempting to activate crisis mode when already active.

**Solution**: Deactivate first or skip activation.

---

## Not Found Errors (404)

### Resource Not Found

```json
{
  "detail": "Person with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Cause**: Requested resource does not exist.

**Solution**: Verify ID is correct, resource hasn't been deleted.

---

## Rate Limiting Errors (429)

### Rate Limit Exceeded

```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds."
}
```

**Cause**: Too many requests in time window.

**Solution**: Wait for specified time, then retry. Check rate limit headers.

### Rate Limit Headers

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1720012800
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp when limit resets |

---

## Application-Specific Errors

### ACGME Compliance

#### 80-Hour Violation

Returned in validation results, not as HTTP error:

```json
{
  "type": "80_HOUR_RULE",
  "severity": "CRITICAL",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_name": "PGY1-01",
  "message": "80-hour rule violated: 84.5 hours in 4-week period ending 2024-07-28",
  "details": {
    "actual_hours": 84.5,
    "max_hours": 80.0,
    "excess_hours": 4.5
  }
}
```

**Note**: ACGME violations are returned in validation results, not as HTTP errors. Schedule generation may succeed (207) with violations.

---

### Swap Validation

#### Back-to-Back Conflict

```json
{
  "success": false,
  "validation": {
    "valid": false,
    "errors": [
      "Back-to-back weeks detected: FAC-PD would have weeks 2024-07-01 and 2024-07-08"
    ],
    "back_to_back_conflict": true
  }
}
```

**Cause**: Swap would create consecutive FMIT weeks.

**Solution**: Choose different week or different faculty.

---

#### External Conflict

```json
{
  "success": false,
  "validation": {
    "valid": false,
    "errors": [
      "External conflict: FAC-PD has leave on 2024-07-08"
    ],
    "external_conflict": true
  }
}
```

**Cause**: Swap conflicts with leave, TDY, or deployment.

**Solution**: Check absence records and choose different date.

---

### Resilience

#### Rollback Window Expired

```json
{
  "detail": "Swap cannot be rolled back (either not found, already rolled back, or outside rollback window)"
}
```

**Cause**: Attempting to rollback swap >24 hours after execution.

**Solution**: Swaps can only be rolled back within 24 hours.

---

## Error Handling Best Practices

### 1. Always Check Status Code

```python
import requests

response = requests.post("http://localhost:8000/api/v1/assignments", json=data)

if response.status_code == 201:
    assignment = response.json()
    print(f"Created: {assignment['id']}")
elif response.status_code == 409:
    print("Conflict: Resource was modified by another user")
elif response.status_code == 422:
    errors = response.json()['detail']
    for error in errors:
        print(f"Validation error: {error['msg']}")
else:
    print(f"Error: {response.json()['detail']}")
```

### 2. Handle Validation Errors

```python
def create_assignment(data, token):
    response = requests.post(
        "http://localhost:8000/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )

    if response.status_code == 422:
        # Parse validation errors
        for error in response.json()['detail']:
            field = '.'.join(str(loc) for loc in error['loc'])
            print(f"Error in {field}: {error['msg']}")
        return None

    response.raise_for_status()
    return response.json()
```

### 3. Implement Retry Logic for Rate Limits

```python
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def create_session_with_retries():
    session = requests.Session()
    retry = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1  # Wait 1, 2, 4 seconds
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

session = create_session_with_retries()
response = session.post("http://localhost:8000/api/auth/login", json=credentials)
```

### 4. Handle Token Expiration

```python
def api_request(url, method="GET", **kwargs):
    """Make API request with automatic token refresh."""
    response = requests.request(method, url, **kwargs)

    if response.status_code == 401:
        # Token expired, refresh it
        refresh_response = requests.post(
            "http://localhost:8000/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        if refresh_response.status_code == 200:
            tokens = refresh_response.json()
            # Update headers with new token
            kwargs['headers']['Authorization'] = f"Bearer {tokens['access_token']}"
            # Retry original request
            response = requests.request(method, url, **kwargs)

    return response
```

### 5. Use Idempotency for Critical Operations

```python
import uuid

def generate_schedule_idempotent(data, token):
    """Generate schedule with idempotency protection."""
    idempotency_key = str(uuid.uuid4())

    response = requests.post(
        "http://localhost:8000/api/v1/schedule/generate",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key
        },
        json=data
    )

    if response.status_code == 409:
        # Request already in progress
        print("Request in progress, waiting...")
        time.sleep(5)
        # Retry with same key - will get cached result
        response = requests.post(
            "http://localhost:8000/api/v1/schedule/generate",
            headers={
                "Authorization": f"Bearer {token}",
                "Idempotency-Key": idempotency_key
            },
            json=data
        )

    return response.json()
```

---

## Error Code Summary Table

| Code | Category | Examples | Retryable |
|------|----------|----------|-----------|
| 400 | Bad Request | Invalid parameters, malformed JSON | No - fix request |
| 401 | Unauthorized | Expired token, invalid credentials | Yes - refresh token |
| 403 | Forbidden | Insufficient role | No - requires different user |
| 404 | Not Found | Resource doesn't exist | No - verify ID |
| 409 | Conflict | Concurrent update, idempotency | Yes - retry with updated version |
| 422 | Validation Error | ACGME violations, invalid data | No - fix data |
| 429 | Rate Limit | Too many requests | Yes - wait and retry |
| 500 | Server Error | Internal error | Yes - retry with backoff |
| 503 | Service Unavailable | Maintenance, overload | Yes - retry later |

---

## See Also

- [Authentication](authentication.md) - Token management
- [Pagination](pagination.md) - Paginated responses
- [Schedules API](endpoints/schedules.md) - Schedule error codes
- [Assignments API](endpoints/assignments.md) - Assignment error codes
- [Swaps API](endpoints/swaps.md) - Swap error codes
