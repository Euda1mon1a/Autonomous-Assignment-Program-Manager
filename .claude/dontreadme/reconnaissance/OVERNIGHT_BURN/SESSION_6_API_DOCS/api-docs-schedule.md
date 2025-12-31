# Schedule API Complete Documentation

**Status:** Comprehensive Reconnaissance Complete
**Last Updated:** 2025-12-30
**Source Files:**
- `/backend/app/api/routes/schedule.py` (1,302 lines)
- `/backend/app/schemas/schedule.py` (350 lines)
- `/docs/api/routes/schedule.md` (existing)
- `/docs/api/endpoints/schedules.md` (existing)

---

## Table of Contents

1. [Overview](#overview)
2. [Core Features](#core-features)
3. [API Endpoint Catalog](#api-endpoint-catalog)
4. [Authentication & Authorization](#authentication--authorization)
5. [Request/Response Schemas](#requestresponse-schemas)
6. [Generation Parameters & Options](#generation-parameters--options)
7. [Response Formats](#response-formats)
8. [Integration Guide](#integration-guide)
9. [Error Handling](#error-handling)
10. [Advanced Features](#advanced-features)
11. [Implementation Notes](#implementation-notes)

---

## Overview

The Schedule API (`/api/v1/schedule`) provides comprehensive schedule generation, validation, emergency coverage, import/analysis, swap matching, and faculty outpatient assignment capabilities. All endpoints use REST conventions with JSON payloads.

**Base Path:** `/api/v1/schedule`
**Protocol:** HTTP/HTTPS
**Content-Type:** `application/json` (all requests/responses)
**Authentication:** JWT Bearer token (required for most endpoints)

---

## Core Features

### 1. Schedule Generation
- **Constraint-based optimization** using multiple solvers
- **ACGME compliance** validation (80-hour rule, 1-in-7, supervision ratios)
- **Idempotency support** via `Idempotency-Key` header
- **Multiple algorithms**: Greedy, CP-SAT, PuLP, Hybrid
- **Solver statistics** including branch counts and conflict metrics
- **Night Float to Post-Call audit** for proper coverage transitions

### 2. Schedule Validation
- Real-time ACGME compliance checking
- Violation detection with severity levels
- Coverage rate calculation
- Statistics on residents, assignments, and work hours

### 3. Emergency Coverage
- Handle military deployments, TDY, medical/family emergencies
- Auto-find replacement coverage
- Critical service prioritization
- Manual review flagging for gaps

### 4. Import & Analysis
- Parse Excel schedule files (FMIT and clinic)
- Detect conflicts: double-bookings, specialty gaps, alternating patterns
- Fuzzy-tolerant block schedule parsing with anchor-based matching
- Provider summary with alternating pattern detection

### 5. Swap Finding
- Find swap candidates for FMIT weeks
- File-based (Excel) and JSON-based lookups
- Rank candidates by viability
- External conflict detection (leave, TDY, conferences)
- Alternating pattern identification

### 6. Faculty Outpatient Assignment
- Generate faculty primary clinic sessions
- Generate faculty supervision assignments
- Role-based clinic session limits
- Batch generation with reporting

---

## API Endpoint Catalog

### Core Endpoints (Schedule Management)

#### POST /generate
**Generate Schedule for Date Range**

```
POST /api/v1/schedule/generate
Authorization: Bearer <token>
Idempotency-Key: <optional-unique-key>
Content-Type: application/json

{
  "start_date": "2024-07-01",
  "end_date": "2025-06-30",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": ["uuid1", "uuid2"],
  "algorithm": "hybrid",
  "timeout_seconds": 120.0
}
```

**Status Codes:**
- `200 OK` - Success (fully compliant schedule)
- `207 Multi-Status` - Partial success (violations present)
- `401 Unauthorized` - Missing/invalid authentication
- `409 Conflict` - Generation in progress or idempotency conflict
- `422 Unprocessable Entity` - Validation failure or complete failure
- `500 Internal Server Error` - Server error

**Key Features:**
- Idempotency caching with `X-Idempotency-Replayed` header
- Double-submit protection (checks for overlapping date ranges)
- Solver metrics collection
- Post-generation Night Float to Post-Call audit

---

#### GET /validate
**Validate Schedule for ACGME Compliance**

```
GET /api/v1/schedule/validate?start_date=2025-01-01&end_date=2025-01-31
Authorization: Bearer <token>
```

**Query Parameters:**
- `start_date` (string, required): YYYY-MM-DD
- `end_date` (string, required): YYYY-MM-DD

**Status Codes:**
- `200 OK` - Validation complete
- `400 Bad Request` - Invalid date format
- `401 Unauthorized` - Missing/invalid authentication

**Validation Checks:**
1. **80-Hour Rule**: Max 80 hours/week (rolling 4-week average)
2. **1-in-7 Rule**: One 24-hour period off every 7 days
3. **Supervision Ratios**: PGY-1: 1:2, PGY-2/3: 1:4 faculty-to-resident

---

#### GET /{start_date}/{end_date}
**Retrieve Schedule for Date Range**

```
GET /api/v1/schedule/2024-07-01/2024-07-31
Authorization: Bearer <token>
```

**Path Parameters:**
- `start_date` (string): YYYY-MM-DD
- `end_date` (string): YYYY-MM-DD

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid date format

**Response Format:** Schedule grouped by date with AM/PM sessions

---

#### POST /emergency-coverage
**Handle Emergency Absence & Find Replacement Coverage**

```
POST /api/v1/schedule/emergency-coverage
Authorization: Bearer <token>
Content-Type: application/json

{
  "person_id": "uuid",
  "start_date": "2025-01-15",
  "end_date": "2025-02-15",
  "reason": "Military deployment",
  "is_deployment": true
}
```

**Status Codes:**
- `200 OK` - Coverage handled
- `401 Unauthorized` - Missing/invalid authentication
- `422 Unprocessable Entity` - Validation failure

**Use Cases:**
- Military deployments
- TDY (Temporary Duty) assignments
- Medical emergencies
- Family emergencies

---

### Import & Analysis Endpoints

#### POST /import/analyze
**Analyze Multiple Schedule Files for Conflicts**

```
POST /api/v1/schedule/import/analyze
Content-Type: multipart/form-data

fmit_file: [Excel file]
clinic_file: [Excel file] (optional)
specialty_providers: {"Sports Medicine": ["FAC-SPORTS"]} (optional JSON string)
```

**Status Codes:**
- `200 OK` - Analysis complete
- `400 Bad Request` - Failed to read file or invalid JSON
- `401 Unauthorized` - Missing/invalid authentication
- `422 Unprocessable Entity` - Analysis failed

**Detections:**
- Double-bookings (same provider on FMIT and clinic)
- Specialty unavailability (specialty provider on FMIT creates clinic gap)
- Alternating patterns (week-on/week-off patterns)

**Note:** Analysis-only (no database writes). Use to identify conflicts before finalizing.

---

#### POST /import/analyze-file
**Quick Analysis of Single Schedule File**

```
POST /api/v1/schedule/import/analyze-file
Content-Type: multipart/form-data

file: [Excel file]
file_type: "auto" (or "fmit", "clinic")
specialty_providers: {"Sports Medicine": ["FAC-SPORTS"]} (optional JSON string)
```

**Status Codes:**
- `200 OK` - Analysis complete
- `400 Bad Request` - Failed to read file
- `401 Unauthorized` - Missing/invalid authentication
- `422 Unprocessable Entity` - Failed to parse file

**Returns:**
- Provider summary with slot counts
- FMIT weeks by provider
- Alternating pattern detection
- Date range and statistics

---

#### POST /import/block
**Parse Specific Block Schedule from Excel (Anchor-Based Fuzzy Matching)**

```
POST /api/v1/schedule/import/block
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: [Excel file]
block_number: 10 (1-13)
known_people: ["PGY1-01", "PGY2-03", "FAC-PD"] (optional JSON array)
include_fmit: true (optional, default: true)
```

**Status Codes:**
- `200 OK` - Parse successful
- `400 Bad Request` - Invalid file or JSON format
- `401 Unauthorized` - Missing/invalid authentication
- `422 Unprocessable Entity` - Parse failed

**Extraction Capabilities:**
- Resident roster grouped by template (R1, R2, R3)
- FMIT attending schedule (weekly faculty assignments)
- Daily assignments with AM/PM slots

**Handles:**
- Column shifts from copy/paste
- Merged cells
- Name typos (fuzzy matching with `known_people` list)

---

### Swap Finder Endpoints

#### POST /swaps/find
**Find Swap Candidates for FMIT Week (Excel-Based)**

```
POST /api/v1/schedule/swaps/find
Authorization: Bearer <token>
Content-Type: multipart/form-data

fmit_file: [Excel file]
request_json: {
  "target_faculty": "Dr. Smith",
  "target_week": "2025-01-13",
  "faculty_targets": [...],
  "external_conflicts": [...],
  "include_absence_conflicts": true,
  "schedule_release_days": 90
}
```

**Status Codes:**
- `200 OK` - Candidates found
- `400 Bad Request` - Invalid request JSON or file read failure
- `401 Unauthorized` - Missing/invalid authentication
- `404 Not Found` - Target faculty not in schedule
- `422 Unprocessable Entity` - Invalid request parameters

**Process:**
1. Parse FMIT schedule from Excel
2. Cross-reference with database absence records (if enabled)
3. Find all faculty who could take target week
4. Rank candidates by viability

**Returns:**
- Ranked swap candidates with match details
- 1:1 swap vs. absorb indicators
- External conflict flags
- Alternating pattern analysis

---

#### POST /swaps/candidates
**Find Swap Candidates Using JSON (No File Upload, MCP-Compatible)**

```
POST /api/v1/schedule/swaps/candidates
Authorization: Bearer <token>
Content-Type: application/json

{
  "person_id": "uuid",
  "assignment_id": "uuid" (optional),
  "block_id": "uuid" (optional),
  "max_candidates": 10
}
```

**Status Codes:**
- `200 OK` - Candidates found
- `400 Bad Request` - Invalid person_id format
- `401 Unauthorized` - Missing/invalid authentication
- `404 Not Found` - Person not found

**Advantages:**
- No file upload required
- Direct database queries
- Suitable for MCP tool integration
- Returns ranked candidates with match scores

---

### Faculty Outpatient Endpoints

#### POST /faculty-outpatient/generate
**Generate Faculty Primary Clinic & Supervision Assignments**

```
POST /api/v1/schedule/faculty-outpatient/generate?block_number=10&regenerate=true
Authorization: Bearer <token>
```

**Query Parameters:**
- `block_number` (int, required): Block 1-13
- `regenerate` (bool, optional, default: true): Clear existing assignments first
- `include_clinic` (bool, optional, default: true): Generate clinic sessions
- `include_supervision` (bool, optional, default: true): Generate supervision

**Status Codes:**
- `200 OK` - Generation successful
- `400 Bad Request` - Generation failed
- `401 Unauthorized` - Missing/invalid authentication
- `500 Internal Server Error` - Server error

**Generates:**
1. **Faculty Clinic Sessions** - Based on role limits:
   - PD: 0 sessions/week
   - APD: 2 sessions/week
   - Core Faculty: 4 sessions/week

2. **Faculty Supervision** - ACGME-compliant supervision ratios

**Warning:** This endpoint modifies the database. Ensure backup before use.

---

## Authentication & Authorization

### Authorization Requirements

- **All endpoints except `/validate` and `/{start_date}/{end_date}`**: Require JWT Bearer token
- **Token Format**: `Authorization: Bearer <jwt_token>`
- **Token Source**: User login or service account credentials
- **Token Validation**: Checked at `get_current_active_user` dependency

### User Roles

Schedules can be generated/managed by users with following role-based permissions:
- Admin
- Coordinator
- Program Director (PD)
- Associate Program Director (APD)

### Rate Limiting

- **Limit**: 10 schedule generation requests per minute per user
- **Headers**: Standard rate limiting response headers returned
- **Exceeded**: HTTP 429 Too Many Requests

---

## Request/Response Schemas

### ScheduleRequest Schema

```json
{
  "start_date": "2024-07-01",
  "end_date": "2025-06-30",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "algorithm": "hybrid",
  "timeout_seconds": 120.0
}
```

**Field Definitions:**

| Field | Type | Required | Default | Min/Max | Description |
|-------|------|----------|---------|---------|-------------|
| `start_date` | date | Yes | - | - | Schedule start (YYYY-MM-DD) |
| `end_date` | date | Yes | - | - | Schedule end (YYYY-MM-DD) |
| `pgy_levels` | array[int] | No | - | - | Filter residents by PGY (1, 2, or 3) |
| `rotation_template_ids` | array[UUID] | No | - | - | Specific rotation templates to use |
| `algorithm` | string | No | "greedy" | - | Algorithm: "greedy", "cp_sat", "pulp", "hybrid" |
| `timeout_seconds` | float | No | 60.0 | 5.0-300.0 | Max solver runtime in seconds |

**Validation Rules:**
- Both dates must be valid academic year dates
- `start_date` must be <= `end_date`
- `timeout_seconds` must be between 5 and 300

---

### ScheduleResponse Schema

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

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | "success", "partial", or "failed" |
| `message` | string | Human-readable result message |
| `total_blocks_assigned` | int | Blocks with assignments |
| `total_blocks` | int | Total blocks in range |
| `validation` | ValidationResult | ACGME validation results |
| `run_id` | UUID | Schedule run identifier for tracking |
| `solver_stats` | SolverStatistics | Solver algorithm statistics |
| `nf_pc_audit` | NFPCAudit | Night Float to Post-Call audit results |
| `acgme_override_count` | int | Acknowledged ACGME overrides |

---

### ValidationResult Schema

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

**Violation Types:**

| Type | Severity | Description |
|------|----------|-------------|
| `80_HOUR` | CRITICAL | Exceeds 80 hours/week rolling average |
| `1_IN_7` | HIGH | Lacks proper time off in 7-day period |
| `SUPERVISION_RATIO` | HIGH | Supervision ratios violated |
| `COVERAGE_GAP` | MEDIUM | Block lacks required coverage |
| `CONFLICT` | LOW | Potential scheduling conflict |

---

### EmergencyRequest/Response Schema

**Request:**
```json
{
  "person_id": "cc0e8400-e29b-41d4-a716-446655440003",
  "start_date": "2025-01-15",
  "end_date": "2025-02-15",
  "reason": "Military deployment",
  "is_deployment": true
}
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

### SwapFinderRequest Schema

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

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `target_faculty` | string | Yes | Faculty looking to offload |
| `target_week` | date | Yes | Monday of week to offload |
| `faculty_targets` | array | No | Target week allocations for each faculty |
| `external_conflicts` | array | No | Known conflicts (leave, TDY, conferences) |
| `include_absence_conflicts` | bool | No | Use database absence records (default: true) |
| `schedule_release_days` | int | No | Days ahead schedules released (default: 90) |

---

### SwapCandidateJsonRequest Schema

```json
{
  "person_id": "dd0e8400-e29b-41d4-a716-446655440004",
  "assignment_id": "ee0e8400-e29b-41d4-a716-446655440005",
  "block_id": "ff0e8400-e29b-41d4-a716-446655440006",
  "max_candidates": 10
}
```

**Field Definitions:**

| Field | Type | Required | Default | Min/Max | Description |
|-------|------|----------|---------|---------|-------------|
| `person_id` | string | Yes | - | - | Person requesting swap |
| `assignment_id` | string | No | - | - | Specific assignment (optional) |
| `block_id` | string | No | - | - | Specific block (optional) |
| `max_candidates` | int | No | 10 | 1-50 | Max candidates to return |

---

## Generation Parameters & Options

### Algorithm Selection

The `algorithm` parameter determines the solver approach:

| Algorithm | Speed | Optimality | Best For | Notes |
|-----------|-------|------------|----------|-------|
| **greedy** | Fast (seconds) | Good | Prototyping, initial solutions | Heuristic-based, fast even for large problems |
| **cp_sat** | Slow (minutes) | Optimal | Small ranges (1-2 weeks), high-quality required | Google OR-Tools constraint programming |
| **pulp** | Medium (10-30s) | Near-optimal | Large problems, production | Linear programming, scales well |
| **hybrid** | Medium (10-30s) | Best | Most production use | Combines CP-SAT + PuLP for best results |

### Date Range Considerations

**Recommended Date Ranges:**

| Range | Algorithm | Timeout |
|-------|-----------|---------|
| Single day | any | 5-10s |
| 1 week | cp_sat or hybrid | 30-60s |
| 2-4 weeks | hybrid or pulp | 60-120s |
| 1 month+ | pulp or hybrid | 120-300s |
| Full year | pulp | 300s |

**Key Rules:**
- Dates must be within academic year (typically July 1 - June 30)
- Both start and end dates must be valid
- Longer ranges require more solver time
- Set `timeout_seconds` based on your time constraints

### PGY Level Filtering

The `pgy_levels` parameter restricts which residents appear in the schedule:

```json
{
  "pgy_levels": [1, 2, 3]  // Include all PGY levels
  "pgy_levels": [1]        // PGY-1 residents only
  "pgy_levels": [2, 3]     // PGY-2 and PGY-3 only
  "pgy_levels": null       // No filtering (all residents)
}
```

### Rotation Template Selection

The `rotation_template_ids` parameter restricts which rotations are scheduled:

```json
{
  "rotation_template_ids": ["uuid1", "uuid2", "uuid3"]  // Specific templates only
  "rotation_template_ids": null                         // All templates
}
```

---

## Response Formats

### Schedule Response Status Values

```
"status": "success"   // Fully generated, no ACGME violations
"status": "partial"   // Some assignments created, violations present
"status": "failed"    // Generation failed, no assignments created
```

### HTTP Status Code Semantics

**200 OK (Success)**
- Full schedule generated with no ACGME violations
- All assignments created successfully
- Response contains complete validation results

**207 Multi-Status (Partial Success)**
- Schedule partially generated
- Some assignments created but violations present
- Indicates degraded but acceptable state
- Client should review violations and take corrective action

**400 Bad Request**
- Invalid date format
- Malformed request body
- Invalid parameter values

**401 Unauthorized**
- Missing JWT token
- Expired JWT token
- Invalid JWT token

**409 Conflict**
- Another generation already in progress for overlapping dates
- Idempotency key conflict (same key, different body)
- Idempotency request still pending

**422 Unprocessable Entity**
- Validation failed (date range, parameters)
- Schedule generation failed (insufficient residents, infeasible constraints)
- File validation failed (unsupported format)
- Parse error (malformed Excel)

**500 Internal Server Error**
- Database error
- Solver error
- Unexpected exception

### Response Header Details

**Standard Headers:**

```
Content-Type: application/json
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 1704038401
```

**Idempotency Headers:**

```
X-Idempotency-Replayed: true     // Response cached (if applicable)
X-Idempotency-Key: <key>          // Echo of request idempotency key
```

---

## Integration Guide

### Python Client Example

```python
import requests
from datetime import date

# Authentication
token = "your_jwt_token"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Generate schedule
payload = {
    "start_date": "2024-07-01",
    "end_date": "2024-07-31",
    "pgy_levels": [1, 2, 3],
    "algorithm": "hybrid",
    "timeout_seconds": 120
}

response = requests.post(
    "http://localhost:8000/api/v1/schedule/generate",
    headers=headers,
    json=payload
)

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Assignments: {result['total_blocks_assigned']}/{result['total_blocks']}")
    print(f"Violations: {result['validation']['total_violations']}")
elif response.status_code == 207:
    result = response.json()
    print(f"Partial success: {result['message']}")
    print(f"Violations: {result['validation']['violations']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### JavaScript/TypeScript Example

```typescript
interface ScheduleRequest {
  start_date: string;
  end_date: string;
  pgy_levels?: number[];
  rotation_template_ids?: string[];
  algorithm?: "greedy" | "cp_sat" | "pulp" | "hybrid";
  timeout_seconds?: number;
}

async function generateSchedule(request: ScheduleRequest, token: string) {
  const response = await fetch('/api/v1/schedule/generate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Idempotency-Key': `schedule-${Date.now()}`
    },
    body: JSON.stringify(request)
  });

  if (response.status === 200) {
    const result = await response.json();
    console.log(`Status: ${result.status}`);
    console.log(`Coverage: ${result.total_blocks_assigned}/${result.total_blocks}`);
    return result;
  } else if (response.status === 207) {
    const result = await response.json();
    console.log(`Partial: ${result.message}`);
    console.warn('Violations:', result.validation.violations);
    return result;
  } else {
    throw new Error(`Schedule generation failed: ${response.status}`);
  }
}
```

### cURL Examples

**Basic Schedule Generation:**
```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-07-01",
    "end_date": "2024-07-31",
    "algorithm": "hybrid",
    "timeout_seconds": 120
  }'
```

**With Idempotency:**
```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: schedule-gen-2025-01-15-001" \
  -d '{
    "start_date": "2024-07-01",
    "end_date": "2024-07-31",
    "pgy_levels": [1, 2, 3],
    "algorithm": "hybrid"
  }'
```

**Validate Schedule:**
```bash
curl http://localhost:8000/api/v1/schedule/validate \
  -G \
  -d "start_date=2024-07-01" \
  -d "end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Parse Block Schedule:**
```bash
curl -X POST http://localhost:8000/api/v1/schedule/import/block \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@block_schedule.xlsx" \
  -F "block_number=10" \
  -F "known_people=[\"PGY1-01\", \"PGY2-03\"]"
```

---

## Error Handling

### Common Error Responses

**400 Bad Request - Invalid Date Format**
```json
{
  "detail": "Invalid date format. Use YYYY-MM-DD"
}
```

**400 Bad Request - Invalid Date Range**
```json
{
  "detail": "start_date (2024-07-31) must be before or equal to end_date (2024-07-01)"
}
```

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**409 Conflict - Generation In Progress**
```json
{
  "detail": "Schedule generation already in progress for overlapping date range. Please wait for the current run to complete."
}
```

**409 Conflict - Idempotency Pending**
```json
{
  "detail": "A request with this idempotency key is currently being processed. Please wait for it to complete."
}
```

**422 Unprocessable Entity - Idempotency Conflict**
```json
{
  "detail": "Idempotency key was already used with different request parameters. Use a new key for different requests."
}
```

**422 Unprocessable Entity - Generation Failure**
```json
{
  "detail": "Schedule generation failed: insufficient residents for date range"
}
```

**422 Unprocessable Entity - Validation Failure**
```json
{
  "detail": "File validation failed"
}
```

**500 Internal Server Error**
```json
{
  "detail": "An error occurred generating the schedule"
}
```

### Error Recovery Strategies

**409 Conflict (Generation In Progress):**
1. Wait 5-10 seconds
2. Retry with same idempotency key
3. Or use new key with same parameters
4. Or use endpoint to cancel in-progress generation

**422 Unprocessable Entity (Idempotency Conflict):**
1. Verify request parameters are identical
2. If parameters differ, use new idempotency key
3. If parameters same, retry (may be race condition)

**422 Unprocessable Entity (Generation Failure):**
1. Check error message for specific cause
2. Adjust parameters (algorithm, timeout, date range)
3. Verify residents exist for PGY levels specified
4. Check database connectivity

---

## Advanced Features

### Idempotency Implementation

The `/generate` endpoint implements RFC 7231 idempotency semantics:

```
POST /api/v1/schedule/generate
Idempotency-Key: my-unique-key-12345
```

**Caching Behavior:**
1. Same key + same body → Returns cached 200/207 response
2. Same key + different body → Returns 422 error
3. Key already in-flight → Returns 409 error
4. Key with failed request → Returns cached error

**Cache Duration:** Typically 24 hours (implementation dependent)

**Use Cases:**
- Prevent duplicate schedule generations from browser retries
- Network resilience (safe to retry POST)
- Pagination through large result sets

### Night Float to Post-Call Audit

The response includes an `nf_pc_audit` object:

```json
{
  "nf_pc_audit": {
    "compliant": true,
    "total_nf_transitions": 45,
    "violations": [],
    "message": "All Night Float transitions have proper Post-Call coverage"
  }
}
```

**What it checks:**
- Each Night Float assignment followed by appropriate Post-Call coverage
- No gaps in coverage at NF→PC transitions
- Proper time off between shifts

**Violations indicate:**
- Improper scheduling around night shifts
- Missing Post-Call coverage
- Coverage policy breaches

### Solver Statistics

The `solver_stats` object provides algorithm metrics:

```json
{
  "solver_stats": {
    "total_blocks": 730,
    "total_residents": 24,
    "coverage_rate": 98.6,
    "branches": 1500,
    "conflicts": 32
  }
}
```

**Metrics:**
- `total_blocks`: Blocks in date range
- `total_residents`: Residents scheduled
- `coverage_rate`: % of blocks with assignments (0.0-1.0)
- `branches`: Solver branch-and-bound iterations
- `conflicts`: Constraint violations in solution

---

## Implementation Notes

### Architecture Overview

```
Route Handler (schedule.py)
    ↓
Controller/Request Validation (ScheduleRequest schema)
    ↓
Business Logic (SchedulingEngine)
    ↓
Constraint Programming (CP-SAT, PuLP, or Greedy)
    ↓
Result Formatting (ScheduleResponse schema)
    ↓
Response (JSON)
```

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `backend/app/api/routes/schedule.py` | Endpoint handlers | 1,302 |
| `backend/app/schemas/schedule.py` | Request/response schemas | 350 |
| `backend/app/scheduling/engine.py` | Scheduling algorithm | Variable |
| `backend/app/scheduling/validator.py` | ACGME validation | Variable |

### Database Models Used

- `Assignment` - Resident/faculty schedule assignments
- `Block` - 4-hour scheduling blocks (AM/PM)
- `Person` - Residents and faculty
- `RotationTemplate` - Rotation definitions
- `ScheduleRun` - Metadata about generations
- `IdempotencyRequest` - Idempotency tracking

### Async/Concurrency

- **Async Support**: Routes use `async def` with `await`
- **Database Session**: Dependency-injected via `get_db`
- **Concurrency Limits**: Double-submit protection prevents overlapping date range generations
- **Rate Limiting**: 10 requests/minute per user

### Error Handling Strategy

1. **Input Validation**: Pydantic schemas validate all requests
2. **Date Validation**: Academic year dates validated
3. **Authorization**: JWT token required (except public endpoints)
4. **Business Logic**: SchedulingEngine checks feasibility
5. **Database Operations**: Transactions with rollback on error
6. **Response Format**: Consistent JSON error format with HTTP semantics

### Payload Sizes

**Typical Request Sizes:**
- Schedule generation: 200 bytes
- Emergency coverage: 300 bytes
- Swap finder: 500+ bytes (depending on conflicts/targets)
- File uploads: Up to server limits (typically 10-100 MB)

**Typical Response Sizes:**
- Success response: 1-5 KB
- Full year schedule: 50-200 KB
- With violations: 10-50 KB

### Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Generate (1 day) | 2-5s | Greedy, highly optimized |
| Generate (1 week) | 10-30s | CP-SAT or Hybrid |
| Generate (1 month) | 30-120s | PuLP recommended |
| Validate | <1s | Real-time query |
| Parse Excel | 5-10s | Depends on file size |
| Find swaps | 2-5s | Database query |

### Failure Modes & Recovery

**Solver Timeout:**
- Set longer `timeout_seconds`
- Use faster algorithm (greedy)
- Reduce date range
- Reduce number of residents/rotations

**Infeasible Schedule:**
- Check resident availability
- Verify rotation requirements are achievable
- Reduce coverage requirements
- Check for impossible constraints

**Database Issues:**
- Check database connectivity
- Verify migrations are applied
- Check disk space
- Check transaction deadlocks in logs

---

## Summary

The Schedule API provides a comprehensive, production-ready system for medical residency scheduling. Key capabilities include:

- Multiple constraint-solving algorithms for various use cases
- Strict ACGME compliance validation
- Robust error handling with meaningful feedback
- Idempotency for safe retries
- Support for emergency coverage scenarios
- Flexible import/analysis tools
- Advanced swap matching for faculty satisfaction

All endpoints follow REST conventions, require proper authentication, and return consistent JSON responses with appropriate HTTP status codes.

For integration support, consult:
- Existing API documentation in `/docs/api/`
- Code examples in respective language sections above
- ACGME compliance rules in `/docs/architecture/`
- Scheduling algorithm details in solver documentation

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Maintainer:** Medical Residency Scheduler Project
