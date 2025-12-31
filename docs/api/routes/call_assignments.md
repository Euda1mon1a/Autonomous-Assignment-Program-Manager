# Call Assignments API

Complete reference for the `/api/v1/call-assignments` endpoints.

> **Base Path:** `/api/v1/call-assignments`
> **Authentication:** Required (Bearer token)
> **Source:** `backend/app/api/routes/call_assignments.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Reports](#reports)
4. [Schemas](#schemas)
5. [Examples](#examples)
6. [Error Handling](#error-handling)

---

## Overview

The Call Assignments API manages overnight and weekend faculty call assignments. Solver-generated call assignments emerge from constraint optimization during schedule generation.

### Key Features

- **Call Types**: Overnight (Sun-Thu), Weekend (Fri-Sat FMIT), Backup
- **Equity Tracking**: Sunday call and weekday call distribution
- **Coverage Reports**: Identify gaps in call coverage
- **Bulk Operations**: Solver-generated bulk assignment creation
- **Role-Based Access**: Read (all users), Write (Admin/Coordinator/Faculty), Reports (Admin/Coordinator)

---

## Endpoints

### List Call Assignments

```http
GET /api/v1/call-assignments
```

List call assignments with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | - | Filter by start date (inclusive, YYYY-MM-DD) |
| `end_date` | date | No | - | Filter by end date (inclusive, YYYY-MM-DD) |
| `person_id` | UUID | No | - | Filter by person ID |
| `call_type` | string | No | - | Filter by call type: `overnight`, `weekend`, `backup` |
| `skip` | int | No | 0 | Number of records to skip (pagination) |
| `limit` | int | No | 100 | Max records to return (1-1000) |

**Response:** `CallAssignmentListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication

---

### Get Call Assignment

```http
GET /api/v1/call-assignments/{call_id}
```

Get a single call assignment by ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `call_id` | UUID | Yes | Call assignment ID |

**Response:** `CallAssignmentResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Call assignment not found

---

### Create Call Assignment

```http
POST /api/v1/call-assignments
```

Create a new call assignment.

**Authorization:** Admin, Coordinator, or Faculty role

**Request Body:** `CallAssignmentCreate`

**Response:** `CallAssignmentResponse` (201 Created)

**Status Codes:**
- `201 Created`: Call assignment created successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: Validation failure

---

### Update Call Assignment

```http
PUT /api/v1/call-assignments/{call_id}
```

Update an existing call assignment.

**Authorization:** Admin, Coordinator, or Faculty role

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `call_id` | UUID | Yes | Call assignment ID |

**Request Body:** `CallAssignmentUpdate`

**Response:** `CallAssignmentResponse`

**Status Codes:**
- `200 OK`: Call assignment updated successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Call assignment not found
- `422 Unprocessable Entity`: Validation failure

---

### Delete Call Assignment

```http
DELETE /api/v1/call-assignments/{call_id}
```

Delete a call assignment.

**Authorization:** Admin, Coordinator, or Faculty role

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `call_id` | UUID | Yes | Call assignment ID |

**Status Codes:**
- `204 No Content`: Call assignment deleted successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Call assignment not found

---

### Bulk Create Call Assignments

```http
POST /api/v1/call-assignments/bulk
```

Bulk create multiple call assignments. Used by solver for schedule generation.

**Authorization:** Admin or Coordinator role

**Request Body:** `BulkCallAssignmentCreate`

**Response:** `BulkCallAssignmentResponse` (201 Created)

**Status Codes:**
- `201 Created`: Bulk creation successful
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: Validation failure

**Notes:**
- Optionally replace existing assignments in date range first
- Returns count of created assignments and any errors

---

### Get Call Assignments by Person

```http
GET /api/v1/call-assignments/by-person/{person_id}
```

Get all call assignments for a specific person.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter by start date |
| `end_date` | date | No | Filter by end date |

**Response:** `CallAssignmentListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

---

### Get Call Assignments by Date

```http
GET /api/v1/call-assignments/by-date/{on_date}
```

Get all call assignments for a specific date.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `on_date` | date | Yes | Date (YYYY-MM-DD) |

**Response:** `CallAssignmentListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication

---

## Reports

### Get Coverage Report

```http
GET /api/v1/call-assignments/reports/coverage
```

Get a report showing call coverage gaps.

**Authorization:** Admin or Coordinator role

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date for report (YYYY-MM-DD) |
| `end_date` | date | Yes | End date for report (YYYY-MM-DD) |

**Response:** `CallCoverageReport`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions

**Returns:**
- Total expected nights requiring coverage
- Covered nights count
- Coverage percentage
- List of dates without coverage (gaps)

---

### Get Equity Report

```http
GET /api/v1/call-assignments/reports/equity
```

Get a report showing call distribution across faculty.

**Authorization:** Admin or Coordinator role

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date for report (YYYY-MM-DD) |
| `end_date` | date | Yes | End date for report (YYYY-MM-DD) |

**Response:** `CallEquityReport`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions

**Returns:**
- Faculty count
- Total overnight calls
- Sunday call statistics (min, max, mean, stdev)
- Weekday call statistics (Mon-Thu)
- Per-faculty distribution details

---

## Schemas

### CallAssignmentCreate

```json
{
  "call_date": "2025-01-15",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_type": "overnight",
  "is_weekend": false,
  "is_holiday": false
}
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `call_date` | date | Yes | - | Date of the call assignment |
| `person_id` | UUID | Yes | - | Faculty member assigned to call |
| `call_type` | string | No | overnight | Type: `overnight`, `weekend`, `backup` |
| `is_weekend` | bool | No | false | Whether this is a weekend call |
| `is_holiday` | bool | No | false | Whether this is a holiday call |

---

### CallAssignmentUpdate

All fields are optional.

```json
{
  "call_date": "2025-01-16",
  "person_id": "660e8400-e29b-41d4-a716-446655440001",
  "call_type": "weekend",
  "is_weekend": true,
  "is_holiday": false
}
```

---

### CallAssignmentResponse

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "call_date": "2025-01-15",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_type": "overnight",
  "is_weekend": false,
  "is_holiday": false,
  "person": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Dr. Smith",
    "faculty_role": "core"
  }
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Call assignment ID |
| `call_date` | date | Date of call assignment |
| `person_id` | UUID | Faculty member ID |
| `call_type` | string | Type: `overnight`, `weekend`, `backup` |
| `is_weekend` | bool | Whether this is a weekend call |
| `is_holiday` | bool | Whether this is a holiday call |
| `person` | PersonBrief | Embedded person details (optional) |

---

### CallAssignmentListResponse

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "call_date": "2025-01-15",
      // ... (all CallAssignmentResponse fields) ...
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `items` | array[CallAssignmentResponse] | Call assignment items |
| `total` | int | Total count of call assignments |
| `skip` | int | Number of records skipped |
| `limit` | int | Max records returned |

---

### BulkCallAssignmentCreate

```json
{
  "assignments": [
    {
      "call_date": "2025-01-15",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "call_type": "overnight",
      "is_weekend": false,
      "is_holiday": false
    },
    {
      "call_date": "2025-01-16",
      "person_id": "660e8400-e29b-41d4-a716-446655440001",
      "call_type": "overnight",
      "is_weekend": false,
      "is_holiday": false
    }
  ],
  "replace_existing": false
}
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `assignments` | array[CallAssignmentCreate] | Yes | - | List of call assignments to create |
| `replace_existing` | bool | No | false | If true, delete existing assignments in date range first |

---

### BulkCallAssignmentResponse

```json
{
  "created": 50,
  "errors": [
    "Failed to create assignment for 2025-01-20: Person not found"
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `created` | int | Number of assignments created |
| `errors` | array[string] | Error messages for failed creations |

---

### CallCoverageReport

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "total_expected_nights": 22,
  "covered_nights": 20,
  "coverage_percentage": 90.91,
  "gaps": ["2025-01-15", "2025-01-22"]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | date | Report start date |
| `end_date` | date | Report end date |
| `total_expected_nights` | int | Total nights requiring coverage (Sun-Thu) |
| `covered_nights` | int | Nights with call assignments |
| `coverage_percentage` | float | Percentage of nights covered (0-100) |
| `gaps` | array[date] | Dates without call coverage |

---

### CallEquityReport

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "faculty_count": 8,
  "total_overnight_calls": 22,
  "sunday_call_stats": {
    "min": 0,
    "max": 2,
    "mean": 0.75,
    "stdev": 0.5
  },
  "weekday_call_stats": {
    "min": 2,
    "max": 4,
    "mean": 2.75,
    "stdev": 0.71
  },
  "distribution": [
    {
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. Smith",
      "sunday_calls": 2,
      "weekday_calls": 3,
      "total_calls": 5
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | date | Report start date |
| `end_date` | date | Report end date |
| `faculty_count` | int | Number of faculty with call assignments |
| `total_overnight_calls` | int | Total overnight call assignments |
| `sunday_call_stats` | dict | Statistics for Sunday calls (min, max, mean, stdev) |
| `weekday_call_stats` | dict | Statistics for Mon-Thu calls (min, max, mean, stdev) |
| `distribution` | array[dict] | Per-faculty call distribution details |

---

## Call Types

### Overnight Call

- **Days:** Sunday PM → Monday AM through Thursday PM → Friday AM
- **Type:** `overnight`
- **Description:** Sun-Thu overnight call assignments

### Weekend Call

- **Days:** Friday PM → Sunday PM
- **Type:** `weekend`
- **Description:** Fri-Sat FMIT coverage (FMIT faculty only)

### Backup Call

- **Days:** Any day as needed
- **Type:** `backup`
- **Description:** Emergency backup coverage

---

## Examples

### List Call Assignments with Filters

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/call-assignments?start_date=2025-01-01&end_date=2025-01-31&call_type=overnight&limit=50" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "call_date": "2025-01-05",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "call_type": "overnight",
      "is_weekend": false,
      "is_holiday": false,
      "person": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dr. Smith",
        "faculty_role": "core"
      }
    }
  ],
  "total": 22,
  "skip": 0,
  "limit": 50
}
```

---

### Create Call Assignment

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/call-assignments" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "call_date": "2025-01-15",
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "call_type": "overnight",
    "is_weekend": false,
    "is_holiday": false
  }'
```

**Response (201 Created):**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "call_date": "2025-01-15",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "call_type": "overnight",
  "is_weekend": false,
  "is_holiday": false,
  "person": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Dr. Smith",
    "faculty_role": "core"
  }
}
```

---

### Bulk Create Call Assignments

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/call-assignments/bulk" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "assignments": [
      {
        "call_date": "2025-01-15",
        "person_id": "550e8400-e29b-41d4-a716-446655440000",
        "call_type": "overnight",
        "is_weekend": false,
        "is_holiday": false
      },
      {
        "call_date": "2025-01-16",
        "person_id": "660e8400-e29b-41d4-a716-446655440001",
        "call_type": "overnight",
        "is_weekend": false,
        "is_holiday": false
      }
    ],
    "replace_existing": false
  }'
```

**Response (201 Created):**

```json
{
  "created": 2,
  "errors": []
}
```

---

### Get Call Assignments by Person

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/call-assignments/by-person/550e8400-e29b-41d4-a716-446655440000?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "call_date": "2025-01-05",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "call_type": "overnight",
      "is_weekend": false,
      "is_holiday": false,
      "person": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Dr. Smith",
        "faculty_role": "core"
      }
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 100
}
```

---

### Get Coverage Report

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/call-assignments/reports/coverage?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "total_expected_nights": 22,
  "covered_nights": 20,
  "coverage_percentage": 90.91,
  "gaps": ["2025-01-15", "2025-01-22"]
}
```

---

### Get Equity Report

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/call-assignments/reports/equity?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "faculty_count": 8,
  "total_overnight_calls": 22,
  "sunday_call_stats": {
    "min": 0,
    "max": 2,
    "mean": 0.75,
    "stdev": 0.5
  },
  "weekday_call_stats": {
    "min": 2,
    "max": 4,
    "mean": 2.75,
    "stdev": 0.71
  },
  "distribution": [
    {
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. Smith",
      "sunday_calls": 2,
      "weekday_calls": 3,
      "total_calls": 5
    },
    {
      "person_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. Jones",
      "sunday_calls": 1,
      "weekday_calls": 2,
      "total_calls": 3
    }
  ]
}
```

---

## Error Handling

### 403 Forbidden - Insufficient Permissions

```json
{
  "detail": "Insufficient permissions. Admin, Coordinator, or Faculty role required."
}
```

**Cause:** User does not have required role for the operation.

**Resolution:** Contact an administrator to grant appropriate permissions.

---

### 404 Not Found - Call Assignment Not Found

```json
{
  "detail": "Call assignment not found"
}
```

**Cause:** Call assignment ID does not exist.

**Resolution:** Verify the call assignment ID.

---

### 422 Unprocessable Entity - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "call_type"],
      "msg": "call_type must be 'overnight', 'weekend', or 'backup'",
      "type": "value_error"
    }
  ]
}
```

**Cause:** Invalid field value in request body.

**Resolution:** Correct the invalid field and retry.

---

## Related Documentation

- [People API](people.md) - Faculty member management
- [Schedule API](schedule.md) - Schedule generation (creates call assignments)
- [Assignments API](assignments.md) - General assignment management
- [Call Distribution](../../architecture/call-distribution.md) - Call equity algorithms

---

## Notes

### Call Assignment vs Regular Assignment

| Feature | Call Assignment | Regular Assignment |
|---------|----------------|-------------------|
| **Purpose** | Overnight/weekend call | Regular scheduled activities |
| **Table** | `call_assignments` | `assignments` |
| **Tracking** | Person equity counters | Block-based scheduling |
| **Generation** | Solver or manual | Solver-generated |

### Equity Tracking

The system automatically tracks call equity through read-only counters on the `Person` model:
- `sunday_call_count`: Count of Sunday call assignments
- `weekday_call_count`: Count of Mon-Thu call assignments

These counters are used by the solver to ensure fair call distribution.

---

*Last Updated: 2025-12-31*
