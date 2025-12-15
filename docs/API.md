***REMOVED*** Residency Scheduler API Documentation

Complete API reference with curl examples for the Residency Scheduler backend.

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Authentication](***REMOVED***authentication)
3. [People API](***REMOVED***people-api)
4. [Rotation Templates API](***REMOVED***rotation-templates-api)
5. [Absences API](***REMOVED***absences-api)
6. [Schedule API](***REMOVED***schedule-api)
7. [Error Handling](***REMOVED***error-handling)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

***REMOVED******REMOVED******REMOVED*** Authentication

The API uses JWT Bearer token authentication. Obtain a token via the login endpoint and include it in the `Authorization` header for protected endpoints.

```bash
Authorization: Bearer <your_jwt_token>
```

***REMOVED******REMOVED******REMOVED*** Response Format

All successful responses return JSON. List endpoints return:

```json
{
  "items": [...],
  "total": 100
}
```

***REMOVED******REMOVED******REMOVED*** Health Check Endpoints

```bash
***REMOVED*** Basic health check
curl http://localhost:8000/

***REMOVED*** Response:
***REMOVED*** {
***REMOVED***   "name": "Residency Scheduler API",
***REMOVED***   "version": "1.0.0",
***REMOVED***   "status": "healthy"
***REMOVED*** }

***REMOVED*** Detailed health check
curl http://localhost:8000/health

***REMOVED*** Response:
***REMOVED*** {
***REMOVED***   "status": "healthy",
***REMOVED***   "database": "connected"
***REMOVED*** }
```

---

***REMOVED******REMOVED*** Authentication

Base path: `/api/auth`

***REMOVED******REMOVED******REMOVED*** Register User

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
***REMOVED*** Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john.doe@hospital.org",
    "password": "SecurePassword123!",
    "role": "coordinator"
  }'

***REMOVED*** Response (201 Created):
***REMOVED*** {
***REMOVED***   "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "username": "john.doe",
***REMOVED***   "email": "john.doe@hospital.org",
***REMOVED***   "role": "coordinator",
***REMOVED***   "is_active": true
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Login (Form Data - OAuth2)

Authenticates user and returns JWT token using OAuth2 password flow.

**Endpoint:** `POST /api/auth/login`

```bash
***REMOVED*** Login with form data (OAuth2 flow)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe&password=SecurePassword123!"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
***REMOVED***   "token_type": "bearer"
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Login (JSON)

Authenticates user using JSON request body.

**Endpoint:** `POST /api/auth/login/json`

```bash
***REMOVED*** Login with JSON body
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
***REMOVED***   "token_type": "bearer"
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Get Current User

Returns the authenticated user's information.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required

```bash
***REMOVED*** Get current user info
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_jwt_token>"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "username": "john.doe",
***REMOVED***   "email": "john.doe@hospital.org",
***REMOVED***   "role": "coordinator",
***REMOVED***   "is_active": true
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Logout

Logs out the current user (invalidates the session).

**Endpoint:** `POST /api/auth/logout`

**Authentication:** Required

```bash
***REMOVED*** Logout current user
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <your_jwt_token>"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "message": "Successfully logged out"
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** List Users (Admin Only)

Returns all users in the system.

**Endpoint:** `GET /api/auth/users`

**Authentication:** Required (Admin role)

```bash
***REMOVED*** List all users (admin only)
curl http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <admin_jwt_token>"

***REMOVED*** Response (200 OK):
***REMOVED*** [
***REMOVED***   {
***REMOVED***     "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***     "username": "john.doe",
***REMOVED***     "email": "john.doe@hospital.org",
***REMOVED***     "role": "coordinator",
***REMOVED***     "is_active": true
***REMOVED***   }
***REMOVED*** ]
```

---

***REMOVED******REMOVED*** People API

Base path: `/api/people`

Manages residents and faculty members.

***REMOVED******REMOVED******REMOVED*** List All People

Returns all people with optional filtering.

**Endpoint:** `GET /api/people`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `resident` or `faculty` |
| `pgy_level` | integer | No | Filter residents by PGY level (1-3) |

```bash
***REMOVED*** List all people
curl http://localhost:8000/api/people

***REMOVED*** List only residents
curl "http://localhost:8000/api/people?type=resident"

***REMOVED*** List PGY-2 residents
curl "http://localhost:8000/api/people?type=resident&pgy_level=2"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "items": [
***REMOVED***     {
***REMOVED***       "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***       "name": "Dr. Jane Smith",
***REMOVED***       "type": "resident",
***REMOVED***       "email": "jane.smith@hospital.org",
***REMOVED***       "pgy_level": 2,
***REMOVED***       "performs_procedures": false,
***REMOVED***       "specialties": null,
***REMOVED***       "primary_duty": null,
***REMOVED***       "created_at": "2024-01-01T00:00:00Z",
***REMOVED***       "updated_at": "2024-01-01T00:00:00Z"
***REMOVED***     }
***REMOVED***   ],
***REMOVED***   "total": 1
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** List Residents

Returns all residents with optional PGY level filtering.

**Endpoint:** `GET /api/people/residents`

```bash
***REMOVED*** List all residents
curl http://localhost:8000/api/people/residents

***REMOVED*** List PGY-1 residents only
curl "http://localhost:8000/api/people/residents?pgy_level=1"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "items": [...],
***REMOVED***   "total": 12
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** List Faculty

Returns all faculty with optional specialty filtering.

**Endpoint:** `GET /api/people/faculty`

```bash
***REMOVED*** List all faculty
curl http://localhost:8000/api/people/faculty

***REMOVED*** List faculty by specialty
curl "http://localhost:8000/api/people/faculty?specialty=Sports%20Medicine"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "items": [...],
***REMOVED***   "total": 8
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Get Person

Returns a specific person by ID.

**Endpoint:** `GET /api/people/{person_id}`

```bash
***REMOVED*** Get specific person
curl http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "name": "Dr. Jane Smith",
***REMOVED***   "type": "resident",
***REMOVED***   "email": "jane.smith@hospital.org",
***REMOVED***   "pgy_level": 2,
***REMOVED***   "performs_procedures": false,
***REMOVED***   "specialties": null,
***REMOVED***   "primary_duty": null,
***REMOVED***   "created_at": "2024-01-01T00:00:00Z",
***REMOVED***   "updated_at": "2024-01-01T00:00:00Z"
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Create Person

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
***REMOVED*** Create a resident
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

***REMOVED*** Create a faculty member
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

***REMOVED*** Response (201 Created):
***REMOVED*** {
***REMOVED***   "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "name": "Dr. Jane Smith",
***REMOVED***   "type": "resident",
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Update Person

Updates an existing person.

**Endpoint:** `PUT /api/people/{person_id}`

**Authentication:** Required

```bash
***REMOVED*** Update a person
curl -X PUT http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith-Jones",
    "pgy_level": 3,
    "performs_procedures": true
  }'

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "name": "Dr. Jane Smith-Jones",
***REMOVED***   "pgy_level": 3,
***REMOVED***   "performs_procedures": true,
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Delete Person

Deletes a person from the system.

**Endpoint:** `DELETE /api/people/{person_id}`

**Authentication:** Required

```bash
***REMOVED*** Delete a person
curl -X DELETE http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <your_jwt_token>"

***REMOVED*** Response (204 No Content)
```

---

***REMOVED******REMOVED*** Rotation Templates API

Base path: `/api/rotation-templates`

Manages rotation templates that define clinic activities and their requirements.

***REMOVED******REMOVED******REMOVED*** List Rotation Templates

Returns all rotation templates with optional filtering.

**Endpoint:** `GET /api/rotation-templates`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `activity_type` | string | No | Filter by type: `clinic`, `inpatient`, `procedure`, `conference` |

```bash
***REMOVED*** List all rotation templates
curl http://localhost:8000/api/rotation-templates

***REMOVED*** List only clinic templates
curl "http://localhost:8000/api/rotation-templates?activity_type=clinic"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "items": [
***REMOVED***     {
***REMOVED***       "id": "770e8400-e29b-41d4-a716-446655440000",
***REMOVED***       "name": "Sports Medicine Clinic",
***REMOVED***       "activity_type": "clinic",
***REMOVED***       "abbreviation": "SM",
***REMOVED***       "clinic_location": "Building A, Room 102",
***REMOVED***       "max_residents": 4,
***REMOVED***       "requires_specialty": "Sports Medicine",
***REMOVED***       "requires_procedure_credential": false,
***REMOVED***       "supervision_required": true,
***REMOVED***       "max_supervision_ratio": 4,
***REMOVED***       "created_at": "2024-01-01T00:00:00Z"
***REMOVED***     }
***REMOVED***   ],
***REMOVED***   "total": 1
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Get Rotation Template

Returns a specific rotation template.

**Endpoint:** `GET /api/rotation-templates/{template_id}`

```bash
***REMOVED*** Get specific template
curl http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "770e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "name": "Sports Medicine Clinic",
***REMOVED***   "activity_type": "clinic",
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Create Rotation Template

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
***REMOVED*** Create a rotation template
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

***REMOVED*** Response (201 Created):
***REMOVED*** {
***REMOVED***   "id": "770e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "name": "Sports Medicine Clinic",
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Update Rotation Template

Updates an existing rotation template.

**Endpoint:** `PUT /api/rotation-templates/{template_id}`

```bash
***REMOVED*** Update a rotation template
curl -X PUT http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "max_residents": 6,
    "max_supervision_ratio": 3
  }'

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "770e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "max_residents": 6,
***REMOVED***   "max_supervision_ratio": 3,
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Delete Rotation Template

Deletes a rotation template.

**Endpoint:** `DELETE /api/rotation-templates/{template_id}`

```bash
***REMOVED*** Delete a rotation template
curl -X DELETE http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000

***REMOVED*** Response (204 No Content)
```

---

***REMOVED******REMOVED*** Absences API

Base path: `/api/absences`

Manages person absences including vacation, deployment, TDY, and other leave types.

***REMOVED******REMOVED******REMOVED*** List Absences

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
***REMOVED*** List all absences
curl http://localhost:8000/api/absences

***REMOVED*** List absences for a date range
curl "http://localhost:8000/api/absences?start_date=2024-01-01&end_date=2024-03-31"

***REMOVED*** List absences for a specific person
curl "http://localhost:8000/api/absences?person_id=550e8400-e29b-41d4-a716-446655440000"

***REMOVED*** List only deployment absences
curl "http://localhost:8000/api/absences?absence_type=deployment"

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "items": [
***REMOVED***     {
***REMOVED***       "id": "990e8400-e29b-41d4-a716-446655440000",
***REMOVED***       "person_id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***       "start_date": "2024-02-01",
***REMOVED***       "end_date": "2024-02-15",
***REMOVED***       "absence_type": "deployment",
***REMOVED***       "deployment_orders": true,
***REMOVED***       "tdy_location": null,
***REMOVED***       "replacement_activity": null,
***REMOVED***       "notes": "Annual training deployment",
***REMOVED***       "created_at": "2024-01-15T00:00:00Z"
***REMOVED***     }
***REMOVED***   ],
***REMOVED***   "total": 1
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Get Absence

Returns a specific absence by ID.

**Endpoint:** `GET /api/absences/{absence_id}`

```bash
***REMOVED*** Get specific absence
curl http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "990e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "person_id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "start_date": "2024-02-01",
***REMOVED***   "end_date": "2024-02-15",
***REMOVED***   "absence_type": "deployment",
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Create Absence

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
***REMOVED*** Create a vacation absence
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-03-15",
    "end_date": "2024-03-22",
    "absence_type": "vacation",
    "notes": "Spring break vacation"
  }'

***REMOVED*** Create a deployment absence
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

***REMOVED*** Create a TDY absence
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

***REMOVED*** Response (201 Created):
***REMOVED*** {
***REMOVED***   "id": "990e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "person_id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "start_date": "2024-03-15",
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Update Absence

Updates an existing absence.

**Endpoint:** `PUT /api/absences/{absence_id}`

```bash
***REMOVED*** Update an absence
curl -X PUT http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "end_date": "2024-03-25",
    "notes": "Extended vacation by 3 days"
  }'

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "id": "990e8400-e29b-41d4-a716-446655440000",
***REMOVED***   "end_date": "2024-03-25",
***REMOVED***   "notes": "Extended vacation by 3 days",
***REMOVED***   ...
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Delete Absence

Deletes an absence record.

**Endpoint:** `DELETE /api/absences/{absence_id}`

```bash
***REMOVED*** Delete an absence
curl -X DELETE http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000

***REMOVED*** Response (204 No Content)
```

---

***REMOVED******REMOVED*** Schedule API

Base path: `/api/schedule`

Handles schedule generation, validation, and retrieval with ACGME compliance checking.

***REMOVED******REMOVED******REMOVED*** Get Schedule

Retrieves the schedule for a date range formatted for calendar view.

**Endpoint:** `GET /api/schedule/{start_date}/{end_date}`

```bash
***REMOVED*** Get schedule for a week
curl http://localhost:8000/api/schedule/2024-01-15/2024-01-21

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "start_date": "2024-01-15",
***REMOVED***   "end_date": "2024-01-21",
***REMOVED***   "schedule": {
***REMOVED***     "2024-01-15": {
***REMOVED***       "AM": [
***REMOVED***         {
***REMOVED***           "id": "880e8400-e29b-41d4-a716-446655440000",
***REMOVED***           "person": {
***REMOVED***             "id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***             "name": "Dr. Jane Smith",
***REMOVED***             "type": "resident",
***REMOVED***             "pgy_level": 2
***REMOVED***           },
***REMOVED***           "role": "primary",
***REMOVED***           "activity": "Sports Medicine Clinic",
***REMOVED***           "abbreviation": "SM"
***REMOVED***         }
***REMOVED***       ],
***REMOVED***       "PM": [
***REMOVED***         {
***REMOVED***           "id": "880e8400-e29b-41d4-a716-446655440001",
***REMOVED***           "person": {
***REMOVED***             "id": "550e8400-e29b-41d4-a716-446655440001",
***REMOVED***             "name": "Dr. Bob Wilson",
***REMOVED***             "type": "resident",
***REMOVED***             "pgy_level": 1
***REMOVED***           },
***REMOVED***           "role": "primary",
***REMOVED***           "activity": "Primary Care Clinic",
***REMOVED***           "abbreviation": "PC"
***REMOVED***         }
***REMOVED***       ]
***REMOVED***     },
***REMOVED***     "2024-01-16": {
***REMOVED***       "AM": [...],
***REMOVED***       "PM": [...]
***REMOVED***     }
***REMOVED***   },
***REMOVED***   "total_assignments": 42
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** Generate Schedule

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
***REMOVED*** Generate schedule for 6 months
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "algorithm": "greedy"
  }'

***REMOVED*** Generate schedule for specific PGY levels
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "pgy_levels": [1, 2],
    "algorithm": "min_conflicts"
  }'

***REMOVED*** Generate schedule for specific rotation templates
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

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "status": "success",
***REMOVED***   "message": "Schedule generated successfully",
***REMOVED***   "total_blocks_assigned": 2920,
***REMOVED***   "total_blocks": 3650,
***REMOVED***   "validation": {
***REMOVED***     "valid": true,
***REMOVED***     "total_violations": 0,
***REMOVED***     "violations": [],
***REMOVED***     "coverage_rate": 80.0,
***REMOVED***     "statistics": {
***REMOVED***       "total_assignments": 2920,
***REMOVED***       "total_blocks": 3650,
***REMOVED***       "residents_scheduled": 24
***REMOVED***     }
***REMOVED***   },
***REMOVED***   "run_id": "aa0e8400-e29b-41d4-a716-446655440000"
***REMOVED*** }
```

**Response Status Values:**
- `success` - All blocks assigned, no violations
- `partial` - Some blocks unassigned or violations present
- `failed` - Critical error during generation

***REMOVED******REMOVED******REMOVED*** Validate Schedule (ACGME Compliance)

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
***REMOVED*** Validate schedule compliance
curl "http://localhost:8000/api/schedule/validate?start_date=2024-01-01&end_date=2024-03-31"

***REMOVED*** Response with violations (200 OK):
***REMOVED*** {
***REMOVED***   "valid": false,
***REMOVED***   "total_violations": 2,
***REMOVED***   "violations": [
***REMOVED***     {
***REMOVED***       "type": "80_HOUR_VIOLATION",
***REMOVED***       "severity": "CRITICAL",
***REMOVED***       "person_id": "550e8400-e29b-41d4-a716-446655440000",
***REMOVED***       "person_name": "Dr. Jane Smith",
***REMOVED***       "block_id": null,
***REMOVED***       "message": "Dr. Jane Smith: 82.5 hours/week average (limit: 80)",
***REMOVED***       "details": {
***REMOVED***         "window_start": "2024-01-01",
***REMOVED***         "window_end": "2024-01-28",
***REMOVED***         "average_weekly_hours": 82.5
***REMOVED***       }
***REMOVED***     },
***REMOVED***     {
***REMOVED***       "type": "1_IN_7_VIOLATION",
***REMOVED***       "severity": "HIGH",
***REMOVED***       "person_id": "550e8400-e29b-41d4-a716-446655440001",
***REMOVED***       "person_name": "Dr. Bob Wilson",
***REMOVED***       "block_id": null,
***REMOVED***       "message": "Dr. Bob Wilson: No day off in 8 consecutive days",
***REMOVED***       "details": {
***REMOVED***         "consecutive_days": 8,
***REMOVED***         "period_start": "2024-01-08",
***REMOVED***         "period_end": "2024-01-15"
***REMOVED***       }
***REMOVED***     }
***REMOVED***   ],
***REMOVED***   "coverage_rate": 95.5,
***REMOVED***   "statistics": {
***REMOVED***     "total_assignments": 3500,
***REMOVED***     "total_blocks": 3650,
***REMOVED***     "residents_scheduled": 24
***REMOVED***   }
***REMOVED*** }

***REMOVED*** Response without violations (200 OK):
***REMOVED*** {
***REMOVED***   "valid": true,
***REMOVED***   "total_violations": 0,
***REMOVED***   "violations": [],
***REMOVED***   "coverage_rate": 98.2,
***REMOVED***   "statistics": {
***REMOVED***     "total_assignments": 3580,
***REMOVED***     "total_blocks": 3650,
***REMOVED***     "residents_scheduled": 24
***REMOVED***   }
***REMOVED*** }
```

**Violation Types:**
| Type | Severity | Description |
|------|----------|-------------|
| `80_HOUR_VIOLATION` | CRITICAL | Resident exceeds 80 hours/week average |
| `1_IN_7_VIOLATION` | HIGH | Resident missing required day off |
| `SUPERVISION_RATIO_VIOLATION` | CRITICAL | Insufficient faculty supervision |
| `CONSECUTIVE_DUTY_VIOLATION` | HIGH | Too many consecutive duty days |

***REMOVED******REMOVED******REMOVED*** Emergency Coverage

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
***REMOVED*** Request emergency coverage
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

***REMOVED*** Response (200 OK):
***REMOVED*** {
***REMOVED***   "status": "partial",
***REMOVED***   "replacements_found": 8,
***REMOVED***   "coverage_gaps": 2,
***REMOVED***   "requires_manual_review": true,
***REMOVED***   "details": [
***REMOVED***     {
***REMOVED***       "date": "2024-01-20",
***REMOVED***       "time_of_day": "AM",
***REMOVED***       "original_assignment": "Sports Medicine Clinic",
***REMOVED***       "replacement": {
***REMOVED***         "person_id": "550e8400-e29b-41d4-a716-446655440002",
***REMOVED***         "person_name": "Dr. Bob Wilson"
***REMOVED***       },
***REMOVED***       "status": "covered"
***REMOVED***     },
***REMOVED***     {
***REMOVED***       "date": "2024-01-20",
***REMOVED***       "time_of_day": "PM",
***REMOVED***       "original_assignment": "Primary Care Clinic",
***REMOVED***       "replacement": null,
***REMOVED***       "status": "gap"
***REMOVED***     }
***REMOVED***   ]
***REMOVED*** }
```

**Response Status Values:**
- `success` - All slots covered
- `partial` - Some slots have gaps requiring manual review
- `failed` - Unable to find any coverage

---

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** HTTP Status Codes

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

***REMOVED******REMOVED******REMOVED*** Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

***REMOVED******REMOVED******REMOVED*** Common Errors

```bash
***REMOVED*** Authentication required (401)
curl http://localhost:8000/api/people \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

***REMOVED*** Response:
***REMOVED*** {
***REMOVED***   "detail": "Not authenticated"
***REMOVED*** }

***REMOVED*** Invalid token (401)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer invalid_token"

***REMOVED*** Response:
***REMOVED*** {
***REMOVED***   "detail": "Could not validate credentials"
***REMOVED*** }

***REMOVED*** Resource not found (404)
curl http://localhost:8000/api/people/nonexistent-id

***REMOVED*** Response:
***REMOVED*** {
***REMOVED***   "detail": "Person not found"
***REMOVED*** }

***REMOVED*** Validation error (400)
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "type": "resident"}'

***REMOVED*** Response:
***REMOVED*** {
***REMOVED***   "detail": "PGY level required for residents"
***REMOVED*** }
```

---

***REMOVED******REMOVED*** Rate Limiting

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

***REMOVED******REMOVED*** Versioning

The API uses URL path versioning. Current version: v1 (implicit in `/api` prefix).

Future versions will be available at `/api/v2`, etc.

---

*End of API Documentation*
