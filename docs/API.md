# Residency Scheduler API Documentation

Complete API reference with curl examples for the Residency Scheduler backend.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [People API](#people-api)
4. [Rotation Templates API](#rotation-templates-api)
5. [Absences API](#absences-api)
6. [Schedule API](#schedule-api)
7. [Error Handling](#error-handling)

---

## Overview

### Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

### Authentication

The API uses JWT Bearer token authentication. Obtain a token via the login endpoint and include it in the `Authorization` header for protected endpoints.

```bash
Authorization: Bearer <your_jwt_token>
```

### Response Format

All successful responses return JSON. List endpoints return:

```json
{
  "items": [...],
  "total": 100
}
```

### Health Check Endpoints

```bash
# Basic health check
curl http://localhost:8000/

# Response:
# {
#   "name": "Residency Scheduler API",
#   "version": "1.0.0",
#   "status": "healthy"
# }

# Detailed health check
curl http://localhost:8000/health

# Response:
# {
#   "status": "healthy",
#   "database": "connected"
# }
```

---

## Authentication

Base path: `/api/auth`

### Register User

Creates a new user account. The first user registered automatically becomes an admin.

**Endpoint:** `POST /api/auth/register`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | User password |
| `role` | string | No | User role: `admin`, `coordinator`, or `faculty` |

```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john.doe@hospital.org",
    "password": "SecurePassword123!",
    "role": "coordinator"
  }'

# Response (201 Created):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "username": "john.doe",
#   "email": "john.doe@hospital.org",
#   "role": "coordinator",
#   "is_active": true
# }
```

### Login (Form Data - OAuth2)

Authenticates user and returns JWT token using OAuth2 password flow.

**Endpoint:** `POST /api/auth/login`

```bash
# Login with form data (OAuth2 flow)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe&password=SecurePassword123!"

# Response (200 OK):
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

### Login (JSON)

Authenticates user using JSON request body.

**Endpoint:** `POST /api/auth/login/json`

```bash
# Login with JSON body
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'

# Response (200 OK):
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

### Get Current User

Returns the authenticated user's information.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required

```bash
# Get current user info
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_jwt_token>"

# Response (200 OK):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "username": "john.doe",
#   "email": "john.doe@hospital.org",
#   "role": "coordinator",
#   "is_active": true
# }
```

### Logout

Logs out the current user (invalidates the session).

**Endpoint:** `POST /api/auth/logout`

**Authentication:** Required

```bash
# Logout current user
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <your_jwt_token>"

# Response (200 OK):
# {
#   "message": "Successfully logged out"
# }
```

### List Users (Admin Only)

Returns all users in the system.

**Endpoint:** `GET /api/auth/users`

**Authentication:** Required (Admin role)

```bash
# List all users (admin only)
curl http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <admin_jwt_token>"

# Response (200 OK):
# [
#   {
#     "id": "550e8400-e29b-41d4-a716-446655440000",
#     "username": "john.doe",
#     "email": "john.doe@hospital.org",
#     "role": "coordinator",
#     "is_active": true
#   }
# ]
```

---

## People API

Base path: `/api/people`

Manages residents and faculty members.

### List All People

Returns all people with optional filtering.

**Endpoint:** `GET /api/people`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `resident` or `faculty` |
| `pgy_level` | integer | No | Filter residents by PGY level (1-3) |

```bash
# List all people
curl http://localhost:8000/api/people

# List only residents
curl "http://localhost:8000/api/people?type=resident"

# List PGY-2 residents
curl "http://localhost:8000/api/people?type=resident&pgy_level=2"

# Response (200 OK):
# {
#   "items": [
#     {
#       "id": "550e8400-e29b-41d4-a716-446655440000",
#       "name": "Dr. Jane Smith",
#       "type": "resident",
#       "email": "jane.smith@hospital.org",
#       "pgy_level": 2,
#       "performs_procedures": false,
#       "specialties": null,
#       "primary_duty": null,
#       "created_at": "2024-01-01T00:00:00Z",
#       "updated_at": "2024-01-01T00:00:00Z"
#     }
#   ],
#   "total": 1
# }
```

### List Residents

Returns all residents with optional PGY level filtering.

**Endpoint:** `GET /api/people/residents`

```bash
# List all residents
curl http://localhost:8000/api/people/residents

# List PGY-1 residents only
curl "http://localhost:8000/api/people/residents?pgy_level=1"

# Response (200 OK):
# {
#   "items": [...],
#   "total": 12
# }
```

### List Faculty

Returns all faculty with optional specialty filtering.

**Endpoint:** `GET /api/people/faculty`

```bash
# List all faculty
curl http://localhost:8000/api/people/faculty

# List faculty by specialty
curl "http://localhost:8000/api/people/faculty?specialty=Sports%20Medicine"

# Response (200 OK):
# {
#   "items": [...],
#   "total": 8
# }
```

### Get Person

Returns a specific person by ID.

**Endpoint:** `GET /api/people/{person_id}`

```bash
# Get specific person
curl http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000

# Response (200 OK):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "Dr. Jane Smith",
#   "type": "resident",
#   "email": "jane.smith@hospital.org",
#   "pgy_level": 2,
#   "performs_procedures": false,
#   "specialties": null,
#   "primary_duty": null,
#   "created_at": "2024-01-01T00:00:00Z",
#   "updated_at": "2024-01-01T00:00:00Z"
# }
```

### Create Person

Creates a new resident or faculty member.

**Endpoint:** `POST /api/people`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full name (max 255 chars) |
| `type` | string | Yes | `resident` or `faculty` |
| `email` | string | No | Valid email address |
| `pgy_level` | integer | Yes (for residents) | PGY level 1-3 |
| `performs_procedures` | boolean | No | Can perform procedures (default: false) |
| `specialties` | string[] | No | Array of specialty names |
| `primary_duty` | string | No | Primary duty assignment |

```bash
# Create a resident
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith",
    "type": "resident",
    "email": "jane.smith@hospital.org",
    "pgy_level": 2,
    "performs_procedures": false
  }'

# Create a faculty member
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Robert Johnson",
    "type": "faculty",
    "email": "robert.johnson@hospital.org",
    "specialties": ["Sports Medicine", "Primary Care"],
    "primary_duty": "Sports Medicine Clinic"
  }'

# Response (201 Created):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "Dr. Jane Smith",
#   "type": "resident",
#   ...
# }
```

### Update Person

Updates an existing person.

**Endpoint:** `PUT /api/people/{person_id}`

**Authentication:** Required

```bash
# Update a person
curl -X PUT http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith-Jones",
    "pgy_level": 3,
    "performs_procedures": true
  }'

# Response (200 OK):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "name": "Dr. Jane Smith-Jones",
#   "pgy_level": 3,
#   "performs_procedures": true,
#   ...
# }
```

### Delete Person

Deletes a person from the system.

**Endpoint:** `DELETE /api/people/{person_id}`

**Authentication:** Required

```bash
# Delete a person
curl -X DELETE http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_jwt_token>"

# Response (204 No Content)
```

---

## Rotation Templates API

Base path: `/api/rotation-templates`

Manages rotation templates that define clinic activities and their requirements.

### List Rotation Templates

Returns all rotation templates with optional filtering.

**Endpoint:** `GET /api/rotation-templates`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `activity_type` | string | No | Filter by type: `clinic`, `inpatient`, `procedure`, `conference` |

```bash
# List all rotation templates
curl http://localhost:8000/api/rotation-templates

# List only clinic templates
curl "http://localhost:8000/api/rotation-templates?activity_type=clinic"

# Response (200 OK):
# {
#   "items": [
#     {
#       "id": "770e8400-e29b-41d4-a716-446655440000",
#       "name": "Sports Medicine Clinic",
#       "activity_type": "clinic",
#       "abbreviation": "SM",
#       "clinic_location": "Building A, Room 102",
#       "max_residents": 4,
#       "requires_specialty": "Sports Medicine",
#       "requires_procedure_credential": false,
#       "supervision_required": true,
#       "max_supervision_ratio": 4,
#       "created_at": "2024-01-01T00:00:00Z"
#     }
#   ],
#   "total": 1
# }
```

### Get Rotation Template

Returns a specific rotation template.

**Endpoint:** `GET /api/rotation-templates/{template_id}`

```bash
# Get specific template
curl http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000

# Response (200 OK):
# {
#   "id": "770e8400-e29b-41d4-a716-446655440000",
#   "name": "Sports Medicine Clinic",
#   "activity_type": "clinic",
#   ...
# }
```

### Create Rotation Template

Creates a new rotation template.

**Endpoint:** `POST /api/rotation-templates`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique template name |
| `activity_type` | string | Yes | `clinic`, `inpatient`, `procedure`, or `conference` |
| `abbreviation` | string | No | Short code for display |
| `clinic_location` | string | No | Physical location |
| `max_residents` | integer | No | Maximum residents per session |
| `requires_specialty` | string | No | Required faculty specialty |
| `requires_procedure_credential` | boolean | No | Requires procedure credential (default: false) |
| `supervision_required` | boolean | No | Requires supervision (default: true) |
| `max_supervision_ratio` | integer | No | Max residents per supervisor (default: 4) |

```bash
# Create a rotation template
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sports Medicine Clinic",
    "activity_type": "clinic",
    "abbreviation": "SM",
    "clinic_location": "Building A, Room 102",
    "max_residents": 4,
    "requires_specialty": "Sports Medicine",
    "requires_procedure_credential": false,
    "supervision_required": true,
    "max_supervision_ratio": 4
  }'

# Response (201 Created):
# {
#   "id": "770e8400-e29b-41d4-a716-446655440000",
#   "name": "Sports Medicine Clinic",
#   ...
# }
```

### Update Rotation Template

Updates an existing rotation template.

**Endpoint:** `PUT /api/rotation-templates/{template_id}`

```bash
# Update a rotation template
curl -X PUT http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "max_residents": 6,
    "max_supervision_ratio": 3
  }'

# Response (200 OK):
# {
#   "id": "770e8400-e29b-41d4-a716-446655440000",
#   "max_residents": 6,
#   "max_supervision_ratio": 3,
#   ...
# }
```

### Delete Rotation Template

Deletes a rotation template.

**Endpoint:** `DELETE /api/rotation-templates/{template_id}`

```bash
# Delete a rotation template
curl -X DELETE http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000

# Response (204 No Content)
```

---

## Absences API

Base path: `/api/absences`

Manages person absences including vacation, deployment, TDY, and other leave types.

### List Absences

Returns absences with optional filtering.

**Endpoint:** `GET /api/absences`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter absences starting from (YYYY-MM-DD) |
| `end_date` | date | No | Filter absences ending by (YYYY-MM-DD) |
| `person_id` | UUID | No | Filter by person |
| `absence_type` | string | No | Filter by type |

**Valid Absence Types:**
- `vacation` - Personal vacation time
- `deployment` - Military deployment
- `tdy` - Temporary duty assignment
- `medical` - Medical leave
- `family_emergency` - Family emergency leave
- `conference` - Conference attendance

```bash
# List all absences
curl http://localhost:8000/api/absences

# List absences for a date range
curl "http://localhost:8000/api/absences?start_date=2024-01-01&end_date=2024-03-31"

# List absences for a specific person
curl "http://localhost:8000/api/absences?person_id=550e8400-e29b-41d4-a716-446655440000"

# List only deployment absences
curl "http://localhost:8000/api/absences?absence_type=deployment"

# Response (200 OK):
# {
#   "items": [
#     {
#       "id": "990e8400-e29b-41d4-a716-446655440000",
#       "person_id": "550e8400-e29b-41d4-a716-446655440000",
#       "start_date": "2024-02-01",
#       "end_date": "2024-02-15",
#       "absence_type": "deployment",
#       "deployment_orders": true,
#       "tdy_location": null,
#       "replacement_activity": null,
#       "notes": "Annual training deployment",
#       "created_at": "2024-01-15T00:00:00Z"
#     }
#   ],
#   "total": 1
# }
```

### Get Absence

Returns a specific absence by ID.

**Endpoint:** `GET /api/absences/{absence_id}`

```bash
# Get specific absence
curl http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000

# Response (200 OK):
# {
#   "id": "990e8400-e29b-41d4-a716-446655440000",
#   "person_id": "550e8400-e29b-41d4-a716-446655440000",
#   "start_date": "2024-02-01",
#   "end_date": "2024-02-15",
#   "absence_type": "deployment",
#   ...
# }
```

### Create Absence

Creates a new absence record.

**Endpoint:** `POST /api/absences`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person's unique identifier |
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD), must be >= start_date |
| `absence_type` | string | Yes | Type of absence |
| `deployment_orders` | boolean | No | Has deployment orders |
| `tdy_location` | string | No | TDY location if applicable |
| `replacement_activity` | string | No | Replacement activity during absence |
| `notes` | string | No | Additional notes |

```bash
# Create a vacation absence
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-03-15",
    "end_date": "2024-03-22",
    "absence_type": "vacation",
    "notes": "Spring break vacation"
  }'

# Create a deployment absence
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-04-01",
    "end_date": "2024-04-30",
    "absence_type": "deployment",
    "deployment_orders": true,
    "notes": "Annual training deployment"
  }'

# Create a TDY absence
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-05-10",
    "end_date": "2024-05-15",
    "absence_type": "tdy",
    "tdy_location": "Fort Bragg, NC",
    "notes": "Training exercise"
  }'

# Response (201 Created):
# {
#   "id": "990e8400-e29b-41d4-a716-446655440000",
#   "person_id": "550e8400-e29b-41d4-a716-446655440000",
#   "start_date": "2024-03-15",
#   ...
# }
```

### Update Absence

Updates an existing absence.

**Endpoint:** `PUT /api/absences/{absence_id}`

```bash
# Update an absence
curl -X PUT http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "end_date": "2024-03-25",
    "notes": "Extended vacation by 3 days"
  }'

# Response (200 OK):
# {
#   "id": "990e8400-e29b-41d4-a716-446655440000",
#   "end_date": "2024-03-25",
#   "notes": "Extended vacation by 3 days",
#   ...
# }
```

### Delete Absence

Deletes an absence record.

**Endpoint:** `DELETE /api/absences/{absence_id}`

```bash
# Delete an absence
curl -X DELETE http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000

# Response (204 No Content)
```

---

## Schedule API

Base path: `/api/schedule`

Handles schedule generation, validation, and retrieval with ACGME compliance checking.

### Get Schedule

Retrieves the schedule for a date range formatted for calendar view.

**Endpoint:** `GET /api/schedule/{start_date}/{end_date}`

```bash
# Get schedule for a week
curl http://localhost:8000/api/schedule/2024-01-15/2024-01-21

# Response (200 OK):
# {
#   "start_date": "2024-01-15",
#   "end_date": "2024-01-21",
#   "schedule": {
#     "2024-01-15": {
#       "AM": [
#         {
#           "id": "880e8400-e29b-41d4-a716-446655440000",
#           "person": {
#             "id": "550e8400-e29b-41d4-a716-446655440000",
#             "name": "Dr. Jane Smith",
#             "type": "resident",
#             "pgy_level": 2
#           },
#           "role": "primary",
#           "activity": "Sports Medicine Clinic",
#           "abbreviation": "SM"
#         }
#       ],
#       "PM": [
#         {
#           "id": "880e8400-e29b-41d4-a716-446655440001",
#           "person": {
#             "id": "550e8400-e29b-41d4-a716-446655440001",
#             "name": "Dr. Bob Wilson",
#             "type": "resident",
#             "pgy_level": 1
#           },
#           "role": "primary",
#           "activity": "Primary Care Clinic",
#           "abbreviation": "PC"
#         }
#       ]
#     },
#     "2024-01-16": {
#       "AM": [...],
#       "PM": [...]
#     }
#   },
#   "total_assignments": 42
# }
```

### Generate Schedule

Generates assignments for a date range using the scheduling engine.

**Endpoint:** `POST /api/schedule/generate`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |
| `pgy_levels` | integer[] | No | Filter residents by PGY level [1, 2, 3] |
| `rotation_template_ids` | UUID[] | No | Specific templates to schedule |
| `algorithm` | string | No | `greedy`, `min_conflicts`, or `cp_sat` (default: `greedy`) |

**Scheduling Algorithms:**
- `greedy` - Fast, simple assignment algorithm (default)
- `min_conflicts` - Minimizes scheduling conflicts
- `cp_sat` - Constraint programming solver for optimal solutions

```bash
# Generate schedule for 6 months
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "algorithm": "greedy"
  }'

# Generate schedule for specific PGY levels
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "pgy_levels": [1, 2],
    "algorithm": "min_conflicts"
  }'

# Generate schedule for specific rotation templates
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "rotation_template_ids": [
      "770e8400-e29b-41d4-a716-446655440000",
      "770e8400-e29b-41d4-a716-446655440001"
    ],
    "algorithm": "cp_sat"
  }'

# Response (200 OK):
# {
#   "status": "success",
#   "message": "Schedule generated successfully",
#   "total_blocks_assigned": 2920,
#   "total_blocks": 3650,
#   "validation": {
#     "valid": true,
#     "total_violations": 0,
#     "violations": [],
#     "coverage_rate": 80.0,
#     "statistics": {
#       "total_assignments": 2920,
#       "total_blocks": 3650,
#       "residents_scheduled": 24
#     }
#   },
#   "run_id": "aa0e8400-e29b-41d4-a716-446655440000"
# }
```

**Response Status Values:**
- `success` - All blocks assigned, no violations
- `partial` - Some blocks unassigned or violations present
- `failed` - Critical error during generation

### Validate Schedule (ACGME Compliance)

Validates the current schedule for ACGME compliance requirements.

**Endpoint:** `GET /api/schedule/validate`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |

**ACGME Compliance Checks:**
- **80-hour rule**: Average weekly hours over 4-week period
- **1-in-7 rule**: Minimum one day off per seven days
- **Supervision ratios**: Appropriate faculty-to-resident ratios by PGY level

```bash
# Validate schedule compliance
curl "http://localhost:8000/api/schedule/validate?start_date=2024-01-01&end_date=2024-03-31"

# Response with violations (200 OK):
# {
#   "valid": false,
#   "total_violations": 2,
#   "violations": [
#     {
#       "type": "80_HOUR_VIOLATION",
#       "severity": "CRITICAL",
#       "person_id": "550e8400-e29b-41d4-a716-446655440000",
#       "person_name": "Dr. Jane Smith",
#       "block_id": null,
#       "message": "Dr. Jane Smith: 82.5 hours/week average (limit: 80)",
#       "details": {
#         "window_start": "2024-01-01",
#         "window_end": "2024-01-28",
#         "average_weekly_hours": 82.5
#       }
#     },
#     {
#       "type": "1_IN_7_VIOLATION",
#       "severity": "HIGH",
#       "person_id": "550e8400-e29b-41d4-a716-446655440001",
#       "person_name": "Dr. Bob Wilson",
#       "block_id": null,
#       "message": "Dr. Bob Wilson: No day off in 8 consecutive days",
#       "details": {
#         "consecutive_days": 8,
#         "period_start": "2024-01-08",
#         "period_end": "2024-01-15"
#       }
#     }
#   ],
#   "coverage_rate": 95.5,
#   "statistics": {
#     "total_assignments": 3500,
#     "total_blocks": 3650,
#     "residents_scheduled": 24
#   }
# }

# Response without violations (200 OK):
# {
#   "valid": true,
#   "total_violations": 0,
#   "violations": [],
#   "coverage_rate": 98.2,
#   "statistics": {
#     "total_assignments": 3580,
#     "total_blocks": 3650,
#     "residents_scheduled": 24
#   }
# }
```

**Violation Types:**
| Type | Severity | Description |
|------|----------|-------------|
| `80_HOUR_VIOLATION` | CRITICAL | Resident exceeds 80 hours/week average |
| `1_IN_7_VIOLATION` | HIGH | Resident missing required day off |
| `SUPERVISION_RATIO_VIOLATION` | CRITICAL | Insufficient faculty supervision |
| `CONSECUTIVE_DUTY_VIOLATION` | HIGH | Too many consecutive duty days |

### Emergency Coverage

Handles emergency absences and automatically finds replacement coverage.

**Endpoint:** `POST /api/schedule/emergency-coverage`

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person who needs coverage |
| `start_date` | date | Yes | Start date of absence |
| `end_date` | date | Yes | End date of absence |
| `reason` | string | Yes | Reason for emergency absence |
| `is_deployment` | boolean | No | Is this a deployment (default: false) |

```bash
# Request emergency coverage
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-01-20",
    "end_date": "2024-01-25",
    "reason": "Family emergency",
    "is_deployment": false
  }'

# Response (200 OK):
# {
#   "status": "partial",
#   "replacements_found": 8,
#   "coverage_gaps": 2,
#   "requires_manual_review": true,
#   "details": [
#     {
#       "date": "2024-01-20",
#       "time_of_day": "AM",
#       "original_assignment": "Sports Medicine Clinic",
#       "replacement": {
#         "person_id": "550e8400-e29b-41d4-a716-446655440002",
#         "person_name": "Dr. Bob Wilson"
#       },
#       "status": "covered"
#     },
#     {
#       "date": "2024-01-20",
#       "time_of_day": "PM",
#       "original_assignment": "Primary Care Clinic",
#       "replacement": null,
#       "status": "gap"
#     }
#   ]
# }
```

**Response Status Values:**
- `success` - All slots covered
- `partial` - Some slots have gaps requiring manual review
- `failed` - Unable to find any coverage

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | OK - Request succeeded |
| `201` | Created - Resource created successfully |
| `204` | No Content - Request succeeded (DELETE operations) |
| `400` | Bad Request - Invalid input or validation error |
| `401` | Unauthorized - Authentication required or failed |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource not found |
| `500` | Internal Server Error - Server error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

```bash
# Authentication required (401)
curl http://localhost:8000/api/people \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

# Response:
# {
#   "detail": "Not authenticated"
# }

# Invalid token (401)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer invalid_token"

# Response:
# {
#   "detail": "Could not validate credentials"
# }

# Resource not found (404)
curl http://localhost:8000/api/people/nonexistent-id

# Response:
# {
#   "detail": "Person not found"
# }

# Validation error (400)
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "type": "resident"}'

# Response:
# {
#   "detail": "PGY level required for residents"
# }
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse. Default limits:
- 100 requests per minute per IP address
- 1000 requests per hour per authenticated user

Rate limit headers in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

---

## Versioning

The API uses URL path versioning. Current version: v1 (implicit in `/api` prefix).

Future versions will be available at `/api/v2`, etc.

---

*End of API Documentation*
