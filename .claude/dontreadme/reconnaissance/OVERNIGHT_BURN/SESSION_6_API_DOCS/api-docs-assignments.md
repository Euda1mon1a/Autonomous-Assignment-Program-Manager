***REMOVED*** Assignment API Complete Documentation

**SEARCH_PARTY Operation Report**
Generated: 2025-12-30
Source Code Analysis: G2_RECON Complete

---

***REMOVED******REMOVED*** Table of Contents

1. [API Overview](***REMOVED***api-overview)
2. [Endpoint Reference](***REMOVED***endpoint-reference)
3. [CRUD Operations](***REMOVED***crud-operations)
4. [Bulk Operations](***REMOVED***bulk-operations)
5. [Validation Rules](***REMOVED***validation-rules)
6. [Error Handling](***REMOVED***error-handling)
7. [Examples](***REMOVED***examples)
8. [Architecture Notes](***REMOVED***architecture-notes)

---

***REMOVED******REMOVED*** API Overview

***REMOVED******REMOVED******REMOVED*** Base Information

| Property | Value |
|----------|-------|
| **Base URL** | `/api/assignments` |
| **Authentication** | Required (JWT Bearer Token) |
| **Source File** | `backend/app/api/routes/assignments.py` |
| **Controller** | `backend/app/controllers/assignment_controller.py` |
| **Service Layer** | `backend/app/services/assignment_service.py` |
| **Repository** | `backend/app/repositories/assignment.py` |
| **Model** | `backend/app/models/assignment.py` |
| **Schemas** | `backend/app/schemas/assignment.py` |

***REMOVED******REMOVED******REMOVED*** Layered Architecture

The implementation follows strict layered architecture:

```
Route (FastAPI endpoint)
    ↓ [Input Validation]
Controller (Request/Response handling)
    ↓ [Business Logic Delegation]
Service (Business logic & ACGME validation)
    ↓ [Data Access]
Repository (Database operations)
    ↓
Model (SQLAlchemy ORM)
```

***REMOVED******REMOVED******REMOVED*** Key Features

- **ACGME Compliance Validation**: Create/update operations validate against 80-hour rule, 1-in-7 rule, and supervision ratios
- **Optimistic Locking**: Concurrent update detection using `updated_at` timestamps
- **Pagination**: List endpoint supports cursor and page-based pagination
- **Flexible Filtering**: Filter by date range, person, role, or activity type
- **Freeze Horizon Protection**: Check before modifications near freeze cutoff
- **Audit Trail**: Version history tracked via SQLAlchemy-Continuum
- **Cache Invalidation**: Schedule cache automatically invalidated after modifications

---

***REMOVED******REMOVED*** Endpoint Reference

***REMOVED******REMOVED******REMOVED*** 1. List Assignments

**Endpoint**: `GET /api/assignments`

**Authentication**: Required (any authenticated user)

**Role Requirements**: None (read-only access for all)

***REMOVED******REMOVED******REMOVED******REMOVED*** Query Parameters

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `start_date` | string (date) | No | None | YYYY-MM-DD format | Filter assignments from this date (inclusive) |
| `end_date` | string (date) | No | None | YYYY-MM-DD format | Filter assignments until this date (inclusive) |
| `person_id` | UUID | No | None | Valid UUID | Filter by specific person |
| `role` | string | No | None | `primary`, `supervising`, `backup` | Filter by role type |
| `activity_type` | string | No | None | e.g., `clinic`, `inpatient`, `on_call` | Filter by activity type from rotation template |
| `page` | integer | No | 1 | >= 1 | Page number (1-indexed) |
| `page_size` | integer | No | 100 | 1-500 | Items per page |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response Schema: `AssignmentListResponse`

```json
{
  "items": [
    {
      "id": "uuid",
      "block_id": "uuid",
      "person_id": "uuid",
      "rotation_template_id": "uuid",
      "role": "primary",
      "activity_override": null,
      "notes": null,
      "override_reason": null,
      "created_by": "username",
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z",
      "override_acknowledged_at": null,
      "confidence": 0.95,
      "score": 87.5
    }
  ],
  "total": 248,
  "page": 1,
  "page_size": 100
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Results returned with metadata |
| 401 | Unauthorized | Missing or expired token |
| 422 | Invalid Parameters | Date format error, invalid UUID |

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Optimization

- Uses `joinedload()` to eagerly load Person, Block, and RotationTemplate relationships
- Prevents N+1 query problem when iterating results
- Pagination applied at database level (OFFSET/LIMIT)
- Deterministic ordering by block date then assignment ID

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Requests

**Filter by date range and activity type:**
```bash
curl "http://localhost:8000/api/assignments?start_date=2025-01-01&end_date=2025-01-31&activity_type=clinic&page=1&page_size=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get all assignments for a specific person:**
```bash
curl "http://localhost:8000/api/assignments?person_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python example with pagination:**
```python
import requests

def get_all_assignments(token, batch_size=100):
    """Fetch all assignments with automatic pagination."""
    all_assignments = []
    page = 1

    while True:
        response = requests.get(
            "http://localhost:8000/api/assignments",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": page, "page_size": batch_size}
        )
        response.raise_for_status()

        data = response.json()
        all_assignments.extend(data["items"])

        if len(all_assignments) >= data["total"]:
            break
        page += 1

    return all_assignments
```

---

***REMOVED******REMOVED******REMOVED*** 2. Get Assignment

**Endpoint**: `GET /api/assignments/{assignment_id}`

**Authentication**: Required (any authenticated user)

**Role Requirements**: None (read-only access for all)

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | The assignment ID to retrieve |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response Schema: `AssignmentResponse`

Same as list items (see above).

***REMOVED******REMOVED******REMOVED******REMOVED*** Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success - Assignment found and returned |
| 401 | Unauthorized - Missing or invalid token |
| 404 | Not Found - Assignment does not exist |

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl "http://localhost:8000/api/assignments/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED******REMOVED*** 3. Create Assignment

**Endpoint**: `POST /api/assignments`

**Authentication**: Required (JWT Bearer Token)

**Role Requirements**: Scheduler role (Admin or Coordinator only)

**Status Code**: 201 Created

***REMOVED******REMOVED******REMOVED******REMOVED*** Request Schema: `AssignmentCreate`

```json
{
  "block_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_id": "550e8400-e29b-41d4-a716-446655440002",
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "primary",
  "activity_override": null,
  "notes": "Optional notes about this assignment",
  "override_reason": "Reason if ACGME violations acknowledged"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `block_id` | UUID | Yes | Valid block in system | Block this person is assigned to |
| `person_id` | UUID | Yes | Valid person in system | Person being assigned |
| `rotation_template_id` | UUID | No | Valid rotation template | Activity/rotation being performed |
| `role` | string | Yes | `primary`, `supervising`, `backup` | Role in this assignment |
| `activity_override` | string | No | Max 255 chars | Override the activity name from template |
| `notes` | string | No | Max 1000 chars | Additional context |
| `override_reason` | string | No | Max 1000 chars | Justification for ACGME violations |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response Schema: `AssignmentWithWarnings`

Extends `AssignmentResponse` with:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "block_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_id": "550e8400-e29b-41d4-a716-446655440002",
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": "Reason for override",
  "created_by": "scheduler@example.com",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z",
  "override_acknowledged_at": null,
  "confidence": 0.92,
  "score": 85.0,
  "acgme_warnings": [
    "Resident exceeds 80-hour limit in rolling 4-week period"
  ],
  "is_compliant": false
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Status Codes

| Code | Meaning |
|------|---------|
| 201 | Created successfully |
| 400 | Bad Request - Duplicate assignment or invalid data |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Scheduler role required |
| 422 | Validation Error - Invalid field values |

***REMOVED******REMOVED******REMOVED******REMOVED*** Validation Rules

**Uniqueness Constraint:**
- Only one assignment per person per block
- Attempting duplicate returns: `"Person already assigned to this block"`

**ACGME Validation (Non-blocking):**
- Checks 80-hour rule (4-week rolling window)
- Checks 1-in-7 rule (minimum 24-hour rest day)
- Checks supervision ratios (PGY-1: 1:2, PGY-2/3: 1:4)
- Violations return `acgme_warnings` array but do not block creation
- Recommendations: Include `override_reason` when acknowledging violations

**Freeze Horizon Check:**
- Validates that block is not within freeze horizon unless override provided
- Freeze settings configured in `backend/app/models/settings.py`

***REMOVED******REMOVED******REMOVED******REMOVED*** Side Effects

1. **Cache Invalidation**: Schedule cache automatically invalidated
2. **Audit Trail**: Assignment tracked with `created_by` user
3. **Explainability**: Stores confidence score and decision explanation

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Requests

**Basic creation (no violations expected):**
```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
    "role": "primary"
  }'
```

**With override for ACGME violation:**
```bash
curl -X POST http://localhost:8000/api/assignments \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "block_id": "550e8400-e29b-41d4-a716-446655440001",
    "person_id": "550e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
    "role": "primary",
    "override_reason": "Critical staffing shortage - approved by program director"
  }'
```

**Python with warning handling:**
```python
import requests
import json

def create_assignment_with_warnings(token, assignment_data):
    """Create assignment and handle ACGME warnings."""

    response = requests.post(
        "http://localhost:8000/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json=assignment_data
    )

    if response.status_code == 201:
        result = response.json()

        if result.get("acgme_warnings"):
            print("ACGME Warnings detected:")
            for warning in result["acgme_warnings"]:
                print(f"  - {warning}")

            ***REMOVED*** Retry with override
            assignment_data["override_reason"] = \
                "Violation acknowledged by program director"

            response = requests.post(
                "http://localhost:8000/api/assignments",
                headers={"Authorization": f"Bearer {token}"},
                json=assignment_data
            )

        return response.json()
    else:
        raise Exception(f"Create failed: {response.json()}")
```

---

***REMOVED******REMOVED******REMOVED*** 4. Update Assignment

**Endpoint**: `PUT /api/assignments/{assignment_id}`

**Authentication**: Required (JWT Bearer Token)

**Role Requirements**: Scheduler role (Admin or Coordinator only)

**Status Code**: 200 OK

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment to update |

***REMOVED******REMOVED******REMOVED******REMOVED*** Request Schema: `AssignmentUpdate`

```json
{
  "rotation_template_id": "550e8400-e29b-41d4-a716-446655440003",
  "role": "supervising",
  "activity_override": "Procedures",
  "notes": "Updated notes",
  "override_reason": "Covering for deployment",
  "acknowledge_override": true,
  "updated_at": "2025-01-15T10:00:00Z"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `rotation_template_id` | UUID | No | Valid rotation template | New rotation activity |
| `role` | string | No | `primary`, `supervising`, `backup` | New role type |
| `activity_override` | string | No | Max 255 chars | Override activity name |
| `notes` | string | No | Max 1000 chars | Additional notes |
| `override_reason` | string | No | Max 1000 chars | ACGME violation justification |
| `acknowledge_override` | boolean | No | true/false | Sets `override_acknowledged_at` timestamp |
| `updated_at` | datetime | **Yes** | ISO 8601 format | **REQUIRED for optimistic locking** |

***REMOVED******REMOVED******REMOVED******REMOVED*** Optimistic Locking

**Purpose**: Prevent concurrent updates from overwriting each other

**Mechanism**:
1. Client reads assignment (receives `updated_at` timestamp)
2. Client modifies assignment locally
3. Client sends update with original `updated_at`
4. Server compares received `updated_at` with current database value
5. If different: another user modified it → returns 409 Conflict
6. If same: update proceeds → timestamp updated to current time

**Example workflow:**

```python
***REMOVED*** Step 1: Read current assignment
response = requests.get(
    f"http://localhost:8000/api/assignments/{assignment_id}",
    headers={"Authorization": f"Bearer {token}"}
)
assignment = response.json()
original_updated_at = assignment["updated_at"]

***REMOVED*** Step 2: User modifies assignment locally (off-API)
***REMOVED*** ... time passes, other users might modify ...

***REMOVED*** Step 3: Send update with original timestamp
update_data = {
    "role": "backup",
    "updated_at": original_updated_at  ***REMOVED*** MUST include original
}

response = requests.put(
    f"http://localhost:8000/api/assignments/{assignment_id}",
    headers={"Authorization": f"Bearer {token}"},
    json=update_data
)

if response.status_code == 409:
    ***REMOVED*** Conflict - another user modified it
    print("Assignment was modified by another user")
    ***REMOVED*** Retry: fetch latest and try again
elif response.status_code == 200:
    ***REMOVED*** Success
    updated = response.json()
    print(f"Updated at: {updated['updated_at']}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Response Schema: `AssignmentWithWarnings`

Same as Create response (see above).

***REMOVED******REMOVED******REMOVED******REMOVED*** Status Codes

| Code | Meaning |
|------|---------|
| 200 | Updated successfully |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Scheduler role required |
| 404 | Not Found - Assignment doesn't exist |
| 409 | Conflict - Optimistic locking failure (stale `updated_at`) |
| 422 | Validation Error - Invalid field values |

***REMOVED******REMOVED******REMOVED******REMOVED*** Validation Rules

Same ACGME validation as Create:
- 80-hour rule check
- 1-in-7 rule check
- Supervision ratios
- Violations return warnings (non-blocking)

***REMOVED******REMOVED******REMOVED******REMOVED*** Side Effects

1. **Timestamp Update**: `updated_at` automatically updated to current time
2. **Version Increment**: Internal version counter incremented (for audit trail)
3. **Cache Invalidation**: Schedule cache invalidated
4. **Audit Trail**: Change recorded with user who made update

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Request

**Update role with optimistic locking:**
```bash
curl -X PUT http://localhost:8000/api/assignments/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "supervising",
    "updated_at": "2025-01-15T10:00:00Z"
  }'
```

**If update fails with 409 conflict:**
```python
def update_with_retry(token, assignment_id, update_data, max_retries=3):
    """Update with automatic retry on conflict."""

    for attempt in range(max_retries):
        ***REMOVED*** Get fresh copy
        response = requests.get(
            f"http://localhost:8000/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        current = response.json()

        ***REMOVED*** Add current timestamp
        update_data["updated_at"] = current["updated_at"]

        ***REMOVED*** Try update
        response = requests.put(
            f"http://localhost:8000/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code != 409:
            raise Exception(f"Update failed: {response.json()}")

        ***REMOVED*** Conflict - retry
        if attempt < max_retries - 1:
            print(f"Conflict, retrying... (attempt {attempt + 1})")

    raise Exception("Update failed after retries")
```

---

***REMOVED******REMOVED******REMOVED*** 5. Delete Assignment

**Endpoint**: `DELETE /api/assignments/{assignment_id}`

**Authentication**: Required (JWT Bearer Token)

**Role Requirements**: Scheduler role (Admin or Coordinator only)

**Status Code**: 204 No Content

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `assignment_id` | UUID | Yes | Assignment to delete |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

No response body (204 No Content)

***REMOVED******REMOVED******REMOVED******REMOVED*** Status Codes

| Code | Meaning |
|------|---------|
| 204 | Deleted successfully |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Scheduler role required |
| 404 | Not Found - Assignment doesn't exist |

***REMOVED******REMOVED******REMOVED******REMOVED*** Validation Rules

**Freeze Horizon Check:**
- Validates block is not within freeze horizon unless override provided

***REMOVED******REMOVED******REMOVED******REMOVED*** Side Effects

1. **Cache Invalidation**: Schedule cache invalidated
2. **Audit Trail**: Deletion recorded with user who deleted
3. **Cascading Deletes**: No cascade to related entities

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X DELETE http://localhost:8000/api/assignments/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

***REMOVED******REMOVED******REMOVED*** 6. Bulk Delete Assignments

**Endpoint**: `DELETE /api/assignments`

**Authentication**: Required (JWT Bearer Token)

**Role Requirements**: Scheduler role (Admin or Coordinator only)

**Status Code**: 204 No Content

**Warning**: This is a destructive operation. Deleted assignments cannot be recovered.

***REMOVED******REMOVED******REMOVED******REMOVED*** Query Parameters

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `start_date` | string (date) | Yes | YYYY-MM-DD format | Delete from this date (inclusive) |
| `end_date` | string (date) | Yes | YYYY-MM-DD format | Delete until this date (inclusive) |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

No response body (204 No Content)

***REMOVED******REMOVED******REMOVED******REMOVED*** Status Codes

| Code | Meaning |
|------|---------|
| 204 | Deleted successfully |
| 401 | Unauthorized - Missing/invalid token |
| 403 | Forbidden - Scheduler role required |
| 422 | Validation Error - Invalid date format |

***REMOVED******REMOVED******REMOVED******REMOVED*** Validation Rules

**Freeze Horizon Check:**
- If any assignments in date range fall within freeze horizon, deletion requires override
- Entire operation blocked if override needed but not provided

***REMOVED******REMOVED******REMOVED******REMOVED*** Side Effects

1. **Cache Invalidation**: Schedule cache invalidated if any assignments deleted
2. **Audit Trail**: Bulk delete recorded with count of deleted assignments
3. **Cascading**: Deletes all assignments in block IDs matching date range

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Implementation

```python
***REMOVED*** Optimized bulk delete:
***REMOVED*** 1. Get all block IDs in date range
block_ids = repository.get_ids_in_date_range(start_date, end_date)

***REMOVED*** 2. Delete all assignments in those blocks
deleted_count = repository.delete_by_block_ids(block_ids)

***REMOVED*** 3. Invalidate cache
invalidate_schedule_cache()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Request

**Basic bulk delete:**
```bash
curl -X DELETE "http://localhost:8000/api/assignments?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python with confirmation:**
```python
def bulk_delete_with_confirmation(token, start_date, end_date):
    """Delete assignments with user confirmation."""

    ***REMOVED*** Show what would be deleted
    response = requests.get(
        "http://localhost:8000/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params={"start_date": start_date, "end_date": end_date}
    )
    count = response.json()["total"]

    ***REMOVED*** Confirm
    if input(f"Delete {count} assignments? (type 'yes'): ") != "yes":
        print("Cancelled")
        return

    ***REMOVED*** Delete
    response = requests.delete(
        "http://localhost:8000/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params={"start_date": start_date, "end_date": end_date}
    )

    if response.status_code == 204:
        print(f"Deleted {count} assignments")
    else:
        print(f"Error: {response.json()}")
```

---

***REMOVED******REMOVED*** CRUD Operations

***REMOVED******REMOVED******REMOVED*** Complete Create-Read-Update-Delete Lifecycle

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Create

```python
***REMOVED*** POST /api/assignments
{
    "block_id": "660e8400-e29b-41d4-a716-446655440001",
    "person_id": "770e8400-e29b-41d4-a716-446655440002",
    "rotation_template_id": "880e8400-e29b-41d4-a716-446655440003",
    "role": "primary",
    "notes": "Initial assignment"
}

***REMOVED*** Response 201:
{
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z",
    "acgme_warnings": [],
    "is_compliant": true
    // ... rest of fields
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Read (List + Get)

```python
***REMOVED*** List - GET /api/assignments?person_id=...
***REMOVED*** Returns all assignments for person

***REMOVED*** Get - GET /api/assignments/{id}
***REMOVED*** Returns single assignment with all details
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Update

```python
***REMOVED*** PUT /api/assignments/{id}
{
    "role": "supervising",
    "notes": "Changed to supervising role",
    "updated_at": "2025-01-15T10:00:00Z"  ***REMOVED*** REQUIRED
}

***REMOVED*** Response 200:
{
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "role": "supervising",
    "notes": "Changed to supervising role",
    "updated_at": "2025-01-15T10:05:00Z",  ***REMOVED*** Updated
    "acgme_warnings": [],
    "is_compliant": true
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Delete

```python
***REMOVED*** Single: DELETE /api/assignments/{id}
***REMOVED*** Response: 204 No Content

***REMOVED*** Bulk: DELETE /api/assignments?start_date=...&end_date=...
***REMOVED*** Response: 204 No Content
```

---

***REMOVED******REMOVED*** Bulk Operations

***REMOVED******REMOVED******REMOVED*** Use Cases

1. **Bulk Import**: Import schedule from Excel/CSV
2. **Block Regeneration**: Replace assignments for a date range
3. **Cleanup**: Remove expired or invalid assignments
4. **Planning**: Create assignments for upcoming rotations

***REMOVED******REMOVED******REMOVED*** Bulk Create Pattern (Not Directly Supported via API)

While API doesn't have dedicated bulk create endpoint, services support it internally:

```python
***REMOVED*** Service layer supports batch creation:
for assignment_data in assignments:
    result = service.create_assignment(**assignment_data)
    ***REMOVED*** Handles validation and warnings per assignment
```

***REMOVED******REMOVED******REMOVED*** Bulk Delete

```python
***REMOVED*** DELETE /api/assignments?start_date=2025-01-01&end_date=2025-01-31

***REMOVED*** Implementation:
***REMOVED*** 1. Find all blocks in date range
***REMOVED*** 2. Delete all assignments in those blocks
***REMOVED*** 3. Invalidate schedule cache
***REMOVED*** 4. Return 204
```

***REMOVED******REMOVED******REMOVED*** Bulk Update Pattern

Update multiple assignments by calling PUT in sequence:

```python
def bulk_update_assignments(token, assignment_ids, update_data):
    """Update multiple assignments with retry on conflict."""

    results = []

    for assignment_id in assignment_ids:
        ***REMOVED*** Get current version
        response = requests.get(
            f"http://localhost:8000/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        current = response.json()

        ***REMOVED*** Update with current timestamp
        update_data["updated_at"] = current["updated_at"]

        ***REMOVED*** Try update (with retry on conflict)
        for attempt in range(3):
            response = requests.put(
                f"http://localhost:8000/api/assignments/{assignment_id}",
                headers={"Authorization": f"Bearer {token}"},
                json=update_data
            )

            if response.status_code == 200:
                results.append({"id": assignment_id, "status": "success"})
                break
            elif response.status_code == 409:
                ***REMOVED*** Conflict - retry
                time.sleep(0.1)
                continue
            else:
                results.append({
                    "id": assignment_id,
                    "status": "error",
                    "error": response.json()
                })
                break

    return results
```

***REMOVED******REMOVED******REMOVED*** Bulk Export

Use the list endpoint with pagination to export all assignments:

```python
def export_assignments_to_csv(token, start_date, end_date, output_file):
    """Export assignments to CSV."""
    import csv

    all_assignments = []
    page = 1
    page_size = 500

    while True:
        response = requests.get(
            "http://localhost:8000/api/assignments",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "start_date": start_date,
                "end_date": end_date,
                "page": page,
                "page_size": page_size
            }
        )
        data = response.json()
        all_assignments.extend(data["items"])

        if len(all_assignments) >= data["total"]:
            break
        page += 1

    ***REMOVED*** Write to CSV
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "block_id", "person_id", "role", "created_at"]
        )
        writer.writeheader()
        writer.writerows(all_assignments)
```

---

***REMOVED******REMOVED*** Validation Rules

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Validation

Automatically performed on Create and Update:

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. 80-Hour Rule

**Rule**: Maximum 80 hours per week, averaged over rolling 4-week periods

**Validation Window**: 4 weeks before and after assignment date

**Triggers Warning If:**
- Resident's total hours in rolling 4-week period >= 80

**Formula**:
```
total_hours_per_week = sum(all_assignments in 7-day window) / 4 weeks
if total_hours_per_week > 80:
    warning = "Exceeds 80-hour limit"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. 1-in-7 Rule

**Rule**: One 24-hour period off every 7 days (minimum)

**Validation Window**: 7 days

**Triggers Warning If:**
- Resident has 7 consecutive days assigned without day off

**Formula**:
```
for each 7-day window:
    if all 7 days assigned:
        warning = "Missing 1-in-7 rest day"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Supervision Ratios

**Rule**: Supervision requirements by PGY level

| PGY Level | Ratio | Formula |
|-----------|-------|---------|
| PGY-1 | 1:2 | Max 2 residents per faculty supervising |
| PGY-2 | 1:4 | Max 4 residents per faculty supervising |
| PGY-3 | 1:4 | Max 4 residents per faculty supervising |

**Triggers Warning If:**
- Actual ratio exceeds recommended ratio

***REMOVED******REMOVED******REMOVED*** Constraint Validation

***REMOVED******REMOVED******REMOVED******REMOVED*** Uniqueness Constraint

**Rule**: Only one assignment per person per block

**Error**: `"Person already assigned to this block"`

**Implemented As**: SQL UNIQUE constraint on (block_id, person_id)

***REMOVED******REMOVED******REMOVED******REMOVED*** Role Validation

**Valid Values**: `primary`, `supervising`, `backup`

**Error**: `"role must be 'primary', 'supervising', or 'backup'"`

***REMOVED******REMOVED******REMOVED*** Freeze Horizon Validation

**Purpose**: Prevent modifications to frozen schedule periods

**Settings** (in `backend/app/models/settings.py`):
- `freeze_horizon_days`: Days from today to freeze
- `freeze_scope`: `none`, `read_only`, or `locked`

**Behavior**:
- `none`: No freeze applied
- `read_only`: Can read frozen assignments but not modify
- `locked`: Cannot create/update/delete frozen assignments

**When Violated**: Returns error preventing operation

***REMOVED******REMOVED******REMOVED*** Input Validation

***REMOVED******REMOVED******REMOVED******REMOVED*** Field Constraints

| Field | Type | Min | Max | Pattern |
|-------|------|-----|-----|---------|
| `block_id` | UUID | - | - | Valid UUID |
| `person_id` | UUID | - | - | Valid UUID |
| `role` | string | - | - | `primary\|supervising\|backup` |
| `notes` | string | 0 | 1000 | Any text |
| `override_reason` | string | 0 | 1000 | Any text |

***REMOVED******REMOVED******REMOVED******REMOVED*** Date Validation

- `start_date` and `end_date` must be in YYYY-MM-DD format
- `updated_at` must be valid ISO 8601 datetime

---

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** HTTP Status Codes

| Code | Name | Meaning | Example |
|------|------|---------|---------|
| 200 | OK | Successful GET/PUT | List or get assignment |
| 201 | Created | Resource created | POST assignment |
| 204 | No Content | Successful DELETE | Delete assignment |
| 400 | Bad Request | Business logic error | Duplicate assignment |
| 401 | Unauthorized | Missing/invalid token | No Authorization header |
| 403 | Forbidden | Insufficient role | Faculty trying to create |
| 404 | Not Found | Resource doesn't exist | Assignment ID not found |
| 409 | Conflict | Concurrent modification | Stale `updated_at` |
| 422 | Unprocessable Entity | Validation error | Invalid field value |

***REMOVED******REMOVED******REMOVED*** Error Response Format

All errors return consistent JSON:

```json
{
  "detail": "Human-readable error message"
}
```

Or for validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "role"],
      "msg": "role must be 'primary', 'supervising', or 'backup'",
      "type": "value_error"
    }
  ]
}
```

***REMOVED******REMOVED******REMOVED*** Common Error Scenarios

***REMOVED******REMOVED******REMOVED******REMOVED*** 409 Conflict - Optimistic Locking Failure

**Cause**: Another user modified assignment between your read and write

**Response**:
```json
{
  "detail": "Assignment has been modified by another user. Current version: 2025-01-15T10:05:00Z, Your version: 2025-01-15T10:00:00Z"
}
```

**Resolution**: Fetch latest assignment and retry with current timestamp

***REMOVED******REMOVED******REMOVED******REMOVED*** 400 Bad Request - Duplicate Assignment

**Cause**: Person already assigned to this block

**Response**:
```json
{
  "detail": "Person already assigned to this block"
}
```

**Resolution**: Either update existing assignment or delete and recreate

***REMOVED******REMOVED******REMOVED******REMOVED*** 403 Forbidden - Insufficient Permissions

**Cause**: User's role doesn't have required access

**Response**:
```json
{
  "detail": "Schedule management access required"
}
```

**Resolution**: Contact admin to grant appropriate role (Admin or Coordinator)

***REMOVED******REMOVED******REMOVED******REMOVED*** 422 Unprocessable Entity - Validation Error

**Cause**: Invalid field value or type

**Response**:
```json
{
  "detail": [
    {
      "loc": ["query", "page_size"],
      "msg": "ensure this value is less than or equal to 500",
      "type": "value_error.number.not_le"
    }
  ]
}
```

**Resolution**: Check field constraints and retry with valid values

***REMOVED******REMOVED******REMOVED*** Error Code Mapping

Service layer returns structured error codes:

```python
class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"
    CONFLICT = "CONFLICT"
    ***REMOVED*** ... many more
```

Controller uses error codes to determine HTTP status:

```python
if result.get("error_code") == ErrorCode.NOT_FOUND:
    status_code = 404
elif result.get("error_code") == ErrorCode.CONCURRENT_MODIFICATION:
    status_code = 409
else:
    status_code = 400
```

---

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Create Clinic Assignment

```python
import requests
import json

def create_clinic_assignment(token, resident_id, block_id, template_id):
    """Create a clinic assignment for a resident."""

    data = {
        "block_id": block_id,
        "person_id": resident_id,
        "rotation_template_id": template_id,
        "role": "primary",
        "notes": "Primary clinic rotation"
    }

    response = requests.post(
        "http://localhost:8000/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )

    if response.status_code == 201:
        assignment = response.json()

        ***REMOVED*** Check for warnings
        if assignment.get("acgme_warnings"):
            print("Warnings:")
            for warning in assignment["acgme_warnings"]:
                print(f"  - {warning}")

        return assignment
    else:
        print(f"Error: {response.json()}")
        return None
```

***REMOVED******REMOVED******REMOVED*** Example 2: Update Assignment with Retry

```python
def update_assignment_safe(token, assignment_id, new_role, max_retries=3):
    """Update assignment role with automatic retry on conflict."""

    for attempt in range(max_retries):
        ***REMOVED*** Get current version
        response = requests.get(
            f"http://localhost:8000/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code != 200:
            print(f"Failed to fetch: {response.json()}")
            return None

        current = response.json()

        ***REMOVED*** Try update
        update_data = {
            "role": new_role,
            "updated_at": current["updated_at"]
        }

        response = requests.put(
            f"http://localhost:8000/api/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )

        if response.status_code == 200:
            print("Update successful")
            return response.json()
        elif response.status_code == 409:
            print(f"Conflict on attempt {attempt + 1}, retrying...")
            time.sleep(0.5)  ***REMOVED*** Back off before retry
            continue
        else:
            print(f"Error: {response.json()}")
            return None

    print("Failed after retries")
    return None
```

***REMOVED******REMOVED******REMOVED*** Example 3: List All Assignments for Person

```python
def get_person_assignments(token, person_id):
    """Get all assignments for a person."""

    all_assignments = []
    page = 1

    while True:
        response = requests.get(
            "http://localhost:8000/api/assignments",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "person_id": person_id,
                "page": page,
                "page_size": 100
            }
        )

        data = response.json()
        all_assignments.extend(data["items"])

        if len(all_assignments) >= data["total"]:
            break
        page += 1

    ***REMOVED*** Sort by block date (requires fetching block details)
    return sorted(all_assignments,
                  key=lambda x: x["created_at"])
```

***REMOVED******REMOVED******REMOVED*** Example 4: Handle ACGME Violations

```python
def create_assignment_with_violation_handling(token, assignment_data):
    """Create assignment and handle ACGME violations."""

    response = requests.post(
        "http://localhost:8000/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        json=assignment_data
    )

    if response.status_code != 201:
        print(f"Creation failed: {response.json()}")
        return None

    result = response.json()

    ***REMOVED*** Check compliance
    if not result["is_compliant"]:
        print(f"ACGME violations detected ({len(result['acgme_warnings'])} warnings):")

        for warning in result["acgme_warnings"]:
            print(f"  - {warning}")

        ***REMOVED*** Ask for confirmation
        response = input("Override violations? (yes/no): ")

        if response.lower() == "yes":
            reason = input("Reason for override: ")

            ***REMOVED*** Retry with override
            assignment_data["override_reason"] = reason

            response = requests.post(
                "http://localhost:8000/api/assignments",
                headers={"Authorization": f"Bearer {token}"},
                json=assignment_data
            )

            if response.status_code == 201:
                print("Assignment created with override acknowledged")
                return response.json()

    return result
```

***REMOVED******REMOVED******REMOVED*** Example 5: Bulk Delete with Confirmation

```python
def bulk_delete_assignments_interactive(token, start_date, end_date):
    """Delete assignments in date range with safety checks."""

    ***REMOVED*** Preview what would be deleted
    response = requests.get(
        "http://localhost:8000/api/assignments",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "start_date": start_date,
            "end_date": end_date,
            "page_size": 1000
        }
    )

    data = response.json()
    count = data["total"]

    ***REMOVED*** Show sample
    print(f"\nFound {count} assignments to delete from {start_date} to {end_date}:")
    for item in data["items"][:5]:
        print(f"  - {item['person_id']}: {item['role']}")

    if count > 5:
        print(f"  ... and {count - 5} more")

    ***REMOVED*** Get confirmation
    print(f"\nType 'DELETE {count}' to confirm deletion: ", end="")
    confirmation = input()

    if confirmation == f"DELETE {count}":
        response = requests.delete(
            "http://localhost:8000/api/assignments",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "start_date": start_date,
                "end_date": end_date
            }
        )

        if response.status_code == 204:
            print(f"Successfully deleted {count} assignments")
        else:
            print(f"Error: {response.json()}")
    else:
        print("Deletion cancelled")
```

---

***REMOVED******REMOVED*** Architecture Notes

***REMOVED******REMOVED******REMOVED*** Layered Design

```
Route Layer (assignments.py)
  - Thin endpoint wrapper
  - Query parameter validation
  - HTTP response mapping

Controller Layer (assignment_controller.py)
  - Request/response handling
  - Pagination calculation
  - Error code mapping

Service Layer (assignment_service.py)
  - Business logic
  - ACGME validation
  - Freeze horizon check
  - Cache invalidation

Repository Layer (assignment.py)
  - Database queries
  - Eager loading (prevents N+1)
  - Pagination at DB level

Model Layer (assignment.py)
  - SQLAlchemy ORM
  - Relationships
  - Version tracking
```

***REMOVED******REMOVED******REMOVED*** Performance Optimizations

1. **Eager Loading**: `joinedload()` for Person, Block, RotationTemplate
2. **Database Pagination**: OFFSET/LIMIT applied at DB level
3. **Index Strategy**: Indexes on (block_id, person_id) for uniqueness
4. **Cache Invalidation**: Automatic after modifications

***REMOVED******REMOVED******REMOVED*** Concurrency Handling

1. **Optimistic Locking**: Uses `updated_at` timestamp
2. **No Locking Blocks**: Readers don't block writers
3. **Conflict Detection**: Server detects concurrent modifications
4. **Client Retry**: Client must fetch latest and retry

***REMOVED******REMOVED******REMOVED*** Audit Trail

1. **Version History**: SQLAlchemy-Continuum tracks all changes
2. **Created By**: Stored in `created_by` field
3. **Timestamps**: `created_at` and `updated_at` for tracking
4. **Explanability**: Decision explanation stored in `explain_json`

***REMOVED******REMOVED******REMOVED*** Security

1. **Authentication**: JWT Bearer token required for all operations
2. **Authorization**: Role-based access (Scheduler role for writes)
3. **Input Validation**: Pydantic schemas validate all inputs
4. **SQL Injection Prevention**: SQLAlchemy ORM prevents injection
5. **Audit Logging**: All operations logged with user context

---

***REMOVED******REMOVED*** Summary

This API provides complete assignment lifecycle management with:
- **Complete CRUD**: Create, Read (list/get), Update, Delete
- **Bulk Operations**: Delete date ranges, list with filters
- **ACGME Compliance**: Automatic validation with warnings
- **Concurrency Control**: Optimistic locking prevents conflicts
- **Role-Based Access**: Scheduler-only writes, read access for all
- **Comprehensive Validation**: Field constraints, uniqueness, compliance rules
- **Excellent Error Handling**: Clear messages, HTTP status codes, error codes

All endpoints follow RESTful conventions and are secured with JWT authentication.
