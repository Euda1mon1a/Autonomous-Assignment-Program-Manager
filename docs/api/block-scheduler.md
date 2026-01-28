# Block Scheduler API

Leave-eligible rotation matching API for academic block scheduling.

> **Base Path:** `/api/block-scheduler`
> **Authentication:** Bearer token required
> **Added:** 2025-12-30

---

## Overview

The Block Scheduler API enables automated assignment of residents to rotations based on their leave status:

1. **Residents with approved leave** → Assigned to `leave_eligible=True` rotations
2. **Remaining residents** → Fill coverage needs first, then balanced distribution
3. **Coverage gaps** → Identified for non-leave-eligible rotations (FMIT, inpatient)

### Key Concepts

| Term | Description |
|------|-------------|
| **Academic Block** | 28-day scheduling period (blocks 1-13 per year) |
| **Block 0** | Orientation week (late June) |
| **Leave-Eligible** | Rotation where leave doesn't disrupt critical coverage |
| **Coverage Priority** | Non-leave-eligible rotations (FMIT, inpatient) filled first |

---

## Dashboard

<span class="endpoint-badge get">GET</span> `/api/block-scheduler/dashboard`

Get dashboard view for the block scheduler UI.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_number` | int | Yes | Academic block (0-13) |
| `academic_year` | int | Yes | Academic year (e.g., 2025) |

### Response

```json
{
  "block_number": 5,
  "academic_year": 2025,
  "block_start_date": "2025-10-21",
  "block_end_date": "2025-11-17",
  "total_residents": 12,
  "residents_with_leave": [
    {
      "resident_id": "uuid",
      "resident_name": "Dr. Smith",
      "pgy_level": 2,
      "leave_days": 5,
      "leave_types": ["vacation"]
    }
  ],
  "rotation_capacities": [
    {
      "rotation_template_id": "uuid",
      "rotation_name": "FMIT Inpatient",
      "leave_eligible": false,
      "max_residents": 2,
      "current_assigned": 1,
      "available_slots": 1
    },
    {
      "rotation_template_id": "uuid",
      "rotation_name": "Sports Medicine Elective",
      "leave_eligible": true,
      "max_residents": 4,
      "current_assigned": 2,
      "available_slots": 2
    }
  ],
  "leave_eligible_rotations": 5,
  "non_leave_eligible_rotations": 2,
  "current_assignments": [],
  "unassigned_residents": 12
}
```

---

## Schedule Block

<span class="endpoint-badge post">POST</span> `/api/block-scheduler/schedule`

Schedule residents for a block using leave-eligible matching algorithm.

### Request Body

```json
{
  "block_number": 5,
  "academic_year": 2025,
  "dry_run": true,
  "include_all_residents": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `block_number` | int | Required | Academic block (0-13) |
| `academic_year` | int | Required | Academic year |
| `dry_run` | bool | `true` | If true, preview without saving |
| `include_all_residents` | bool | `true` | If false, only schedule residents with leave |

### Response

```json
{
  "block_number": 5,
  "academic_year": 2025,
  "dry_run": true,
  "success": true,
  "message": "Preview generated",
  "assignments": [
    {
      "resident_id": "uuid",
      "resident_name": "Dr. Smith",
      "pgy_level": 2,
      "rotation_template_id": "uuid",
      "rotation_name": "Sports Medicine Elective",
      "has_leave": true,
      "leave_days": 5,
      "assignment_reason": "leave_eligible_match",
      "is_leave_eligible_rotation": true
    },
    {
      "resident_id": "uuid",
      "resident_name": "Dr. Jones",
      "pgy_level": 1,
      "rotation_template_id": "uuid",
      "rotation_name": "FMIT Inpatient",
      "has_leave": false,
      "leave_days": 0,
      "assignment_reason": "coverage_priority",
      "is_leave_eligible_rotation": false
    }
  ],
  "total_residents": 12,
  "residents_with_leave": 3,
  "coverage_gaps": [
    {
      "rotation_template_id": "uuid",
      "rotation_name": "FMIT Inpatient",
      "required_coverage": 2,
      "assigned_coverage": 1,
      "gap": 1,
      "severity": "critical"
    }
  ],
  "leave_conflicts": [],
  "rotation_capacities": [...]
}
```

### Assignment Reasons

| Reason | Description |
|--------|-------------|
| `leave_eligible_match` | Resident has leave, assigned to leave-eligible rotation |
| `coverage_priority` | Assigned to fill non-leave-eligible rotation |
| `balanced` | Assigned for workload balance |
| `manual` | Manually assigned by coordinator |
| `specialty_match` | Matches specialty requirements |

### Coverage Gap Severity

| Severity | Description |
|----------|-------------|
| `critical` | Non-leave-eligible rotation with gap > 1 |
| `warning` | Non-leave-eligible rotation with gap = 1 |
| `info` | Leave-eligible rotation with gap |

---

## Get Assignment

<span class="endpoint-badge get">GET</span> `/api/block-scheduler/assignments/{assignment_id}`

Get a single block assignment by ID.

### Response

```json
{
  "id": "uuid",
  "block_number": 5,
  "academic_year": 2025,
  "resident_id": "uuid",
  "rotation_template_id": "uuid",
  "has_leave": true,
  "leave_days": 5,
  "assignment_reason": "leave_eligible_match",
  "notes": null,
  "created_by": "admin@hospital.org",
  "created_at": "2025-12-30T10:00:00Z",
  "updated_at": "2025-12-30T10:00:00Z",
  "resident": {
    "id": "uuid",
    "name": "Dr. Smith",
    "pgy_level": 2
  },
  "rotation_template": {
    "id": "uuid",
    "name": "Sports Medicine Elective",
    "rotation_type": "elective",
    "leave_eligible": true
  }
}
```

---

## Create Manual Assignment

<span class="endpoint-badge post">POST</span> `/api/block-scheduler/assignments`

Create a manual block assignment (overrides auto-scheduling).

### Request Body

```json
{
  "block_number": 5,
  "academic_year": 2025,
  "resident_id": "uuid",
  "rotation_template_id": "uuid",
  "notes": "Manual override for specialty training"
}
```

### Response

Returns the created assignment (same as Get Assignment response).

### Error Responses

| Code | Description |
|------|-------------|
| 409 | Assignment already exists for this resident in this block |
| 400 | Invalid request data |

---

## Update Assignment

<span class="endpoint-badge put">PUT</span> `/api/block-scheduler/assignments/{assignment_id}`

Update an existing block assignment.

### Request Body

```json
{
  "rotation_template_id": "uuid",
  "notes": "Changed due to schedule conflict"
}
```

All fields are optional. Changing `rotation_template_id` automatically sets `assignment_reason` to `manual`.

---

## Delete Assignment

<span class="endpoint-badge delete">DELETE</span> `/api/block-scheduler/assignments/{assignment_id}`

Delete a block assignment.

### Response

`204 No Content`

---

## Algorithm Details

### Leave-Eligible Matching

```
1. Get all residents with approved leave in block date range
2. For each resident with leave:
   a. Filter rotations where leave_eligible = True
   b. Check capacity constraints
   c. Score by: specialty match, available capacity
   d. Assign to highest-scoring rotation
3. For remaining residents:
   a. Prioritize non-leave-eligible rotations (FMIT, inpatient)
   b. Score by: coverage need, specialty match, capacity
   c. Assign to highest-scoring rotation
4. Generate coverage gap warnings
5. Generate leave conflict warnings (if no capacity)
```

### Block Date Calculation

- Academic year starts July 1
- Block 0: Orientation (June 24-30)
- Block 1: July 1-28
- Block N: July 1 + (N-1) * 28 days

```
Block 1:  Jul 1 - Jul 28
Block 2:  Jul 29 - Aug 25
Block 3:  Aug 26 - Sep 22
...
Block 13: May 27 - Jun 23
```

---

## Related Endpoints

- [`GET /api/absences`](absences.md) - Leave request data
- [`GET /api/rotation-templates`](schedule.md) - Rotation templates with `leave_eligible` flag
- [`GET /api/academic-blocks`](schedule.md) - Academic block definitions

---

## Examples

### Preview Block Schedule

```bash
curl -X POST http://localhost:8000/api/block-scheduler/schedule \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_number": 5,
    "academic_year": 2025,
    "dry_run": true
  }'
```

### Execute Block Schedule

```bash
curl -X POST http://localhost:8000/api/block-scheduler/schedule \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_number": 5,
    "academic_year": 2025,
    "dry_run": false
  }'
```

### Get Dashboard

```bash
curl "http://localhost:8000/api/block-scheduler/dashboard?block_number=5&academic_year=2025" \
  -H "Authorization: Bearer <token>"
```
