# Absences Endpoints

Base path: `/api/absences`

Manages person absences including vacation, military deployment, TDY, medical leave, and other absence types.

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List absences with filtering | No |
| GET | `/{absence_id}` | Get absence by ID | No |
| POST | `/` | Create an absence | No |
| PUT | `/{absence_id}` | Update an absence | No |
| DELETE | `/{absence_id}` | Delete an absence | No |

---

## GET /api/absences

Returns a list of absences with optional filtering.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter absences starting from (YYYY-MM-DD) |
| `end_date` | date | No | Filter absences ending by (YYYY-MM-DD) |
| `person_id` | UUID | No | Filter by person |
| `absence_type` | string | No | Filter by absence type |

### Example Requests

```bash
# List all absences
curl http://localhost:8000/api/absences

# List absences for a date range
curl "http://localhost:8000/api/absences?start_date=2024-01-01&end_date=2024-03-31"

# List absences for a specific person
curl "http://localhost:8000/api/absences?person_id=550e8400-e29b-41d4-a716-446655440000"

# List only deployment absences
curl "http://localhost:8000/api/absences?absence_type=deployment"

# Combined filters
curl "http://localhost:8000/api/absences?start_date=2024-01-01&absence_type=vacation"
```

### Response

**Status:** `200 OK`

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
    },
    {
      "id": "990e8400-e29b-41d4-a716-446655440001",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "start_date": "2024-03-15",
      "end_date": "2024-03-22",
      "absence_type": "vacation",
      "deployment_orders": false,
      "tdy_location": null,
      "replacement_activity": null,
      "notes": "Spring break vacation",
      "created_at": "2024-02-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

---

## GET /api/absences/{absence_id}

Returns a specific absence by its UUID.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `absence_id` | UUID | Yes | Absence's unique identifier |

### Example Request

```bash
curl http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000
```

### Response

**Status:** `200 OK`

```json
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
```

### Errors

| Status | Description |
|--------|-------------|
| 404 | Absence not found |

```json
{
  "detail": "Absence not found"
}
```

---

## POST /api/absences

Creates a new absence record.

### Request Body

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-15",
  "absence_type": "deployment",
  "deployment_orders": true,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Annual training deployment"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Must reference existing person |
| `start_date` | date | Yes | YYYY-MM-DD format |
| `end_date` | date | Yes | Must be >= start_date |
| `absence_type` | string | Yes | See valid types below |
| `deployment_orders` | boolean | No | Has deployment orders (default: `false`) |
| `tdy_location` | string | No | TDY location if applicable |
| `replacement_activity` | string | No | Activity during absence |
| `notes` | string | No | Additional notes |

### Valid Absence Types

| Type | Description | Use Case |
|------|-------------|----------|
| `vacation` | Personal vacation time | Planned time off |
| `deployment` | Military deployment | Active duty deployment |
| `tdy` | Temporary duty assignment | Training or temporary assignment |
| `medical` | Medical leave | Illness or medical procedure |
| `family_emergency` | Family emergency leave | Urgent family matters |
| `conference` | Conference attendance | Educational conferences |

### Example Requests

**Create a Vacation Absence:**

```bash
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-03-15",
    "end_date": "2024-03-22",
    "absence_type": "vacation",
    "notes": "Spring break vacation"
  }'
```

**Create a Deployment Absence:**

```bash
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
```

**Create a TDY Absence:**

```bash
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
```

**Create a Conference Absence:**

```bash
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-06-20",
    "end_date": "2024-06-23",
    "absence_type": "conference",
    "notes": "ACSM Annual Meeting",
    "replacement_activity": "Research presentation"
  }'
```

### Response

**Status:** `201 Created`

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-03-15",
  "end_date": "2024-03-22",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Spring break vacation",
  "created_at": "2024-02-15T10:30:00Z"
}
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid date range (end_date before start_date) |
| 400 | Invalid absence type |
| 404 | Person not found |
| 422 | Validation error |

```json
{
  "detail": "end_date must be greater than or equal to start_date"
}
```

---

## PUT /api/absences/{absence_id}

Updates an existing absence. Only provided fields are updated.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `absence_id` | UUID | Yes | Absence's unique identifier |

### Request Body

All fields are optional:

```json
{
  "end_date": "2024-03-25",
  "notes": "Extended vacation by 3 days"
}
```

### Example Request

```bash
curl -X PUT http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "end_date": "2024-03-25",
    "notes": "Extended vacation by 3 days"
  }'
```

### Response

**Status:** `200 OK`

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-03-15",
  "end_date": "2024-03-25",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Extended vacation by 3 days",
  "created_at": "2024-02-15T10:30:00Z"
}
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid date range |
| 404 | Absence not found |
| 422 | Validation error |

---

## DELETE /api/absences/{absence_id}

Deletes an absence record.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `absence_id` | UUID | Yes | Absence's unique identifier |

### Example Request

```bash
curl -X DELETE http://localhost:8000/api/absences/990e8400-e29b-41d4-a716-446655440000
```

### Response

**Status:** `204 No Content`

### Errors

| Status | Description |
|--------|-------------|
| 404 | Absence not found |

---

## Integration with Scheduling

Absences affect schedule generation:

1. **Automatic Exclusion**: Absent persons are excluded from schedule generation
2. **Emergency Coverage**: Use `/api/schedule/emergency-coverage` for last-minute absences
3. **Conflict Detection**: Creating assignments during absence periods generates warnings

### Emergency Coverage Flow

When a person needs emergency coverage:

```bash
# 1. Record the absence
curl -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "'$PERSON_ID'",
    "start_date": "2024-01-20",
    "end_date": "2024-01-25",
    "absence_type": "family_emergency",
    "notes": "Family emergency"
  }'

# 2. Request emergency coverage
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "'$PERSON_ID'",
    "start_date": "2024-01-20",
    "end_date": "2024-01-25",
    "reason": "Family emergency"
  }'
```

---

## Usage Examples

### Get Upcoming Absences

```bash
# Get absences for next 30 days
TODAY=$(date +%Y-%m-%d)
END=$(date -d "+30 days" +%Y-%m-%d)

curl "http://localhost:8000/api/absences?start_date=$TODAY&end_date=$END"
```

### Check Person's Absences

```bash
# Get all absences for a specific person
curl "http://localhost:8000/api/absences?person_id=550e8400-e29b-41d4-a716-446655440000"
```

### Track Deployments

```bash
# Get all deployment absences
curl "http://localhost:8000/api/absences?absence_type=deployment"
```

### Bulk Import Absences

```bash
# Import vacation schedule from a file
while IFS=',' read -r person_id start_date end_date notes; do
  curl -X POST http://localhost:8000/api/absences \
    -H "Content-Type: application/json" \
    -d "{
      \"person_id\": \"$person_id\",
      \"start_date\": \"$start_date\",
      \"end_date\": \"$end_date\",
      \"absence_type\": \"vacation\",
      \"notes\": \"$notes\"
    }"
done < vacations.csv
```

---

*See also: [Schedule Emergency Coverage](./schedule.md#emergency-coverage) for handling last-minute absences*
