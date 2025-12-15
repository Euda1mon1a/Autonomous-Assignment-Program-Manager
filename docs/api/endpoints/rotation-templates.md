***REMOVED*** Rotation Templates Endpoints

Base path: `/api/rotation-templates`

Manages rotation templates that define clinic activities, procedures, and their requirements.

***REMOVED******REMOVED*** Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List all templates | No |
| GET | `/{template_id}` | Get template by ID | No |
| POST | `/` | Create a template | No |
| PUT | `/{template_id}` | Update a template | No |
| DELETE | `/{template_id}` | Delete a template | No |

---

***REMOVED******REMOVED*** GET /api/rotation-templates

Returns a list of all rotation templates with optional filtering.

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `activity_type` | string | No | Filter by type: `clinic`, `inpatient`, `procedure`, `conference` |

***REMOVED******REMOVED******REMOVED*** Example Requests

```bash
***REMOVED*** List all rotation templates
curl http://localhost:8000/api/rotation-templates

***REMOVED*** List only clinic templates
curl "http://localhost:8000/api/rotation-templates?activity_type=clinic"

***REMOVED*** List procedure templates
curl "http://localhost:8000/api/rotation-templates?activity_type=procedure"
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

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
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "name": "Joint Injection Procedures",
      "activity_type": "procedure",
      "abbreviation": "JI",
      "clinic_location": "Procedure Suite B",
      "max_residents": 2,
      "requires_specialty": "Sports Medicine",
      "requires_procedure_credential": true,
      "supervision_required": true,
      "max_supervision_ratio": 2,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

---

***REMOVED******REMOVED*** GET /api/rotation-templates/{template_id}

Returns a specific rotation template by its UUID.

***REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | UUID | Yes | Template's unique identifier |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
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
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 404 | Rotation template not found |

```json
{
  "detail": "Rotation template not found"
}
```

---

***REMOVED******REMOVED*** POST /api/rotation-templates

Creates a new rotation template.

***REMOVED******REMOVED******REMOVED*** Request Body

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

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique template name |
| `activity_type` | string | Yes | `clinic`, `inpatient`, `procedure`, `conference` |
| `abbreviation` | string | No | Short code (max 10 chars) |
| `clinic_location` | string | No | Physical location description |
| `max_residents` | integer | No | Maximum residents per session |
| `requires_specialty` | string | No | Required faculty specialty |
| `requires_procedure_credential` | boolean | No | Default: `false` |
| `supervision_required` | boolean | No | Default: `true` |
| `max_supervision_ratio` | integer | No | Default: 4 (1:4 ratio) |

***REMOVED******REMOVED******REMOVED*** Example Requests

**Create a Clinic Template:**

```bash
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sports Medicine Clinic",
    "activity_type": "clinic",
    "abbreviation": "SM",
    "clinic_location": "Building A, Room 102",
    "max_residents": 4,
    "requires_specialty": "Sports Medicine",
    "supervision_required": true,
    "max_supervision_ratio": 4
  }'
```

**Create a Procedure Template:**

```bash
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Joint Injection Procedures",
    "activity_type": "procedure",
    "abbreviation": "JI",
    "clinic_location": "Procedure Suite B",
    "max_residents": 2,
    "requires_specialty": "Sports Medicine",
    "requires_procedure_credential": true,
    "supervision_required": true,
    "max_supervision_ratio": 2
  }'
```

**Create a Conference Template:**

```bash
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Grand Rounds",
    "activity_type": "conference",
    "abbreviation": "GR",
    "clinic_location": "Lecture Hall A",
    "max_residents": 30,
    "supervision_required": false
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `201 Created`

```json
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
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 400 | Template name already exists |
| 422 | Validation error |

---

***REMOVED******REMOVED*** PUT /api/rotation-templates/{template_id}

Updates an existing rotation template. Only provided fields are updated.

***REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | UUID | Yes | Template's unique identifier |

***REMOVED******REMOVED******REMOVED*** Request Body

All fields are optional:

```json
{
  "max_residents": 6,
  "max_supervision_ratio": 3,
  "clinic_location": "Building B, Room 205"
}
```

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X PUT http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "max_residents": 6,
    "max_supervision_ratio": 3
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "name": "Sports Medicine Clinic",
  "activity_type": "clinic",
  "abbreviation": "SM",
  "clinic_location": "Building A, Room 102",
  "max_residents": 6,
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 3,
  "created_at": "2024-01-01T00:00:00Z"
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 404 | Rotation template not found |
| 422 | Validation error |

---

***REMOVED******REMOVED*** DELETE /api/rotation-templates/{template_id}

Deletes a rotation template.

***REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | UUID | Yes | Template's unique identifier |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X DELETE http://localhost:8000/api/rotation-templates/770e8400-e29b-41d4-a716-446655440000
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `204 No Content`

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 404 | Rotation template not found |

---

***REMOVED******REMOVED*** Activity Types

| Type | Description | Example |
|------|-------------|---------|
| `clinic` | Outpatient clinic sessions | Sports Medicine Clinic, Primary Care Clinic |
| `inpatient` | Hospital ward rotations | Hospital Medicine, ICU |
| `procedure` | Procedural training | Joint Injections, EMG Studies |
| `conference` | Educational sessions | Grand Rounds, Journal Club |

---

***REMOVED******REMOVED*** Supervision Ratios

The `max_supervision_ratio` field defines how many residents one faculty can supervise:

| Ratio | Meaning | Typical Use |
|-------|---------|-------------|
| 1 | 1 faculty per 1 resident | Procedures |
| 2 | 1 faculty per 2 residents | High-acuity clinics |
| 4 | 1 faculty per 4 residents | Standard clinics |

ACGME requirements by PGY level:
- **PGY-1**: Maximum 1:2 ratio
- **PGY-2/3**: Maximum 1:4 ratio

---

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Create Complete Clinic Schedule

```bash
***REMOVED*** Create all clinic templates for a program

***REMOVED*** Sports Medicine Clinic
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sports Medicine Clinic",
    "activity_type": "clinic",
    "abbreviation": "SM",
    "max_residents": 4,
    "requires_specialty": "Sports Medicine"
  }'

***REMOVED*** Primary Care Clinic
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Primary Care Clinic",
    "activity_type": "clinic",
    "abbreviation": "PC",
    "max_residents": 6
  }'

***REMOVED*** Musculoskeletal Clinic
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Musculoskeletal Clinic",
    "activity_type": "clinic",
    "abbreviation": "MSK",
    "max_residents": 3,
    "requires_specialty": "Physical Medicine"
  }'
```

***REMOVED******REMOVED******REMOVED*** List Templates by Type

```bash
***REMOVED*** Get all clinic activities
curl "http://localhost:8000/api/rotation-templates?activity_type=clinic"

***REMOVED*** Get all procedure activities
curl "http://localhost:8000/api/rotation-templates?activity_type=procedure"
```

---

*See also: [Assignments](./assignments.md) for using templates in assignments*
