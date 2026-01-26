# Assignments API Endpoints

Complete reference for managing individual schedule assignments.

---

## Overview

The Assignments API provides endpoints for:
- Listing assignments with filters and pagination
- Creating individual assignments
- Updating assignments with optimistic locking
- Deleting assignments (single or bulk)
- ACGME compliance validation on create/update

**Base Path**: `/api/v1/assignments`

**Authentication**: All endpoints require JWT authentication.

---

## List Assignments

<span class="endpoint-badge get">GET</span> `/api/v1/assignments`

List all assignments with optional filters and pagination.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string (date) | No | Filter from this date (YYYY-MM-DD) |
| `end_date` | string (date) | No | Filter until this date (YYYY-MM-DD) |
| `person_id` | UUID | No | Filter by person |
| `role` | string | No | Filter by role (resident, faculty, etc.) |
| `rotation_type` | string | No | Filter by rotation type (on_call, clinic, inpatient) |
| `page` | integer | No | Page number (1-indexed, default: 1) |
| `page_size` | integer | No | Items per page (1-500, default: 100) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "block_id": "550e8400-e29b-41d4-a716-446655440001",
      "person_id": "550e8400-e29b-41d4-a716-446655440002",
      "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
      "role": "resident",
      "activity_name": "Clinic",
      "abbreviation": "CLN",
      "created_at": "2024-07-01T10:00:00Z",
      "updated_at": "2024-07-01T10:00:00Z",
      "version": 1,
      "person": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "PGY1-01",
        "type": "resident",
        "pgy_level": 1
      },
      "block": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "date": "2024-07-01",
        "time_of_day": "AM",
        "session": "AM"
      }
    }
  ],
  "total": 248,
  "page": 1,
  "page_size": 100,
  "pages": 3
}
```

### Example Requests

**Filter by date range**

```bash
curl "http://localhost:8000/api/v1/assignments?start_date=2024-07-01&end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by person**

```bash
curl "http://localhost:8000/api/v1/assignments?person_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by rotation type**

```bash
curl "http://localhost:8000/api/v1/assignments?rotation_type=on_call&page=1&page_size=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python example**

```python
import requests

params = {
    "start_date": "2024-07-01",
    "end_date": "2024-07-31",
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "page": 1,
    "page_size": 50
}

response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    headers={"Authorization": f"Bearer {token}"},
    params=params
)

result = response.json()
print(f"Total assignments: {result['total']}")
for assignment in result['items']:
    print(f"{assignment['person']['name']}: {assignment['activity_name']}")
```

---

## Get Assignment

<span class="endpoint-badge get">GET</span> `/api/v1/assignments/{assignment_id}`

Get a specific assignment by ID.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assignment_id` | UUID | Assignment ID |

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "block_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_id": "550e8400-e29b-41d4-a716-446655440002",
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "resident",
  "activity_name": "Clinic",
  "abbreviation": "CLN",
  "created_at": "2024-07-01T10:00:00Z",
  "updated_at": "2024-07-01T10:00:00Z",
  "version": 1,
  "person": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "PGY1-01",
    "type": "resident",
    "pgy_level": 1,
    "email": "pgy1-01@example.com"
  },
  "block": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "date": "2024-07-01",
    "time_of_day": "AM",
    "session": "AM",
    "start_date": "2024-07-01",
    "end_date": "2024-07-01"
  },
  "rotation_template": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "name": "Primary Care Clinic",
    "abbreviation": "CLN",
    "category": "clinic"
  }
}
```

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Assignment with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/assignments/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Create Assignment

<span class="endpoint-badge post">POST</span> `/api/v1/assignments`

Create a new assignment.

**Authorization**: Requires `scheduler` role (admin or coordinator).

### Request Body

```json
{
  "block_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_id": "550e8400-e29b-41d4-a716-446655440002",
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "resident",
  "override_reason": "Manual assignment for coverage gap"
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_id` | UUID | Yes | Block to assign |
| `person_id` | UUID | Yes | Person to assign |
| `rotation_template_id` | UUID | Yes | Rotation template |
| `role` | string | Yes | Role (resident, faculty, etc.) |
| `override_reason` | string | No | Reason if ACGME violations exist |

### Response (201 Created)

```json
{
  "assignment": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
    "role": "resident",
    "activity_name": "Clinic",
    "abbreviation": "CLN",
    "created_at": "2024-07-01T10:00:00Z",
    "updated_at": "2024-07-01T10:00:00Z",
    "version": 1
  },
  "warnings": [
    {
      "type": "SUPERVISION_RATIO",
      "severity": "MEDIUM",
      "person_id": "550e8400-e29b-41d4-a716-446655440002",
      "person_name": "PGY1-01",
      "message": "Supervision ratio slightly high: 1:3 (recommended: 1:2)",
      "details": {
        "actual_ratio": 3,
        "recommended_ratio": 2
      }
    }
  ]
}
```

### ACGME Validation

The system validates assignments against ACGME rules:

| Rule | Description | Action |
|------|-------------|--------|
| **80-Hour Rule** | Max 80 hours/week | Returns warning if violated |
| **1-in-7 Rule** | One 24-hour period off every 7 days | Returns warning if violated |
| **Supervision Ratio** | PGY-1: 1:2, PGY-2/3: 1:4 | Returns warning if violated |

**Note**: Violations generate warnings but do not block creation. Include `override_reason` to document justification.

### Example Requests

**cURL**

```bash
curl -X POST http://localhost:8000/api/v1/assignments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
    "role": "resident"
  }'
```

**Python**

```python
import requests

data = {
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
    "role": "resident",
    "override_reason": "Manual coverage for deployment"
}

response = requests.post(
    "http://localhost:8000/api/v1/assignments",
    headers={"Authorization": f"Bearer {token}"},
    json=data
)

result = response.json()
print(f"Created assignment: {result['assignment']['id']}")
if result['warnings']:
    print(f"Warnings: {len(result['warnings'])}")
```

---

## Update Assignment

<span class="endpoint-badge put">PUT</span> `/api/v1/assignments/{assignment_id}`

Update an existing assignment with optimistic locking.

**Authorization**: Requires `scheduler` role (admin or coordinator).

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assignment_id` | UUID | Assignment ID |

### Request Body

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440004",
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440005",
  "version": 1,
  "override_reason": "Reassignment due to absence"
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | No | New person to assign |
| `rotation_template_id` | UUID | No | New rotation template |
| `version` | integer | Yes | Current version (for optimistic locking) |
| `override_reason` | string | No | Reason if ACGME violations exist |

### Optimistic Locking

The `version` field prevents concurrent updates:

1. Client reads assignment (version = 1)
2. Client modifies assignment
3. Client sends update with version = 1
4. If another user modified the assignment (version = 2), update fails with 409 Conflict

### Response (200 OK)

```json
{
  "assignment": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440004",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440005",
    "role": "resident",
    "activity_name": "Inpatient",
    "abbreviation": "IP",
    "created_at": "2024-07-01T10:00:00Z",
    "updated_at": "2024-07-01T11:30:00Z",
    "version": 2
  },
  "warnings": []
}
```

### Error Responses

**Version Conflict (409)**

```json
{
  "detail": "Assignment has been modified by another user. Please refresh and try again."
}
```

**Not Found (404)**

```json
{
  "detail": "Assignment with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Example

```bash
curl -X PUT http://localhost:8000/api/v1/assignments/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440004",
    "version": 1,
    "override_reason": "Coverage reassignment"
  }'
```

---

## Delete Assignment

<span class="endpoint-badge delete">DELETE</span> `/api/v1/assignments/{assignment_id}`

Delete a single assignment.

**Authorization**: Requires `scheduler` role (admin or coordinator).

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `assignment_id` | UUID | Assignment ID |

### Response (204 No Content)

No response body.

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Assignment with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Example

```bash
curl -X DELETE http://localhost:8000/api/v1/assignments/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Delete Assignments (Bulk)

<span class="endpoint-badge delete">DELETE</span> `/api/v1/assignments`

Delete all assignments in a date range.

**Authorization**: Requires `scheduler` role (admin or coordinator).

**Warning**: This is a destructive operation. Use with caution.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string (date) | Yes | Delete from this date (YYYY-MM-DD) |
| `end_date` | string (date) | Yes | Delete until this date (YYYY-MM-DD) |

### Response (204 No Content)

No response body.

### Example

```bash
curl -X DELETE "http://localhost:8000/api/v1/assignments?start_date=2024-07-01&end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python example with confirmation**

```python
import requests

start_date = "2024-07-01"
end_date = "2024-07-31"

# Confirm with user
confirmation = input(f"Delete all assignments from {start_date} to {end_date}? (yes/no): ")

if confirmation.lower() == "yes":
    response = requests.delete(
        "http://localhost:8000/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params={"start_date": start_date, "end_date": end_date}
    )

    if response.status_code == 204:
        print("Assignments deleted successfully")
    else:
        print(f"Error: {response.json()}")
```

---

## Common Use Cases

### 1. Get All Assignments for a Person

```python
import requests

person_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    headers={"Authorization": f"Bearer {token}"},
    params={"person_id": person_id}
)

assignments = response.json()['items']
print(f"Total assignments: {len(assignments)}")
```

### 2. Find Call Assignments for a Date Range

```python
response = requests.get(
    "http://localhost:8000/api/v1/assignments",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "start_date": "2024-07-01",
        "end_date": "2024-07-31",
        "rotation_type": "on_call"
    }
)

call_assignments = response.json()['items']
```

### 3. Create Assignment with Validation

```python
data = {
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
    "role": "resident"
}

response = requests.post(
    "http://localhost:8000/api/v1/assignments",
    headers={"Authorization": f"Bearer {token}"},
    json=data
)

result = response.json()

# Check for ACGME warnings
if result['warnings']:
    print("⚠️  ACGME Warnings:")
    for warning in result['warnings']:
        print(f"  - {warning['message']}")

    # Retry with override reason
    data['override_reason'] = "Manual coverage for emergency deployment"
    response = requests.post(
        "http://localhost:8000/api/v1/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )
```

### 4. Update Assignment with Optimistic Locking

```python
# 1. Get current assignment
response = requests.get(
    f"http://localhost:8000/api/v1/assignments/{assignment_id}",
    headers={"Authorization": f"Bearer {token}"}
)
assignment = response.json()

# 2. Update with version
update_data = {
    "person_id": "550e8400-e29b-41d4-a716-446655440004",
    "version": assignment['version']  # Include current version
}

response = requests.put(
    f"http://localhost:8000/api/v1/assignments/{assignment_id}",
    headers={"Authorization": f"Bearer {token}"},
    json=update_data
)

if response.status_code == 409:
    print("⚠️  Assignment was modified by another user. Refresh and try again.")
elif response.status_code == 200:
    print("✅ Assignment updated successfully")
```

---

## Pagination

The list endpoint supports pagination. See [Pagination](../pagination.md) for details.

### Response Headers

```
X-Total-Count: 248
X-Page: 1
X-Page-Size: 100
X-Total-Pages: 3
Link: <http://localhost:8000/api/v1/assignments?page=2>; rel="next"
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `ASSIGNMENT_NOT_FOUND` | 404 | Assignment does not exist |
| `PERSON_NOT_FOUND` | 404 | Person does not exist |
| `BLOCK_NOT_FOUND` | 404 | Block does not exist |
| `TEMPLATE_NOT_FOUND` | 404 | Rotation template does not exist |
| `VERSION_CONFLICT` | 409 | Assignment modified by another user |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `INSUFFICIENT_PERMISSIONS` | 403 | Scheduler role required |

---

## See Also

- [Schedules API](schedules.md) - Bulk schedule generation
- [Persons API](persons.md) - Person management
- [Swaps API](swaps.md) - Schedule swaps
- [Authentication](../authentication.md) - Token management
- [Pagination](../pagination.md) - Pagination patterns
