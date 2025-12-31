# Procedures & Credentials API Documentation

**Complete API Reference for Medical Procedure Management and Faculty Credentialing**

> **Base Paths:**
> - Procedures: `/api/v1/procedures`
> - Credentials: `/api/v1/credentials`
>
> **Authentication:** Required for write operations (Bearer token)
> **Source Code:**
> - Procedures: `backend/app/api/routes/procedures.py`
> - Credentials: `backend/app/api/routes/credentials.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [Procedures API](#procedures-api)
4. [Credentials API](#credentials-api)
5. [Credentialing Workflow](#credentialing-workflow)
6. [Data Models](#data-models)
7. [Validation Rules](#validation-rules)
8. [Compliance & Expiration Handling](#compliance--expiration-handling)
9. [Integration Guide](#integration-guide)
10. [Error Handling](#error-handling)
11. [Examples](#examples)

---

## Overview

The Procedures & Credentials system manages:

- **Procedures**: Medical procedures that require credentialed supervision (e.g., Mastectomy, IUD placement, Labor and delivery)
- **Credentials**: Faculty qualifications to supervise specific procedures
- **Competency Levels**: Track expertise progression (Trainee → Qualified → Expert → Master)
- **Supervision Limits**: Per-faculty, per-procedure capacity constraints
- **Expiration Tracking**: Monitor credential validity dates and send renewal reminders

### Key Capabilities

1. **Procedure Management** - Create, update, deactivate medical procedures
2. **Credential Issuance** - Award credentials with validation dates
3. **Batch Qualification** - Grant multiple procedures to faculty at once
4. **Qualified Faculty Lookup** - Find who can supervise any procedure
5. **Expiration Monitoring** - Detect credentials expiring soon
6. **Compliance Validation** - Enforce credential status in scheduling

---

## Core Concepts

### Procedures

A **Procedure** defines a medical activity that requires credentialed faculty supervision.

**Attributes:**
- `name` (unique): Mastectomy, IUD Placement, Colposcopy, etc.
- `category`: 'surgical', 'office', 'obstetric', 'clinic'
- `specialty`: 'OB/GYN', 'Dermatology', 'Sports Medicine'
- `complexity_level`: 'basic' | 'standard' | 'advanced' | 'complex'
- `supervision_ratio`: Max residents per supervising faculty (1 = 1:1)
- `min_pgy_level`: Minimum training level (PGY-1, PGY-2, PGY-3)
- `requires_certification`: Boolean - can it be performed by uncredentialed staff?
- `is_active`: Soft-delete flag

**Example Use Cases:**
```
Name: "Colposcopy"
Category: "office"
Specialty: "OB/GYN"
Complexity: "standard"
Supervision Ratio: 2 (1 faculty can supervise 2 residents)
Min PGY Level: 2
Requires Certification: True
```

### Procedure Credentials

A **Procedure Credential** represents one faculty member's qualification to supervise a specific procedure.

**Attributes:**
- `person_id`, `procedure_id`: Links to faculty and procedure
- `status`: 'active' | 'expired' | 'suspended' | 'pending'
- `competency_level`: 'trainee' | 'qualified' | 'expert' | 'master'
- `issued_date`: When credential was granted
- `expiration_date`: When credential expires (NULL = no expiration)
- `last_verified_date`: Last verification/renewal date
- `max_concurrent_residents`: Supervision capacity override
- `max_per_week`: Limit supervisions per week
- `max_per_academic_year`: Limit supervisions per year

**Credential Lifecycle:**
```
Issue Date → Active (Valid) → Near Expiration → Expired → Renewal or Suspended
     ↓
Optional verification during validity to refresh last_verified_date
```

---

## Procedures API

### List Procedures

```http
GET /api/v1/procedures
```

List all procedures with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `specialty` | string | No | Filter by specialty (e.g., "OB/GYN", "Dermatology") |
| `category` | string | No | Filter by category: 'surgical', 'office', 'obstetric', 'clinic' |
| `is_active` | boolean | No | Filter by active status (true/false) |
| `complexity_level` | string | No | Filter by level: 'basic', 'standard', 'advanced', 'complex' |

**Response:** `ProcedureListResponse`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Colposcopy",
      "description": "Colposcopic examination of the cervix",
      "category": "office",
      "specialty": "OB/GYN",
      "complexity_level": "standard",
      "supervision_ratio": 2,
      "requires_certification": true,
      "min_pgy_level": 2,
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200 OK`: Success
- `422 Unprocessable Entity`: Invalid query parameters

**Examples:**

```bash
# Get all OB/GYN procedures
GET /api/v1/procedures?specialty=OB/GYN

# Get all active surgical procedures
GET /api/v1/procedures?category=surgical&is_active=true

# Get advanced complexity procedures
GET /api/v1/procedures?complexity_level=advanced
```

---

### Get Procedure by ID

```http
GET /api/v1/procedures/{procedure_id}
```

Get a specific procedure by UUID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Response:** `ProcedureResponse`

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Procedure not found

---

### Get Procedure by Name

```http
GET /api/v1/procedures/by-name/{name}
```

Get a procedure by its name (case-sensitive).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Procedure name |

**Response:** `ProcedureResponse`

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Procedure not found

---

### Get All Specialties

```http
GET /api/v1/procedures/specialties
```

Get list of all unique specialties in the procedure database.

**Response:**
```json
[
  "OB/GYN",
  "Dermatology",
  "Sports Medicine",
  "General Surgery"
]
```

**Status Codes:**
- `200 OK`: Success

---

### Get All Categories

```http
GET /api/v1/procedures/categories
```

Get list of all unique categories in the procedure database.

**Response:**
```json
[
  "surgical",
  "office",
  "obstetric",
  "clinic"
]
```

**Status Codes:**
- `200 OK`: Success

---

### Create Procedure

```http
POST /api/v1/procedures
```

Create a new medical procedure. **Requires authentication.**

**Request Body:** `ProcedureCreate`

```json
{
  "name": "Mastectomy",
  "description": "Surgical removal of breast tissue",
  "category": "surgical",
  "specialty": "General Surgery",
  "complexity_level": "advanced",
  "supervision_ratio": 1,
  "requires_certification": true,
  "min_pgy_level": 2,
  "is_active": true
}
```

**Validation Rules:**
- `name`: Required, unique, 1-255 characters
- `complexity_level`: Must be 'basic', 'standard', 'advanced', or 'complex'
- `min_pgy_level`: Must be 1-3
- `supervision_ratio`: Must be >= 1

**Response:** `ProcedureResponse` (201 Created)

**Status Codes:**
- `201 Created`: Success
- `400 Bad Request`: Invalid data or duplicate name
- `401 Unauthorized`: Missing/invalid authentication
- `422 Unprocessable Entity`: Validation error

**Error Examples:**
```json
// Duplicate name
{
  "detail": "Procedure with name 'Mastectomy' already exists"
}

// Invalid complexity level
{
  "detail": "complexity_level must be one of ('basic', 'standard', 'advanced', 'complex')"
}

// Invalid PGY level
{
  "detail": "min_pgy_level must be between 1 and 3"
}
```

---

### Update Procedure

```http
PUT /api/v1/procedures/{procedure_id}
```

Update an existing procedure. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Request Body:** `ProcedureUpdate` (all fields optional)

```json
{
  "description": "Updated description",
  "complexity_level": "complex",
  "is_active": false
}
```

**Response:** `ProcedureResponse`

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Procedure not found

---

### Deactivate Procedure

```http
POST /api/v1/procedures/{procedure_id}/deactivate
```

Soft-delete a procedure (sets `is_active=false`). **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Response:** `ProcedureResponse` with `is_active: false`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Procedure not found

---

### Activate Procedure

```http
POST /api/v1/procedures/{procedure_id}/activate
```

Reactivate a deactivated procedure. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Response:** `ProcedureResponse` with `is_active: true`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Procedure not found

---

### Delete Procedure

```http
DELETE /api/v1/procedures/{procedure_id}
```

Permanently delete a procedure and associated credentials. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Status Codes:**
- `204 No Content`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Procedure not found

**Warning:** Deleting a procedure cascades to delete all associated credentials. Use deactivation for soft-delete if you need to preserve history.

---

## Credentials API

### List Expiring Credentials

```http
GET /api/v1/credentials/expiring
```

List credentials expiring within a specified number of days.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `days` | integer | No | 30 | Look-ahead window in days |

**Response:** `CredentialListResponse`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "procedure_id": "550e8400-e29b-41d4-a716-446655440002",
      "status": "active",
      "competency_level": "expert",
      "issued_date": "2023-06-15",
      "expiration_date": "2025-02-10",
      "last_verified_date": "2024-12-20",
      "is_valid": true,
      "max_concurrent_residents": null,
      "max_per_week": 5,
      "max_per_academic_year": null,
      "notes": "Verified and competent",
      "created_at": "2023-06-15T10:30:00Z",
      "updated_at": "2024-12-20T14:45:00Z"
    }
  ],
  "total": 3
}
```

**Status Codes:**
- `200 OK`: Success
- `422 Unprocessable Entity`: Invalid days parameter

**Use Cases:**
```bash
# Credentials expiring in next 30 days
GET /api/v1/credentials/expiring?days=30

# Urgent: Expiring within 7 days
GET /api/v1/credentials/expiring?days=7

# Planning: Expiring within 90 days
GET /api/v1/credentials/expiring?days=90
```

---

### List Credentials for Person

```http
GET /api/v1/credentials/by-person/{person_id}
```

List all procedure credentials for a specific faculty member.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Faculty ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: 'active', 'expired', 'suspended', 'pending' |
| `include_expired` | boolean | No | Include expired credentials in response (default: false) |

**Response:** `CredentialListResponse`

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Person not found

**Examples:**

```bash
# Get all active credentials for a faculty member
GET /api/v1/credentials/by-person/550e8400-e29b-41d4-a716-446655440001?status=active

# Get all credentials including expired
GET /api/v1/credentials/by-person/550e8400-e29b-41d4-a716-446655440001?include_expired=true

# Get only suspended credentials
GET /api/v1/credentials/by-person/550e8400-e29b-41d4-a716-446655440001?status=suspended
```

---

### List Credentials for Procedure

```http
GET /api/v1/credentials/by-procedure/{procedure_id}
```

List all faculty credentials for a specific procedure.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: 'active', 'expired', 'suspended', 'pending' |
| `include_expired` | boolean | No | Include expired credentials (default: false) |

**Response:** `CredentialListResponse`

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Procedure not found

---

### Get Qualified Faculty for Procedure

```http
GET /api/v1/credentials/qualified-faculty/{procedure_id}
```

Get all faculty members qualified to supervise a specific procedure.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `procedure_id` | UUID | Yes | Procedure ID |

**Response:** `QualifiedFacultyResponse`

```json
{
  "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
  "procedure_name": "Mastectomy",
  "qualified_faculty": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. Jane Smith",
      "type": "faculty"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Dr. John Doe",
      "type": "faculty"
    }
  ],
  "total": 2
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Procedure not found

**Use Case:** When scheduling a procedure, check which faculty are qualified.

---

### Check Faculty Qualification

```http
GET /api/v1/credentials/check/{person_id}/{procedure_id}
```

Check if a specific faculty member is qualified to supervise a procedure.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Faculty ID |
| `procedure_id` | UUID | Yes | Procedure ID |

**Response:**

```json
{
  "is_qualified": true
}
```

**Status Codes:**
- `200 OK`: Always returns 200, check `is_qualified` field

**Use Case:** Gate scheduling decisions on faculty qualifications.

---

### Get Faculty Credential Summary

```http
GET /api/v1/credentials/summary/{person_id}
```

Get a summary of a faculty member's credentials.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Faculty ID |

**Response:** `FacultyCredentialSummary`

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_name": "Dr. Jane Smith",
  "total_credentials": 12,
  "active_credentials": 10,
  "expiring_soon": 2,
  "procedures": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Mastectomy",
      "specialty": "General Surgery",
      "category": "surgical"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "name": "Colposcopy",
      "specialty": "OB/GYN",
      "category": "office"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Person not found or not faculty

---

### Get Credential by ID

```http
GET /api/v1/credentials/{credential_id}
```

Get a specific credential by UUID.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `credential_id` | UUID | Yes | Credential ID |

**Response:** `CredentialResponse`

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Credential not found

---

### Create Credential

```http
POST /api/v1/credentials
```

Award a procedure credential to a faculty member. **Requires authentication.**

**Request Body:** `CredentialCreate`

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "competency_level": "qualified",
  "issued_date": "2025-01-15",
  "expiration_date": "2026-01-15",
  "last_verified_date": null,
  "max_concurrent_residents": null,
  "max_per_week": 5,
  "max_per_academic_year": null,
  "notes": "Credentialed in Jan 2025"
}
```

**Validation Rules:**
- `person_id`: Must exist and be faculty type
- `procedure_id`: Must exist
- `status`: One of 'active', 'expired', 'suspended', 'pending'
- `competency_level`: One of 'trainee', 'qualified', 'expert', 'master'
- `expiration_date` > `issued_date` (if both set)
- One credential per person-procedure pair (unique constraint)

**Response:** `CredentialResponse` (201 Created)

**Status Codes:**
- `201 Created`: Success
- `400 Bad Request`: Invalid data, person not faculty, duplicate credential, etc.
- `401 Unauthorized`: Missing/invalid authentication
- `422 Unprocessable Entity`: Validation error

**Error Examples:**
```json
// Person is not faculty
{
  "detail": "Only faculty can have procedure credentials"
}

// Duplicate credential
{
  "detail": "Credential already exists for Dr. Jane Smith and Mastectomy"
}

// Invalid expiration date
{
  "detail": "expiration_date (2025-01-15) must be after issued_date (2025-06-15)"
}
```

---

### Update Credential

```http
PUT /api/v1/credentials/{credential_id}
```

Update a credential. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `credential_id` | UUID | Yes | Credential ID |

**Request Body:** `CredentialUpdate` (all fields optional)

```json
{
  "status": "active",
  "expiration_date": "2027-01-15",
  "last_verified_date": "2025-01-15",
  "max_per_week": 10
}
```

**Response:** `CredentialResponse`

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Credential not found

---

### Suspend Credential

```http
POST /api/v1/credentials/{credential_id}/suspend
```

Suspend a credential temporarily. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `credential_id` | UUID | Yes | Credential ID |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notes` | string | No | Suspension reason (stored in credential notes) |

**Response:** `CredentialResponse` with `status: "suspended"`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Credential not found

**Use Cases:**
```bash
# Suspend due to competency concerns
POST /api/v1/credentials/{credential_id}/suspend?notes=Competency review pending

# Suspend temporarily
POST /api/v1/credentials/{credential_id}/suspend?notes=On leave until June 2025
```

---

### Activate Credential

```http
POST /api/v1/credentials/{credential_id}/activate
```

Reactivate a suspended credential. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `credential_id` | UUID | Yes | Credential ID |

**Response:** `CredentialResponse` with `status: "active"`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Credential not found

---

### Verify Credential

```http
POST /api/v1/credentials/{credential_id}/verify
```

Mark a credential as verified today (updates `last_verified_date`). **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `credential_id` | UUID | Yes | Credential ID |

**Response:** `CredentialResponse` with updated `last_verified_date`

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Credential not found

**Use Case:** Annual credentialing reviews - call this endpoint when credential is re-verified.

---

### Delete Credential

```http
DELETE /api/v1/credentials/{credential_id}
```

Delete a credential permanently. **Requires authentication.**

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `credential_id` | UUID | Yes | Credential ID |

**Status Codes:**
- `204 No Content`: Success
- `401 Unauthorized`: Missing/invalid authentication
- `404 Not Found`: Credential not found

---

## Credentialing Workflow

### Typical Workflow

```
1. Create Procedures (Admin)
   POST /procedures → Create "Mastectomy", "Colposcopy", etc.

2. Award Credentials to Faculty (Admin/Coordinator)
   POST /credentials → "Dr. Smith can do Mastectomy"
   POST /credentials → "Dr. Smith can do Colposcopy"

3. Check Qualifications (Scheduler)
   GET /credentials/qualified-faculty/{procedure_id} → See available faculty
   GET /credentials/check/{person_id}/{procedure_id} → Verify before scheduling

4. Monitor Expiration (Admin)
   GET /credentials/expiring?days=30 → Get expiring soon

5. Renew Credentials (Admin)
   POST /credentials/{id}/verify → Mark as verified
   PUT /credentials/{id} → Update expiration_date

6. Manage Issues (Admin)
   POST /credentials/{id}/suspend → Suspend due to concern
   POST /credentials/{id}/activate → Restore when resolved
```

### Batch Credential Grant

Use the service method `bulk_create_credentials` to grant multiple procedures to one faculty member:

**Note:** No direct API endpoint exists; use individual POST requests or coordinate via service layer.

```python
# Service-level example (from credential_service.py)
result = credential_service.bulk_create_credentials(
    person_id=faculty_id,
    procedure_ids=[proc1_id, proc2_id, proc3_id],
    competency_level="qualified",
    expiration_date=date(2026, 1, 15)
)
# Returns created credentials and errors
```

### Credential Validity

A credential is **valid** if:
1. Status is 'active'
2. Expiration date is NULL OR expiration_date >= today

Model property:
```python
@property
def is_valid(self) -> bool:
    if self.status != "active":
        return False
    return not (self.expiration_date and self.expiration_date < date.today())
```

---

## Data Models

### ProcedureResponse

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Mastectomy",
  "description": "Surgical removal of breast tissue",
  "category": "surgical",
  "specialty": "General Surgery",
  "supervision_ratio": 1,
  "requires_certification": true,
  "complexity_level": "advanced",
  "min_pgy_level": 2,
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### CredentialResponse

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440100",
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "competency_level": "qualified",
  "issued_date": "2025-01-15",
  "expiration_date": "2026-01-15",
  "last_verified_date": "2025-01-15",
  "is_valid": true,
  "max_concurrent_residents": null,
  "max_per_week": 5,
  "max_per_academic_year": null,
  "notes": "Credentialed in Jan 2025",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### FacultyCredentialSummary

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_name": "Dr. Jane Smith",
  "total_credentials": 12,
  "active_credentials": 10,
  "expiring_soon": 2,
  "procedures": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Mastectomy",
      "specialty": "General Surgery",
      "category": "surgical"
    }
  ]
}
```

### QualifiedFacultyResponse

```json
{
  "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
  "procedure_name": "Mastectomy",
  "qualified_faculty": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. Jane Smith",
      "type": "faculty"
    }
  ],
  "total": 1
}
```

---

## Validation Rules

### Procedure Creation/Update

| Field | Rule | Error |
|-------|------|-------|
| `name` | Unique, 1-255 chars | "Procedure with name '{name}' already exists" |
| `complexity_level` | One of: basic, standard, advanced, complex | "complexity_level must be one of..." |
| `min_pgy_level` | 1-3 | "min_pgy_level must be between 1 and 3" |
| `supervision_ratio` | >= 1 | "supervision_ratio must be at least 1" |

### Credential Creation/Update

| Field | Rule | Error |
|-------|------|-------|
| `person_id` | Must exist and be faculty | "Person not found" or "Only faculty can have procedure credentials" |
| `procedure_id` | Must exist | "Procedure not found" |
| `status` | One of: active, expired, suspended, pending | "status must be one of..." |
| `competency_level` | One of: trainee, qualified, expert, master | "competency_level must be one of..." |
| Unique constraint | One credential per (person_id, procedure_id) pair | "Credential already exists for {name} and {procedure}" |
| Date range | expiration_date > issued_date | "expiration_date must be after issued_date" |
| Dates | Must be valid calendar dates, not in far future | Validated by `validate_date_range()` |

---

## Compliance & Expiration Handling

### Credential Status Transitions

```
           create (status="active")
                    ↓
        Active & Valid
        (today < expiration OR no expiration)
       /                    \
      /                      \
   Manual Suspend      Natural Expiration
      ↓                      ↓
   Suspended           Expired
      ↓                      ↓
   Activate            Create New Credential
      ↓
   Back to Active
```

### Expiration Monitoring

The system provides several ways to track expiring credentials:

1. **Near Expiration Alert** (30 days):
   ```bash
   GET /credentials/expiring?days=30
   ```
   Use this in a daily background job to email admins.

2. **Faculty Summary** (built-in):
   ```bash
   GET /credentials/summary/{person_id}
   ```
   Returns `expiring_soon` count (within 30 days).

3. **Compliance Check** (before scheduling):
   Use `is_valid` property to reject scheduling with expired credentials:
   ```python
   if not credential.is_valid:
       raise SchedulingError("Credential expired")
   ```

### Supervision Capacity

Credentials can override procedure-level supervision limits:

```json
{
  "procedure": {
    "supervision_ratio": 2  // Default: 1 faculty per 2 residents
  },
  "credential": {
    "max_concurrent_residents": 1  // Override: this faculty can only supervise 1
  }
}
```

Scheduling should use:
```python
limit = credential.max_concurrent_residents or procedure.supervision_ratio
```

### Weekly/Annual Caps

Credentials can limit total supervisions:

```json
{
  "max_per_week": 5,           // No more than 5 supervisions per week
  "max_per_academic_year": 50  // No more than 50 supervisions per year
}
```

Enforce in scheduling logic before assigning.

---

## Integration Guide

### Integration Points

1. **Scheduling Engine**: Check qualified faculty and supervision limits
2. **Dashboard**: Show expiring credentials
3. **Admin Panel**: CRUD for procedures and credentials
4. **Assignment Validation**: Verify faculty has valid credential before scheduling
5. **Reporting**: Track credential coverage and gaps

### Common Integration Patterns

**Pattern 1: Check if Faculty Can Supervise**

```python
from app.services.credential_service import CredentialService

service = CredentialService(db)
is_qualified = service.is_faculty_qualified(faculty_id, procedure_id)

if not is_qualified:
    raise ValidationError(f"Faculty {faculty_id} not qualified for {procedure_id}")
```

**Pattern 2: Find All Available Supervisors**

```python
# Get qualified faculty for a procedure
qualified = service.list_qualified_faculty_for_procedure(procedure_id)
available_faculty = [f["id"] for f in qualified["qualified_faculty"]]

# Filter by supervision capacity
for faculty_id in available_faculty:
    credential = service.get_credential_for_person_procedure(faculty_id, procedure_id)
    if credential.is_valid:
        # Check capacity limits
        if has_capacity(credential, procedure):
            selected_faculty.append(faculty_id)
```

**Pattern 3: Dashboard Alert**

```python
# Show expiring credentials in next 30 days
expiring = service.list_expiring_credentials(days=30)

for cred in expiring["items"]:
    days_until = (cred.expiration_date - date.today()).days
    alert(f"Credential expires in {days_until} days")
```

**Pattern 4: Annual Renewal**

```python
# Get all credentials for a faculty member
summary = service.get_faculty_credential_summary(faculty_id)

for procedure_id in summary["procedures"]:
    credential = service.get_credential_for_person_procedure(faculty_id, procedure_id)

    # Check expiration and renew if needed
    if credential.expiration_date <= today + timedelta(days=30):
        service.update_credential(
            credential.id,
            {
                "expiration_date": today + timedelta(days=365),
                "last_verified_date": today
            }
        )
```

---

## Error Handling

### Common Error Codes

| HTTP Status | Error | Cause |
|-------------|-------|-------|
| 400 | "Procedure with name 'X' already exists" | Duplicate procedure name |
| 400 | "Only faculty can have procedure credentials" | Person not faculty |
| 400 | "Credential already exists for X and Y" | Duplicate credential |
| 404 | "Procedure not found" | Invalid procedure_id |
| 404 | "Person not found" | Invalid person_id |
| 404 | "Credential not found" | Invalid credential_id |
| 422 | Validation errors | Schema validation failure |

### Error Response Format

```json
{
  "detail": "Person not found"
}
```

### Handling Errors in Client Code

```python
try:
    response = requests.post(
        f"{BASE_URL}/credentials",
        json=credential_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 400:
        error = e.response.json()
        print(f"Validation error: {error['detail']}")
    elif e.response.status_code == 404:
        print("Resource not found")
    else:
        print(f"Unexpected error: {e}")
```

---

## Examples

### Example 1: Create Procedures

```bash
# Create a surgical procedure
curl -X POST http://localhost:8000/api/v1/procedures \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Mastectomy",
    "description": "Surgical removal of breast tissue",
    "category": "surgical",
    "specialty": "General Surgery",
    "complexity_level": "advanced",
    "supervision_ratio": 1,
    "requires_certification": true,
    "min_pgy_level": 2,
    "is_active": true
  }'

# Create an office procedure
curl -X POST http://localhost:8000/api/v1/procedures \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Colposcopy",
    "description": "Colposcopic examination of the cervix",
    "category": "office",
    "specialty": "OB/GYN",
    "complexity_level": "standard",
    "supervision_ratio": 2,
    "requires_certification": true,
    "min_pgy_level": 1,
    "is_active": true
  }'
```

### Example 2: Award Credentials to Faculty

```bash
# Give Dr. Smith credential for Mastectomy
curl -X POST http://localhost:8000/api/v1/credentials \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "competency_level": "expert",
    "issued_date": "2025-01-15",
    "expiration_date": "2026-01-15",
    "max_per_week": 5,
    "notes": "Expert in breast surgery"
  }'

# Response (201 Created):
# {
#   "id": "550e8400-e29b-41d4-a716-446655440100",
#   "person_id": "550e8400-e29b-41d4-a716-446655440001",
#   "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "active",
#   "competency_level": "expert",
#   "issued_date": "2025-01-15",
#   "expiration_date": "2026-01-15",
#   "last_verified_date": null,
#   "is_valid": true,
#   "max_per_week": 5,
#   "notes": "Expert in breast surgery",
#   "created_at": "2025-01-15T10:30:00Z",
#   "updated_at": "2025-01-15T10:30:00Z"
# }
```

### Example 3: Check Qualifications Before Scheduling

```bash
# Is Dr. Smith qualified for Mastectomy?
curl -X GET "http://localhost:8000/api/v1/credentials/check/550e8400-e29b-41d4-a716-446655440001/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {"is_qualified": true}

# Get all faculty qualified for Mastectomy
curl -X GET "http://localhost:8000/api/v1/credentials/qualified-faculty/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
#   "procedure_name": "Mastectomy",
#   "qualified_faculty": [
#     {
#       "id": "550e8400-e29b-41d4-a716-446655440001",
#       "name": "Dr. Jane Smith",
#       "type": "faculty"
#     },
#     {
#       "id": "550e8400-e29b-41d4-a716-446655440002",
#       "name": "Dr. John Doe",
#       "type": "faculty"
#     }
#   ],
#   "total": 2
# }
```

### Example 4: Monitor Expiring Credentials

```bash
# Get credentials expiring in next 30 days
curl -X GET "http://localhost:8000/api/v1/credentials/expiring?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get credentials expiring in next 7 days (urgent)
curl -X GET "http://localhost:8000/api/v1/credentials/expiring?days=7" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "items": [
#     {
#       "id": "550e8400-e29b-41d4-a716-446655440100",
#       "person_id": "550e8400-e29b-41d4-a716-446655440001",
#       "procedure_id": "550e8400-e29b-41d4-a716-446655440000",
#       "status": "active",
#       "competency_level": "qualified",
#       "expiration_date": "2025-02-10",
#       "is_valid": true,
#       ...
#     }
#   ],
#   "total": 1
# }
```

### Example 5: Renew a Credential

```bash
# Mark credential as verified today
curl -X POST http://localhost:8000/api/v1/credentials/550e8400-e29b-41d4-a716-446655440100/verify \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update expiration date
curl -X PUT http://localhost:8000/api/v1/credentials/550e8400-e29b-41d4-a716-446655440100 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "expiration_date": "2026-01-15",
    "last_verified_date": "2025-01-15"
  }'
```

### Example 6: Faculty Credential Summary

```bash
# Get summary of Dr. Smith's credentials
curl -X GET "http://localhost:8000/api/v1/credentials/summary/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response:
# {
#   "person_id": "550e8400-e29b-41d4-a716-446655440001",
#   "person_name": "Dr. Jane Smith",
#   "total_credentials": 12,
#   "active_credentials": 10,
#   "expiring_soon": 2,
#   "procedures": [
#     {
#       "id": "550e8400-e29b-41d4-a716-446655440000",
#       "name": "Mastectomy",
#       "specialty": "General Surgery",
#       "category": "surgical"
#     },
#     {
#       "id": "550e8400-e29b-41d4-a716-446655440003",
#       "name": "Colposcopy",
#       "specialty": "OB/GYN",
#       "category": "office"
#     }
#   ]
# }
```

---

## Additional Notes

### Database Schema

**procedures table:**
- `id` (UUID, PK)
- `name` (VARCHAR 255, UNIQUE)
- `description` (TEXT)
- `category` (VARCHAR 100)
- `specialty` (VARCHAR 100)
- `supervision_ratio` (INT, default=1)
- `requires_certification` (BOOLEAN, default=true)
- `complexity_level` (VARCHAR 50, default='standard')
- `min_pgy_level` (INT, default=1)
- `is_active` (BOOLEAN, default=true)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**procedure_credentials table:**
- `id` (UUID, PK)
- `person_id` (UUID, FK → people.id)
- `procedure_id` (UUID, FK → procedures.id)
- `status` (VARCHAR 50, default='active')
- `competency_level` (VARCHAR 50, default='qualified')
- `issued_date` (DATE)
- `expiration_date` (DATE, nullable)
- `last_verified_date` (DATE, nullable)
- `max_concurrent_residents` (INT, nullable)
- `max_per_week` (INT, nullable)
- `max_per_academic_year` (INT, nullable)
- `notes` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- **Unique Constraint:** (person_id, procedure_id)

### Related Documentation

- **Security**: PERSEC consideration - never export real procedure assignments in test/demo data
- **ACGME Compliance**: Ensure scheduling respects procedure supervision ratios
- **Scheduling Engine**: Must query this API before assigning residents to procedures
- **Audit Logging**: All credential changes are tracked in audit trails

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Maintained By:** G2_RECON (Session 6)
