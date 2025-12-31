# People/Personnel API Documentation

**Status:** Complete Reconnaissance
**Target:** `/api/people` endpoints
**Version:** 1.0
**Last Updated:** 2025-12-30

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Endpoints Reference](#endpoints-reference)
4. [Data Models](#data-models)
5. [Filtering & Pagination](#filtering--pagination)
6. [Credential Management](#credential-management)
7. [Relationships](#relationships)
8. [Error Handling](#error-handling)
9. [Usage Examples](#usage-examples)
10. [Implementation Details](#implementation-details)

---

## Overview

The People API manages residents and faculty members in the medical residency scheduling system.

### Base Path
```
/api/people
```

### Key Features
- **Person Management**: Create, read, update, delete residents and faculty
- **Role-Based Filtering**: Query by type (resident/faculty), PGY level, specialty
- **Credential Tracking**: Manage faculty procedure qualifications and certifications
- **Equity Tracking**: Monitor call and FMIT distributions
- **ACGME Compliance**: Automatic supervision ratio calculations

### Person Types

#### Resident
- **Required Fields**: `name`, `type`, `pgy_level`
- **PGY Levels**: 1, 2, or 3
- **Supervision**: Inherent ratios (PGY-1: 1:2, PGY-2/3: 1:4)
- **Call Equity**: Sunday and weekday call tracking
- **FMIT**: First Month In Training tracking

#### Faculty
- **Optional Specialties**: List of specialty areas
- **Procedure Credentials**: Tracked for procedure-performing faculty
- **Faculty Roles**: PD, APD, OIC, Dept Chief, Sports Med, Core, Adjunct
- **Screener Roles**: Optional clinic support roles (dedicated, RN, EMT, resident)

---

## Authentication & Authorization

### Requirements
- **All endpoints require authentication** via JWT token (httpOnly cookie)
- Bearer token format: `Authorization: Bearer <jwt_token>`
- Endpoints delegate to FastAPI's `get_current_active_user()` dependency

### Access Control
Standard RBAC (Role-Based Access Control) applies:
- Admin, Coordinator: Full access
- Faculty: View own and assigned residents
- Resident: View own data
- Clinical staff: View schedules only

---

## Endpoints Reference

### 1. List All People

**Endpoint**
```
GET /api/people
```

**Description**
List all people (residents and faculty) with optional filtering.

**Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter: `"resident"` or `"faculty"` |
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) - only valid when `type="resident"` |

**Request Example**
```bash
# Get all people
curl -X GET "http://localhost:8000/api/people" \
  -H "Authorization: Bearer <token>"

# Filter by type
curl -X GET "http://localhost:8000/api/people?type=resident" \
  -H "Authorization: Bearer <token>"

# Filter by type and PGY level
curl -X GET "http://localhost:8000/api/people?type=resident&pgy_level=1" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. Jane Resident",
      "type": "resident",
      "email": "jane.resident@hospital.org",
      "pgy_level": 2,
      "performs_procedures": false,
      "specialties": null,
      "primary_duty": null,
      "faculty_role": null,
      "sunday_call_count": 3,
      "weekday_call_count": 12,
      "fmit_weeks_count": 2,
      "created_at": "2025-01-01T08:00:00",
      "updated_at": "2025-12-20T14:30:00"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. John Faculty",
      "type": "faculty",
      "email": "john.faculty@hospital.org",
      "pgy_level": null,
      "performs_procedures": true,
      "specialties": ["Cardiology", "Internal Medicine"],
      "primary_duty": "Outpatient Clinic",
      "faculty_role": "core",
      "sunday_call_count": 1,
      "weekday_call_count": 8,
      "fmit_weeks_count": 0,
      "created_at": "2024-06-15T10:00:00",
      "updated_at": "2025-12-18T09:15:00"
    }
  ],
  "total": 2
}
```

**Status Codes**
| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized (missing/invalid token) |
| 422 | Validation error (invalid filter values) |

---

### 2. List Residents

**Endpoint**
```
GET /api/people/residents
```

**Description**
List all residents, optionally filtered by PGY level.

**Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) |

**Request Example**
```bash
# All residents
curl -X GET "http://localhost:8000/api/people/residents" \
  -H "Authorization: Bearer <token>"

# PGY-1 residents only
curl -X GET "http://localhost:8000/api/people/residents?pgy_level=1" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Dr. Jane Resident",
      "type": "resident",
      "email": "jane.resident@hospital.org",
      "pgy_level": 2,
      "performs_procedures": false,
      "specialties": null,
      "primary_duty": null,
      "faculty_role": null,
      "sunday_call_count": 3,
      "weekday_call_count": 12,
      "fmit_weeks_count": 2,
      "created_at": "2025-01-01T08:00:00",
      "updated_at": "2025-12-20T14:30:00"
    }
  ],
  "total": 1
}
```

---

### 3. List Faculty

**Endpoint**
```
GET /api/people/faculty
```

**Description**
List all faculty members, optionally filtered by specialty.

**Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `specialty` | string | No | Filter by specialty name (case-sensitive) |

**Request Example**
```bash
# All faculty
curl -X GET "http://localhost:8000/api/people/faculty" \
  -H "Authorization: Bearer <token>"

# Faculty with specific specialty
curl -X GET "http://localhost:8000/api/people/faculty?specialty=Cardiology" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. John Faculty",
      "type": "faculty",
      "email": "john.faculty@hospital.org",
      "pgy_level": null,
      "performs_procedures": true,
      "specialties": ["Cardiology", "Internal Medicine"],
      "primary_duty": "Outpatient Clinic",
      "faculty_role": "core",
      "sunday_call_count": 1,
      "weekday_call_count": 8,
      "fmit_weeks_count": 0,
      "created_at": "2024-06-15T10:00:00",
      "updated_at": "2025-12-18T09:15:00"
    }
  ],
  "total": 1
}
```

---

### 4. Get Person by ID

**Endpoint**
```
GET /api/people/{person_id}
```

**Description**
Retrieve a single person by UUID.

**Path Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | The person's unique identifier |

**Request Example**
```bash
curl -X GET "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Dr. Jane Resident",
  "type": "resident",
  "email": "jane.resident@hospital.org",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "faculty_role": null,
  "sunday_call_count": 3,
  "weekday_call_count": 12,
  "fmit_weeks_count": 2,
  "created_at": "2025-01-01T08:00:00",
  "updated_at": "2025-12-20T14:30:00"
}
```

**Status Codes**
| Code | Description |
|------|-------------|
| 200 | Success |
| 404 | Person not found |
| 401 | Unauthorized |

---

### 5. Create Person

**Endpoint**
```
POST /api/people
```

**Description**
Create a new resident or faculty member.

**Request Body**
```json
{
  "name": "Dr. New Person",
  "type": "resident",
  "email": "new.person@hospital.org",
  "pgy_level": 1,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "faculty_role": null
}
```

**Request Parameters**
| Field | Type | Required | Rules | Description |
|-------|------|----------|-------|-------------|
| `name` | string | Yes | Max 255 chars | Person's full name |
| `type` | string | Yes | `"resident"` or `"faculty"` | Person type |
| `email` | email | No | Must be unique | Contact email (EmailStr format) |
| `pgy_level` | integer | Conditional | 1-3 for residents | **Required for residents**, must be null for faculty |
| `performs_procedures` | boolean | No | Defaults to false | Can perform/supervise procedures |
| `specialties` | array | No | List of strings | Medical specialties (faculty only) |
| `primary_duty` | string | No | Max 255 chars | Primary role/duty |
| `faculty_role` | string | No | See FacultyRole enum | Faculty position role |

**FacultyRole Enum Values**
```
"pd"          - Program Director
"apd"         - Associate Program Director
"oic"         - Officer in Charge
"dept_chief"  - Department Chief
"sports_med"  - Sports Medicine
"core"        - Core Faculty
"adjunct"     - Adjunct Faculty
```

**Request Examples**

Create Resident:
```bash
curl -X POST "http://localhost:8000/api/people" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Sarah Rodriguez",
    "type": "resident",
    "email": "sarah.rodriguez@hospital.org",
    "pgy_level": 1
  }'
```

Create Faculty:
```bash
curl -X POST "http://localhost:8000/api/people" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Michael Chen",
    "type": "faculty",
    "email": "michael.chen@hospital.org",
    "performs_procedures": true,
    "specialties": ["Cardiology", "Internal Medicine"],
    "faculty_role": "core",
    "primary_duty": "Inpatient Service"
  }'
```

**Response (201 Created)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Dr. Sarah Rodriguez",
  "type": "resident",
  "email": "sarah.rodriguez@hospital.org",
  "pgy_level": 1,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "faculty_role": null,
  "sunday_call_count": 0,
  "weekday_call_count": 0,
  "fmit_weeks_count": 0,
  "created_at": "2025-12-30T10:00:00",
  "updated_at": "2025-12-30T10:00:00"
}
```

**Status Codes**
| Code | Description |
|------|-------------|
| 201 | Created successfully |
| 400 | Business logic error (e.g., missing PGY for resident) |
| 422 | Validation error (invalid data) |
| 401 | Unauthorized |

**Validation Errors**
| Condition | Status | Detail |
|-----------|--------|--------|
| Resident without PGY level | 400 | "PGY level required for residents" |
| Invalid type | 422 | "type must be 'resident' or 'faculty'" |
| Invalid PGY level | 422 | "pgy_level must be between 1 and 3" |
| Duplicate email | 422 | "Email already registered" |

---

### 6. Update Person

**Endpoint**
```
PUT /api/people/{person_id}
```

**Description**
Update a person's information. All fields are optional (partial updates supported).

**Path Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | The person's unique identifier |

**Request Body** (all fields optional)
```json
{
  "name": "Dr. Updated Name",
  "email": "updated@hospital.org",
  "pgy_level": 2,
  "performs_procedures": true,
  "specialties": ["Cardiology"],
  "primary_duty": "Clinic",
  "faculty_role": "core"
}
```

**Request Parameters**
| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Only provided field(s) are updated |
| `email` | email | Must be unique if changed |
| `pgy_level` | integer | 1-3 for residents |
| `performs_procedures` | boolean | - |
| `specialties` | array | Replaces existing array |
| `primary_duty` | string | - |
| `faculty_role` | string | FacultyRole enum value |

**Request Examples**

Partial update (name only):
```bash
curl -X PUT "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith"
  }'
```

Update PGY level:
```bash
curl -X PUT "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "pgy_level": 3
  }'
```

Update faculty role:
```bash
curl -X PUT "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "faculty_role": "apd"
  }'
```

**Response (200 OK)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.resident@hospital.org",
  "pgy_level": 3,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "faculty_role": null,
  "sunday_call_count": 3,
  "weekday_call_count": 12,
  "fmit_weeks_count": 2,
  "created_at": "2025-01-01T08:00:00",
  "updated_at": "2025-12-30T11:45:00"
}
```

**Status Codes**
| Code | Description |
|------|-------------|
| 200 | Updated successfully |
| 404 | Person not found |
| 422 | Validation error |
| 401 | Unauthorized |

---

### 7. Delete Person

**Endpoint**
```
DELETE /api/people/{person_id}
```

**Description**
Delete a person. Cascading deletes related data (assignments, credentials, certifications).

**Path Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | The person's unique identifier |

**Request Example**
```bash
curl -X DELETE "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"
```

**Response (204 No Content)**
```
(Empty response body)
```

**Status Codes**
| Code | Description |
|------|-------------|
| 204 | Deleted successfully |
| 404 | Person not found |
| 401 | Unauthorized |

**Cascade Behavior**
Deleting a person cascades to:
- Assignments (links to schedule blocks)
- Procedure Credentials (qualifications)
- Certifications/PersonCertifications
- Absences/Leave records

---

### 8. Get Person Credentials

**Endpoint**
```
GET /api/people/{person_id}/credentials
```

**Description**
Get all credentials (procedure qualifications) for a faculty member.

**Path Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | The faculty member's ID |

**Query Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: `"active"`, `"expired"`, `"suspended"`, `"pending"` |
| `include_expired` | boolean | No | Include expired credentials in results (default: false) |

**Request Examples**
```bash
# All active credentials
curl -X GET "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001/credentials" \
  -H "Authorization: Bearer <token>"

# Include expired credentials
curl -X GET "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001/credentials?include_expired=true" \
  -H "Authorization: Bearer <token>"

# Filter by status
curl -X GET "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001/credentials?status=active" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "procedure_id": "550e8400-e29b-41d4-a716-446655440200",
      "status": "active",
      "competency_level": "qualified",
      "issued_date": "2024-01-15",
      "expiration_date": "2026-01-15",
      "last_verified_date": "2025-12-01",
      "max_concurrent_residents": 4,
      "max_per_week": 2,
      "max_per_academic_year": 20,
      "notes": "Verified in Jan 2025",
      "is_valid": true,
      "created_at": "2024-01-15T10:00:00",
      "updated_at": "2025-12-01T14:30:00"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "procedure_id": "550e8400-e29b-41d4-a716-446655440201",
      "status": "expired",
      "competency_level": "qualified",
      "issued_date": "2023-06-01",
      "expiration_date": "2025-06-01",
      "last_verified_date": "2025-05-01",
      "max_concurrent_residents": 2,
      "max_per_week": 1,
      "max_per_academic_year": 10,
      "notes": "Needs renewal",
      "is_valid": false,
      "created_at": "2023-06-01T10:00:00",
      "updated_at": "2025-06-01T14:30:00"
    }
  ],
  "total": 2
}
```

**Status Codes**
| Code | Description |
|------|-------------|
| 200 | Success |
| 404 | Person not found |
| 401 | Unauthorized |

---

### 9. Get Person Credential Summary

**Endpoint**
```
GET /api/people/{person_id}/credentials/summary
```

**Description**
Get a high-level summary of a faculty member's credential status.

**Path Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | The faculty member's ID |

**Request Example**
```bash
curl -X GET "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001/credentials/summary" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_name": "Dr. John Faculty",
  "total_credentials": 5,
  "active_credentials": 4,
  "expiring_soon": 1,
  "procedures": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440200",
      "name": "Knee Arthroscopy",
      "code": "KNEE_ARTHRO",
      "category": "Surgical",
      "description": "Minimally invasive knee procedures"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440201",
      "name": "Shoulder Dislocation Reduction",
      "code": "SHOULDER_DR",
      "category": "Procedural",
      "description": "Reduction of shoulder dislocation"
    }
  ]
}
```

**Summary Fields**
| Field | Type | Description |
|-------|------|-------------|
| `person_id` | UUID | Faculty member ID |
| `person_name` | string | Faculty name |
| `total_credentials` | int | Total procedure qualifications |
| `active_credentials` | int | Count of active (non-expired) credentials |
| `expiring_soon` | int | Credentials expiring in next 30 days |
| `procedures` | array | List of qualified procedures |

---

### 10. Get Person Procedures

**Endpoint**
```
GET /api/people/{person_id}/procedures
```

**Description**
Get all procedures a faculty member is qualified to supervise.

**Path Parameters**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | The faculty member's ID |

**Request Example**
```bash
curl -X GET "http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001/procedures" \
  -H "Authorization: Bearer <token>"
```

**Response (200 OK)**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440200",
      "name": "Knee Arthroscopy",
      "code": "KNEE_ARTHRO",
      "category": "Surgical",
      "description": "Minimally invasive knee procedures"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440201",
      "name": "Shoulder Dislocation Reduction",
      "code": "SHOULDER_DR",
      "category": "Procedural",
      "description": "Reduction of shoulder dislocation"
    }
  ],
  "total": 2
}
```

**Status Codes**
| Code | Description |
|------|-------------|
| 200 | Success |
| 404 | Person not found |
| 401 | Unauthorized |

---

## Data Models

### PersonResponse Schema

**Full Response Structure**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "string",
  "type": "resident|faculty",
  "email": "user@example.com",
  "pgy_level": null | 1 | 2 | 3,
  "performs_procedures": boolean,
  "specialties": [string] | null,
  "primary_duty": "string" | null,
  "faculty_role": "pd|apd|oic|dept_chief|sports_med|core|adjunct" | null,
  "sunday_call_count": integer,
  "weekday_call_count": integer,
  "fmit_weeks_count": integer,
  "created_at": "2025-01-01T08:00:00",
  "updated_at": "2025-01-01T08:00:00"
}
```

**Field Descriptions**

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID | Unique person identifier |
| `name` | string | Full name (max 255 chars) |
| `type` | string | "resident" or "faculty" |
| `email` | string | Unique email address |
| `pgy_level` | int | PGY level for residents (1-3) |
| `performs_procedures` | bool | Can perform/supervise procedures |
| `specialties` | array | Medical specialties (faculty) |
| `primary_duty` | string | Primary role/assignment |
| `faculty_role` | string | Faculty position type |
| `sunday_call_count` | int | Sunday calls (reset annually) |
| `weekday_call_count` | int | Mon-Thu calls (reset annually) |
| `fmit_weeks_count` | int | First Month in Training weeks (reset annually) |
| `created_at` | datetime | Record creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### Resident Properties

**Automatic Calculations**
```python
# supervision_ratio: ACGME required supervision ratio
pgy_1_resident.supervision_ratio  # Returns: 2 (1 faculty per 2 residents)
pgy_2_resident.supervision_ratio  # Returns: 4 (1 faculty per 4 residents)
pgy_3_resident.supervision_ratio  # Returns: 4 (1 faculty per 4 residents)

# is_resident: Boolean check
resident.is_resident  # Returns: True
faculty.is_resident   # Returns: False
```

### Faculty Properties

**Role-Based Calculations**
```python
# Clinic hour limits (per role)
faculty.weekly_clinic_limit        # Returns: 0-4 depending on role
faculty.block_clinic_limit         # Returns: 0-16 depending on role

# Role-specific flags
faculty.avoid_tuesday_call         # Returns: True for PD/APD only
faculty.prefer_wednesday_call      # Returns: True for Dept Chief only

# Specialty checks
faculty.is_sports_medicine         # Returns: True if sports med role or specialty
faculty.role_enum                  # Returns: FacultyRole enum value
```

**Faculty Role Reference**

| Role | Code | Clinic/Week | Clinic/Block | Call Notes |
|------|------|-------------|--------------|-----------|
| Program Director | `pd` | 0 | 0 | Avoid Tue |
| Associate Program Director | `apd` | 2 | 8 (flexible) | Avoid Tue |
| Officer in Charge | `oic` | 2 | 8 (flexible) | None |
| Department Chief | `dept_chief` | 1 | 4 | Prefers Wed |
| Sports Medicine | `sports_med` | 0 | 0 | SM clinic: 4/week |
| Core Faculty | `core` | 4 | 16 (hard max) | None |
| Adjunct | `adjunct` | 0 | 0 | Not auto-scheduled |

---

## Filtering & Pagination

### List Endpoint Filtering

The API provides filtering on list endpoints:

**Resident Filtering**
```bash
# By PGY level
GET /api/people/residents?pgy_level=1

# By type
GET /api/people?type=resident
```

**Faculty Filtering**
```bash
# By specialty
GET /api/people/faculty?specialty=Cardiology

# By type
GET /api/people?type=faculty
```

**Combined Filtering**
```bash
# Type + PGY level
GET /api/people?type=resident&pgy_level=2
```

### Pagination

**Current Implementation**
- No pagination implemented (returns all results)
- `total` field in response indicates full result count
- Suitable for small to medium datasets

**Response Structure**
```json
{
  "items": [...],     // Array of results
  "total": 42         // Total count of all matching records
}
```

**Future Pagination** (if needed)
```
GET /api/people?skip=0&limit=20
```

---

## Credential Management

### Credential Status Values

| Status | Meaning | Eligible for Scheduling |
|--------|---------|------------------------|
| `active` | Valid and current | Yes |
| `expired` | Expiration date passed | No (unless included in query) |
| `suspended` | Temporarily unavailable | No |
| `pending` | Awaiting approval | No |

### Competency Levels

| Level | Meaning |
|-------|---------|
| `trainee` | Learning; requires supervision |
| `qualified` | Meets standard requirements |
| `expert` | Advanced level |
| `master` | Exceptional expertise |

### Credential Limits

**Per-Credential Constraints**

```json
{
  "max_concurrent_residents": 4,      // Max residents supervised simultaneously
  "max_per_week": 2,                  // Max procedures per week
  "max_per_academic_year": 20         // Max procedures per 365-day period
}
```

---

## Relationships

### Entity Relationship Diagram

```
Person (residents & faculty)
  ├── Assignments (multiple)
  │   ├── Block (single)
  │   └── RotationTemplate (single)
  ├── Absences (multiple)
  ├── CallAssignments (multiple)
  ├── ProcedureCredentials (multiple, faculty only)
  │   └── Procedure (single)
  └── Certifications (multiple)
```

### N+1 Query Optimization

The service layer provides eager-loading options:

```python
# Without assignments (default, fast)
service.list_people(type="resident")

# With assignments (uses selectinload to prevent N+1)
service.list_people(type="resident", include_assignments=True)
```

### Cascade Delete

When a person is deleted:
```
Person DELETE
  ├── Assignments → DELETED (cascade)
  ├── Absences → DELETED (cascade)
  ├── CallAssignments → DELETED (cascade)
  ├── ProcedureCredentials → DELETED (cascade)
  └── Certifications → DELETED (cascade)
```

---

## Error Handling

### HTTP Status Codes

| Code | Condition | Example |
|------|-----------|---------|
| 200 | Success (GET/PUT) | Person retrieved or updated |
| 201 | Created (POST) | New person created |
| 204 | No Content (DELETE) | Person deleted successfully |
| 400 | Bad Request | Missing PGY for resident |
| 401 | Unauthorized | Missing/invalid JWT token |
| 404 | Not Found | Person ID does not exist |
| 422 | Validation Error | Invalid data type (e.g., pgy_level=5) |

### Error Response Format

**400 Bad Request**
```json
{
  "detail": "PGY level required for residents"
}
```

**404 Not Found**
```json
{
  "detail": "Person not found"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "pgy_level"],
      "msg": "pgy_level must be between 1 and 3",
      "input": 5
    }
  ]
}
```

### Common Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "type must be 'resident' or 'faculty'" | Invalid type value | Use only "resident" or "faculty" |
| "pgy_level must be between 1 and 3" | Invalid PGY value | Use 1, 2, or 3 |
| "PGY level required for residents" | Resident without PGY | Set pgy_level for resident type |
| "Person not found" | Invalid person_id UUID | Verify UUID is correct and exists |
| "Email already registered" | Duplicate email | Use unique email address |

---

## Usage Examples

### Complete Workflow: Create and Configure Resident

```bash
# 1. Create resident
RESIDENT_ID=$(curl -s -X POST "http://localhost:8000/api/people" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Emily Watson",
    "type": "resident",
    "email": "emily.watson@hospital.org",
    "pgy_level": 1
  }' | jq -r '.id')

echo "Created resident: $RESIDENT_ID"

# 2. Update resident after first month
curl -X PUT "http://localhost:8000/api/people/$RESIDENT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pgy_level": 1,
    "primary_duty": "Inpatient Service"
  }'

# 3. Get updated resident
curl -X GET "http://localhost:8000/api/people/$RESIDENT_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 4. Promote to PGY-2 next year
curl -X PUT "http://localhost:8000/api/people/$RESIDENT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pgy_level": 2
  }'
```

### Create Faculty with Procedure Credentials

```bash
# 1. Create faculty
FACULTY_ID=$(curl -s -X POST "http://localhost:8000/api/people" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Robert Chang",
    "type": "faculty",
    "email": "robert.chang@hospital.org",
    "performs_procedures": true,
    "specialties": ["Orthopedics", "Sports Medicine"],
    "faculty_role": "core",
    "primary_duty": "Clinic"
  }' | jq -r '.id')

echo "Created faculty: $FACULTY_ID"

# 2. Get their procedures (separate endpoint)
curl -X GET "http://localhost:8000/api/people/$FACULTY_ID/procedures" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# 3. Get credential summary
curl -X GET "http://localhost:8000/api/people/$FACULTY_ID/credentials/summary" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

### Filter and Report

```bash
# Get all PGY-1 residents
curl -X GET "http://localhost:8000/api/people/residents?pgy_level=1" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[] | {name, pgy_level}'

# Get all faculty with Cardiology specialty
curl -X GET "http://localhost:8000/api/people/faculty?specialty=Cardiology" \
  -H "Authorization: Bearer $TOKEN" | jq '.items[] | {name, specialties}'

# Count residents by PGY level
for pgy in 1 2 3; do
  count=$(curl -s -X GET "http://localhost:8000/api/people/residents?pgy_level=$pgy" \
    -H "Authorization: Bearer $TOKEN" | jq '.total')
  echo "PGY-$pgy: $count residents"
done
```

---

## Implementation Details

### API Architecture

**Layer Breakdown**

```
FastAPI Route (people.py)
    ↓
PersonController (person_controller.py)
    ↓
PersonService (person_service.py)
    ↓
PersonRepository (person_repository.py)
    ↓
SQLAlchemy ORM (person.py model)
    ↓
PostgreSQL Database
```

### Key Files

| File | Purpose |
|------|---------|
| `backend/app/api/routes/people.py` | Route definitions and request handling |
| `backend/app/controllers/person_controller.py` | Request/response validation and delegation |
| `backend/app/services/person_service.py` | Business logic and filtering |
| `backend/app/repositories/person.py` | Database access layer |
| `backend/app/models/person.py` | SQLAlchemy ORM definition |
| `backend/app/schemas/person.py` | Pydantic validation schemas |

### Database Constraints

**Table: people**

```sql
-- Type must be resident or faculty
CHECK (type IN ('resident', 'faculty'))

-- PGY level (if present) must be 1-3
CHECK (pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3)

-- Faculty role validation (if present)
CHECK (faculty_role IS NULL OR faculty_role IN
  ('pd', 'apd', 'oic', 'dept_chief', 'sports_med', 'core', 'adjunct'))

-- Screener role validation (if present)
CHECK (screener_role IS NULL OR screener_role IN
  ('dedicated', 'rn', 'emt', 'resident'))

-- Screening efficiency 0-100
CHECK (screening_efficiency IS NULL OR
  screening_efficiency BETWEEN 0 AND 100)

-- Email must be unique
UNIQUE (email)
```

### Performance Considerations

**Query Optimization**

1. **Index on Type**: Queries filtered by `type` benefit from index
2. **Index on PGY Level**: PGY filtering is optimized
3. **Index on Specialties**: Array contains filtering (partial index)
4. **Eager Loading**: Use `include_assignments=True` to prevent N+1 queries

**Example N+1 Problem**
```python
# BAD: N+1 query (1 for people + N for assignments)
people = service.list_people()  # Default: no assignments
for person in people:
    assignments = person.assignments  # Separate query for each person!

# GOOD: Single batch query with selectinload
people = service.list_people(include_assignments=True)
for person in people:
    assignments = person.assignments  # Already loaded
```

### Testing Coverage

**Test Files**
- `backend/tests/test_people_api.py` - 25+ endpoint tests
- `backend/tests/test_people_routes.py` - Route integration tests
- `backend/tests/services/test_person_service.py` - Service layer tests

**Test Categories**
- CRUD operations (create, read, update, delete)
- Filtering (type, PGY level, specialty)
- Validation (required fields, data types)
- Error handling (404, 400, 422 responses)
- Relationships (assignments, credentials)

---

## Undocumented Features & Edge Cases

### Equity Tracking Fields

These fields are **read-only** and managed by the system:

```json
{
  "sunday_call_count": 0,      // Sunday calls (separate pool)
  "weekday_call_count": 0,     // Mon-Thu calls (combined pool)
  "fmit_weeks_count": 0        // First Month in Training weeks
}
```

**Reset Policy**: All counters reset annually (typically January 1).

### Screener Role Support

The Person model includes optional screener configuration:

```json
{
  "screener_role": "dedicated|rn|emt|resident",
  "can_screen": true,
  "screening_efficiency": 100    // 70-100% range
}
```

**Current API Status**: Screener fields are NOT exposed in the API but are present in the database model for future integration.

### Target Clinical Blocks

Residents can have a `target_clinical_blocks` field (not exposed in current API):

```
Regular resident: 48-56 blocks (12-14 weeks * 4 blocks/week)
Chief resident: 24 blocks (6 clinical + 6 admin)
Research track: 8 blocks (2 clinical weeks)
```

---

## Summary

The People API provides complete management of residents and faculty with:
- **Full CRUD operations** for personnel
- **Role-based filtering** (type, specialty, PGY)
- **Credential tracking** for faculty qualifications
- **ACGME compliance** (supervision ratios, equity tracking)
- **N+1 optimization** with eager loading support
- **Cascade delete** for clean data removal

**Base Path**: `/api/people`
**Authentication**: JWT required
**Response Format**: JSON
**Documentation**: This guide + inline docstrings in code
