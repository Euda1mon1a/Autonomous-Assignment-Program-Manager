# API Endpoints Reference

This document provides detailed information about all available REST endpoints in the Residency Scheduler API.

## Table of Contents

- [Authentication](#authentication)
- [People](#people)
- [Blocks](#blocks)
- [Rotation Templates](#rotation-templates)
- [Absences](#absences)
- [Assignments](#assignments)
- [Schedule](#schedule)
- [Settings](#settings)
- [Export](#export)

---

## Authentication

Base path: `/api/auth`

### POST /api/auth/login

Authenticate with OAuth2 password flow (form data).

**Request Body (Form Data):**
```
username=admin
password=secret123
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Incorrect credentials

---

### POST /api/auth/login/json

Authenticate with JSON body (alternative to form-based login).

**Request Body:**
```json
{
  "username": "admin",
  "password": "secret123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized` - Incorrect credentials

---

### POST /api/auth/logout

Logout current user (client should discard token).

**Authentication:** Required

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /api/auth/me

Get current authenticated user information.

**Authentication:** Required

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true
}
```

**Error Responses:**
- `401 Unauthorized` - Not authenticated

---

### POST /api/auth/register

Register a new user. First user becomes admin automatically.

**Authentication:** Required for subsequent users (admin only)

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "securePassword123",
  "role": "coordinator"
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "newuser",
  "email": "newuser@example.com",
  "role": "coordinator",
  "is_active": true
}
```

**Error Responses:**
- `400 Bad Request` - Username or email already exists
- `403 Forbidden` - Non-admin trying to create user

---

### GET /api/auth/users

List all users (admin only).

**Authentication:** Required (admin role)

**Response (200):**
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  }
]
```

**Error Responses:**
- `403 Forbidden` - Non-admin access

---

## People

Base path: `/api/people`

### GET /api/people

List all people (residents and faculty).

**Query Parameters:**
- `type` (optional): Filter by type (`resident` or `faculty`)
- `pgy_level` (optional): Filter residents by PGY level (1, 2, or 3)

**Examples:**
```
GET /api/people
GET /api/people?type=resident
GET /api/people?type=resident&pgy_level=2
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Dr. Jane Smith",
      "type": "resident",
      "email": "jane.smith@example.com",
      "pgy_level": 2,
      "performs_procedures": false,
      "specialties": null,
      "primary_duty": null,
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

---

### GET /api/people/residents

List all residents with optional PGY level filter.

**Query Parameters:**
- `pgy_level` (optional): Filter by PGY level (1, 2, or 3)

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Dr. Jane Smith",
      "type": "resident",
      "email": "jane.smith@example.com",
      "pgy_level": 2,
      "performs_procedures": false,
      "specialties": null,
      "primary_duty": null,
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

---

### GET /api/people/faculty

List all faculty with optional specialty filter.

**Query Parameters:**
- `specialty` (optional): Filter by specialty

**Response (200):**
```json
{
  "items": [
    {
      "id": "456e7890-e89b-12d3-a456-426614174000",
      "name": "Dr. John Doe",
      "type": "faculty",
      "email": "john.doe@example.com",
      "pgy_level": null,
      "performs_procedures": true,
      "specialties": ["cardiology", "internal medicine"],
      "primary_duty": "teaching",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

---

### GET /api/people/{person_id}

Get a person by ID.

**Path Parameters:**
- `person_id` (UUID): Person identifier

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@example.com",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Person not found

---

### POST /api/people

Create a new person (resident or faculty).

**Authentication:** Required

**Request Body:**
```json
{
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@example.com",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@example.com",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `400 Bad Request` - PGY level required for residents
- `401 Unauthorized` - Not authenticated

---

### PUT /api/people/{person_id}

Update an existing person.

**Authentication:** Required

**Path Parameters:**
- `person_id` (UUID): Person identifier

**Request Body:**
```json
{
  "name": "Dr. Jane Smith",
  "email": "jane.smith@newemail.com",
  "pgy_level": 3
}
```

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@newemail.com",
  "pgy_level": 3,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-02T12:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Person not found

---

### DELETE /api/people/{person_id}

Delete a person.

**Authentication:** Required

**Path Parameters:**
- `person_id` (UUID): Person identifier

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Person not found

---

## Blocks

Base path: `/api/blocks`

Blocks represent time slots (AM/PM) for scheduling assignments.

### GET /api/blocks

List blocks with optional filters.

**Query Parameters:**
- `start_date` (optional): Filter blocks from this date (YYYY-MM-DD)
- `end_date` (optional): Filter blocks until this date (YYYY-MM-DD)
- `block_number` (optional): Filter by academic block number

**Examples:**
```
GET /api/blocks
GET /api/blocks?start_date=2024-01-01&end_date=2024-01-28
GET /api/blocks?block_number=1
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "date": "2024-01-01",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 1
}
```

---

### GET /api/blocks/{block_id}

Get a block by ID.

**Path Parameters:**
- `block_id` (UUID): Block identifier

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2024-01-01",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Error Responses:**
- `404 Not Found` - Block not found

---

### POST /api/blocks

Create a single block.

**Request Body:**
```json
{
  "date": "2024-01-01",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2024-01-01",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**Error Responses:**
- `400 Bad Request` - Block already exists for this date and time

---

### POST /api/blocks/generate

Generate blocks for a date range (creates AM and PM blocks for each day).

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)
- `base_block_number` (optional, default=1): Starting block number

**Example:**
```
POST /api/blocks/generate?start_date=2024-01-01&end_date=2024-01-28&base_block_number=1
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "date": "2024-01-01",
      "time_of_day": "AM",
      "block_number": 1,
      "is_weekend": false,
      "is_holiday": false,
      "holiday_name": null
    }
  ],
  "total": 56
}
```

---

### DELETE /api/blocks/{block_id}

Delete a block.

**Path Parameters:**
- `block_id` (UUID): Block identifier

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Block not found

---

## Rotation Templates

Base path: `/api/rotation-templates`

Rotation templates define the types of activities/rotations available for assignments.

### GET /api/rotation-templates

List all rotation templates.

**Query Parameters:**
- `activity_type` (optional): Filter by activity type

**Examples:**
```
GET /api/rotation-templates
GET /api/rotation-templates?activity_type=clinic
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Cardiology Clinic",
      "activity_type": "clinic",
      "abbreviation": "CARD",
      "clinic_location": "Building A",
      "max_residents": 4,
      "requires_specialty": null,
      "requires_procedure_credential": false,
      "supervision_required": true,
      "max_supervision_ratio": 4,
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

---

### GET /api/rotation-templates/{template_id}

Get a rotation template by ID.

**Path Parameters:**
- `template_id` (UUID): Template identifier

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Cardiology Clinic",
  "activity_type": "clinic",
  "abbreviation": "CARD",
  "clinic_location": "Building A",
  "max_residents": 4,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4,
  "created_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Template not found

---

### POST /api/rotation-templates

Create a new rotation template.

**Request Body:**
```json
{
  "name": "Cardiology Clinic",
  "activity_type": "clinic",
  "abbreviation": "CARD",
  "clinic_location": "Building A",
  "max_residents": 4,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Cardiology Clinic",
  "activity_type": "clinic",
  "abbreviation": "CARD",
  "clinic_location": "Building A",
  "max_residents": 4,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4,
  "created_at": "2024-01-01T12:00:00"
}
```

---

### PUT /api/rotation-templates/{template_id}

Update an existing rotation template.

**Path Parameters:**
- `template_id` (UUID): Template identifier

**Request Body:**
```json
{
  "name": "Cardiology Clinic - Updated",
  "max_residents": 6
}
```

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Cardiology Clinic - Updated",
  "activity_type": "clinic",
  "abbreviation": "CARD",
  "clinic_location": "Building A",
  "max_residents": 6,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4,
  "created_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Template not found

---

### DELETE /api/rotation-templates/{template_id}

Delete a rotation template.

**Path Parameters:**
- `template_id` (UUID): Template identifier

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Template not found

---

## Absences

Base path: `/api/absences`

Track resident and faculty absences (vacation, deployment, TDY, medical, etc.).

### GET /api/absences

List absences with optional filters.

**Query Parameters:**
- `start_date` (optional): Filter absences starting from (YYYY-MM-DD)
- `end_date` (optional): Filter absences ending by (YYYY-MM-DD)
- `person_id` (optional): Filter by person UUID
- `absence_type` (optional): Filter by absence type

**Examples:**
```
GET /api/absences
GET /api/absences?start_date=2024-01-01&end_date=2024-12-31
GET /api/absences?person_id=123e4567-e89b-12d3-a456-426614174000
GET /api/absences?absence_type=vacation
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "person_id": "456e7890-e89b-12d3-a456-426614174000",
      "start_date": "2024-02-01",
      "end_date": "2024-02-07",
      "absence_type": "vacation",
      "deployment_orders": false,
      "tdy_location": null,
      "replacement_activity": null,
      "notes": "Pre-planned vacation",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

---

### GET /api/absences/{absence_id}

Get an absence by ID.

**Path Parameters:**
- `absence_id` (UUID): Absence identifier

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "person_id": "456e7890-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Pre-planned vacation",
  "created_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Absence not found

---

### POST /api/absences

Create a new absence.

**Request Body:**
```json
{
  "person_id": "456e7890-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Pre-planned vacation"
}
```

**Absence Types:**
- `vacation` - Planned time off
- `deployment` - Military deployment
- `tdy` - Temporary duty assignment
- `medical` - Medical leave
- `family_emergency` - Family emergency
- `conference` - Conference attendance

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "person_id": "456e7890-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Pre-planned vacation",
  "created_at": "2024-01-01T12:00:00"
}
```

---

### PUT /api/absences/{absence_id}

Update an existing absence.

**Path Parameters:**
- `absence_id` (UUID): Absence identifier

**Request Body:**
```json
{
  "end_date": "2024-02-10",
  "notes": "Extended vacation"
}
```

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "person_id": "456e7890-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-10",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Extended vacation",
  "created_at": "2024-01-01T12:00:00"
}
```

**Error Responses:**
- `404 Not Found` - Absence not found

---

### DELETE /api/absences/{absence_id}

Delete an absence.

**Path Parameters:**
- `absence_id` (UUID): Absence identifier

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Absence not found

---

## Assignments

Base path: `/api/assignments`

Assignments link people to blocks with specific rotations and roles.

### GET /api/assignments

List assignments with optional filters.

**Authentication:** Required

**Query Parameters:**
- `start_date` (optional): Filter from this date (YYYY-MM-DD)
- `end_date` (optional): Filter until this date (YYYY-MM-DD)
- `person_id` (optional): Filter by person UUID
- `role` (optional): Filter by role (`primary`, `supervising`, `backup`)

**Examples:**
```
GET /api/assignments
GET /api/assignments?start_date=2024-01-01&end_date=2024-01-28
GET /api/assignments?person_id=123e4567-e89b-12d3-a456-426614174000
GET /api/assignments?role=primary
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "block_id": "456e7890-e89b-12d3-a456-426614174000",
      "person_id": "789e0123-e89b-12d3-a456-426614174000",
      "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
      "role": "primary",
      "activity_override": null,
      "notes": null,
      "override_reason": null,
      "created_by": "admin",
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00",
      "override_acknowledged_at": null
    }
  ],
  "total": 1
}
```

---

### GET /api/assignments/{assignment_id}

Get an assignment by ID.

**Authentication:** Required

**Path Parameters:**
- `assignment_id` (UUID): Assignment identifier

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "block_id": "456e7890-e89b-12d3-a456-426614174000",
  "person_id": "789e0123-e89b-12d3-a456-426614174000",
  "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": null,
  "created_by": "admin",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "override_acknowledged_at": null
}
```

**Error Responses:**
- `404 Not Found` - Assignment not found

---

### POST /api/assignments

Create a new assignment with ACGME validation.

**Authentication:** Required (scheduler role: admin or coordinator)

**Request Body:**
```json
{
  "block_id": "456e7890-e89b-12d3-a456-426614174000",
  "person_id": "789e0123-e89b-12d3-a456-426614174000",
  "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": "Approved by Program Director"
}
```

**Role Values:**
- `primary` - Primary assignee for the block
- `supervising` - Supervising faculty
- `backup` - Backup coverage

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "block_id": "456e7890-e89b-12d3-a456-426614174000",
  "person_id": "789e0123-e89b-12d3-a456-426614174000",
  "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": null,
  "created_by": "admin",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "override_acknowledged_at": null,
  "acgme_warnings": [
    "HIGH: Resident exceeds 80-hour work week average"
  ],
  "is_compliant": false
}
```

**Error Responses:**
- `400 Bad Request` - Person already assigned to this block
- `403 Forbidden` - Insufficient permissions

---

### PUT /api/assignments/{assignment_id}

Update an existing assignment with optimistic locking.

**Authentication:** Required (scheduler role: admin or coordinator)

**Path Parameters:**
- `assignment_id` (UUID): Assignment identifier

**Request Body:**
```json
{
  "role": "supervising",
  "notes": "Changed to supervising role",
  "override_reason": "Approved by Program Director",
  "updated_at": "2024-01-01T12:00:00"
}
```

**Note:** The `updated_at` field is required for optimistic locking to prevent concurrent modifications.

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "block_id": "456e7890-e89b-12d3-a456-426614174000",
  "person_id": "789e0123-e89b-12d3-a456-426614174000",
  "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
  "role": "supervising",
  "activity_override": null,
  "notes": "Changed to supervising role",
  "override_reason": null,
  "created_by": "admin",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:05:00",
  "override_acknowledged_at": null,
  "acgme_warnings": [],
  "is_compliant": true
}
```

**Error Responses:**
- `404 Not Found` - Assignment not found
- `409 Conflict` - Assignment modified by another user (optimistic locking)

---

### DELETE /api/assignments/{assignment_id}

Delete a single assignment.

**Authentication:** Required (scheduler role: admin or coordinator)

**Path Parameters:**
- `assignment_id` (UUID): Assignment identifier

**Response (204):** No content

**Error Responses:**
- `404 Not Found` - Assignment not found

---

### DELETE /api/assignments

Bulk delete assignments in a date range.

**Authentication:** Required (scheduler role: admin or coordinator)

**Query Parameters:**
- `start_date` (required): Delete assignments from this date (YYYY-MM-DD)
- `end_date` (required): Delete assignments until this date (YYYY-MM-DD)

**Example:**
```
DELETE /api/assignments?start_date=2024-01-01&end_date=2024-01-28
```

**Response (200):**
```json
{
  "deleted": 150
}
```

---

## Schedule

Base path: `/api/schedule`

Schedule generation, validation, and emergency coverage endpoints.

### POST /api/schedule/generate

Generate a schedule for a date range using constraint-based optimization.

**Authentication:** Required

**Request Body:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-28",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": null,
  "algorithm": "greedy",
  "timeout_seconds": 60.0
}
```

**Algorithm Options:**
- `greedy` - Fast heuristic, good for initial solutions
- `cp_sat` - OR-Tools constraint programming, optimal solutions
- `pulp` - PuLP linear programming, fast for large problems
- `hybrid` - Combines CP-SAT and PuLP for best results

**Response (200 or 207):**
```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 150,
  "total_blocks": 160,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 93.75,
    "statistics": {}
  },
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "solver_stats": {
    "total_blocks": 160,
    "total_residents": 12,
    "coverage_rate": 93.75,
    "branches": 1024,
    "conflicts": 45
  },
  "acgme_override_count": 0
}
```

**Status Codes:**
- `200 OK` - Complete success
- `207 Multi-Status` - Partial success (some assignments with warnings)
- `409 Conflict` - Schedule generation already in progress
- `422 Unprocessable Entity` - Validation error or failure

---

### GET /api/schedule/validate

Validate current schedule for ACGME compliance.

**Query Parameters:**
- `start_date` (required): Start date (YYYY-MM-DD)
- `end_date` (required): End date (YYYY-MM-DD)

**Example:**
```
GET /api/schedule/validate?start_date=2024-01-01&end_date=2024-01-28
```

**Response (200):**
```json
{
  "valid": true,
  "total_violations": 0,
  "violations": [],
  "coverage_rate": 93.75,
  "statistics": {
    "total_residents": 12,
    "total_blocks": 160,
    "avg_hours_per_week": 68.5
  }
}
```

**Violations Example:**
```json
{
  "valid": false,
  "total_violations": 2,
  "violations": [
    {
      "type": "80_HOUR",
      "severity": "CRITICAL",
      "person_id": "123e4567-e89b-12d3-a456-426614174000",
      "person_name": "Dr. Jane Smith",
      "block_id": null,
      "message": "Resident exceeds 80-hour work week average",
      "details": {
        "avg_hours": 85.5,
        "week_range": "2024-01-08 to 2024-02-04"
      }
    }
  ],
  "coverage_rate": 93.75,
  "statistics": {}
}
```

**Violation Types:**
- `80_HOUR` - Exceeds 80-hour weekly average (4-week rolling)
- `1_IN_7` - Missing 1-in-7 days off requirement
- `SUPERVISION_RATIO` - Inadequate supervision ratio

**Severity Levels:**
- `CRITICAL` - Immediate attention required
- `HIGH` - Should be addressed soon
- `MEDIUM` - Minor concern
- `LOW` - Informational

---

### POST /api/schedule/emergency-coverage

Handle emergency absence and find replacement coverage.

**Authentication:** Required

**Request Body:**
```json
{
  "person_id": "123e4567-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-15",
  "end_date": "2024-02-20",
  "reason": "Family emergency",
  "is_deployment": false
}
```

**Response (200):**
```json
{
  "status": "success",
  "replacements_found": 8,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2024-02-15",
      "time_of_day": "AM",
      "original_person": "Dr. Jane Smith",
      "replacement_person": "Dr. John Doe",
      "rotation": "Cardiology Clinic"
    }
  ]
}
```

---

### GET /api/schedule/{start_date}/{end_date}

Get the schedule for a date range.

**Path Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)

**Example:**
```
GET /api/schedule/2024-01-01/2024-01-28
```

**Response (200):**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-28",
  "schedule": {
    "2024-01-01": {
      "AM": [
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "person": {
            "id": "456e7890-e89b-12d3-a456-426614174000",
            "name": "Dr. Jane Smith",
            "type": "resident",
            "pgy_level": 2
          },
          "role": "primary",
          "activity": "Cardiology Clinic",
          "abbreviation": "CARD"
        }
      ],
      "PM": []
    }
  },
  "total_assignments": 150
}
```

---

## Settings

Base path: `/api/settings`

Manage application-wide settings for scheduling and ACGME compliance.

### GET /api/settings

Get current application settings.

**Response (200):**
```json
{
  "scheduling_algorithm": "greedy",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

---

### POST /api/settings

Update application settings (full replacement).

**Request Body:**
```json
{
  "scheduling_algorithm": "cp_sat",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

**Response (200):**
```json
{
  "scheduling_algorithm": "cp_sat",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

---

### PATCH /api/settings

Partially update application settings.

**Request Body:**
```json
{
  "scheduling_algorithm": "hybrid",
  "work_hours_per_week": 75
}
```

**Response (200):**
```json
{
  "scheduling_algorithm": "hybrid",
  "work_hours_per_week": 75,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

---

### DELETE /api/settings

Reset settings to defaults.

**Response (204):** No content

---

## Export

Base path: `/api/export`

Export data in various formats (CSV, JSON, Excel).

### GET /api/export/people

Export all people data.

**Query Parameters:**
- `format` (optional, default=csv): Export format (`csv` or `json`)

**Examples:**
```
GET /api/export/people
GET /api/export/people?format=json
```

**Response (200):**
- CSV file download for `format=csv`
- JSON file download for `format=json`

---

### GET /api/export/absences

Export absences data.

**Query Parameters:**
- `format` (optional, default=csv): Export format (`csv` or `json`)
- `start_date` (optional): Filter absences starting from (YYYY-MM-DD)
- `end_date` (optional): Filter absences ending by (YYYY-MM-DD)

**Examples:**
```
GET /api/export/absences
GET /api/export/absences?format=json&start_date=2024-01-01&end_date=2024-12-31
```

**Response (200):**
- CSV or JSON file download

---

### GET /api/export/schedule

Export schedule data for a date range.

**Query Parameters:**
- `format` (optional, default=csv): Export format (`csv` or `json`)
- `start_date` (required): Schedule start date (YYYY-MM-DD)
- `end_date` (required): Schedule end date (YYYY-MM-DD)

**Examples:**
```
GET /api/export/schedule?start_date=2024-01-01&end_date=2024-01-28
GET /api/export/schedule?format=json&start_date=2024-01-01&end_date=2024-01-28
```

**Response (200):**
- CSV or JSON file download

---

### GET /api/export/schedule/xlsx

Export schedule in legacy Excel format with formatting.

**Query Parameters:**
- `start_date` (required): Schedule start date (YYYY-MM-DD)
- `end_date` (required): Schedule end date (YYYY-MM-DD)
- `block_number` (optional): Block number for header (auto-calculated if not provided)
- `federal_holidays` (optional): Comma-separated holiday dates (YYYY-MM-DD)

**Example:**
```
GET /api/export/schedule/xlsx?start_date=2024-01-01&end_date=2024-01-28&block_number=1&federal_holidays=2024-01-15,2024-01-16
```

**Response (200):**
- Excel (.xlsx) file download with color-coded formatting

**Error Responses:**
- `400 Bad Request` - Invalid date format in parameters
- `500 Internal Server Error` - Failed to generate Excel file
