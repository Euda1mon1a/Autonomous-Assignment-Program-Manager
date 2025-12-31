# Schedule API Endpoints

Complete reference for schedule generation, validation, and management endpoints.

---

## Overview

The Schedule API provides endpoints for:
- Automated schedule generation with multiple algorithms
- ACGME compliance validation
- Emergency coverage handling
- Schedule import and conflict analysis
- Swap candidate finding
- Faculty outpatient assignment generation

**Base Path**: `/api/v1/schedule`

**Authentication**: All endpoints require JWT authentication unless otherwise noted.

---

## Generate Schedule

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/generate`

Generate a new schedule for a date range using constraint-based optimization.

### Request Body

```json
{
  "start_date": "2024-07-01",
  "end_date": "2024-07-31",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "algorithm": "hybrid",
  "timeout_seconds": 120.0
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `start_date` | string (date) | Yes | Start date in YYYY-MM-DD format |
| `end_date` | string (date) | Yes | End date in YYYY-MM-DD format |
| `pgy_levels` | array[integer] | No | Filter residents by PGY level (1, 2, or 3) |
| `rotation_template_ids` | array[UUID] | No | Specific rotation templates to use |
| `algorithm` | string | No | Algorithm: `greedy`, `cp_sat`, `pulp`, or `hybrid` (default: `greedy`) |
| `timeout_seconds` | number | No | Maximum solver runtime (5-300 seconds, default: 60) |

### Algorithms

| Algorithm | Speed | Optimality | Use Case |
|-----------|-------|------------|----------|
| `greedy` | Fast | Good | Initial solutions, prototyping |
| `cp_sat` | Slow | Optimal | Small date ranges, high-quality schedules |
| `pulp` | Medium | Near-optimal | Large problems, production use |
| `hybrid` | Medium | Best | Recommended for most cases |

### Response

**Success (200 OK)**

```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 248,
  "total_blocks": 248,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 1.0,
    "statistics": {
      "total_residents": 9,
      "total_faculty": 12,
      "avg_hours_per_week": 68.5
    }
  },
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "solver_stats": {
    "total_blocks": 248,
    "total_residents": 9,
    "coverage_rate": 1.0,
    "branches": 1247,
    "conflicts": 89
  },
  "nf_pc_audit": {
    "compliant": true,
    "total_nf_transitions": 12,
    "violations": [],
    "message": "All Night Float -> Post-Call transitions properly covered"
  }
}
```

**Partial Success (207 Multi-Status)**

```json
{
  "status": "partial",
  "message": "Schedule generated with some violations",
  "total_blocks_assigned": 230,
  "total_blocks": 248,
  "validation": {
    "valid": false,
    "total_violations": 3,
    "violations": [
      {
        "type": "SUPERVISION_RATIO",
        "severity": "HIGH",
        "person_id": "550e8400-e29b-41d4-a716-446655440001",
        "person_name": "Dr. Smith",
        "block_id": "550e8400-e29b-41d4-a716-446655440002",
        "message": "Supervision ratio violated: 1:5 (required: 1:4)",
        "details": {
          "actual_ratio": 5,
          "required_ratio": 4,
          "date": "2024-07-15"
        }
      }
    ],
    "coverage_rate": 0.93
  },
  "run_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Error (422 Unprocessable Entity)**

```json
{
  "detail": "Schedule generation failed: insufficient residents for date range"
}
```

**Conflict (409 Conflict)**

```json
{
  "detail": "Schedule generation already in progress for overlapping date range. Please wait for the current run to complete."
}
```

### Idempotency

This endpoint supports idempotency via the `Idempotency-Key` header:

```http
POST /api/v1/schedule/generate
Idempotency-Key: unique-key-12345
Content-Type: application/json

{
  "start_date": "2024-07-01",
  "end_date": "2024-07-31"
}
```

**Behavior:**
- Same key + same body → Returns cached result (header: `X-Idempotency-Replayed: true`)
- Same key + different body → Returns 422 error
- Request in progress → Returns 409 error

### Rate Limiting

- **Limit**: 10 requests per minute per user
- **Headers**: See [Rate Limiting](../rate-limiting.md)

### Example Requests

**cURL**

```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-07-01",
    "end_date": "2024-07-31",
    "algorithm": "hybrid"
  }'
```

**Python**

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/schedule/generate",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "start_date": "2024-07-01",
        "end_date": "2024-07-31",
        "algorithm": "hybrid",
        "timeout_seconds": 120
    }
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Assignments: {result['total_blocks_assigned']}/{result['total_blocks']}")
```

**JavaScript**

```javascript
const response = await fetch('http://localhost:8000/api/v1/schedule/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    start_date: '2024-07-01',
    end_date: '2024-07-31',
    algorithm: 'hybrid'
  })
});

const result = await response.json();
console.log(`Status: ${result.status}`);
```

---

## Validate Schedule

<span class="endpoint-badge get">GET</span> `/api/v1/schedule/validate`

Validate an existing schedule for ACGME compliance.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |

### Response

```json
{
  "valid": true,
  "total_violations": 0,
  "violations": [],
  "coverage_rate": 0.98,
  "statistics": {
    "total_residents": 9,
    "residents_checked": 9,
    "date_range_days": 31,
    "80_hour_violations": 0,
    "1_in_7_violations": 0,
    "supervision_violations": 0
  }
}
```

### Validation Rules

| Rule | Description | Severity |
|------|-------------|----------|
| **80-Hour Rule** | Max 80 hours/week, rolling 4-week average | CRITICAL |
| **1-in-7 Rule** | One 24-hour period off every 7 days | HIGH |
| **Supervision Ratio** | PGY-1: 1:2, PGY-2/3: 1:4 | HIGH |

### Example

```bash
curl "http://localhost:8000/api/v1/schedule/validate?start_date=2024-07-01&end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Schedule

<span class="endpoint-badge get">GET</span> `/api/v1/schedule/{start_date}/{end_date}`

Retrieve schedule for a date range.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | string | Start date (YYYY-MM-DD) |
| `end_date` | string | End date (YYYY-MM-DD) |

### Response

```json
{
  "start_date": "2024-07-01",
  "end_date": "2024-07-31",
  "total_assignments": 496,
  "schedule": {
    "2024-07-01": {
      "AM": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "PGY1-01",
            "type": "resident",
            "pgy_level": 1
          },
          "role": "resident",
          "activity": "Clinic",
          "abbreviation": "CLN"
        }
      ],
      "PM": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440002",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "PGY1-01",
            "type": "resident",
            "pgy_level": 1
          },
          "role": "resident",
          "activity": "Clinic",
          "abbreviation": "CLN"
        }
      ]
    }
  }
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/schedule/2024-07-01/2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Emergency Coverage

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/emergency-coverage`

Handle emergency absence and find replacement coverage.

### Use Cases

- Military deployments
- TDY assignments
- Medical emergencies
- Family emergencies

### Request Body

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-07-15",
  "end_date": "2024-07-22",
  "reason": "Military deployment",
  "is_deployment": true
}
```

### Response

```json
{
  "status": "success",
  "replacements_found": 12,
  "coverage_gaps": [],
  "requires_manual_review": false,
  "details": {
    "affected_assignments": 14,
    "replacements": [
      {
        "original_person": "PGY2-03",
        "replacement_person": "PGY2-04",
        "date": "2024-07-15",
        "session": "AM",
        "activity": "Inpatient"
      }
    ],
    "critical_services_covered": true
  }
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/schedule/emergency-coverage \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-07-15",
    "end_date": "2024-07-22",
    "reason": "Medical emergency"
  }'
```

---

## Import and Analyze Schedule

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/import/analyze`

Import and analyze Excel schedules for conflicts.

### Request (Multipart Form Data)

```
Content-Type: multipart/form-data

fmit_file: [Excel file]
clinic_file: [Excel file] (optional)
specialty_providers: {"Sports Medicine": ["FAC-SPORTS"]}
```

### Response

```json
{
  "success": true,
  "fmit_schedule": {
    "provider_count": 12,
    "date_range": {
      "start": "2024-07-01",
      "end": "2024-07-31"
    },
    "total_weeks": 4
  },
  "clinic_schedule": {
    "provider_count": 12,
    "date_range": {
      "start": "2024-07-01",
      "end": "2024-07-31"
    },
    "total_slots": 120
  },
  "conflicts": [
    {
      "type": "double_booking",
      "severity": "high",
      "provider": "FAC-PD",
      "date": "2024-07-15",
      "fmit_assignment": "Week 3",
      "clinic_assignment": "Tuesday AM clinic",
      "recommendation": "Reassign clinic to another provider"
    }
  ],
  "recommendations": [
    {
      "type": "alternating_pattern",
      "provider": "FAC-APD",
      "pattern": "Week on/Week off",
      "impact": "Family disruption",
      "suggestion": "Consolidate FMIT weeks"
    }
  ],
  "summary": {
    "total_conflicts": 3,
    "double_bookings": 2,
    "specialty_gaps": 1,
    "alternating_patterns": 1
  }
}
```

### Conflict Types

| Type | Severity | Description |
|------|----------|-------------|
| `double_booking` | HIGH | Same provider scheduled for FMIT and clinic |
| `specialty_unavailable` | MEDIUM | Specialty provider on FMIT creates clinic gap |
| `alternating_pattern` | LOW | Week-on/week-off pattern (family burden) |

---

## Parse Block Schedule

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/import/block`

Parse a specific block schedule from an Excel file using anchor-based fuzzy matching.

### Request (Multipart Form Data)

```
Content-Type: multipart/form-data

file: [Excel file]
block_number: 10
known_people: ["PGY1-01", "PGY2-03", "FAC-PD"]
include_fmit: true
```

### Response

```json
{
  "success": true,
  "block_number": 10,
  "start_date": "2024-07-01",
  "end_date": "2024-07-28",
  "residents": [
    {
      "name": "PGY1-01",
      "template": "R1",
      "pgy_level": 1
    }
  ],
  "residents_by_template": {
    "R1": [
      {"name": "PGY1-01", "template": "R1", "pgy_level": 1}
    ],
    "R2": [
      {"name": "PGY2-03", "template": "R2", "pgy_level": 2}
    ]
  },
  "fmit_schedule": [
    {
      "block_number": 10,
      "week_number": 1,
      "start_date": "2024-07-01",
      "end_date": "2024-07-07",
      "faculty_name": "FAC-PD",
      "is_holiday_call": false
    }
  ],
  "assignments": [
    {
      "person_name": "PGY1-01",
      "date": "2024-07-01",
      "template": "R1",
      "role": "resident",
      "slot_am": "CLN",
      "slot_pm": "CLN",
      "row_idx": 5,
      "confidence": 0.95
    }
  ],
  "warnings": [
    "Name 'JohnSmith' fuzzy matched to 'John Smith' (confidence: 0.92)"
  ],
  "errors": [],
  "total_residents": 9,
  "total_assignments": 252
}
```

---

## Find Swap Candidates

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/swaps/find`

Find swap candidates for an FMIT week.

### Request (Multipart Form Data)

```
Content-Type: multipart/form-data

fmit_file: [Excel file]
request_json: {
  "target_faculty": "FAC-PD",
  "target_week": "2024-07-08",
  "faculty_targets": [
    {
      "name": "FAC-APD",
      "target_weeks": 10,
      "role": "APD",
      "current_weeks": 8
    }
  ],
  "external_conflicts": [],
  "include_absence_conflicts": true,
  "schedule_release_days": 14
}
```

### Response

```json
{
  "success": true,
  "target_faculty": "FAC-PD",
  "target_week": "2024-07-08",
  "candidates": [
    {
      "faculty": "FAC-APD",
      "can_take_week": "2024-07-08",
      "gives_week": "2024-07-15",
      "back_to_back_ok": true,
      "external_conflict": false,
      "flexibility": 0.85,
      "reason": "Can swap week 2024-07-15 for 2024-07-08",
      "rank": 1
    }
  ],
  "total_candidates": 5,
  "viable_candidates": 3,
  "alternating_patterns": [
    {
      "faculty": "FAC-CORE",
      "cycle_count": 4,
      "fmit_weeks": ["2024-07-01", "2024-07-15", "2024-07-29"],
      "recommendation": "Consider consolidating FMIT weeks to reduce family burden"
    }
  ],
  "message": "Found 3 viable swap candidates out of 5 total"
}
```

---

## Faculty Outpatient Generation

<span class="endpoint-badge post">POST</span> `/api/v1/schedule/faculty-outpatient/generate`

Generate faculty primary clinic and supervision assignments for a block.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_number` | integer | Yes | Block number (1-13) |
| `regenerate` | boolean | No | Clear existing assignments (default: true) |
| `include_clinic` | boolean | No | Generate clinic sessions (default: true) |
| `include_supervision` | boolean | No | Generate supervision (default: true) |

### Response

```json
{
  "success": true,
  "message": "Faculty outpatient assignments generated successfully",
  "block_number": 10,
  "block_start": "2024-07-01",
  "block_end": "2024-07-28",
  "total_clinic_assignments": 48,
  "total_supervision_assignments": 96,
  "cleared_count": 0,
  "faculty_summaries": [
    {
      "faculty_id": "550e8400-e29b-41d4-a716-446655440000",
      "faculty_name": "FAC-CORE",
      "faculty_role": "core_faculty",
      "clinic_sessions": 16,
      "supervision_sessions": 32,
      "total_sessions": 48
    }
  ],
  "warnings": [],
  "errors": []
}
```

### Faculty Clinic Limits by Role

| Role | Clinic Sessions/Week |
|------|---------------------|
| PD (Program Director) | 0 |
| APD (Associate PD) | 2 |
| Core Faculty | 4 |

### Example

```bash
curl -X POST "http://localhost:8000/api/v1/schedule/faculty-outpatient/generate?block_number=10&regenerate=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_DATE_FORMAT` | 400 | Date must be in YYYY-MM-DD format |
| `INVALID_DATE_RANGE` | 400 | start_date must be before end_date |
| `SCHEDULE_IN_PROGRESS` | 409 | Another schedule generation is running |
| `IDEMPOTENCY_CONFLICT` | 422 | Idempotency key used with different body |
| `IDEMPOTENCY_PENDING` | 409 | Request with this key is being processed |
| `GENERATION_FAILED` | 422 | Schedule generation failed |
| `VALIDATION_FAILED` | 422 | File validation failed |
| `PARSE_ERROR` | 422 | Failed to parse Excel file |

---

## See Also

- [Assignments API](assignments.md) - Individual assignment management
- [Swaps API](swaps.md) - Schedule swap execution
- [Authentication](../authentication.md) - Token management
- [Error Codes](../error-codes.md) - Complete error reference
- [Pagination](../pagination.md) - Pagination patterns
