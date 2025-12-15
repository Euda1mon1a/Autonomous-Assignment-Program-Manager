***REMOVED*** Assignments Endpoints

Base path: `/api/assignments`

Manages person assignments to schedule blocks with ACGME compliance validation.

***REMOVED******REMOVED*** Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List assignments with filtering | Yes |
| GET | `/{assignment_id}` | Get assignment by ID | Yes |
| POST | `/` | Create an assignment | Yes (Scheduler) |
| PUT | `/{assignment_id}` | Update an assignment | Yes (Scheduler) |
| DELETE | `/{assignment_id}` | Delete an assignment | Yes (Scheduler) |
| DELETE | `/` | Bulk delete assignments | Yes (Scheduler) |

**Note:** "Scheduler" role means admin or coordinator.

---

***REMOVED******REMOVED*** GET /api/assignments

Returns a list of assignments with optional filtering.

**Authentication Required**

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Filter from this date (YYYY-MM-DD) |
| `end_date` | date | No | Filter until this date (YYYY-MM-DD) |
| `person_id` | UUID | No | Filter by person |
| `role` | string | No | Filter by role: `primary`, `supervising`, `backup` |

***REMOVED******REMOVED******REMOVED*** Example Requests

```bash
***REMOVED*** List all assignments
curl http://localhost:8000/api/assignments \
  -H "Authorization: Bearer <token>"

***REMOVED*** List assignments for a date range
curl "http://localhost:8000/api/assignments?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <token>"

***REMOVED*** List assignments for a specific person
curl "http://localhost:8000/api/assignments?person_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <token>"

***REMOVED*** List all supervising assignments
curl "http://localhost:8000/api/assignments?role=supervising" \
  -H "Authorization: Bearer <token>"
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

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
      "updated_at": "2024-01-01T00:00:00Z",
      "override_acknowledged_at": null
    }
  ],
  "total": 1
}
```

---

***REMOVED******REMOVED*** GET /api/assignments/{assignment_id}

Returns a specific assignment by its UUID.

**Authentication Required**

***REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment's unique identifier |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl http://localhost:8000/api/assignments/880e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "primary",
  "activity_override": null,
  "notes": "Coverage for Dr. Jones",
  "created_by": "coordinator@hospital.org",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "override_acknowledged_at": null
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 404 | Assignment not found |

---

***REMOVED******REMOVED*** POST /api/assignments

Creates a new assignment. Validates ACGME compliance and returns warnings if violations detected.

**Authentication Required** (admin or coordinator)

***REMOVED******REMOVED******REMOVED*** Request Body

```json
{
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "primary",
  "activity_override": null,
  "notes": "Coverage for Dr. Jones",
  "override_reason": null
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `block_id` | UUID | Yes | Must reference existing block |
| `person_id` | UUID | Yes | Must reference existing person |
| `rotation_template_id` | UUID | No | Template for this assignment |
| `role` | string | Yes | `primary`, `supervising`, or `backup` |
| `activity_override` | string | No | Override activity name from template |
| `notes` | string | No | Assignment notes |
| `override_reason` | string | No | Reason for ACGME override |

***REMOVED******REMOVED******REMOVED*** Example Requests

**Create Resident Assignment:**

```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "660e8400-e29b-41d4-a716-446655440000",
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
    "role": "primary"
  }'
```

**Create Faculty Supervising Assignment:**

```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "660e8400-e29b-41d4-a716-446655440000",
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
    "role": "supervising"
  }'
```

**Create Backup Assignment:**

```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "660e8400-e29b-41d4-a716-446655440000",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "role": "backup",
    "notes": "On-call backup"
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `201 Created`

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "created_by": "coordinator@hospital.org",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "override_acknowledged_at": null,
  "acgme_warnings": [],
  "is_compliant": true
}
```

***REMOVED******REMOVED******REMOVED*** Response with ACGME Warnings

If the assignment creates ACGME compliance issues:

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "block_id": "...",
  "person_id": "...",
  "role": "primary",
  "acgme_warnings": [
    "Approaching 80-hour weekly limit (78.5 hours this week)"
  ],
  "is_compliant": true
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 400 | Person already assigned to this block |
| 401 | Not authenticated |
| 403 | Not authorized (requires scheduler role) |
| 404 | Block or person not found |
| 422 | Validation error |

```json
{
  "detail": "Person already assigned to this block"
}
```

---

***REMOVED******REMOVED*** PUT /api/assignments/{assignment_id}

Updates an existing assignment. Uses optimistic locking to prevent concurrent modifications.

**Authentication Required** (admin or coordinator)

***REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment's unique identifier |

***REMOVED******REMOVED******REMOVED*** Request Body

All fields are optional except `updated_at` for optimistic locking:

```json
{
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440001",
  "role": "backup",
  "notes": "Reassigned due to conflict",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rotation_template_id` | UUID | No | New template |
| `role` | string | No | New role |
| `activity_override` | string | No | Override activity |
| `notes` | string | No | Updated notes |
| `override_reason` | string | No | ACGME override reason |
| `updated_at` | datetime | Yes | For optimistic locking |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X PUT http://localhost:8000/api/assignments/880e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "backup",
    "notes": "Reassigned due to conflict",
    "updated_at": "2024-01-01T00:00:00Z"
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "backup",
  "activity_override": null,
  "notes": "Reassigned due to conflict",
  "created_by": "coordinator@hospital.org",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "override_acknowledged_at": null
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 403 | Not authorized |
| 404 | Assignment not found |
| 409 | Concurrent modification conflict |
| 422 | Validation error |

**Optimistic Locking Error:**

```json
{
  "detail": "Assignment has been modified by another user. Please refresh and try again."
}
```

---

***REMOVED******REMOVED*** DELETE /api/assignments/{assignment_id}

Deletes a single assignment.

**Authentication Required** (admin or coordinator)

***REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment's unique identifier |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X DELETE http://localhost:8000/api/assignments/880e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `204 No Content`

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 403 | Not authorized |
| 404 | Assignment not found |

---

***REMOVED******REMOVED*** DELETE /api/assignments

Bulk deletes all assignments within a date range.

**Authentication Required** (admin or coordinator)

***REMOVED******REMOVED******REMOVED*** Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Delete from this date (YYYY-MM-DD) |
| `end_date` | date | Yes | Delete until this date (YYYY-MM-DD) |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X DELETE "http://localhost:8000/api/assignments?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <token>"
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "deleted": 156
}
```

---

***REMOVED******REMOVED*** Assignment Roles

| Role | Description | Typical Person |
|------|-------------|----------------|
| `primary` | Primary assigned person | Resident |
| `supervising` | Supervising faculty | Attending physician |
| `backup` | On-call backup | Available resident |

---

***REMOVED******REMOVED*** ACGME Compliance

Assignments are validated against ACGME requirements:

***REMOVED******REMOVED******REMOVED*** Validation Checks

1. **80-Hour Rule**: Weekly hours averaged over 4 weeks
2. **1-in-7 Rule**: At least one day off per seven days
3. **Supervision Ratios**: Faculty-to-resident ratios by PGY level
4. **Consecutive Days**: Maximum consecutive working days

***REMOVED******REMOVED******REMOVED*** Override Handling

When ACGME rules would be violated, provide an `override_reason`:

```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "...",
    "person_id": "...",
    "role": "primary",
    "override_reason": "Emergency coverage - no other residents available"
  }'
```

The `override_acknowledged_at` timestamp records when the override was approved.

---

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Assign Multiple Residents to a Block

```bash
***REMOVED*** Assign primary resident
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "'$BLOCK_ID'",
    "person_id": "'$RESIDENT_1'",
    "rotation_template_id": "'$TEMPLATE_ID'",
    "role": "primary"
  }'

***REMOVED*** Assign supervising faculty
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "'$BLOCK_ID'",
    "person_id": "'$FACULTY_ID'",
    "rotation_template_id": "'$TEMPLATE_ID'",
    "role": "supervising"
  }'
```

***REMOVED******REMOVED******REMOVED*** Clear and Regenerate Schedule

```bash
***REMOVED*** Clear existing assignments for date range
curl -X DELETE "http://localhost:8000/api/assignments?start_date=2024-01-01&end_date=2024-03-31" \
  -H "Authorization: Bearer $TOKEN"

***REMOVED*** Generate new schedule
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-03-31"
  }'
```

---

*See also: [Schedule](./schedule.md) for automated schedule generation*
