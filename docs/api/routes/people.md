# People API

Complete reference for the `/api/v1/people` endpoints.

> **Base Path:** `/api/v1/people`
> **Authentication:** Required (Bearer token)
> **Source:** `backend/app/api/routes/people.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Schemas](#schemas)
4. [Examples](#examples)
5. [Error Handling](#error-handling)

---

## Overview

The People API manages residents and faculty members in the residency program. This includes basic information, role assignments, credentials, and procedure qualifications.

### Key Features

- **Type-Based Filtering**: Separate endpoints for residents and faculty
- **PGY Level Support**: Filter residents by training year (PGY-1, PGY-2, PGY-3)
- **Specialty Tracking**: Faculty specialty information for scheduling
- **Credential Integration**: View credentials and qualified procedures
- **Call Equity Tracking**: Read-only counters for Sunday/weekday call and FMIT weeks

---

## Endpoints

### List People

```http
GET /api/v1/people
```

List all people (residents and faculty) with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `type` | string | No | - | Filter by type: `resident` or `faculty` |
| `pgy_level` | int | No | - | Filter residents by PGY level (1, 2, or 3) |

**Response:** `PersonListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Invalid query parameters

---

### List Residents

```http
GET /api/v1/people/residents
```

List all residents, optionally filtered by PGY level.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `pgy_level` | int | No | - | Filter by PGY level (1, 2, or 3) |

**Response:** `PersonListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication

---

### List Faculty

```http
GET /api/v1/people/faculty
```

List all faculty, optionally filtered by specialty.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `specialty` | string | No | - | Filter by specialty (e.g., "Sports Medicine", "Primary Care") |

**Response:** `PersonListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication

---

### Get Person

```http
GET /api/v1/people/{person_id}
```

Get a single person by ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Response:** `PersonResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

---

### Create Person

```http
POST /api/v1/people
```

Create a new person (resident or faculty).

**Authorization:** Required (authenticated user)

**Request Body:** `PersonCreate`

**Response:** `PersonResponse` (201 Created)

**Status Codes:**
- `201 Created`: Person created successfully
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Validation failure

---

### Update Person

```http
PUT /api/v1/people/{person_id}
```

Update an existing person.

**Authorization:** Required (authenticated user)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Request Body:** `PersonUpdate`

**Response:** `PersonResponse`

**Status Codes:**
- `200 OK`: Person updated successfully
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found
- `422 Unprocessable Entity`: Validation failure

---

### Delete Person

```http
DELETE /api/v1/people/{person_id}
```

Delete a person.

**Authorization:** Required (authenticated user)

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Status Codes:**
- `204 No Content`: Person deleted successfully
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

---

### Get Person Credentials

```http
GET /api/v1/people/{person_id}/credentials
```

Get all credentials for a faculty member.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | - | Filter by status (`active`, `suspended`, `expired`) |
| `include_expired` | bool | No | false | Include expired credentials |

**Response:** `CredentialListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

---

### Get Person Credential Summary

```http
GET /api/v1/people/{person_id}/credentials/summary
```

Get a summary of a faculty member's credentials.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Response:** `FacultyCredentialSummary`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

---

### Get Person Procedures

```http
GET /api/v1/people/{person_id}/procedures
```

Get all procedures a faculty member is qualified to supervise.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person ID |

**Response:** `ProcedureListResponse`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

---

## Schemas

### PersonCreate

```json
{
  "name": "Dr. Jane Smith",
  "type": "faculty",
  "email": "jane.smith@example.com",
  "pgy_level": null,
  "performs_procedures": true,
  "specialties": ["Primary Care", "Sports Medicine"],
  "primary_duty": "Clinical",
  "faculty_role": "core"
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full name |
| `type` | string | Yes | Type: `resident` or `faculty` |
| `email` | string | No | Email address |
| `pgy_level` | int | No | PGY level (1-3) for residents only |
| `performs_procedures` | bool | No | Whether person performs procedures (default: false) |
| `specialties` | array[string] | No | List of specialties (faculty only) |
| `primary_duty` | string | No | Primary duty description |
| `faculty_role` | string | No | Faculty role: `pd`, `apd`, `oic`, `dept_chief`, `sports_med`, `core`, `adjunct` |

---

### PersonUpdate

All fields are optional. Omitted fields remain unchanged.

```json
{
  "name": "Dr. Jane Smith-Johnson",
  "email": "jane.smith-johnson@example.com",
  "specialties": ["Primary Care", "Sports Medicine", "Preventive Medicine"]
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Full name |
| `email` | string | No | Email address |
| `pgy_level` | int | No | PGY level (1-3) for residents |
| `performs_procedures` | bool | No | Whether person performs procedures |
| `specialties` | array[string] | No | List of specialties |
| `primary_duty` | string | No | Primary duty description |
| `faculty_role` | string | No | Faculty role |

---

### PersonResponse

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Dr. Jane Smith",
  "type": "faculty",
  "email": "jane.smith@example.com",
  "pgy_level": null,
  "performs_procedures": true,
  "specialties": ["Primary Care", "Sports Medicine"],
  "primary_duty": "Clinical",
  "faculty_role": "core",
  "created_at": "2024-07-01T08:00:00Z",
  "updated_at": "2024-07-01T08:00:00Z",
  "sunday_call_count": 3,
  "weekday_call_count": 12,
  "fmit_weeks_count": 6
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Person ID |
| `name` | string | Full name |
| `type` | string | Type: `resident` or `faculty` |
| `email` | string | Email address |
| `pgy_level` | int | PGY level (residents only) |
| `performs_procedures` | bool | Whether person performs procedures |
| `specialties` | array[string] | List of specialties (faculty only) |
| `primary_duty` | string | Primary duty description |
| `faculty_role` | string | Faculty role |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |
| `sunday_call_count` | int | Count of Sunday call assignments (read-only) |
| `weekday_call_count` | int | Count of Mon-Thu call assignments (read-only) |
| `fmit_weeks_count` | int | Count of FMIT weeks assigned (read-only) |

---

### PersonListResponse

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. Jane Smith",
      "type": "faculty",
      // ... (all PersonResponse fields) ...
    }
  ],
  "total": 25
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `items` | array[PersonResponse] | Person items |
| `total` | int | Total count of people |

---

### Faculty Roles

| Role | Description |
|------|-------------|
| `pd` | Program Director |
| `apd` | Associate Program Director |
| `oic` | Officer in Charge |
| `dept_chief` | Department Chief |
| `sports_med` | Sports Medicine Faculty |
| `core` | Core Faculty |
| `adjunct` | Adjunct Faculty |

---

## Examples

### List All Residents by PGY Level

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/people/residents?pgy_level=2" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "PGY2-01",
      "type": "resident",
      "email": "pgy2-01@example.com",
      "pgy_level": 2,
      "performs_procedures": false,
      "specialties": null,
      "primary_duty": "Training",
      "faculty_role": null,
      "created_at": "2024-07-01T08:00:00Z",
      "updated_at": "2024-07-01T08:00:00Z",
      "sunday_call_count": 0,
      "weekday_call_count": 0,
      "fmit_weeks_count": 0
    }
  ],
  "total": 8
}
```

---

### List Faculty by Specialty

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/people/faculty?specialty=Sports%20Medicine" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Dr. Sports Med",
      "type": "faculty",
      "email": "sports.med@example.com",
      "pgy_level": null,
      "performs_procedures": true,
      "specialties": ["Sports Medicine", "Primary Care"],
      "primary_duty": "Clinical",
      "faculty_role": "sports_med",
      "created_at": "2024-07-01T08:00:00Z",
      "updated_at": "2024-07-01T08:00:00Z",
      "sunday_call_count": 2,
      "weekday_call_count": 10,
      "fmit_weeks_count": 5
    }
  ],
  "total": 1
}
```

---

### Create Faculty Member

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/people" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. New Faculty",
    "type": "faculty",
    "email": "new.faculty@example.com",
    "performs_procedures": true,
    "specialties": ["Primary Care"],
    "faculty_role": "core"
  }'
```

**Response (201 Created):**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "name": "Dr. New Faculty",
  "type": "faculty",
  "email": "new.faculty@example.com",
  "pgy_level": null,
  "performs_procedures": true,
  "specialties": ["Primary Care"],
  "primary_duty": null,
  "faculty_role": "core",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z",
  "sunday_call_count": 0,
  "weekday_call_count": 0,
  "fmit_weeks_count": 0
}
```

---

### Create Resident

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/people" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PGY1-05",
    "type": "resident",
    "email": "pgy1-05@example.com",
    "pgy_level": 1,
    "primary_duty": "Training"
  }'
```

**Response (201 Created):**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "name": "PGY1-05",
  "type": "resident",
  "email": "pgy1-05@example.com",
  "pgy_level": 1,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": "Training",
  "faculty_role": null,
  "created_at": "2025-01-15T10:35:00Z",
  "updated_at": "2025-01-15T10:35:00Z",
  "sunday_call_count": 0,
  "weekday_call_count": 0,
  "fmit_weeks_count": 0
}
```

---

### Update Person

**Request:**

```bash
curl -X PUT "http://localhost:8000/api/v1/people/880e8400-e29b-41d4-a716-446655440003" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "specialties": ["Primary Care", "Preventive Medicine"],
    "faculty_role": "apd"
  }'
```

**Response (200 OK):**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "name": "Dr. New Faculty",
  "type": "faculty",
  "email": "new.faculty@example.com",
  "pgy_level": null,
  "performs_procedures": true,
  "specialties": ["Primary Care", "Preventive Medicine"],
  "primary_duty": null,
  "faculty_role": "apd",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:40:00Z",
  "sunday_call_count": 0,
  "weekday_call_count": 0,
  "fmit_weeks_count": 0
}
```

---

### Get Person Credentials

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/people/880e8400-e29b-41d4-a716-446655440003/credentials" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "person_id": "880e8400-e29b-41d4-a716-446655440003",
      "procedure_id": "bb0e8400-e29b-41d4-a716-446655440006",
      "status": "active",
      "granted_at": "2024-07-01T00:00:00Z",
      "expires_at": "2026-07-01T00:00:00Z",
      "is_verified": true
    }
  ],
  "total": 12
}
```

---

### Get Person Procedures

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/people/880e8400-e29b-41d4-a716-446655440003/procedures" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "items": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "name": "Joint Injection",
      "specialty": "Sports Medicine",
      "category": "Musculoskeletal",
      "is_active": true
    }
  ],
  "total": 15
}
```

---

## Error Handling

### 422 Unprocessable Entity - Invalid Type

```json
{
  "detail": [
    {
      "loc": ["body", "type"],
      "msg": "type must be 'resident' or 'faculty'",
      "type": "value_error"
    }
  ]
}
```

**Cause:** Invalid `type` field value.

**Resolution:** Use `resident` or `faculty`.

---

### 422 Unprocessable Entity - Invalid PGY Level

```json
{
  "detail": [
    {
      "loc": ["body", "pgy_level"],
      "msg": "pgy_level must be between 1 and 3",
      "type": "value_error"
    }
  ]
}
```

**Cause:** PGY level outside valid range (1-3).

**Resolution:** Use PGY level 1, 2, or 3.

---

### 404 Not Found

```json
{
  "detail": "Person not found"
}
```

**Cause:** Person ID does not exist.

**Resolution:** Verify the person ID.

---

## Related Documentation

- [Assignments API](assignments.md) - Schedule assignments
- [Credentials API](../ENDPOINT_CATALOG.md#credentials) - Credential management
- [Procedures API](../ENDPOINT_CATALOG.md#procedures) - Procedure definitions
- [Call Assignments API](call_assignments.md) - Call assignment management

---

*Last Updated: 2025-12-31*
