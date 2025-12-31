# Swap API Documentation

**Complete reference guide for FMIT swap endpoints, workflows, and state transitions**

## Overview

The Swap API enables FMIT (Flexible Mandatory In-clinic Time) schedule exchanges between faculty members with full ACGME compliance validation. The system supports two swap types:

1. **One-to-One**: Mutual exchange of weeks between two faculty
2. **Absorb**: One faculty takes another's week (no return exchange)

---

## Table of Contents

1. [Endpoints](#endpoints)
2. [Swap State Transitions](#swap-state-transitions)
3. [Swap Workflows](#swap-workflows)
4. [Auto-Matching System](#auto-matching-system)
5. [Validation Rules](#validation-rules)
6. [Error Handling](#error-handling)
7. [Examples](#examples)

---

## Endpoints

### Base URL

```
POST /api/swaps/execute
POST /api/swaps/validate
GET  /api/swaps/history
GET  /api/swaps/{swap_id}
POST /api/swaps/{swap_id}/rollback
```

All endpoints require **Bearer token authentication** via `Authorization` header.

---

## POST /api/swaps/execute

Execute a validated FMIT swap between two faculty members.

### Request

```json
{
  "source_faculty_id": "UUID",
  "source_week": "YYYY-MM-DD",
  "target_faculty_id": "UUID",
  "target_week": "YYYY-MM-DD",
  "swap_type": "one_to_one" | "absorb",
  "reason": "string (optional, max 500 chars)"
}
```

### Parameters

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `source_faculty_id` | UUID | Yes | Faculty member giving up the week |
| `source_week` | Date | Yes | Week to be transferred (YYYY-MM-DD) |
| `target_faculty_id` | UUID | Yes | Faculty member receiving the week |
| `target_week` | Date | Conditional | Required for `one_to_one`, null for `absorb` |
| `swap_type` | Enum | Yes | `one_to_one` or `absorb` |
| `reason` | String | No | Business rationale for the swap (e.g., "vacation conflict", "conference") |

### Response (200 OK)

```json
{
  "success": true,
  "swap_id": "UUID",
  "message": "Swap executed. Week 2025-02-03 transferred.",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "back_to_back_conflict": false,
    "external_conflict": null
  }
}
```

### Failure Response (200 OK - Validation Returned)

When validation fails, the endpoint returns HTTP 200 with `success: false`:

```json
{
  "success": false,
  "swap_id": null,
  "message": "Swap validation failed",
  "validation": {
    "valid": false,
    "errors": [
      "Back-to-back FMIT would violate scheduling policy",
      "Target faculty has deployment conflict week of 2025-02-03"
    ],
    "warnings": [],
    "back_to_back_conflict": true,
    "external_conflict": "deployment"
  }
}
```

### Behavior

1. **Validates** the swap against ACGME rules, back-to-back conflicts, and external constraints
2. **Executes** if validation passes
3. **Creates** SwapRecord with status `EXECUTED`
4. **Updates** schedule assignments for both parties
5. **Updates** call cascade (Fri/Sat FMIT call assignments)
6. **Returns** validation details regardless of outcome

### Errors

| Code | Status | Reason |
|------|--------|--------|
| 401 | Unauthorized | Missing or invalid authentication token |
| 400 | Bad Request | Invalid request format (malformed JSON, missing required fields) |

---

## POST /api/swaps/validate

Validate a proposed swap without executing it. Use this to preview swap impacts.

### Request

```json
{
  "source_faculty_id": "UUID",
  "source_week": "YYYY-MM-DD",
  "target_faculty_id": "UUID",
  "target_week": "YYYY-MM-DD",
  "swap_type": "one_to_one" | "absorb",
  "reason": "string (optional)"
}
```

**Request format is identical to `/execute`**

### Response (200 OK)

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Week 2025-02-03 is within 2 weeks (imminent swap)"
  ],
  "back_to_back_conflict": false,
  "external_conflict": null
}
```

### Validation Failure Response

```json
{
  "valid": false,
  "errors": [
    "SOURCE_NOT_FOUND: Source faculty not found",
    "PAST_DATE: Cannot swap past week 2024-12-15"
  ],
  "warnings": [],
  "back_to_back_conflict": false,
  "external_conflict": null
}
```

### Validation Rules Checked

The validator checks for:

1. **Faculty Validity**: Both source and target faculty exist
2. **Date Range**: Dates within academic year (not in past)
3. **Back-to-Back Conflicts**: Taking the week wouldn't create consecutive FMIT duty
4. **External Conflicts**: Target faculty has no blocking absences (deployment, TDY, leave)
5. **Imminent Warnings**: Week within 14 days generates warning
6. **Swap Type Consistency**: `one_to_one` requires `target_week`, `absorb` requires null

### Errors

| Code | Status | Reason |
|------|--------|--------|
| 401 | Unauthorized | Missing or invalid authentication token |
| 400 | Bad Request | Invalid request format |

---

## GET /api/swaps/history

Retrieve swap history with filtering and pagination.

### Query Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `faculty_id` | UUID | None | Filter by faculty (source OR target) |
| `status` | String | None | Filter by swap status (see [Statuses](#statuses)) |
| `start_date` | Date | None | Filter swaps with source_week >= start_date |
| `end_date` | Date | None | Filter swaps with source_week <= end_date |
| `page` | Integer | 1 | Page number (1-indexed) |
| `page_size` | Integer | 20 | Items per page (1-100) |

### Example Request

```bash
GET /api/swaps/history?faculty_id=550e8400-e29b-41d4-a716-446655440000&status=executed&start_date=2025-01-01&page=1&page_size=20
```

### Response (200 OK)

```json
{
  "items": [
    {
      "id": "UUID",
      "source_faculty_id": "UUID",
      "source_faculty_name": "Dr. Smith",
      "source_week": "2025-02-03",
      "target_faculty_id": "UUID",
      "target_faculty_name": "Dr. Jones",
      "target_week": "2025-02-10",
      "swap_type": "one_to_one",
      "status": "executed",
      "reason": "Vacation conflict",
      "requested_at": "2025-01-15T10:30:00Z",
      "executed_at": "2025-01-15T10:35:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### Pagination

- **total**: Total number of records matching filters
- **pages**: Total number of pages
- **page**: Current page (1-indexed)
- **page_size**: Records per page

To get page 2:
```bash
GET /api/swaps/history?page=2&page_size=20
```

### Errors

| Code | Status | Reason |
|------|--------|--------|
| 401 | Unauthorized | Missing or invalid authentication token |

---

## GET /api/swaps/{swap_id}

Retrieve a specific swap record with full details.

### Path Parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `swap_id` | UUID | Swap record ID |

### Example Request

```bash
GET /api/swaps/550e8400-e29b-41d4-a716-446655440000
```

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_faculty_id": "UUID",
  "source_faculty_name": "Dr. Smith",
  "source_week": "2025-02-03",
  "target_faculty_id": "UUID",
  "target_faculty_name": "Dr. Jones",
  "target_week": "2025-02-10",
  "swap_type": "one_to_one",
  "status": "executed",
  "reason": "Vacation conflict",
  "requested_at": "2025-01-15T10:30:00Z",
  "executed_at": "2025-01-15T10:35:00Z"
}
```

### Errors

| Code | Status | Reason |
|------|--------|--------|
| 404 | Not Found | Swap with given ID does not exist |
| 401 | Unauthorized | Missing or invalid authentication token |

---

## POST /api/swaps/{swap_id}/rollback

Rollback an executed swap within the 24-hour window.

### Path Parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `swap_id` | UUID | Swap record ID |

### Request

```json
{
  "reason": "string (required, 10-500 chars)"
}
```

### Request Parameters

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `reason` | String | Yes | Why the swap is being rolled back (min 10, max 500 characters) |

### Response (200 OK)

```json
{
  "message": "Swap rolled back successfully",
  "success": true
}
```

### Constraints

- **24-hour window**: Only swaps executed within the last 24 hours can be rolled back
- **Status check**: Cannot rollback already-rolled-back or non-executed swaps
- **Schedule updates**: All assignment and call cascade changes are reversed

### Error Cases

| Condition | Response |
|-----------|----------|
| Swap not found | 404 Not Found |
| Outside 24-hour window | 400 Bad Request: "Swap cannot be rolled back (outside rollback window)" |
| Already rolled back | 400 Bad Request: "Swap cannot be rolled back (already rolled back)" |
| Reason too short | 400 Bad Request: "ensure this value has at least 10 characters" |
| Unauthorized | 401 Unauthorized |

---

## Swap State Transitions

### State Machine

```
┌─────────┐
│ PENDING │  (Not used in current implementation - swaps execute immediately)
└────┬────┘
     │
     ▼
┌──────────┐
│ EXECUTED │  ◄─────────────────┐
└────┬─────┘                   │
     │                         │
     ├─ (within 24h) ────────────┤ ROLLBACK
     │                         │
     ▼                         │
┌──────────────┐               │
│ ROLLED_BACK  │ ──────────────┘
└──────────────┘

Also possible:
┌──────────┐
│ APPROVED │  (Unused in current implementation)
└──────────┘

┌──────────┐
│ REJECTED │  (Unused in current implementation)
└──────────┘

┌────────────┐
│ CANCELLED  │  (Unused in current implementation)
└────────────┘
```

### Status Definitions

| Status | Description | Can Transition To | Notes |
|--------|-------------|-------------------|-------|
| `PENDING` | Awaiting approval | EXECUTED, REJECTED, CANCELLED | Not currently used; swaps execute immediately |
| `APPROVED` | Approved but not executed | EXECUTED, CANCELLED | Not currently used |
| `EXECUTED` | Swap completed, assignments updated | ROLLED_BACK | Terminal state (except rollback) |
| `REJECTED` | Swap request was declined | None | Terminal state; unused currently |
| `CANCELLED` | Swap was withdrawn | None | Terminal state; unused currently |
| `ROLLED_BACK` | Swap was reversed | None | Terminal state; can transition back to EXECUTED if re-executed |

### Current Implementation

In the current implementation:

1. **No approval workflow**: Swaps execute immediately upon validation success
2. **Direct execution**: POST /api/swaps/execute validates, then immediately creates EXECUTED record
3. **Rollback only**: The only state transition after EXECUTED is to ROLLED_BACK (within 24 hours)
4. **No state re-use**: PENDING, APPROVED, REJECTED, CANCELLED are defined but not used

### Historical Record

All state transitions are recorded:
- `requested_at`: When swap was first requested
- `executed_at`: When swap was executed (same as requested_at currently)
- `rolled_back_at`: When swap was rolled back (if applicable)
- `approved_at`, `approved_by_id`: Reserved for future approval workflow
- `executed_by_id`: User who executed the swap
- `rolled_back_by_id`: User who rolled back the swap

---

## Swap Workflows

### Workflow 1: Simple One-to-One Swap

Two faculty members exchange FMIT weeks.

#### Prerequisites

- Source faculty has FMIT assignment week of 2025-02-03
- Target faculty has FMIT assignment week of 2025-02-10
- No back-to-back conflicts
- No external conflicts (deployments, leave, etc.)
- Both dates are in future and within academic year

#### Flow

```
1. Source (Dr. Smith) initiates:
   POST /api/swaps/execute
   {
     "source_faculty_id": "smith-uuid",
     "source_week": "2025-02-03",
     "target_faculty_id": "jones-uuid",
     "target_week": "2025-02-10",
     "swap_type": "one_to_one",
     "reason": "Conference attendance"
   }

2. System validates:
   - Faculty exists
   - Dates in range and in future
   - No back-to-back conflicts for Jones
   - Jones has no blocking absences week of 2025-02-10
   - Smith has no blocking absences week of 2025-02-03

3. System executes (if valid):
   - Creates SwapRecord (EXECUTED)
   - Updates assignments: Smith → 2025-02-10, Jones → 2025-02-03
   - Updates call cascade (Fri/Sat FMIT calls)
   - Returns success with swap_id

4. Smith can rollback within 24 hours:
   POST /api/swaps/{swap_id}/rollback
   {
     "reason": "Conference cancelled, back to original schedule"
   }
```

#### Expected Validation Result

```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "back_to_back_conflict": false,
  "external_conflict": null
}
```

---

### Workflow 2: Absorb Swap (Give Away Week)

Faculty member absorbs another's week (no return week expected).

#### Prerequisites

- Source faculty has FMIT assignment week of 2025-02-03
- Target faculty is available week of 2025-02-03 (no blocking absence)
- No back-to-back conflicts for target
- Target week is null (absorb type)

#### Flow

```
1. Source initiates:
   POST /api/swaps/execute
   {
     "source_faculty_id": "smith-uuid",
     "source_week": "2025-02-03",
     "target_faculty_id": "jones-uuid",
     "target_week": null,
     "swap_type": "absorb",
     "reason": "Emergency personal matter"
   }

2. System validates:
   - Faculty exists
   - Dates in range and in future
   - No back-to-back conflicts for Jones taking 2025-02-03
   - Jones has no blocking absences week of 2025-02-03
   - target_week is null (required for absorb)

3. System executes:
   - Creates SwapRecord (EXECUTED, target_week = null)
   - Updates assignments: Smith removed, Jones added
   - Updates call cascade
   - Returns success

4. Rollback within 24 hours reverses to original state
```

---

### Workflow 3: Validation Check Before Committing

Faculty preview swap impact before requesting.

#### Flow

```
1. Faculty wants to check if swap is possible:
   POST /api/swaps/validate
   {
     "source_faculty_id": "smith-uuid",
     "source_week": "2025-02-03",
     "target_faculty_id": "jones-uuid",
     "target_week": "2025-02-10",
     "swap_type": "one_to_one",
     "reason": "Vacation conflict"
   }

2. System returns validation result (NO DATABASE CHANGES):
   {
     "valid": true,
     "errors": [],
     "warnings": [
       "Week 2025-02-03 is within 2 weeks (imminent swap)"
     ],
     "back_to_back_conflict": false,
     "external_conflict": null
   }

3. Faculty reviews warnings and decides:
   - If valid=true: Can proceed with execute
   - If valid=false: Address errors or try different swap
```

---

### Workflow 4: Retrieving Swap History

Coordinators query swap patterns and audit trail.

#### Example: All Swaps by Faculty

```bash
GET /api/swaps/history?faculty_id=smith-uuid&page=1&page_size=20
```

Response shows all swaps where Smith is source OR target:

```json
{
  "items": [
    {
      "id": "...",
      "source_faculty_name": "Dr. Smith",
      "target_faculty_name": "Dr. Jones",
      "source_week": "2025-02-03",
      "target_week": "2025-02-10",
      "swap_type": "one_to_one",
      "status": "executed",
      "requested_at": "2025-01-15T10:30:00Z",
      "executed_at": "2025-01-15T10:30:00Z"
    },
    {
      "id": "...",
      "source_faculty_name": "Dr. Smith",
      "target_faculty_name": "Dr. Chen",
      "source_week": "2025-02-17",
      "target_week": null,
      "swap_type": "absorb",
      "status": "rolled_back",
      "requested_at": "2025-01-16T14:00:00Z",
      "executed_at": "2025-01-16T14:00:00Z",
      "rolled_back_at": "2025-01-16T16:30:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

#### Example: All Swaps This Month

```bash
GET /api/swaps/history?start_date=2025-01-01&end_date=2025-01-31&page_size=50
```

---

## Auto-Matching System

The swap system includes an intelligent auto-matching service to suggest compatible swaps without requiring manual negotiation.

### Overview

The `SwapAutoMatcher` service finds compatible swap matches using a **5-factor scoring algorithm**:

1. **Date Proximity** (Weight: 20%) - Closer dates score higher
2. **Preference Alignment** (Weight: 35%) - Match faculty preferences
3. **Workload Balance** (Weight: 15%) - Help both balance workload
4. **Past Swap History** (Weight: 15%) - Reward successful pairs, penalize rejections
5. **Faculty Availability** (Weight: 15%) - Prefer available weeks

### Scoring Breakdown

Each match receives a detailed scoring breakdown:

```json
{
  "date_proximity_score": 0.95,
  "preference_alignment_score": 0.80,
  "workload_balance_score": 0.70,
  "history_score": 0.85,
  "availability_score": 0.90,
  "blocking_penalty": 1.0,
  "total_score": 0.84
}
```

**Scoring Rules:**
- Each factor: 0.0 (worst) to 1.0 (best)
- **Date Proximity**: 1.0 for dates within 2 weeks, 0.0 for dates >60 days apart
- **Preference Alignment**: 1.0 for mutual preference match, 0.0 for blocked weeks
- **Workload Balance**: Higher when swap helps both parties reach target workload
- **History Score**: Bonuses for successful past swaps (+0.3 max), penalties for rejections (-0.6 max)
- **Availability**: 1.0 both available/prefer, 0.5 one prefers, 0.0 blocked
- **Blocking Penalty**: 1.0 no blocked weeks, 0.0 if either week blocked

**Final Score = Σ(factor_score × weight)**

### Match Priority Levels

Matches are prioritized based on compatibility score:

| Priority | Score Range | Meaning |
|----------|-------------|---------|
| **CRITICAL** | ≥ 0.95 | Blocked week, urgent need |
| **HIGH** | 0.80-0.94 | Strong preference alignment |
| **MEDIUM** | 0.50-0.79 | Good compatibility |
| **LOW** | < 0.50 | Acceptable match |

### Match Types

| Type | Description |
|------|-------------|
| **MUTUAL** | Both parties want each other's weeks (ideal match) |
| **ONE_WAY** | One party wants, other is available |
| **ABSORB** | One party takes on a week (no return) |

### API Endpoints (Planned)

While the auto-matching service is implemented, public API endpoints are not yet available but would include:

**Proposed endpoints:**
- `GET /api/swaps/{request_id}/matches` - Find matches for a request
- `GET /api/swaps/{request_id}/matches/optimal` - Get ranked matches
- `POST /api/swaps/auto-match` - Run batch auto-matching
- `GET /api/faculty/{faculty_id}/swap-suggestions` - Proactive suggestions for faculty

### Matching Criteria Customization

When implementing auto-matching endpoints, applications can customize:

```json
{
  "date_proximity_weight": 0.25,
  "preference_alignment_weight": 0.40,
  "workload_balance_weight": 0.15,
  "history_weight": 0.10,
  "availability_weight": 0.10,
  "minimum_score_threshold": 0.5,
  "high_priority_threshold": 0.80,
  "max_date_separation_days": 60,
  "require_mutual_availability": true,
  "exclude_blocked_weeks": true
}
```

---

## Validation Rules

### Core Validation Checks

All swaps are validated against these rules:

#### 1. Faculty Validation

**Rule**: Both source and target faculty must exist and be of type "faculty"

```
ERROR: SOURCE_NOT_FOUND - Source faculty {id} does not exist
ERROR: TARGET_NOT_FOUND - Target faculty {id} does not exist
```

#### 2. Date Range Validation

**Rule**: Dates must be within academic year and not in the past

```
ERROR: PAST_DATE - Cannot swap past week {date}
WARNING: IMMINENT_SWAP - Week {date} is within 2 weeks
```

**Academic Year**: August 1 (previous year) - July 31 (current year)

#### 3. Swap Type Consistency

**Rule**: `one_to_one` requires `target_week`; `absorb` requires `target_week = null`

```
ERROR: target_week required for one-to-one swaps
ERROR: target_week must be null for absorb swaps
```

#### 4. Back-to-Back Conflict

**Rule**: Target faculty cannot have consecutive FMIT duty days

```
ERROR: BACK_TO_BACK - Taking week {date} would create back-to-back FMIT for {name}
```

**Definition of back-to-back**: Two FMIT weeks with ≤ 2 calendar days between them.

#### 5. External Conflicts

**Rule**: Target faculty cannot have blocking absences during the week

```
ERROR: EXTERNAL_CONFLICT - {name} has {absence_type} conflict during week {date}
```

**Blocking absence types**: deployment, TDY (Temporary Duty), extended leave, medical leave, suspended privileges

#### 6. ACGME Compliance (Future Implementation)

Planned validations (not yet fully implemented in current version):

- 80-hour week limit (rolling 4-week average)
- 1-in-7 day off requirement
- Supervision ratios (faculty-to-resident)
- Continuous duty limits

---

## Error Handling

### HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Request successful (even if validation fails) |
| 400 | Bad request (invalid format, malformed JSON, missing required fields) |
| 401 | Unauthorized (missing or invalid authentication) |
| 404 | Swap not found (for GET /swaps/{id} or rollback of non-existent swap) |

### Validation vs. HTTP Errors

**Important distinction:**
- **Validation failures** (swap can't proceed) return **200 OK** with `valid: false`
- **HTTP errors** (malformed request, auth issues) return **4xx status codes**

### Error Response Format

**HTTP 400/401/404:**
```json
{
  "detail": "error message"
}
```

**Validation Failure (HTTP 200):**
```json
{
  "success": false,
  "swap_id": null,
  "message": "Swap validation failed",
  "validation": {
    "valid": false,
    "errors": [
      "Back-to-back FMIT conflict",
      "Target faculty has deployment conflict"
    ],
    "warnings": [],
    "back_to_back_conflict": true,
    "external_conflict": "deployment"
  }
}
```

---

## Examples

### Example 1: Execute One-to-One Swap

```bash
curl -X POST https://api.example.com/api/swaps/execute \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2025-02-03",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "target_week": "2025-02-10",
    "swap_type": "one_to_one",
    "reason": "Conference attendance"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "swap_id": "550e8400-e29b-41d4-a716-446655440002",
  "message": "Swap executed. Week 2025-02-03 transferred.",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "back_to_back_conflict": false,
    "external_conflict": null
  }
}
```

---

### Example 2: Absorb Swap (One-Way)

```bash
curl -X POST https://api.example.com/api/swaps/execute \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2025-02-03",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "swap_type": "absorb",
    "reason": "Personal emergency"
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "swap_id": "550e8400-e29b-41d4-a716-446655440003",
  "message": "Swap executed. Week 2025-02-03 transferred.",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "back_to_back_conflict": false,
    "external_conflict": null
  }
}
```

---

### Example 3: Validation Failure - Back-to-Back Conflict

```bash
curl -X POST https://api.example.com/api/swaps/validate \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2025-02-03",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "target_week": "2025-02-04",
    "swap_type": "one_to_one"
  }'
```

**Response (Failure):**
```json
{
  "valid": false,
  "errors": [
    "BACK_TO_BACK: Taking week 2025-02-03 would create back-to-back FMIT for Dr. Jones"
  ],
  "warnings": [
    "IMMINENT_SWAP: Week 2025-02-03 is within 2 weeks"
  ],
  "back_to_back_conflict": true,
  "external_conflict": null
}
```

---

### Example 4: Query Swap History

```bash
curl -X GET 'https://api.example.com/api/swaps/history?faculty_id=550e8400-e29b-41d4-a716-446655440000&status=executed&page=1&page_size=20' \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
      "source_faculty_name": "Dr. Smith",
      "source_week": "2025-02-03",
      "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
      "target_faculty_name": "Dr. Jones",
      "target_week": "2025-02-10",
      "swap_type": "one_to_one",
      "status": "executed",
      "reason": "Conference attendance",
      "requested_at": "2025-01-15T10:30:00Z",
      "executed_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### Example 5: Rollback Swap

```bash
curl -X POST https://api.example.com/api/swaps/550e8400-e29b-41d4-a716-446655440002/rollback \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Conference cancelled unexpectedly"
  }'
```

**Response (Success):**
```json
{
  "message": "Swap rolled back successfully",
  "success": true
}
```

**Response (Outside Window):**
```json
{
  "detail": "Swap cannot be rolled back (either not found, already rolled back, or outside rollback window)"
}
```

---

### Example 6: Invalid Swap Type Consistency

```bash
curl -X POST https://api.example.com/api/swaps/execute \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2025-02-03",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "swap_type": "one_to_one"
  }'
```

**Response (Validation Error):**
```json
{
  "success": false,
  "swap_id": null,
  "message": "Swap validation failed",
  "validation": {
    "valid": false,
    "errors": [
      "target_week required for one-to-one swaps"
    ],
    "warnings": [],
    "back_to_back_conflict": false,
    "external_conflict": null
  }
}
```

---

## Implementation Notes

### Database Schema

**SwapRecord Table:**
```sql
CREATE TABLE swap_records (
  id UUID PRIMARY KEY,
  source_faculty_id UUID NOT NULL REFERENCES people(id),
  source_week DATE NOT NULL,
  target_faculty_id UUID NOT NULL REFERENCES people(id),
  target_week DATE,
  swap_type ENUM('one_to_one', 'absorb') NOT NULL,
  status ENUM(...) DEFAULT 'executed',
  requested_at TIMESTAMP DEFAULT now(),
  requested_by_id UUID REFERENCES users(id),
  executed_at TIMESTAMP,
  executed_by_id UUID REFERENCES users(id),
  rolled_back_at TIMESTAMP,
  rolled_back_by_id UUID REFERENCES users(id),
  rollback_reason TEXT,
  reason TEXT,
  notes TEXT
);
```

**SwapApproval Table (Not Used Currently):**
```sql
CREATE TABLE swap_approvals (
  id UUID PRIMARY KEY,
  swap_id UUID NOT NULL REFERENCES swap_records(id),
  faculty_id UUID NOT NULL REFERENCES people(id),
  role VARCHAR(20) NOT NULL,
  approved BOOLEAN,
  responded_at TIMESTAMP,
  response_notes TEXT
);
```

### Service Layer

**SwapExecutor** (`backend/app/services/swap_executor.py`):
- Executes validated swaps
- Updates schedule assignments
- Updates call cascade
- Handles rollbacks

**SwapValidationService** (`backend/app/services/swap_validation.py`):
- Validates swap requests
- Checks for conflicts
- Returns detailed error/warning lists

**SwapAutoMatcher** (`backend/app/services/swap_auto_matcher.py`):
- Finds compatible matches
- Scores compatibility
- Ranks matches by priority

---

## Future Enhancements

Planned features not yet implemented:

1. **Approval Workflow**: Add approval step before execution
2. **ACGME Compliance Checks**: Full 80-hour, 1-in-7, supervision ratio validation
3. **Auto-Matching API**: Public endpoints for match suggestions
4. **Multi-Party Swaps**: Support 3+ faculty in single transaction
5. **Swap Marketplace**: UI-driven swap matching without direct negotiation
6. **Notifications**: Email/SMS alerts for swap requests and matches
7. **Audit Trail**: Enhanced logging of all swap operations

---

## See Also

- [User Guide: Swaps](../user-guide/swaps.md)
- [Swap Management Workflows](../guides/swap-management.md)
- [ACGME Compliance](compliance.md)
- [Call Assignment System](call-assignments.md)

