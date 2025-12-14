# API Reference

## Document Purpose

Complete API documentation for the Residency Scheduler backend. All endpoints are prefixed with `/api`.

**Author:** Opus 4.5 (Opus-Docs)
**Status:** APPROVED FOR IMPLEMENTATION
**Last Updated:** 2024-12-14
**Base URL:** `http://localhost:8000/api`

---

## Table of Contents

1. [Overview](#overview)
2. [People API](#people-api)
3. [Blocks API](#blocks-api)
4. [Rotation Templates API](#rotation-templates-api)
5. [Assignments API](#assignments-api)
6. [Absences API](#absences-api)
7. [Schedule API](#schedule-api)
8. [Common Response Formats](#common-response-formats)

---

## Overview

### Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

### Authentication

All endpoints (except health checks) require authentication via JWT tokens stored in HttpOnly cookies. See [AUTH_ARCHITECTURE.md](./AUTH_ARCHITECTURE.md) for details.

### Common Headers

```http
Content-Type: application/json
PGY2-01ie: access_token=<jwt>
```

### Health Check Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Basic health check |
| GET | `/health` | Detailed health status |

---

## People API

Base path: `/api/people`

Manages residents and faculty members.

### List All People

```http
GET /api/people
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `resident` or `faculty` |
| `pgy_level` | integer | No | Filter residents by PGY level (1, 2, or 3) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. Jane Smith",
      "type": "resident",
      "email": "jane.smith@hospital.org",
      "pgy_level": 2,
      "performs_procedures": false,
      "specialties": null,
      "primary_duty": null,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### List Residents

```http
GET /api/people/residents
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) |

**Response:** `200 OK` - Same format as List All People

### List Faculty

```http
GET /api/people/faculty
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `specialty` | string | No | Filter by specialty |

**Response:** `200 OK` - Same format as List All People

### Get Person

```http
GET /api/people/{person_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person's unique identifier |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@hospital.org",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Person not found

### Create Person

```http
POST /api/people
```

**Request Body:**

```json
{
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@hospital.org",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | Max 255 characters |
| `type` | string | Yes | `resident` or `faculty` |
| `email` | string | No | Valid email format, unique |
| `pgy_level` | integer | Yes (residents) | 1, 2, or 3 |
| `performs_procedures` | boolean | No | Default: false |
| `specialties` | string[] | No | Array of specialty names |
| `primary_duty` | string | No | Max 255 characters |

**Response:** `201 Created`

**Errors:**
- `400 Bad Request` - PGY level required for residents
- `400 Bad Request` - Validation error

### Update Person

```http
PUT /api/people/{person_id}
```

**Request Body:** (all fields optional)

```json
{
  "name": "Dr. Jane Smith-Jones",
  "email": "jane.smith-jones@hospital.org",
  "pgy_level": 3
}
```

**Response:** `200 OK` - Updated person object

**Errors:**
- `404 Not Found` - Person not found

### Delete Person

```http
DELETE /api/people/{person_id}
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Person not found

---

## Blocks API

Base path: `/api/blocks`

Manages schedule blocks (AM/PM time slots).

### List Blocks

```http
GET /api/blocks
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter blocks from this date (YYYY-MM-DD) |
| `end_date` | date | No | Filter blocks until this date (YYYY-MM-DD) |
| `block_number` | integer | No | Filter by academic block number |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "date": "2024-01-15",
      "time_of_day": "AM",
      "block_number": 5,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 1
}
```

### Get Block

```http
GET /api/blocks/{block_id}
```

**Response:** `200 OK` - Block object

**Errors:**
- `404 Not Found` - Block not found

### Create Block

```http
POST /api/blocks
```

**Request Body:**

```json
{
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 5,
  "is_weekend": false,
  "is_holiday": false
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `date` | date | Yes | YYYY-MM-DD format |
| `time_of_day` | string | Yes | `AM` or `PM` |
| `block_number` | integer | Yes | Academic block number |
| `is_weekend` | boolean | No | Default: false |
| `is_holiday` | boolean | No | Default: false |

**Response:** `201 Created`

**Errors:**
- `400 Bad Request` - Block already exists for this date and time

### Generate Blocks

```http
POST /api/blocks/generate
```

Generates AM and PM blocks for a date range (730 blocks per year).

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |
| `base_block_number` | integer | No | Starting block number (default: 1) |

**Response:** `200 OK`

```json
{
  "items": [...],
  "total": 730
}
```

### Delete Block

```http
DELETE /api/blocks/{block_id}
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Block not found

---

## Rotation Templates API

Base path: `/api/rotation-templates`

Manages rotation templates (clinic types, activities).

### List Rotation Templates

```http
GET /api/rotation-templates
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `activity_type` | string | No | Filter by activity type |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "name": "Sports Medicine Clinic",
      "activity_type": "clinic",
      "abbreviation": "SM",
      "clinic_location": "Building A, Room 102",
      "max_residents": 4,
      "requires_specialty": "Sports Medicine",
      "requires_procedure_credential": false,
      "supervision_required": true,
      "max_supervision_ratio": 4,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Rotation Template

```http
GET /api/rotation-templates/{template_id}
```

**Response:** `200 OK` - Template object

**Errors:**
- `404 Not Found` - Rotation template not found

### Create Rotation Template

```http
POST /api/rotation-templates
```

**Request Body:**

```json
{
  "name": "Sports Medicine Clinic",
  "activity_type": "clinic",
  "abbreviation": "SM",
  "clinic_location": "Building A, Room 102",
  "max_residents": 4,
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique template name |
| `activity_type` | string | Yes | `clinic`, `inpatient`, `procedure`, `conference` |
| `abbreviation` | string | No | Short code for display |
| `clinic_location` | string | No | Physical location |
| `max_residents` | integer | No | Maximum residents per session |
| `requires_specialty` | string | No | Required faculty specialty |
| `requires_procedure_credential` | boolean | No | Default: false |
| `supervision_required` | boolean | No | Default: true |
| `max_supervision_ratio` | integer | No | Default: 4 (1:4 ratio) |

**Response:** `201 Created`

### Update Rotation Template

```http
PUT /api/rotation-templates/{template_id}
```

**Request Body:** (all fields optional)

**Response:** `200 OK` - Updated template object

**Errors:**
- `404 Not Found` - Rotation template not found

### Delete Rotation Template

```http
DELETE /api/rotation-templates/{template_id}
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Rotation template not found

---

## Assignments API

Base path: `/api/assignments`

Manages person assignments to schedule blocks.

### List Assignments

```http
GET /api/assignments
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter from this date (YYYY-MM-DD) |
| `end_date` | date | No | Filter until this date (YYYY-MM-DD) |
| `person_id` | UUID | No | Filter by person |
| `role` | string | No | Filter by role: `primary`, `supervising`, `backup` |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440000",
      "block_id": "660e8400-e29b-41d4-a716-446655440000",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
      "role": "primary",
      "activity_override": null,
      "notes": null,
      "created_by": "system",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Assignment

```http
GET /api/assignments/{assignment_id}
```

**Response:** `200 OK` - Assignment object

**Errors:**
- `404 Not Found` - Assignment not found

### Create Assignment

```http
POST /api/assignments
```

**Request Body:**

```json
{
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "primary",
  "activity_override": null,
  "notes": "Coverage for Dr. Jones",
  "created_by": "coordinator@hospital.org"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `block_id` | UUID | Yes | Must exist |
| `person_id` | UUID | Yes | Must exist |
| `rotation_template_id` | UUID | No | Template reference |
| `role` | string | Yes | `primary`, `supervising`, or `backup` |
| `activity_override` | string | No | Override template activity name |
| `notes` | string | No | Assignment notes |
| `created_by` | string | No | Who created the assignment |

**Response:** `201 Created`

**Errors:**
- `400 Bad Request` - Person already assigned to this block

### Update Assignment

```http
PUT /api/assignments/{assignment_id}
```

**Request Body:** (all fields optional)

```json
{
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440001",
  "role": "backup",
  "notes": "Reassigned due to conflict"
}
```

**Response:** `200 OK` - Updated assignment object

**Errors:**
- `404 Not Found` - Assignment not found

### Delete Assignment

```http
DELETE /api/assignments/{assignment_id}
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Assignment not found

### Bulk Delete Assignments

```http
DELETE /api/assignments
```

Deletes all assignments in a date range.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Delete from this date (YYYY-MM-DD) |
| `end_date` | date | Yes | Delete until this date (YYYY-MM-DD) |

**Response:** `200 OK`

```json
{
  "deleted": 156
}
```

---

## Absences API

Base path: `/api/absences`

Manages person absences (vacation, deployment, TDY, etc.).

### List Absences

```http
GET /api/absences
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter absences starting from (YYYY-MM-DD) |
| `end_date` | date | No | Filter absences ending by (YYYY-MM-DD) |
| `person_id` | UUID | No | Filter by person |
| `absence_type` | string | No | Filter by type |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "start_date": "2024-02-01",
      "end_date": "2024-02-15",
      "absence_type": "deployment",
      "deployment_orders": true,
      "tdy_location": null,
      "replacement_activity": null,
      "notes": "Annual training deployment",
      "created_at": "2024-01-15T00:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Absence

```http
GET /api/absences/{absence_id}
```

**Response:** `200 OK` - Absence object

**Errors:**
- `404 Not Found` - Absence not found

### Create Absence

```http
POST /api/absences
```

**Request Body:**

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-15",
  "absence_type": "deployment",
  "deployment_orders": true,
  "tdy_location": null,
  "notes": "Annual training deployment"
}
```

**Valid Absence Types:**
- `vacation`
- `deployment`
- `tdy`
- `medical`
- `family_emergency`
- `conference`

**Response:** `201 Created`

### Update Absence

```http
PUT /api/absences/{absence_id}
```

**Request Body:** (all fields optional)

**Response:** `200 OK` - Updated absence object

**Errors:**
- `404 Not Found` - Absence not found

### Delete Absence

```http
DELETE /api/absences/{absence_id}
```

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - Absence not found

---

## Schedule API

Base path: `/api/schedule`

Schedule generation, validation, and retrieval.

### Generate Schedule

```http
POST /api/schedule/generate
```

Generates assignments for a date range using the scheduling engine.

**Request Body:**

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": [
    "770e8400-e29b-41d4-a716-446655440000"
  ],
  "algorithm": "greedy"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `start_date` | date | Yes | YYYY-MM-DD format |
| `end_date` | date | Yes | Must be > start_date |
| `pgy_levels` | integer[] | No | Filter residents by PGY level |
| `rotation_template_ids` | UUID[] | No | Specific templates to schedule |
| `algorithm` | string | No | `greedy`, `min_conflicts`, or `cp_sat` (default: `greedy`) |

**Response:** `200 OK`

```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 2920,
  "total_blocks": 3650,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 80.0,
    "statistics": {
      "total_assignments": 2920,
      "total_blocks": 3650,
      "residents_scheduled": 24
    }
  },
  "run_id": "aa0e8400-e29b-41d4-a716-446655440000"
}
```

**Status Values:**
- `success` - All blocks assigned, no violations
- `partial` - Some blocks unassigned or violations present
- `failed` - Critical error during generation

### Validate Schedule

```http
GET /api/schedule/validate
```

Validates current schedule for ACGME compliance.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |

**Response:** `200 OK`

```json
{
  "valid": false,
  "total_violations": 2,
  "violations": [
    {
      "type": "80_HOUR_VIOLATION",
      "severity": "CRITICAL",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "person_name": "Dr. Jane Smith",
      "message": "Dr. Jane Smith: 82.5 hours/week (limit: 80)",
      "details": {
        "window_start": "2024-01-01",
        "window_end": "2024-01-28",
        "average_weekly_hours": 82.5
      }
    }
  ],
  "coverage_rate": 95.5,
  "statistics": {
    "total_assignments": 3500,
    "total_blocks": 3650,
    "residents_scheduled": 24
  }
}
```

**Violation Types:**
- `80_HOUR_VIOLATION` - Resident exceeds 80 hours/week average
- `1_IN_7_VIOLATION` - Resident missing required days off
- `SUPERVISION_RATIO_VIOLATION` - Insufficient faculty supervision

### Get Schedule

```http
GET /api/schedule/{start_date}/{end_date}
```

Retrieves the schedule for a date range, formatted for calendar view.

**Response:** `200 OK`

```json
{
  "start_date": "2024-01-15",
  "end_date": "2024-01-16",
  "schedule": {
    "2024-01-15": {
      "AM": [
        {
          "id": "880e8400-e29b-41d4-a716-446655440000",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Dr. Jane Smith",
            "type": "resident",
            "pgy_level": 2
          },
          "role": "primary",
          "activity": "Sports Medicine Clinic",
          "abbreviation": "SM"
        }
      ],
      "PM": []
    }
  },
  "total_assignments": 1
}
```

### Handle Emergency Coverage

```http
POST /api/schedule/emergency-coverage
```

Handles emergency absence and finds replacement coverage.

**Request Body:**

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-01-20",
  "end_date": "2024-01-25",
  "reason": "Family emergency",
  "is_deployment": false
}
```

**Response:** `200 OK`

```json
{
  "status": "partial",
  "replacements_found": 8,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2024-01-20",
      "time_of_day": "AM",
      "original_assignment": "Sports Medicine Clinic",
      "replacement": {
        "person_id": "550e8400-e29b-41d4-a716-446655440002",
        "person_name": "Dr. Bob Wilson"
      },
      "status": "covered"
    }
  ]
}
```

---

## Common Response Formats

### Pagination

List endpoints return paginated results:

```json
{
  "items": [...],
  "total": 100
}
```

### Error Response

All errors follow this format:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [...],
  "timestamp": "2024-12-14T10:30:00.000Z",
  "trace_id": "abc123"
}
```

See [ERROR_HANDLING.md](./ERROR_HANDLING.md) for complete error documentation.

### Date Formats

- All dates use ISO 8601 format: `YYYY-MM-DD`
- All timestamps use ISO 8601 with timezone: `YYYY-MM-DDTHH:MM:SSZ`

### UUID Format

All IDs use UUID v4 format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

---

*End of API Reference Document*
