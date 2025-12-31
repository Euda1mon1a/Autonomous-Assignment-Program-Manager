# Schedule API Reference

**Endpoint Prefix:** `/api/schedule`

## Overview

The Schedule API manages residency schedule generation, validation, and analysis. It provides constraint-based optimization using multiple solvers to generate ACGME-compliant schedules while optimizing for coverage, fairness, and faculty preferences.

### Key Features

- **Schedule Generation**: Automated schedule creation using constraint programming
- **ACGME Validation**: Real-time compliance checking (80-hour rule, 1-in-7, supervision)
- **Emergency Coverage**: Handle unexpected absences and deployments
- **Import & Analysis**: Parse Excel schedules and detect conflicts
- **Swap Finder**: Identify compatible faculty swaps
- **Faculty Outpatient**: Generate faculty clinic and supervision assignments
- **Idempotency**: Prevent duplicate schedule generations with idempotency keys

### Scheduling Algorithms

1. **Greedy**: Fast heuristic, good for initial solutions (< 1 second)
2. **CP-SAT**: OR-Tools constraint programming, optimal solutions (5-30 seconds)
3. **PuLP**: Linear programming, fast for large problems (1-10 seconds)
4. **Hybrid**: Combines CP-SAT and PuLP for best results (10-60 seconds)

---

## Endpoints

### POST /generate

Generate a schedule for a date range.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: schedule-jan-2025-cpsat" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "algorithm": "cp_sat",
    "pgy_levels": [1, 2, 3],
    "rotation_template_ids": null,
    "timeout_seconds": 30
  }'
```

**Request Body:**
```json
{
  "start_date": "string (YYYY-MM-DD, required)",
  "end_date": "string (YYYY-MM-DD, required)",
  "algorithm": "greedy | cp_sat | pulp | hybrid (default: cp_sat)",
  "pgy_levels": "array of numbers (default: [1, 2, 3])",
  "rotation_template_ids": "array of UUIDs (optional, null = all templates)",
  "timeout_seconds": "number (default: 30, max: 300)"
}
```

**Headers:**
- `Idempotency-Key` (optional): Unique key for request deduplication
  - Same key + params = cached result returned
  - Same key + different params = 422 error
  - Different key = new schedule generated

**Response (200):**
```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 730,
  "total_blocks": 730,
  "validation": {
    "valid": true,
    "acgme_compliant": true,
    "violations": [],
    "warnings": []
  },
  "run_id": "550e8400-e29b-41d4-a716-446655440800",
  "solver_stats": {
    "total_blocks": 730,
    "total_residents": 15,
    "coverage_rate": 1.0,
    "branches": 4523,
    "conflicts": 0
  }
}
```

**Response (207 Multi-Status)** - Partial success:
```json
{
  "status": "partial",
  "message": "Schedule generated with 3 coverage gaps",
  "total_blocks_assigned": 727,
  "total_blocks": 730,
  "validation": {
    "valid": false,
    "acgme_compliant": true,
    "violations": [],
    "warnings": [
      {
        "rule": "coverage",
        "message": "3 blocks unassigned: dates 1/15-17 clinic slots",
        "affected_blocks": 3
      }
    ]
  },
  "run_id": "550e8400-e29b-41d4-a716-446655440800"
}
```

**Status Codes:**
- `200 OK`: Complete success, all blocks assigned and ACGME compliant
- `207 Multi-Status`: Partial success (some blocks unassigned but compliant)
- `422 Unprocessable Entity`: Failed completely (ACGME violations, infeasible constraints)

**Error Responses:**

- **400 Bad Request**: Invalid date range
  ```json
  {
    "detail": "Invalid date range"
  }
  ```

- **409 Conflict**: Generation already in progress for overlapping dates
  ```json
  {
    "detail": "Schedule generation already in progress for overlapping date range"
  }
  ```

- **422 Unprocessable Entity**: Idempotency key conflict
  ```json
  {
    "detail": "Idempotency key was already used with different request parameters"
  }
  ```

---

### GET /validate

Validate current schedule for ACGME compliance.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/schedule/validate?start_date=2025-01-01&end_date=2025-01-31' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `start_date` (required, YYYY-MM-DD): Validation from date
- `end_date` (required, YYYY-MM-DD): Validation to date

**Response (200):**
```json
{
  "valid": true,
  "acgme_compliant": true,
  "violations": [],
  "warnings": []
}
```

**Response with Issues:**
```json
{
  "valid": false,
  "acgme_compliant": false,
  "violations": [
    {
      "rule": "one_in_seven",
      "severity": "error",
      "person": "PGY1-01",
      "message": "No day off in 8 consecutive days",
      "dates": ["2025-01-15", "2025-01-22"]
    }
  ],
  "warnings": [
    {
      "rule": "80_hour_rule",
      "severity": "warning",
      "person": "PGY2-03",
      "message": "Weekly hours 82 (limit: 80)",
      "dates": ["2025-01-20"]
    }
  ]
}
```

---

### POST /emergency-coverage

Handle emergency absence and find replacement coverage.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/emergency-coverage \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "start_date": "2025-02-01",
    "end_date": "2025-02-07",
    "reason": "Medical emergency",
    "is_deployment": false
  }'
```

**Request Body:**
```json
{
  "person_id": "string (UUID, required)",
  "start_date": "string (YYYY-MM-DD, required)",
  "end_date": "string (YYYY-MM-DD, required)",
  "reason": "string (required)",
  "is_deployment": "boolean (default: false)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "replacements_found": 12,
  "coverage_gaps": 1,
  "requires_manual_review": false,
  "details": {
    "affected_assignments": 13,
    "covered_assignments": 12,
    "unassigned_slots": [
      {
        "date": "2025-02-05",
        "session": "PM",
        "rotation": "Cardiology Call",
        "reason": "No qualified attending available"
      }
    ],
    "replacement_suggestions": [
      {
        "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
        "date": "2025-02-01",
        "recommended_replacement": "Dr. Sarah Johnson (Cardiologist)"
      }
    ]
  }
}
```

---

### GET /{start_date}/{end_date}

Get the schedule for a date range.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/schedule/2025-01-01/2025-01-31' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `start_date` (required, YYYY-MM-DD): From date
- `end_date` (required, YYYY-MM-DD): To date

**Response (200):**
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "schedule": {
    "2025-01-01": {
      "AM": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440300",
          "person": {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "PGY1-01",
            "type": "resident",
            "pgy_level": 1
          },
          "role": "resident",
          "activity": "Inpatient",
          "abbreviation": "IP"
        }
      ],
      "PM": [...]
    }
  },
  "total_assignments": 730
}
```

---

## Import & Analysis

### POST /import/analyze

Analyze imported FMIT and clinic schedules for conflicts.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/import/analyze \
  -F "fmit_file=@fmit_schedule.xlsx" \
  -F "clinic_file=@clinic_schedule.xlsx" \
  -F 'specialty_providers={"Sports Medicine":["FAC-SPORTS"]}'
```

**Form Parameters:**
- `fmit_file` (required): FMIT rotation schedule Excel file
- `clinic_file` (optional): Clinic schedule Excel file
- `specialty_providers` (optional): JSON mapping specialties to provider names

**Response (200):**
```json
{
  "success": true,
  "fmit_schedule": {
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-12-31"
    },
    "total_weeks": 52,
    "providers": 22,
    "total_slots": 550
  },
  "clinic_schedule": {
    "date_range": {
      "start": "2025-01-01",
      "end": "2025-12-31"
    },
    "total_weeks": 52,
    "providers": 22,
    "total_slots": 440
  },
  "conflicts": [
    {
      "type": "double_booking",
      "provider": "Dr. Sarah Johnson",
      "fmit_dates": ["2025-02-01", "2025-02-07"],
      "clinic_dates": ["2025-02-03", "2025-02-05"],
      "overlapping_dates": ["2025-02-03", "2025-02-05"],
      "severity": "high"
    }
  ],
  "recommendations": [
    {
      "type": "consolidate_fmit",
      "provider": "Dr. Michael Chen",
      "current_pattern": "alternating weeks",
      "recommendation": "Consolidate FMIT weeks to reduce family burden",
      "impact": "Improves work-life balance"
    }
  ],
  "summary": {
    "total_conflicts": 3,
    "double_bookings": 2,
    "alternating_patterns": 5,
    "specialty_unavailability": 1
  }
}
```

### POST /import/analyze-file

Quick analysis of a single schedule file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/import/analyze-file \
  -F "file=@schedule.xlsx" \
  -F "file_type=auto" \
  -F 'specialty_providers={"Cardiology":["Dr. Johnson"]}'
```

**Form Parameters:**
- `file` (required): Excel schedule file
- `file_type` (optional): `'fmit'`, `'clinic'`, or `'auto'` (default)
- `specialty_providers` (optional): JSON mapping

**Response (200):**
```json
{
  "success": true,
  "file_name": "schedule.xlsx",
  "date_range": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "statistics": {
    "total_providers": 22,
    "total_slots": 550,
    "fmit_slots": 330,
    "clinic_slots": 220
  },
  "providers": [
    {
      "name": "Dr. Sarah Johnson",
      "total_slots": 26,
      "fmit_slots": 13,
      "clinic_slots": 13,
      "specialties": ["Cardiology"],
      "fmit_weeks": [
        {"start": "2025-01-01", "end": "2025-01-07"},
        {"start": "2025-03-01", "end": "2025-03-07"}
      ]
    }
  ],
  "alternating_patterns": [
    {
      "name": "Dr. Michael Chen",
      "fmit_weeks": ["2025-01-01", "2025-02-01", "2025-03-01"],
      "pattern": "alternating",
      "recommendation": "Consider consolidating FMIT weeks"
    }
  ],
  "warnings": []
}
```

### POST /import/block

Parse a specific block from an Excel schedule file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/import/block \
  -F "file=@block_schedule.xlsx" \
  -F "block_number=1" \
  -F 'known_people=["Dr. Sarah Johnson","Dr. Michael Chen","Dr. Lisa Anderson"]' \
  -F "include_fmit=true"
```

**Form Parameters:**
- `file` (required): Excel schedule file
- `block_number` (required): Block to parse (1-13)
- `known_people` (optional): JSON array of known names for fuzzy matching
- `include_fmit` (optional, default: true): Include FMIT schedule

**Response (200):**
```json
{
  "success": true,
  "block_number": 1,
  "start_date": "2025-01-01",
  "end_date": "2025-04-30",
  "residents": [
    {
      "name": "PGY1-01",
      "template": "PGY1",
      "confidence": 0.98
    }
  ],
  "residents_by_template": {
    "PGY1": [
      {"name": "PGY1-01", "template": "PGY1", "confidence": 0.98},
      {"name": "PGY1-02", "template": "PGY1", "confidence": 0.97}
    ]
  },
  "fmit_schedule": [
    {
      "block_number": 1,
      "week_number": 1,
      "start_date": "2025-01-01",
      "end_date": "2025-01-07",
      "faculty_name": "Dr. Sarah Johnson",
      "is_holiday_call": false
    }
  ],
  "assignments": [
    {
      "person_name": "Dr. Sarah Johnson",
      "date": "2025-01-01",
      "template": "Attending",
      "role": "FMIT",
      "slot_am": "IP",
      "slot_pm": "IP",
      "row_idx": 3,
      "confidence": 0.99
    }
  ],
  "warnings": [],
  "errors": [],
  "total_residents": 15,
  "total_assignments": 42
}
```

---

## Excel-Based Swap Finder

### POST /swaps/find

Find swap candidates from FMIT rotation schedule file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/swaps/find \
  -F "fmit_file=@fmit_schedule.xlsx" \
  -F 'request_json={"target_faculty":"Dr. Sarah Johnson","target_week":"2025-02-01","schedule_release_days":2,"include_absence_conflicts":true}'
```

**Form Parameters:**
- `fmit_file` (required): FMIT schedule Excel file
- `request_json` (required): SwapFinderRequest JSON string

**Request JSON Structure:**
```json
{
  "target_faculty": "string (faculty name, required)",
  "target_week": "string (YYYY-MM-DD, required)",
  "faculty_targets": [
    {
      "name": "string",
      "target_weeks": ["2025-02-01"],
      "role": "string (optional)",
      "current_weeks": ["2025-01-01"]
    }
  ],
  "external_conflicts": [
    {
      "faculty": "string",
      "start_date": "2025-02-01",
      "end_date": "2025-02-07",
      "conflict_type": "leave | tdy | deployment",
      "description": "string (optional)"
    }
  ],
  "schedule_release_days": 2,
  "include_absence_conflicts": true
}
```

**Response (200):**
```json
{
  "success": true,
  "target_faculty": "Dr. Sarah Johnson",
  "target_week": "2025-02-01",
  "candidates": [
    {
      "faculty": "Dr. Michael Chen",
      "can_take_week": "2025-02-01",
      "gives_week": "2025-03-01",
      "back_to_back_ok": true,
      "external_conflict": false,
      "flexibility": 0.85,
      "reason": "Can swap with Dr. Chen for week of 3/1",
      "rank": 1
    }
  ],
  "total_candidates": 5,
  "viable_candidates": 3,
  "alternating_patterns": [
    {
      "faculty": "Dr. James Wilson",
      "cycle_count": 4,
      "fmit_weeks": ["2025-01-01", "2025-03-01"],
      "recommendation": "Consider consolidating FMIT weeks"
    }
  ],
  "message": "Found 3 viable swap candidates out of 5 total"
}
```

### POST /swaps/candidates

Find swap candidates using JSON input (no file upload).

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/swaps/candidates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
    "max_candidates": 10
  }'
```

**Request Body:**
```json
{
  "person_id": "string (UUID, required)",
  "assignment_id": "string (UUID, optional)",
  "block_id": "string (UUID, optional)",
  "max_candidates": "number (default: 10)"
}
```

**Response (200):** (See SWAPS_API.md for full response format)

---

## Faculty Outpatient Assignments

### POST /faculty-outpatient/generate

Generate faculty primary clinic and supervision assignments for a block.

**Request:**
```bash
curl -X POST 'http://localhost:8000/api/schedule/faculty-outpatient/generate?block_number=1&regenerate=true&include_clinic=true&include_supervision=true' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `block_number` (required): Block number (1-13)
- `regenerate` (optional, default: true): Clear existing assignments first
- `include_clinic` (optional, default: true): Generate clinic assignments
- `include_supervision` (optional, default: true): Generate supervision assignments

**Response (200):**
```json
{
  "success": true,
  "message": "Faculty outpatient assignments generated successfully",
  "block_number": 1,
  "block_start": "2025-01-01",
  "block_end": "2025-04-30",
  "total_clinic_assignments": 156,
  "total_supervision_assignments": 78,
  "cleared_count": 234,
  "faculty_summaries": [
    {
      "faculty_id": "550e8400-e29b-41d4-a716-446655440010",
      "faculty_name": "Dr. Sarah Johnson",
      "faculty_role": "attending",
      "clinic_sessions": 13,
      "supervision_sessions": 6,
      "total_sessions": 19
    }
  ],
  "warnings": [],
  "errors": []
}
```

---

## Data Models

### Schedule Generation Request

```json
{
  "start_date": "string",
  "end_date": "string",
  "algorithm": "string",
  "pgy_levels": "array",
  "rotation_template_ids": "array or null",
  "timeout_seconds": "number"
}
```

### Validation Result

```json
{
  "valid": "boolean",
  "acgme_compliant": "boolean",
  "violations": ["object"],
  "warnings": ["object"]
}
```

### Violation Item

```json
{
  "rule": "string",
  "severity": "string",
  "message": "string",
  "affected_dates": ["string"],
  "person": "string (optional)"
}
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Generation in progress |
| 422 | Unprocessable Entity | Request conflict or validation error |
| 500 | Internal Server Error | Server error |

---

## Best Practices

### 1. Use Idempotency Keys

```bash
# Generate with idempotency key
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Idempotency-Key: block-1-jan-2025-v2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{...}'

# Same key + params = returns cached result (instant)
# Retry-safe: Can safely retry without duplicating
```

### 2. Use Appropriate Algorithm

- **Greedy**: Quick tests, initial solutions
- **CP-SAT**: Production schedules, optimal solutions
- **Hybrid**: Best quality, slower (use for final generation)

### 3. Validate Before Finalizing

```bash
# Generate schedule
curl -X POST http://localhost:8000/api/schedule/generate ...

# Then validate
curl -X GET 'http://localhost:8000/api/schedule/validate?start_date=2025-01-01&end_date=2025-01-31'

# Check for violations before publishing
```

---

## Related Documentation

- [Scheduling Algorithm Details](../architecture/SOLVER_ALGORITHM.md)
- [ACGME Compliance Rules](../architecture/ACGME_COMPLIANCE.md)
- [Import Guide - FMIT Schedules](../user-guide/fmit-import.md)
- [Excel Format Requirements](../user-guide/excel-format.md)
