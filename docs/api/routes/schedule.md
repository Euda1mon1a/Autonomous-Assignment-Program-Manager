# Schedule API

Complete reference for the `/api/v1/schedule` endpoints.

> **Base Path:** `/api/v1/schedule`
> **Authentication:** Required (Bearer token)
> **Source:** `backend/app/api/routes/schedule.py`

---

## Table of Contents

1. [Overview](#overview)
2. [Core Endpoints](#core-endpoints)
3. [Import & Analysis Endpoints](#import--analysis-endpoints)
4. [Swap Finder Endpoints](#swap-finder-endpoints)
5. [Faculty Outpatient Endpoints](#faculty-outpatient-endpoints)
6. [Schemas](#schemas)
7. [Examples](#examples)
8. [Error Handling](#error-handling)

---

## Overview

The Schedule API provides schedule generation, validation, emergency coverage, import/analysis, and swap finding capabilities.

### Key Features

- **Multiple Algorithms**: Greedy, CP-SAT, PuLP, and Hybrid solvers
- **ACGME Validation**: Automatic compliance checking (80-hour rule, 1-in-7 rule, supervision ratios)
- **Idempotency**: Prevent duplicate generations with `Idempotency-Key` header
- **Emergency Coverage**: Handle deployments, TDY, and medical emergencies
- **Import Analysis**: Parse Excel schedules and detect conflicts
- **Swap Finder**: Find swap candidates for FMIT weeks
- **Block Parsing**: Extract resident rosters and FMIT schedules from Excel

---

## Core Endpoints

### Generate Schedule

```http
POST /api/v1/schedule/generate
```

Generate schedule for a date range using constraint-based optimization.

**Authorization:** Required (authenticated user)

**Request Body:** `ScheduleRequest`

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Idempotency-Key` | string | No | Unique key to prevent duplicate generations |

**Response:** `ScheduleResponse`

**Status Codes:**
- `200 OK`: Schedule generated successfully
- `207 Multi-Status`: Partial success (some assignments created but with violations)
- `401 Unauthorized`: Missing or invalid authentication
- `409 Conflict`: Schedule generation already in progress or idempotency key conflict
- `422 Unprocessable Entity`: Validation failure or generation failed
- `500 Internal Server Error`: Server error

**Notes:**
- Uses idempotency to prevent duplicate generations with same key
- Returns cached result if same key is sent with identical parameters
- Validates ACGME compliance and returns warnings
- Supports multiple algorithms (greedy, cp_sat, pulp, hybrid)

---

### Validate Schedule

```http
GET /api/v1/schedule/validate
```

Validate current schedule for ACGME compliance.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |

**Response:** `ValidationResult`

**Status Codes:**
- `200 OK`: Validation complete
- `400 Bad Request`: Invalid date format
- `401 Unauthorized`: Missing or invalid authentication

**Checks:**
- 80-hour rule (rolling 4-week average)
- 1-in-7 days off
- Supervision ratios (1:2 for PGY-1, 1:4 for PGY-2/3)

---

### Handle Emergency Coverage

```http
POST /api/v1/schedule/emergency-coverage
```

Handle emergency absence and find replacement coverage.

**Authorization:** Required (authenticated user)

**Request Body:** `EmergencyRequest`

**Response:** `EmergencyResponse`

**Status Codes:**
- `200 OK`: Coverage handled successfully
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Validation failure

**Use Cases:**
- Military deployments
- TDY assignments
- Medical emergencies
- Family emergencies

---

### Get Schedule

```http
GET /api/v1/schedule/{start_date}/{end_date}
```

Get the schedule for a date range.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | string | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string | Yes | End date (YYYY-MM-DD) |

**Response:** Schedule object with assignments grouped by date

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid date format

**Returns:** All assignments with person and rotation template details, grouped by date.

---

## Import & Analysis Endpoints

### Analyze Imported Schedules

```http
POST /api/v1/schedule/import/analyze
```

Import and analyze schedules for conflicts.

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fmit_file` | file | Yes | FMIT rotation schedule Excel file |
| `clinic_file` | file | No | Clinic schedule Excel file (optional) |
| `specialty_providers` | string | No | JSON mapping of specialty to providers |

**Response:** `ImportAnalysisResponse`

**Status Codes:**
- `200 OK`: Analysis complete
- `400 Bad Request`: Failed to read file or invalid JSON
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Analysis failed

**Detects:**
- Double-bookings (same provider scheduled for FMIT and clinic)
- Specialty unavailability (specialty provider on FMIT creates clinic gap)
- Alternating patterns (week-on/week-off that's hard on families)

**Notes:**
- Analysis-only endpoint - no data written to database
- Use to identify conflicts before finalizing schedules

---

### Analyze Single File

```http
POST /api/v1/schedule/import/analyze-file
```

Quick analysis of a single schedule file.

**Form Data:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | Yes | - | Schedule Excel file to analyze |
| `file_type` | string | No | auto | File type: `fmit`, `clinic`, or `auto` to detect |
| `specialty_providers` | string | No | - | JSON mapping of specialty to providers |

**Response:** File analysis with provider summary and alternating patterns

**Status Codes:**
- `200 OK`: Analysis complete
- `400 Bad Request`: Failed to read file
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Failed to parse file

---

### Parse Block Schedule

```http
POST /api/v1/schedule/import/block
```

Parse a specific block schedule from an Excel file.

**Authorization:** Required (authenticated user)

**Form Data:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | Yes | - | Excel schedule file |
| `block_number` | int | Yes | - | Block number to parse (1-13) |
| `known_people` | string | No | - | JSON array of known names for fuzzy matching |
| `include_fmit` | bool | No | true | Include FMIT attending schedule |

**Response:** `BlockParseResponse`

**Status Codes:**
- `200 OK`: Parse successful
- `400 Bad Request`: Invalid file or JSON format
- `401 Unauthorized`: Missing or invalid authentication
- `422 Unprocessable Entity`: Parse failed

**Extracts:**
- Resident roster grouped by template (R1, R2, R3)
- FMIT attending schedule (weekly faculty assignments)
- Daily assignments with AM/PM slots

**Handles:**
- Column shifts from copy/paste
- Merged cells
- Name typos (fuzzy matching with known_people list)

---

## Swap Finder Endpoints

### Find Swap Candidates (Excel)

```http
POST /api/v1/schedule/swaps/find
```

Find swap candidates for an FMIT week using Excel file.

**Authorization:** Required (authenticated user)

**Form Data:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fmit_file` | file | Yes | FMIT rotation schedule Excel file |
| `request_json` | string | Yes | `SwapFinderRequest` as JSON string |

**Response:** `SwapFinderResponse`

**Status Codes:**
- `200 OK`: Candidates found
- `400 Bad Request`: Invalid request JSON or failed to read file
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Target faculty not found in schedule
- `422 Unprocessable Entity`: Invalid request parameters

**Process:**
1. Parses FMIT schedule from Excel
2. Cross-references with database absence records (if enabled)
3. Finds all faculty who could take the target week
4. Ranks candidates by viability

**Returns:**
- Ranked list of swap candidates
- Whether they can do 1:1 swap or must absorb
- External conflicts (leave, TDY, etc.)
- Faculty with excessive alternating patterns

---

### Find Swap Candidates (JSON)

```http
POST /api/v1/schedule/swaps/candidates
```

Find swap candidates using JSON input (no file upload).

**Authorization:** Required (authenticated user)

**Request Body:** `SwapCandidateJsonRequest`

**Response:** `SwapCandidateJsonResponse`

**Status Codes:**
- `200 OK`: Candidates found
- `400 Bad Request`: Invalid person_id format
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Person not found

**Notes:**
- Queries database directly (no Excel file required)
- Suitable for MCP tool integration
- Returns ranked candidates based on match score

---

## Faculty Outpatient Endpoints

### Generate Faculty Outpatient Assignments

```http
POST /api/v1/schedule/faculty-outpatient/generate
```

Generate faculty PRIMARY clinic and SUPERVISION assignments for a block.

**Authorization:** Required (authenticated user)

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `block_number` | int | Yes | - | Block number (1-13) |
| `regenerate` | bool | No | true | Clear existing faculty outpatient assignments first |
| `include_clinic` | bool | No | true | Generate faculty primary clinic assignments |
| `include_supervision` | bool | No | true | Generate faculty supervision assignments |

**Response:** Generation result with assignment counts and faculty summaries

**Status Codes:**
- `200 OK`: Generation successful
- `400 Bad Request`: Generation failed
- `401 Unauthorized`: Missing or invalid authentication
- `500 Internal Server Error`: Server error

**Generates:**
1. Faculty clinic sessions - Based on role limits (PD=0, APD=2, Core=4/week)
2. Faculty supervision - ACGME-compliant supervision of resident assignments

**Warning:** This endpoint modifies the database. Ensure backup before use.

---

## Schemas

### ScheduleRequest

```json
{
  "start_date": "2024-07-01",
  "end_date": "2025-06-30",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": ["uuid1", "uuid2"],
  "algorithm": "hybrid",
  "timeout_seconds": 60.0
}
```

**Fields:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `start_date` | date | Yes | - | Start date for schedule |
| `end_date` | date | Yes | - | End date for schedule |
| `pgy_levels` | array[int] | No | - | Filter residents by PGY level |
| `rotation_template_ids` | array[UUID] | No | - | Specific templates to use |
| `algorithm` | string | No | greedy | Algorithm: `greedy`, `cp_sat`, `pulp`, `hybrid` |
| `timeout_seconds` | float | No | 60.0 | Maximum solver runtime (5-300 seconds) |

---

### ScheduleResponse

```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 720,
  "total_blocks": 730,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 98.6,
    "statistics": {}
  },
  "run_id": "uuid",
  "solver_stats": {
    "total_blocks": 730,
    "total_residents": 24,
    "coverage_rate": 98.6,
    "branches": 1500,
    "conflicts": 32
  },
  "nf_pc_audit": {
    "compliant": true,
    "total_nf_transitions": 45,
    "violations": [],
    "message": "All Night Float transitions have proper Post-Call coverage"
  },
  "acgme_override_count": 0
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Status: `success`, `partial`, `failed` |
| `message` | string | Human-readable message |
| `total_blocks_assigned` | int | Number of blocks assigned |
| `total_blocks` | int | Total blocks in range |
| `validation` | ValidationResult | ACGME validation results |
| `run_id` | UUID | Schedule run ID (for tracking) |
| `solver_stats` | SolverStatistics | Solver statistics |
| `nf_pc_audit` | NFPCAudit | Night Float to Post-Call audit results |
| `acgme_override_count` | int | Number of acknowledged ACGME overrides |

---

### ValidationResult

```json
{
  "valid": true,
  "total_violations": 0,
  "violations": [],
  "coverage_rate": 98.6,
  "statistics": {
    "total_residents": 24,
    "total_assignments": 720,
    "avg_hours_per_week": 65.5
  }
}
```

---

### EmergencyRequest

```json
{
  "person_id": "uuid",
  "start_date": "2025-01-15",
  "end_date": "2025-02-15",
  "reason": "Deployment",
  "is_deployment": true
}
```

---

### EmergencyResponse

```json
{
  "status": "success",
  "replacements_found": 25,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2025-01-15",
      "original_person": "Dr. Smith",
      "replacement_person": "Dr. Jones",
      "activity": "Inpatient"
    }
  ]
}
```

---

### SwapFinderRequest

```json
{
  "target_faculty": "Dr. Smith",
  "target_week": "2025-01-13",
  "faculty_targets": [
    {
      "name": "Dr. Jones",
      "target_weeks": 6,
      "role": "faculty",
      "current_weeks": 5
    }
  ],
  "external_conflicts": [
    {
      "faculty": "Dr. Brown",
      "start_date": "2025-01-15",
      "end_date": "2025-01-20",
      "conflict_type": "conference",
      "description": "AAFP Conference"
    }
  ],
  "include_absence_conflicts": true,
  "schedule_release_days": 90
}
```

---

### SwapFinderResponse

```json
{
  "success": true,
  "target_faculty": "Dr. Smith",
  "target_week": "2025-01-13",
  "candidates": [
    {
      "faculty": "Dr. Jones",
      "can_take_week": "2025-01-13",
      "gives_week": "2025-02-10",
      "back_to_back_ok": true,
      "external_conflict": null,
      "flexibility": "easy",
      "reason": "1:1 swap available",
      "rank": 1
    }
  ],
  "total_candidates": 12,
  "viable_candidates": 8,
  "alternating_patterns": [
    {
      "faculty": "Dr. Brown",
      "cycle_count": 4,
      "fmit_weeks": ["2025-01-06", "2025-01-20", "2025-02-03"],
      "recommendation": "Consider consolidating FMIT weeks to reduce family burden"
    }
  ],
  "message": "Found 8 viable swap candidates out of 12 total"
}
```

---

## Examples

### Generate Schedule with Idempotency

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/schedule/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: schedule-gen-2025-01-15-001" \
  -d '{
    "start_date": "2024-07-01",
    "end_date": "2025-06-30",
    "pgy_levels": [1, 2, 3],
    "algorithm": "hybrid",
    "timeout_seconds": 120.0
  }'
```

**Response (200 OK):**

```json
{
  "status": "success",
  "message": "Schedule generated successfully using hybrid algorithm",
  "total_blocks_assigned": 720,
  "total_blocks": 730,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 98.6,
    "statistics": {
      "total_residents": 24,
      "total_assignments": 720,
      "avg_hours_per_week": 65.5
    }
  },
  "run_id": "aa0e8400-e29b-41d4-a716-446655440001",
  "solver_stats": {
    "total_blocks": 730,
    "total_residents": 24,
    "coverage_rate": 98.6,
    "branches": 1500,
    "conflicts": 32
  },
  "nf_pc_audit": {
    "compliant": true,
    "total_nf_transitions": 45,
    "violations": [],
    "message": "All Night Float transitions have proper Post-Call coverage"
  },
  "acgme_override_count": 0
}
```

---

### Validate Schedule

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/schedule/validate?start_date=2025-01-01&end_date=2025-01-31" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "valid": false,
  "total_violations": 2,
  "violations": [
    {
      "type": "80_HOUR",
      "severity": "CRITICAL",
      "person_id": "bb0e8400-e29b-41d4-a716-446655440002",
      "person_name": "PGY2-01",
      "block_id": null,
      "message": "Resident exceeds 80-hour limit in rolling 4-week period (actual: 82.5 hours)",
      "details": {
        "hours": 82.5,
        "period_start": "2025-01-01",
        "period_end": "2025-01-28"
      }
    }
  ],
  "coverage_rate": 98.5,
  "statistics": {
    "total_residents": 24,
    "total_assignments": 720,
    "avg_hours_per_week": 65.5
  }
}
```

---

### Handle Emergency Coverage

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/schedule/emergency-coverage" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "cc0e8400-e29b-41d4-a716-446655440003",
    "start_date": "2025-01-15",
    "end_date": "2025-02-15",
    "reason": "Military deployment",
    "is_deployment": true
  }'
```

**Response:**

```json
{
  "status": "partial",
  "replacements_found": 25,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2025-01-15",
      "time_of_day": "AM",
      "original_person": "Dr. Smith",
      "replacement_person": "Dr. Jones",
      "activity": "Inpatient",
      "success": true
    },
    {
      "date": "2025-01-16",
      "time_of_day": "PM",
      "original_person": "Dr. Smith",
      "replacement_person": null,
      "activity": "Call",
      "success": false,
      "reason": "No qualified faculty available"
    }
  ]
}
```

---

### Find Swap Candidates (JSON)

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/schedule/swaps/candidates" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "dd0e8400-e29b-41d4-a716-446655440004",
    "max_candidates": 10
  }'
```

**Response:**

```json
{
  "success": true,
  "requester_person_id": "dd0e8400-e29b-41d4-a716-446655440004",
  "requester_name": "Dr. Smith",
  "original_assignment_id": "ee0e8400-e29b-41d4-a716-446655440005",
  "candidates": [
    {
      "candidate_person_id": "ff0e8400-e29b-41d4-a716-446655440006",
      "candidate_name": "Dr. Jones",
      "candidate_role": "Faculty",
      "assignment_id": "000e8400-e29b-41d4-a716-446655440007",
      "block_date": "2025-01-20",
      "block_session": "AM",
      "match_score": 0.85,
      "rotation_name": "FMIT",
      "compatibility_factors": {
        "same_type": true,
        "same_block": false
      },
      "mutual_benefit": false,
      "approval_likelihood": "high"
    }
  ],
  "total_candidates": 10,
  "top_candidate_id": "ff0e8400-e29b-41d4-a716-446655440006",
  "message": "Found 10 swap candidates"
}
```

---

## Error Handling

### 409 Conflict - Idempotency Key Conflict

```json
{
  "detail": "Idempotency key was already used with different request parameters. Use a new key for different requests."
}
```

**Cause:** Same idempotency key used with different request body.

**Resolution:** Use a new idempotency key or resend with identical parameters.

---

### 409 Conflict - Generation In Progress

```json
{
  "detail": "Schedule generation already in progress for overlapping date range. Please wait for the current run to complete."
}
```

**Cause:** Another schedule generation is running for overlapping dates.

**Resolution:** Wait for current generation to complete or cancel it.

---

### 207 Multi-Status - Partial Success

**Status Code:** 207

```json
{
  "status": "partial",
  "message": "Schedule partially generated with some violations",
  "total_blocks_assigned": 650,
  "total_blocks": 730,
  "validation": {
    "valid": false,
    "total_violations": 15,
    "violations": [...]
  }
}
```

**Cause:** Some assignments created but with ACGME violations.

**Resolution:** Review violations and adjust schedule as needed.

---

## Related Documentation

- [Assignments API](assignments.md) - View and manage generated assignments
- [Blocks API](blocks.md) - Block structure and management
- [ACGME Compliance](../../architecture/acgme-compliance.md) - Compliance rules
- [Solver Algorithm](../../architecture/SOLVER_ALGORITHM.md) - Scheduling engine details

---

*Last Updated: 2025-12-31*
