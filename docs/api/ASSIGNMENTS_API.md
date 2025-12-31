# Assignments API Reference

**Endpoint Prefix:** `/api/assignments`

## Overview

The Assignments API manages individual schedule assignments for residents and faculty. This API integrates with the ACGME validator to ensure compliance with work hour limits, supervision ratios, and other regulatory requirements.

### Key Features

- **CRUD Operations**: Create, read, update, delete assignments
- **Bulk Operations**: Delete assignments in date ranges
- **ACGME Validation**: Real-time compliance checking with warning/violation reporting
- **Filtering & Pagination**: Advanced query support for schedule analysis
- **Optimistic Locking**: Prevent concurrent modification conflicts

### Data Model

```
Assignment
├── Person (resident or faculty)
├── Block (date + AM/PM)
├── Rotation Template (activity type)
├── Role (resident or supervising faculty)
└── Warnings (ACGME compliance issues)
```

---

## Endpoints

### GET /

List assignments with optional filtering and pagination.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/assignments?start_date=2025-01-01&end_date=2025-12-31&person_id=550e8400-e29b-41d4-a716-446655440001&page=1&page_size=50' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `start_date` (optional, YYYY-MM-DD): Filter assignments from this date
- `end_date` (optional, YYYY-MM-DD): Filter assignments until this date
- `person_id` (optional, UUID): Filter assignments for a specific person
- `role` (optional): Filter by role - `'resident'`, `'faculty'`, `'attending'`, etc.
- `activity_type` (optional): Filter by activity type - `'on_call'`, `'clinic'`, `'inpatient'`, etc.
- `page` (optional, default: 1): Page number (1-indexed)
- `page_size` (optional, default: 100): Items per page (max: 500)

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440300",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "person_name": "Dr. Jane Smith",
      "block_id": "550e8400-e29b-41d4-a716-446655440400",
      "block_date": "2025-01-15",
      "session": "AM",
      "rotation_template_id": "550e8400-e29b-41d4-a716-446655440500",
      "rotation_name": "Internal Medicine Inpatient",
      "role": "resident",
      "activity_name": "Inpatient",
      "abbreviation": "IP",
      "status": "assigned",
      "created_at": "2025-12-31T10:00:00Z",
      "updated_at": "2025-12-31T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

**Error Responses:**

- **401 Unauthorized**: Missing authentication
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

---

### GET /{assignment_id}

Get a specific assignment by ID.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/assignments/550e8400-e29b-41d4-a716-446655440300' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `assignment_id` (required, UUID): Assignment ID to retrieve

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440300",
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_name": "Dr. Jane Smith",
  "block_id": "550e8400-e29b-41d4-a716-446655440400",
  "block_date": "2025-01-15",
  "session": "AM",
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440500",
  "rotation_name": "Internal Medicine Inpatient",
  "role": "resident",
  "activity_name": "Inpatient",
  "abbreviation": "IP",
  "status": "assigned",
  "notes": "Lead resident for this shift",
  "created_at": "2025-12-31T10:00:00Z",
  "updated_at": "2025-12-31T10:00:00Z"
}
```

**Error Responses:**

- **404 Not Found**: Assignment doesn't exist
  ```json
  {
    "detail": "Assignment not found"
  }
  ```

---

### POST /

Create a new assignment.

**Request:**
```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "block_id": "550e8400-e29b-41d4-a716-446655440400",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440500",
    "role": "resident",
    "override_reason": "Scheduled after ACGME validation"
  }'
```

**Request Body:**
```json
{
  "person_id": "string (UUID, required)",
  "block_id": "string (UUID, required)",
  "rotation_template_id": "string (UUID, required)",
  "role": "string (required, e.g., 'resident', 'supervising_faculty')",
  "notes": "string (optional)",
  "override_reason": "string (optional, required if ACGME violations exist)"
}
```

**Response (201):**
```json
{
  "assignment": {
    "id": "550e8400-e29b-41d4-a716-446655440300",
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_name": "Dr. Jane Smith",
    "block_id": "550e8400-e29b-41d4-a716-446655440400",
    "block_date": "2025-01-15",
    "session": "AM",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440500",
    "rotation_name": "Internal Medicine Inpatient",
    "role": "resident",
    "activity_name": "Inpatient",
    "abbreviation": "IP",
    "status": "assigned",
    "created_at": "2025-12-31T10:00:00Z",
    "updated_at": "2025-12-31T10:00:00Z"
  },
  "warnings": [],
  "violations": []
}
```

**ACGME Compliance Warnings:**

When violations are detected, they are returned but do not block creation. Example response with warnings:

```json
{
  "assignment": { ... },
  "warnings": [
    {
      "rule": "80_hour_rule",
      "severity": "warning",
      "message": "Weekly hours exceed 80. Current: 82 hours in rolling 4-week period",
      "affected_dates": ["2025-01-15", "2025-01-22"]
    }
  ],
  "violations": [
    {
      "rule": "one_in_seven",
      "severity": "error",
      "message": "No day off in 8 consecutive days",
      "affected_dates": ["2025-01-15 to 2025-01-22"]
    }
  ]
}
```

**Error Responses:**

- **400 Bad Request**: Invalid request data
  ```json
  {
    "detail": "Invalid assignment data"
  }
  ```

- **404 Not Found**: Person, block, or rotation doesn't exist
  ```json
  {
    "detail": "Person not found"
  }
  ```

- **403 Forbidden**: User doesn't have scheduler role
  ```json
  {
    "detail": "Only administrators and coordinators can create assignments"
  }
  ```

---

### PUT /{assignment_id}

Update an existing assignment.

**Request:**
```bash
curl -X PUT 'http://localhost:8000/api/assignments/550e8400-e29b-41d4-a716-446655440300' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440501",
    "role": "resident",
    "notes": "Changed to Internal Medicine Clinic",
    "version": 1
  }'
```

**Path Parameters:**
- `assignment_id` (required, UUID): Assignment ID to update

**Request Body:**
```json
{
  "person_id": "string (UUID, optional)",
  "block_id": "string (UUID, optional)",
  "rotation_template_id": "string (UUID, optional)",
  "role": "string (optional)",
  "notes": "string (optional)",
  "override_reason": "string (optional, required if ACGME violations exist)",
  "version": "number (required for optimistic locking)"
}
```

**Response (200):**
```json
{
  "assignment": { ... },
  "warnings": [],
  "violations": []
}
```

**Optimistic Locking:**
- The `version` field is used to detect concurrent modifications
- If the assignment was modified since you last read it, the update will fail with a 409 error
- Always include the current `version` from the last GET request

**Error Responses:**

- **404 Not Found**: Assignment doesn't exist
  ```json
  {
    "detail": "Assignment not found"
  }
  ```

- **409 Conflict**: Concurrent modification detected
  ```json
  {
    "detail": "Assignment was modified by another user. Please refresh and try again."
  }
  ```

---

### DELETE /{assignment_id}

Delete a single assignment.

**Request:**
```bash
curl -X DELETE 'http://localhost:8000/api/assignments/550e8400-e29b-41d4-a716-446655440300' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `assignment_id` (required, UUID): Assignment ID to delete

**Response (204):**
No content returned.

**Error Responses:**

- **404 Not Found**: Assignment doesn't exist
  ```json
  {
    "detail": "Assignment not found"
  }
  ```

- **403 Forbidden**: User doesn't have scheduler role
  ```json
  {
    "detail": "Only administrators and coordinators can delete assignments"
  }
  ```

---

### DELETE /

Delete all assignments in a date range (bulk operation).

**Request:**
```bash
curl -X DELETE 'http://localhost:8000/api/assignments?start_date=2025-01-01&end_date=2025-01-31' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `start_date` (required, YYYY-MM-DD): Delete assignments from this date
- `end_date` (required, YYYY-MM-DD): Delete assignments until this date

**Response (204):**
No content returned.

**Notes:**
- This operation is permanent and cannot be undone (use database backups if needed)
- Only schedule administrators should have access to this operation
- Recommended: Backup database before bulk deletion

---

## ACGME Compliance Validation

The API validates all assignments against ACGME compliance rules:

### Rules Checked

1. **80-Hour Rule**: Maximum 80 hours per week (rolling 4-week average)
   - Calculated across all assignments for the person
   - Considers time zone differences
   - Returns warning if approaching limit

2. **1-in-7 Rule**: At least one 24-hour period off every 7 consecutive days
   - Checks continuous duty periods
   - Returns violation if consecutive duty exceeds safe limits
   - Does not block creation (must be overridden)

3. **Supervision Ratios**: Proper faculty supervision
   - PGY-1: Maximum 2 residents per supervising faculty
   - PGY-2/3: Maximum 4 residents per supervising faculty
   - Returns warning if ratios exceeded

### Violation Response Format

```json
{
  "rule": "rule_identifier",
  "severity": "warning | error",
  "message": "Human-readable description",
  "affected_dates": ["2025-01-15", "2025-01-16"],
  "metric": 85.5,
  "limit": 80,
  "current_assignments": 12
}
```

### Creating Assignments with Violations

To create assignments despite ACGME violations, include `override_reason`:

```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "block_id": "550e8400-e29b-41d4-a716-446655440400",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440500",
    "role": "resident",
    "override_reason": "Emergency coverage: Faculty TDY"
  }'
```

---

## Filtering Examples

### Get All Clinic Assignments for a Resident

```bash
curl -X GET 'http://localhost:8000/api/assignments?person_id=550e8400-e29b-41d4-a716-446655440001&activity_type=clinic' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get All Call Assignments in January

```bash
curl -X GET 'http://localhost:8000/api/assignments?start_date=2025-01-01&end_date=2025-01-31&activity_type=on_call' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get All Faculty Supervision Assignments

```bash
curl -X GET 'http://localhost:8000/api/assignments?role=supervising_faculty' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Get All Assignments with Pagination

```bash
# Page 1 (items 1-50)
curl -X GET 'http://localhost:8000/api/assignments?page=1&page_size=50' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Page 2 (items 51-100)
curl -X GET 'http://localhost:8000/api/assignments?page=2&page_size=50' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Common Use Cases

### 1. Get a Resident's Full Schedule

```bash
RESIDENT_ID="550e8400-e29b-41d4-a716-446655440001"
START_DATE="2025-01-01"
END_DATE="2025-12-31"

curl -X GET "http://localhost:8000/api/assignments?person_id=$RESIDENT_ID&start_date=$START_DATE&end_date=$END_DATE&page_size=500" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.items | length'
```

### 2. Check for ACGME Violations Before Bulk Assignment

```bash
# Get current hours for resident
curl -X GET "http://localhost:8000/api/assignments?person_id=$RESIDENT_ID&start_date=2025-01-01&end_date=2025-01-28" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.items | length'

# Then create assignment and check response for violations
curl -X POST http://localhost:8000/api/assignments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{...}' | jq '.violations'
```

### 3. Clear January and Regenerate Schedule

```bash
# Delete all assignments for January
curl -X DELETE 'http://localhost:8000/api/assignments?start_date=2025-01-01&end_date=2025-01-31' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Then regenerate via /schedule/generate endpoint
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "algorithm": "cp_sat"
  }'
```

---

## Data Models

### Assignment Response

```json
{
  "id": "string (UUID)",
  "person_id": "string (UUID)",
  "person_name": "string",
  "block_id": "string (UUID)",
  "block_date": "string (YYYY-MM-DD)",
  "session": "string (AM or PM)",
  "rotation_template_id": "string (UUID)",
  "rotation_name": "string",
  "role": "string",
  "activity_name": "string",
  "abbreviation": "string",
  "status": "string",
  "notes": "string or null",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "version": "number"
}
```

### Violation Item

```json
{
  "rule": "string",
  "severity": "string (warning or error)",
  "message": "string",
  "affected_dates": ["string"],
  "metric": "number or null",
  "limit": "number or null",
  "current_assignments": "number or null"
}
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request format or validation error |
| 401 | Unauthorized | Authentication required or invalid token |
| 403 | Forbidden | Insufficient permissions (must be scheduler role) |
| 404 | Not Found | Assignment, person, block, or rotation not found |
| 409 | Conflict | Concurrent modification (optimistic locking) |
| 422 | Unprocessable Entity | ACGME violation without override reason |
| 500 | Internal Server Error | Server error |

---

## Best Practices

### Before Creating Assignments

1. **Verify Person Exists**: Check that person_id is valid
2. **Check Block Availability**: Ensure block hasn't been assigned
3. **Validate Credentials**: For faculty supervising, check their credentials
4. **Review ACGME Status**: Check if person is near hour limits

### Handling ACGME Violations

```javascript
const response = await fetch('/api/assignments', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(assignmentData)
});

const result = await response.json();

if (result.violations.length > 0) {
  // User must confirm override
  if (userConfirmedOverride) {
    // Retry with override_reason
    const overrideData = {
      ...assignmentData,
      override_reason: `Confirmed by ${username}: ${reason}`
    };
    // Re-submit
  }
}
```

---

## Related Documentation

- [Schedule API](SCHEDULE_API.md)
- [People API](PEOPLE_API.md)
- [ACGME Compliance Rules](../architecture/ACGME_COMPLIANCE.md)
