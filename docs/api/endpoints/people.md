# People Endpoints

Base path: `/api/people`

Manages residents and faculty members in the scheduling system.

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List all people | No |
| GET | `/residents` | List residents only | No |
| GET | `/faculty` | List faculty only | No |
| GET | `/{person_id}` | Get person by ID | No |
| POST | `/` | Create a person | Yes |
| PUT | `/{person_id}` | Update a person | Yes |
| DELETE | `/{person_id}` | Delete a person | Yes |

---

## GET /api/people

Returns a list of all people with optional filtering.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `resident` or `faculty` |
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) |

### Example Requests

```bash
# List all people
curl http://localhost:8000/api/people

# List only residents
curl "http://localhost:8000/api/people?type=resident"

# List PGY-2 residents
curl "http://localhost:8000/api/people?type=resident&pgy_level=2"

# List only faculty
curl "http://localhost:8000/api/people?type=faculty"
```

### Response

**Status:** `200 OK`

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
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. Robert Johnson",
      "type": "faculty",
      "email": "robert.johnson@hospital.org",
      "pgy_level": null,
      "performs_procedures": true,
      "specialties": ["Sports Medicine", "Primary Care"],
      "primary_duty": "Sports Medicine Clinic",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

---

## GET /api/people/residents

Returns a list of all residents with optional PGY level filtering.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) |

### Example Requests

```bash
# List all residents
curl http://localhost:8000/api/people/residents

# List PGY-1 residents only
curl "http://localhost:8000/api/people/residents?pgy_level=1"
```

### Response

**Status:** `200 OK`

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

---

## GET /api/people/faculty

Returns a list of all faculty members with optional specialty filtering.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `specialty` | string | No | Filter by specialty |

### Example Requests

```bash
# List all faculty
curl http://localhost:8000/api/people/faculty

# List faculty by specialty
curl "http://localhost:8000/api/people/faculty?specialty=Sports%20Medicine"
```

### Response

**Status:** `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. Robert Johnson",
      "type": "faculty",
      "email": "robert.johnson@hospital.org",
      "pgy_level": null,
      "performs_procedures": true,
      "specialties": ["Sports Medicine", "Primary Care"],
      "primary_duty": "Sports Medicine Clinic",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

## GET /api/people/{person_id}

Returns a specific person by their UUID.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person's unique identifier |

### Example Request

```bash
curl http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000
```

### Response

**Status:** `200 OK`

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

### Errors

| Status | Description |
|--------|-------------|
| 404 | Person not found |

```json
{
  "detail": "Person not found"
}
```

---

## POST /api/people

Creates a new person (resident or faculty member).

**Authentication Required**

### Request Body

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

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | Max 255 characters |
| `type` | string | Yes | `resident` or `faculty` |
| `email` | string | No | Valid email format |
| `pgy_level` | integer | Yes (for residents) | 1, 2, or 3 |
| `performs_procedures` | boolean | No | Default: `false` |
| `specialties` | string[] | No | Array of specialty names |
| `primary_duty` | string | No | Primary duty assignment |

### Example Requests

**Create a Resident:**

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith",
    "type": "resident",
    "email": "jane.smith@hospital.org",
    "pgy_level": 2,
    "performs_procedures": false
  }'
```

**Create a Faculty Member:**

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Robert Johnson",
    "type": "faculty",
    "email": "robert.johnson@hospital.org",
    "specialties": ["Sports Medicine", "Primary Care"],
    "performs_procedures": true,
    "primary_duty": "Sports Medicine Clinic"
  }'
```

### Response

**Status:** `201 Created`

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

### Errors

| Status | Description |
|--------|-------------|
| 400 | PGY level required for residents |
| 400 | Invalid type value |
| 401 | Not authenticated |
| 422 | Validation error |

```json
{
  "detail": "PGY level required for residents"
}
```

---

## PUT /api/people/{person_id}

Updates an existing person. Only provided fields are updated.

**Authentication Required**

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person's unique identifier |

### Request Body

All fields are optional:

```json
{
  "name": "Dr. Jane Smith-Jones",
  "email": "jane.jones@hospital.org",
  "pgy_level": 3,
  "performs_procedures": true
}
```

### Example Request

```bash
curl -X PUT http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith-Jones",
    "pgy_level": 3,
    "performs_procedures": true
  }'
```

### Response

**Status:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Dr. Jane Smith-Jones",
  "type": "resident",
  "email": "jane.smith@hospital.org",
  "pgy_level": 3,
  "performs_procedures": true,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 404 | Person not found |
| 422 | Validation error |

---

## DELETE /api/people/{person_id}

Deletes a person from the system.

**Authentication Required**

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | Yes | Person's unique identifier |

### Example Request

```bash
curl -X DELETE http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

### Response

**Status:** `204 No Content`

### Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 404 | Person not found |

---

## Person Types

### Resident

Residents are medical trainees with PGY (Post-Graduate Year) levels:

| PGY Level | Description |
|-----------|-------------|
| 1 | First-year resident (intern) |
| 2 | Second-year resident |
| 3 | Third-year resident |

**Required Fields:**
- `name`
- `type`: `"resident"`
- `pgy_level`: 1, 2, or 3

### Faculty

Faculty are attending physicians who supervise residents:

**Required Fields:**
- `name`
- `type`: `"faculty"`

**Optional Fields:**
- `specialties`: Array of specialty names
- `primary_duty`: Primary duty assignment
- `performs_procedures`: Whether they perform procedures

---

## Usage Examples

### Bulk Import Residents

```bash
# Import multiple residents
for name in "Dr. Smith" "Dr. Jones" "Dr. Wilson"; do
  curl -X POST http://localhost:8000/api/people \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"$name\",
      \"type\": \"resident\",
      \"pgy_level\": 1
    }"
done
```

### Update PGY Level for Year Advancement

```bash
# Get all PGY-2 residents and advance to PGY-3
RESIDENTS=$(curl -s "http://localhost:8000/api/people/residents?pgy_level=2")

for id in $(echo $RESIDENTS | jq -r '.items[].id'); do
  curl -X PUT "http://localhost:8000/api/people/$id" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"pgy_level": 3}'
done
```

---

*See also: [Schemas](../schemas.md) for complete field definitions*
