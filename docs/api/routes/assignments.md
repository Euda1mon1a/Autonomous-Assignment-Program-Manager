# Assignments API

Complete reference for the `/api/v1/assignments` endpoints.

> **Base Path:** `/api/v1/assignments`
> **Authentication:** Required (Bearer token)
> **Source:** `backend/app/api/routes/assignments.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Schemas](#schemas)
4. [Examples](#examples)
5. [Error Handling](#error-handling)

---

## Overview

The Assignments API manages schedule assignments linking people (residents/faculty) to specific blocks and rotations. Each assignment represents a scheduled activity at a specific time slot.

### Key Features

- **ACGME Validation**: Creates/updates validate compliance and return warnings
- **Optimistic Locking**: Updates use `updated_at` timestamp to prevent concurrent modifications
- **Pagination**: List endpoint supports pagination with configurable page size
- **Filtering**: Filter by date range, person, role, or activity type

---

## Endpoints

### List Assignments

```http
GET /api/v1/assignments
```

List assignments with optional filters and pagination.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | date | No | - | Filter from this date (YYYY-MM-DD) |
| `end_date` | date | No | - | Filter until this date (YYYY-MM-DD) |
| `person_id` | UUID | No | - | Filter by person |
| `role` | string | No | - | Filter by role (`primary`, `supervising`, `backup`) |
| `activity_type` | string | No | - | Filter by activity type (e.g., `on_call`, `clinic`, `inpatient`) |
| `page` | int | No | 1 | Page number (1-indexed) |
| `page_size` | int | No | 100 | Items per page (max 500) |

**Response:** `AssignmentListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Invalid query parameters

---

### Get Assignment

```http
GET /api/v1/assignments/{assignment_id}
```

Get a single assignment by ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment ID |

**Response:** `AssignmentResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Assignment not found

---

### Create Assignment

```http
POST /api/v1/assignments
```

Create a new assignment. Validates ACGME compliance and returns warnings if violations exist.

**Authorization:** Scheduler role (Admin or Coordinator)

**Request Body:** `AssignmentCreate`

**Response:** `AssignmentWithWarnings` (201 Created)

**Status Codes:**
- `201 Created`: Assignment created successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: Validation failure

**Notes:**
- ACGME violations do not block creation but should be acknowledged with `override_reason`
- Returns `acgme_warnings` array and `is_compliant` boolean

---

### Update Assignment

```http
PUT /api/v1/assignments/{assignment_id}
```

Update an existing assignment with optimistic locking.

**Authorization:** Scheduler role (Admin or Coordinator)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment ID |

**Request Body:** `AssignmentUpdate`

**Response:** `AssignmentWithWarnings`

**Status Codes:**
- `200 OK`: Assignment updated successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Assignment not found
- `409 Conflict`: Optimistic locking failure (stale `updated_at`)
- `422 Unprocessable Entity`: Validation failure

**Notes:**
- Requires `updated_at` field for optimistic locking
- Set `acknowledge_override: true` to timestamp `override_acknowledged_at`

---

### Delete Assignment

```http
DELETE /api/v1/assignments/{assignment_id}
```

Delete a single assignment.

**Authorization:** Scheduler role (Admin or Coordinator)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment ID |

**Status Codes:**
- `204 No Content`: Assignment deleted successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Assignment not found

---

### Bulk Delete Assignments

```http
DELETE /api/v1/assignments
```

Delete all assignments in a date range.

**Authorization:** Scheduler role (Admin or Coordinator)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Delete assignments from this date |
| `end_date` | date | Yes | Delete assignments until this date |

**Status Codes:**
- `204 No Content`: Assignments deleted successfully
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: Invalid date parameters

---

## Schemas

### AssignmentCreate

```json
{
  "block_id": "uuid",
  "person_id": "uuid",
  "rotation_template_id": "uuid",
  "role": "primary",
  "activity_override": "Clinic",
  "notes": "Optional notes",
  "override_reason": "Reason for ACGME override",
  "created_by": "user@example.com"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_id` | UUID | Yes | Block ID |
| `person_id` | UUID | Yes | Person ID |
| `rotation_template_id` | UUID | No | Rotation template ID |
| `role` | string | Yes | Role (`primary`, `supervising`, `backup`) |
| `activity_override` | string | No | Override activity name |
| `notes` | string | No | Additional notes |
| `override_reason` | string | No | Reason for acknowledging ACGME violations |
| `created_by` | string | No | User who created the assignment |

---

### AssignmentUpdate

```json
{
  "rotation_template_id": "uuid",
  "role": "supervising",
  "activity_override": "Procedures",
  "notes": "Updated notes",
  "override_reason": "Covering for deployment",
  "acknowledge_override": true,
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rotation_template_id` | UUID | No | Rotation template ID |
| `role` | string | No | Role (`primary`, `supervising`, `backup`) |
| `activity_override` | string | No | Override activity name |
| `notes` | string | No | Additional notes |
| `override_reason` | string | No | Reason for ACGME override |
| `acknowledge_override` | bool | No | Set to `true` to timestamp `override_acknowledged_at` |
| `updated_at` | datetime | Yes | Current timestamp for optimistic locking |

---

### AssignmentResponse

```json
{
  "id": "uuid",
  "block_id": "uuid",
  "person_id": "uuid",
  "rotation_template_id": "uuid",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": null,
  "created_by": "user@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "override_acknowledged_at": null,
  "confidence": 0.95,
  "score": 87.5
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Assignment ID |
| `block_id` | UUID | Block ID |
| `person_id` | UUID | Person ID |
| `rotation_template_id` | UUID | Rotation template ID |
| `role` | string | Role (`primary`, `supervising`, `backup`) |
| `activity_override` | string | Override activity name |
| `notes` | string | Additional notes |
| `override_reason` | string | Reason for ACGME override |
| `created_by` | string | User who created the assignment |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `override_acknowledged_at` | datetime | When ACGME violation was acknowledged |
| `confidence` | float | Confidence score (0-1) for this assignment |
| `score` | float | Objective score for this assignment |

---

### AssignmentWithWarnings

Extends `AssignmentResponse` with ACGME validation results:

```json
{
  "id": "uuid",
  "block_id": "uuid",
  "person_id": "uuid",
  // ... (all AssignmentResponse fields) ...
  "acgme_warnings": [
    "Resident exceeds 80-hour limit in rolling 4-week period"
  ],
  "is_compliant": false
}
```

**Additional Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `acgme_warnings` | array[string] | List of ACGME compliance warnings |
| `is_compliant` | bool | Whether assignment is ACGME compliant |

---

### AssignmentListResponse

```json
{
  "items": [
    {
      "id": "uuid",
      // ... (AssignmentResponse fields) ...
    }
  ],
  "total": 250,
  "page": 1,
  "page_size": 100
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `items` | array[AssignmentResponse] | Assignment items |
| `total` | int | Total count of assignments |
| `page` | int | Current page number |
| `page_size` | int | Items per page |

---

## Examples

### List Assignments with Filters

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/assignments?start_date=2025-01-01&end_date=2025-01-31&role=primary&page=1&page_size=50" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "block_id": "660e8400-e29b-41d4-a716-446655440001",
      "person_id": "770e8400-e29b-41d4-a716-446655440002",
      "rotation_template_id": "880e8400-e29b-41d4-a716-446655440003",
      "role": "primary",
      "activity_override": null,
      "notes": null,
      "override_reason": null,
      "created_by": "scheduler@example.com",
      "created_at": "2025-01-15T08:00:00Z",
      "updated_at": "2025-01-15T08:00:00Z",
      "override_acknowledged_at": null,
      "confidence": 0.92,
      "score": 85.0
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50
}
```

---

### Create Assignment with ACGME Warning

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/assignments" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "660e8400-e29b-41d4-a716-446655440001",
    "person_id": "770e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "880e8400-e29b-41d4-a716-446655440003",
    "role": "primary",
    "override_reason": "Emergency coverage for deployment"
  }'
```

**Response (201 Created):**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "block_id": "660e8400-e29b-41d4-a716-446655440001",
  "person_id": "770e8400-e29b-41d4-a716-446655440002",
  "rotation_template_id": "880e8400-e29b-41d4-a716-446655440003",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": "Emergency coverage for deployment",
  "created_by": "scheduler@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "override_acknowledged_at": null,
  "confidence": 0.88,
  "score": 78.5,
  "acgme_warnings": [
    "Resident may exceed 80-hour limit in rolling 4-week period"
  ],
  "is_compliant": false
}
```

---

### Update Assignment

**Request:**

```bash
curl -X PUT "http://localhost:8000/api/v1/assignments/990e8400-e29b-41d4-a716-446655440004" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "supervising",
    "acknowledge_override": true,
    "updated_at": "2025-01-15T10:30:00Z"
  }'
```

**Response (200 OK):**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "block_id": "660e8400-e29b-41d4-a716-446655440001",
  "person_id": "770e8400-e29b-41d4-a716-446655440002",
  "rotation_template_id": "880e8400-e29b-41d4-a716-446655440003",
  "role": "supervising",
  "activity_override": null,
  "notes": null,
  "override_reason": "Emergency coverage for deployment",
  "created_by": "scheduler@example.com",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z",
  "override_acknowledged_at": "2025-01-15T10:35:00Z",
  "confidence": 0.88,
  "score": 78.5,
  "acgme_warnings": [],
  "is_compliant": true
}
```

---

### Bulk Delete Assignments

**Request:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/assignments?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response (204 No Content)**

---

## Error Handling

### 409 Conflict - Optimistic Locking Failure

```json
{
  "detail": "Assignment has been modified by another user. Please refresh and try again."
}
```

**Cause:** The `updated_at` timestamp in the request does not match the current value in the database.

**Resolution:** Fetch the latest assignment data and retry the update.

---

### 422 Unprocessable Entity - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "role"],
      "msg": "role must be 'primary', 'supervising', or 'backup'",
      "type": "value_error"
    }
  ]
}
```

**Cause:** Invalid field value in request body.

**Resolution:** Correct the invalid field and retry.

---

### 403 Forbidden - Insufficient Permissions

```json
{
  "detail": "Insufficient permissions. Scheduler role required."
}
```

**Cause:** User does not have Admin or Coordinator role.

**Resolution:** Contact an administrator to grant appropriate permissions.

---

## Related Documentation

- [People API](people.md) - Person (resident/faculty) management
- [Blocks API](blocks.md) - Block (time slot) management
- [Schedule API](schedule.md) - Schedule generation and validation
- [ACGME Compliance](../../architecture/acgme-compliance.md) - Compliance rules

---

*Last Updated: 2025-12-31*
