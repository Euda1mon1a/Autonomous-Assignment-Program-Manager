# Swaps API Reference

**Endpoint Prefix:** `/api/swaps`

## Overview

The Swaps API manages faculty shift exchanges and FMIT rotation swaps. This system allows faculty to request schedule swaps while maintaining ACGME compliance and preventing coverage gaps.

### Key Features

- **Swap Request Execution**: Execute 1:1 swaps and absorb operations
- **Swap Validation**: Check compatibility before execution
- **Swap History**: Track all swap operations and reversions
- **Rollback Support**: Revert swaps within 24-hour window
- **Excel Integration**: Find swap candidates from FMIT schedules

### Swap Types

- **1:1 Swap**: Direct exchange between two faculty for specific weeks
- **Absorb**: One faculty takes an assignment, original person is freed up
- **Multi-way Swap**: Coordinated swaps between multiple faculty (future)

---

## Endpoints

### POST /execute

Execute an FMIT rotation swap between two faculty members.

**Request:**
```bash
curl -X POST http://localhost:8000/api/swaps/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440010",
    "source_week": "2025-02-01",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440011",
    "target_week": "2025-03-01",
    "swap_type": "one_to_one",
    "reason": "Conference attendance for source faculty"
  }'
```

**Request Body:**
```json
{
  "source_faculty_id": "string (UUID, required)",
  "source_week": "string (YYYY-MM-DD, required)",
  "target_faculty_id": "string (UUID, required)",
  "target_week": "string (YYYY-MM-DD, required)",
  "swap_type": "one_to_one | absorb (required)",
  "reason": "string (required, reason for swap)"
}
```

**Response (200):**
```json
{
  "success": true,
  "swap_id": "550e8400-e29b-41d4-a716-446655440600",
  "message": "Swap executed successfully",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "back_to_back_conflict": false,
    "external_conflict": false
  }
}
```

**Swap Type Details:**

- **one_to_one**: Source and target swap weeks
  - Source gives source_week to target
  - Target gives target_week to source
  - Both faculty end up with different weeks

- **absorb**: Target takes source's week
  - Source gives source_week to target
  - Target doesn't give anything back
  - Source becomes free for source_week

**Error Responses:**

- **400 Bad Request**: Invalid request
  ```json
  {
    "detail": "Invalid swap request"
  }
  ```

- **404 Not Found**: Faculty or assignment not found
  ```json
  {
    "detail": "Faculty not found"
  }
  ```

- **422 Unprocessable Entity**: Swap validation failed
  ```json
  {
    "success": false,
    "swap_id": null,
    "message": "Swap validation failed",
    "validation": {
      "valid": false,
      "errors": [
        "Target faculty already has assignment for week 2025-03-01"
      ],
      "warnings": [
        "Back-to-back assignments will result (weeks 2025-02-28 and 2025-03-01)"
      ],
      "back_to_back_conflict": true,
      "external_conflict": false
    }
  }
  ```

---

### POST /validate

Validate a proposed swap without executing it.

**Request:**
```bash
curl -X POST http://localhost:8000/api/swaps/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440010",
    "source_week": "2025-02-01",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440011",
    "target_week": "2025-03-01",
    "swap_type": "one_to_one",
    "reason": "Test validation"
  }'
```

**Request Body:**
Same as `/execute` endpoint.

**Response (200):**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "back_to_back_conflict": false,
  "external_conflict": false
}
```

**Response Fields:**

- `valid` (boolean): True if swap can be executed
- `errors` (array): List of errors preventing swap
- `warnings` (array): List of warnings (swap allowed but not ideal)
- `back_to_back_conflict` (boolean): Faculty has assignments on adjacent weeks
- `external_conflict` (boolean): External constraints detected (leave, TDY, etc.)

---

### GET /history

Get swap history with optional filtering.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/swaps/history?faculty_id=550e8400-e29b-41d4-a716-446655440010&status=executed&start_date=2025-01-01&end_date=2025-12-31&page=1&page_size=20' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `faculty_id` (optional, UUID): Filter by source or target faculty
- `status` (optional): Filter by swap status:
  - `pending`: Awaiting approval
  - `executed`: Successfully completed
  - `rolled_back`: Reverted
  - `cancelled`: Cancelled by user
  - `failed`: Failed to execute
- `start_date` (optional, YYYY-MM-DD): Filter swaps from this date
- `end_date` (optional, YYYY-MM-DD): Filter swaps until this date
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20): Items per page

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440600",
      "source_faculty_id": "550e8400-e29b-41d4-a716-446655440010",
      "source_faculty_name": "Dr. Sarah Johnson",
      "source_week": "2025-02-01",
      "target_faculty_id": "550e8400-e29b-41d4-a716-446655440011",
      "target_faculty_name": "Dr. Michael Chen",
      "target_week": "2025-03-01",
      "swap_type": "one_to_one",
      "status": "executed",
      "reason": "Conference attendance for source faculty",
      "requested_at": "2025-12-30T14:30:00Z",
      "executed_at": "2025-12-30T15:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440601",
      "source_faculty_id": "550e8400-e29b-41d4-a716-446655440010",
      "source_faculty_name": "Dr. Sarah Johnson",
      "source_week": "2025-04-01",
      "target_faculty_id": "550e8400-e29b-41d4-a716-446655440012",
      "target_faculty_name": "Dr. Lisa Anderson",
      "target_week": "2025-04-15",
      "swap_type": "absorb",
      "status": "executed",
      "reason": "Medical leave",
      "requested_at": "2025-12-25T10:00:00Z",
      "executed_at": "2025-12-25T10:30:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**Swap Record Fields:**

- `id`: Unique swap identifier
- `source_faculty_id`: Faculty giving up week
- `source_week`: Week being given up (first day of week)
- `target_faculty_id`: Faculty taking the week (or receiving in 1:1)
- `target_week`: Week being received (first day of week)
- `swap_type`: Type of swap operation
- `status`: Current status
- `reason`: Reason provided by requester
- `requested_at`: When swap was requested
- `executed_at`: When swap was actually executed

---

## Excel-Based Swap Finder

### POST /swaps/find (in schedule.py)

Find swap candidates from FMIT rotation schedule Excel file.

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/swaps/find \
  -F "fmit_file=@schedule.xlsx" \
  -F "request_json={\"target_faculty\":\"Dr. Sarah Johnson\",\"target_week\":\"2025-02-01\",\"schedule_release_days\":2,\"include_absence_conflicts\":true}" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Form Parameters:**
- `fmit_file` (required): Excel file with FMIT rotation schedule
- `request_json` (required): JSON string with swap finder request:
  ```json
  {
    "target_faculty": "string (faculty name)",
    "target_week": "string (YYYY-MM-DD)",
    "faculty_targets": [
      {
        "name": "string",
        "target_weeks": ["2025-02-01", "2025-03-01"],
        "role": "string (optional)"
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
    },
    {
      "faculty": "Dr. Lisa Anderson",
      "can_take_week": "2025-02-01",
      "gives_week": "2025-02-15",
      "back_to_back_ok": false,
      "external_conflict": false,
      "flexibility": 0.65,
      "reason": "Back-to-back weeks would result",
      "rank": 2
    }
  ],
  "total_candidates": 2,
  "viable_candidates": 1,
  "alternating_patterns": [
    {
      "faculty": "Dr. James Wilson",
      "cycle_count": 4,
      "fmit_weeks": ["2025-01-01", "2025-03-01", "2025-05-01", "2025-07-01"],
      "recommendation": "Consider consolidating FMIT weeks to reduce family burden"
    }
  ],
  "message": "Found 1 viable swap candidates out of 2 total"
}
```

**Candidate Fields:**

- `faculty`: Name of potential swap partner
- `can_take_week`: Week they can take (source_week in swap)
- `gives_week`: Week they would give back (target_week in swap)
- `back_to_back_ok`: True if no adjacent assignment conflicts
- `external_conflict`: True if leave/TDY/etc. conflicts
- `flexibility`: Score 0.0-1.0 indicating how flexible this candidate is
- `reason`: Human-readable explanation
- `rank`: Ranking among candidates (1 = best match)

---

### POST /swaps/candidates (in schedule.py)

Find swap candidates using JSON input (no file upload).

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/swaps/candidates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440010",
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

**Response (200):**
```json
{
  "success": true,
  "requester_person_id": "550e8400-e29b-41d4-a716-446655440010",
  "requester_name": "Dr. Sarah Johnson",
  "original_assignment_id": "550e8400-e29b-41d4-a716-446655440300",
  "candidates": [
    {
      "candidate_person_id": "550e8400-e29b-41d4-a716-446655440011",
      "candidate_name": "Dr. Michael Chen",
      "candidate_role": "Faculty",
      "assignment_id": "550e8400-e29b-41d4-a716-446655440301",
      "block_date": "2025-02-01",
      "block_session": "AM",
      "match_score": 0.95,
      "rotation_name": "Internal Medicine Clinic",
      "compatibility_factors": {
        "same_type": true,
        "same_block": true
      },
      "mutual_benefit": true,
      "approval_likelihood": "high"
    }
  ],
  "total_candidates": 5,
  "top_candidate_id": "550e8400-e29b-41d4-a716-446655440011",
  "message": "Found 5 swap candidates"
}
```

---

## Swap Validation Rules

The swap validation system checks multiple constraints:

### 1. Availability Conflicts
- **Error**: Target faculty already assigned to target_week
- **Error**: Source faculty not assigned to source_week
- **Fix**: Verify assignments exist before submitting

### 2. Back-to-Back Conflicts
- **Warning**: Faculty would have assignments on adjacent weeks
- **Allows**: Users can accept this (may indicate poor schedule design)
- **Mitigation**: Recommend consolidating assignments

### 3. External Conflicts
- **Error**: Faculty has approved leave during week
- **Error**: Faculty has TDY/deployment scheduled
- **Error**: Faculty has medical emergency
- **Fix**: Wait until absence ends or choose different candidate

### 4. Coverage Requirements
- **Error**: Swap would leave rotation unassigned
- **Error**: Supervision ratios would be violated
- **Fix**: Find coverage before executing swap

---

## Common Workflows

### 1. Faculty Initiates Swap Request

```bash
# Step 1: Find swap candidates
curl -X POST http://localhost:8000/api/schedule/swaps/candidates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "person_id": "faculty_id",
    "assignment_id": "assignment_id",
    "max_candidates": 10
  }' | jq '.top_candidate_id'

# Step 2: Validate the swap before executing
curl -X POST http://localhost:8000/api/swaps/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "source_faculty_id": "faculty_id",
    "source_week": "2025-02-01",
    "target_faculty_id": "candidate_id",
    "target_week": "2025-03-01",
    "swap_type": "one_to_one",
    "reason": "Conference attendance"
  }' | jq '.valid'

# Step 3: Execute if valid
curl -X POST http://localhost:8000/api/swaps/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "source_faculty_id": "faculty_id",
    "source_week": "2025-02-01",
    "target_faculty_id": "candidate_id",
    "target_week": "2025-03-01",
    "swap_type": "one_to_one",
    "reason": "Conference attendance"
  }'
```

### 2. Import Excel Schedule and Find Swaps

```bash
# From FMIT Excel file
curl -X POST http://localhost:8000/api/schedule/swaps/find \
  -F "fmit_file=@fmit_schedule.xlsx" \
  -F 'request_json={"target_faculty":"Dr. Sarah Johnson","target_week":"2025-02-01","schedule_release_days":2,"include_absence_conflicts":true}' \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  | jq '.candidates[0]'
```

### 3. View All Swaps for a Faculty

```bash
curl -X GET 'http://localhost:8000/api/swaps/history?faculty_id=550e8400-e29b-41d4-a716-446655440010' \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.items'
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Authentication required |
| 404 | Not Found | Faculty or assignment not found |
| 422 | Unprocessable Entity | Swap validation failed |
| 500 | Internal Server Error | Server error |

---

## Related Documentation

**Related API Documentation:**
- [Schedule API - Swap Finder](SCHEDULE_API.md#excel-based-swap-finder) - Excel-based swap candidate finding
- [FMIT Health API](FMIT_HEALTH_API.md) - FMIT coverage monitoring and metrics
- [Resilience API](RESILIENCE_API.md) - System health and crisis management
- [People API](PEOPLE_API.md) - Faculty and resident management

**Architecture Decision Records:**
- [ADR-006: Swap System with Auto-Matching](../.claude/dontreadme/synthesis/DECISIONS.md#adr-006-swap-system-with-auto-matching) - Swap system design rationale

**Implementation Code:**
- `backend/app/api/routes/swaps.py` - Swap API routes
- `backend/app/services/swap_executor.py` - Swap execution logic
- `backend/app/services/swap_matcher.py` - Auto-matching algorithm

**User Guides:**
- [Swap Management Guide](../user-guide/swaps.md) - User-facing swap documentation
- [FMIT Rotation Import Guide](../user-guide/fmit-import.md) - Excel import workflow
