# Schedule Endpoints

Base path: `/api/schedule`

Handles automated schedule generation, ACGME compliance validation, schedule retrieval, and emergency coverage management.

## Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/{start_date}/{end_date}` | Get schedule for date range | No |
| POST | `/generate` | Generate schedule | Yes |
| GET | `/validate` | Validate ACGME compliance | No |
| POST | `/emergency-coverage` | Handle emergency absence | Yes |

---

## GET /api/schedule/{start_date}/{end_date}

Retrieves the schedule for a date range, formatted for calendar display.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |

### Example Request

```bash
curl http://localhost:8000/api/schedule/2024-01-15/2024-01-21
```

### Response

**Status:** `200 OK`

```json
{
  "start_date": "2024-01-15",
  "end_date": "2024-01-21",
  "schedule": {
    "2024-01-15": {
      "AM": [
        {
          "id": "880e8400-e29b-41d4-a716-446655440000",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Dr. Jane Smith",
            "type": "resident",
            "pgy_level": 2
          },
          "role": "primary",
          "activity": "Sports Medicine Clinic",
          "abbreviation": "SM"
        },
        {
          "id": "880e8400-e29b-41d4-a716-446655440002",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Dr. Robert Johnson",
            "type": "faculty",
            "pgy_level": null
          },
          "role": "supervising",
          "activity": "Sports Medicine Clinic",
          "abbreviation": "SM"
        }
      ],
      "PM": [
        {
          "id": "880e8400-e29b-41d4-a716-446655440001",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Dr. Bob Wilson",
            "type": "resident",
            "pgy_level": 1
          },
          "role": "primary",
          "activity": "Primary Care Clinic",
          "abbreviation": "PC"
        }
      ]
    },
    "2024-01-16": {
      "AM": [...],
      "PM": [...]
    }
  },
  "total_assignments": 42
}
```

---

## POST /api/schedule/generate

Generates assignments for a date range using the scheduling engine with ACGME compliance validation.

**Authentication Required**

### Request Body

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": ["770e8400-e29b-41d4-a716-446655440000"],
  "algorithm": "greedy",
  "timeout_seconds": 60.0
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `start_date` | date | Yes | YYYY-MM-DD format |
| `end_date` | date | Yes | Must be > start_date |
| `pgy_levels` | integer[] | No | Filter by PGY levels [1, 2, 3] |
| `rotation_template_ids` | UUID[] | No | Specific templates to include |
| `algorithm` | string | No | `greedy`, `cp_sat`, `pulp`, `hybrid` (default: `greedy`) |
| `timeout_seconds` | float | No | 5.0 to 300.0 (default: 60.0) |

### Scheduling Algorithms

| Algorithm | Description | Speed | Quality | Use Case |
|-----------|-------------|-------|---------|----------|
| `greedy` | Fast heuristic assignment | Fast | Good | Quick schedule generation |
| `cp_sat` | Google OR-Tools constraint programming | Slow | Optimal | Best quality schedules |
| `pulp` | PuLP linear programming | Medium | Good | Alternative optimizer |
| `hybrid` | Combined approach | Medium | Very Good | Balanced performance |

### Example Requests

**Basic Schedule Generation:**

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"
  }'
```

**Schedule for Specific PGY Levels:**

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "pgy_levels": [1, 2]
  }'
```

**Schedule with Optimal Algorithm:**

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "algorithm": "cp_sat",
    "timeout_seconds": 120.0
  }'
```

**Schedule Specific Rotations:**

```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "rotation_template_ids": [
      "770e8400-e29b-41d4-a716-446655440000",
      "770e8400-e29b-41d4-a716-446655440001"
    ]
  }'
```

### Response

**Status:** `200 OK` (success) or `207 Multi-Status` (partial success)

```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 2920,
  "total_blocks": 3650,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 80.0,
    "statistics": {
      "total_assignments": 2920,
      "total_blocks": 3650,
      "residents_scheduled": 24
    }
  },
  "run_id": "aa0e8400-e29b-41d4-a716-446655440000",
  "solver_stats": {
    "total_blocks": 3650,
    "total_residents": 24,
    "coverage_rate": 80.0,
    "branches": 1250,
    "conflicts": 45
  }
}
```

### Status Values

| Status | HTTP Code | Description |
|--------|-----------|-------------|
| `success` | 200 | All blocks assigned, no violations |
| `partial` | 207 | Some blocks unassigned or violations present |
| `failed` | 422 | Critical error during generation |

### Response with Violations

```json
{
  "status": "partial",
  "message": "Schedule generated with violations",
  "total_blocks_assigned": 2800,
  "total_blocks": 3650,
  "validation": {
    "valid": false,
    "total_violations": 2,
    "violations": [
      {
        "type": "80_HOUR_VIOLATION",
        "severity": "CRITICAL",
        "person_id": "550e8400-e29b-41d4-a716-446655440000",
        "person_name": "Dr. Jane Smith",
        "block_id": null,
        "message": "Dr. Jane Smith: 82.5 hours/week average (limit: 80)",
        "details": {
          "window_start": "2024-01-01",
          "window_end": "2024-01-28",
          "average_weekly_hours": 82.5
        }
      }
    ],
    "coverage_rate": 76.7,
    "statistics": {...}
  },
  "run_id": "aa0e8400-e29b-41d4-a716-446655440001"
}
```

### Errors

| Status | Description |
|--------|-------------|
| 400 | Invalid date range |
| 401 | Not authenticated |
| 409 | Schedule generation already in progress |
| 422 | Generation failed |

```json
{
  "detail": "Schedule generation already in progress for overlapping date range"
}
```

---

## GET /api/schedule/validate

Validates the current schedule for ACGME compliance without modifying it.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |

### Example Request

```bash
curl "http://localhost:8000/api/schedule/validate?start_date=2024-01-01&end_date=2024-03-31"
```

### Response

**Status:** `200 OK`

**Compliant Schedule:**

```json
{
  "valid": true,
  "total_violations": 0,
  "violations": [],
  "coverage_rate": 98.2,
  "statistics": {
    "total_assignments": 3580,
    "total_blocks": 3650,
    "residents_scheduled": 24
  }
}
```

**Schedule with Violations:**

```json
{
  "valid": false,
  "total_violations": 3,
  "violations": [
    {
      "type": "80_HOUR_VIOLATION",
      "severity": "CRITICAL",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "person_name": "Dr. Jane Smith",
      "block_id": null,
      "message": "Dr. Jane Smith: 82.5 hours/week average (limit: 80)",
      "details": {
        "window_start": "2024-01-01",
        "window_end": "2024-01-28",
        "average_weekly_hours": 82.5
      }
    },
    {
      "type": "1_IN_7_VIOLATION",
      "severity": "HIGH",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "person_name": "Dr. Bob Wilson",
      "block_id": null,
      "message": "Dr. Bob Wilson: No day off in 8 consecutive days",
      "details": {
        "consecutive_days": 8,
        "period_start": "2024-01-08",
        "period_end": "2024-01-15"
      }
    },
    {
      "type": "SUPERVISION_RATIO_VIOLATION",
      "severity": "CRITICAL",
      "person_id": null,
      "person_name": null,
      "block_id": "660e8400-e29b-41d4-a716-446655440000",
      "message": "Sports Medicine Clinic: 5 residents with 1 supervisor (max ratio: 1:4)",
      "details": {
        "residents": 5,
        "supervisors": 1,
        "max_ratio": 4
      }
    }
  ],
  "coverage_rate": 95.5,
  "statistics": {
    "total_assignments": 3500,
    "total_blocks": 3650,
    "residents_scheduled": 24
  }
}
```

### Violation Types

| Type | Severity | Description | ACGME Rule |
|------|----------|-------------|------------|
| `80_HOUR_VIOLATION` | CRITICAL | Weekly hours exceed 80 average | 80-hour rule |
| `1_IN_7_VIOLATION` | HIGH | Missing required day off | 1-in-7 rule |
| `SUPERVISION_RATIO_VIOLATION` | CRITICAL | Too many residents per faculty | Supervision ratios |
| `CONSECUTIVE_DUTY_VIOLATION` | HIGH | Too many consecutive days | Duty hour limits |

### Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| `CRITICAL` | Must be resolved | Immediate correction |
| `HIGH` | Should be resolved | Review and fix |
| `MEDIUM` | Monitor | Track for patterns |
| `LOW` | Informational | No action needed |

---

## POST /api/schedule/emergency-coverage

Handles emergency absences by automatically finding replacement coverage.

**Authentication Required**

### Request Body

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-01-20",
  "end_date": "2024-01-25",
  "reason": "Family emergency",
  "is_deployment": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person who needs coverage |
| `start_date` | date | Yes | Start of absence |
| `end_date` | date | Yes | End of absence |
| `reason` | string | Yes | Reason for emergency |
| `is_deployment` | boolean | No | Military deployment (default: `false`) |

### Example Request

```bash
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440000",
    "start_date": "2024-01-20",
    "end_date": "2024-01-25",
    "reason": "Family emergency",
    "is_deployment": false
  }'
```

### Response

**Status:** `200 OK`

```json
{
  "status": "partial",
  "replacements_found": 8,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2024-01-20",
      "time_of_day": "AM",
      "original_assignment": "Sports Medicine Clinic",
      "replacement": {
        "person_id": "550e8400-e29b-41d4-a716-446655440002",
        "person_name": "Dr. Bob Wilson"
      },
      "status": "covered"
    },
    {
      "date": "2024-01-20",
      "time_of_day": "PM",
      "original_assignment": "Primary Care Clinic",
      "replacement": {
        "person_id": "550e8400-e29b-41d4-a716-446655440003",
        "person_name": "Dr. Alice Brown"
      },
      "status": "covered"
    },
    {
      "date": "2024-01-21",
      "time_of_day": "AM",
      "original_assignment": "Procedure Clinic",
      "replacement": null,
      "status": "gap"
    }
  ]
}
```

### Response Status Values

| Status | Description |
|--------|-------------|
| `success` | All slots covered |
| `partial` | Some gaps require manual review |
| `failed` | Unable to find any coverage |

### Coverage Detail Status

| Status | Description |
|--------|-------------|
| `covered` | Replacement found and assigned |
| `gap` | No replacement found |
| `unchanged` | No assignment existed |

### Errors

| Status | Description |
|--------|-------------|
| 401 | Not authenticated |
| 404 | Person not found |
| 422 | Invalid date range |

---

## Usage Examples

### Weekly Schedule Review

```bash
# Get this week's schedule
START=$(date -d "monday" +%Y-%m-%d)
END=$(date -d "friday" +%Y-%m-%d)

curl "http://localhost:8000/api/schedule/$START/$END"
```

### Quarterly Schedule Generation

```bash
# Generate Q1 schedule
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "algorithm": "hybrid"
  }'
```

### Compliance Monitoring

```bash
# Validate current month's schedule
MONTH_START=$(date +%Y-%m-01)
MONTH_END=$(date -d "$MONTH_START +1 month -1 day" +%Y-%m-%d)

curl "http://localhost:8000/api/schedule/validate?start_date=$MONTH_START&end_date=$MONTH_END"
```

### Emergency Coverage Workflow

```bash
# 1. Create absence record
ABSENCE_ID=$(curl -s -X POST http://localhost:8000/api/absences \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "'$PERSON_ID'",
    "start_date": "2024-01-20",
    "end_date": "2024-01-22",
    "absence_type": "family_emergency"
  }' | jq -r '.id')

# 2. Request emergency coverage
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "'$PERSON_ID'",
    "start_date": "2024-01-20",
    "end_date": "2024-01-22",
    "reason": "Family emergency"
  }'

# 3. Review gaps and manually assign if needed
```

---

*See also: [Assignments](./assignments.md) for manual assignment management*
