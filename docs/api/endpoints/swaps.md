# Swaps API Endpoints

Complete reference for FMIT swap management and execution.

---

## Overview

The Swaps API provides endpoints for:
- Executing faculty schedule swaps
- Validating proposed swaps before execution
- Viewing swap history
- Rolling back swaps within allowed window

**Base Path**: `/api/v1/swaps`

**Authentication**: All endpoints require JWT authentication.

---

## Execute Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/execute`

Execute an FMIT swap between two faculty members.

### Request Body

```json
{
  "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_week": "2024-07-08",
  "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
  "target_week": "2024-07-15",
  "swap_type": "one_to_one",
  "reason": "Family commitment conflict"
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_faculty_id` | UUID | Yes | Faculty initiating the swap |
| `source_week` | string (date) | Yes | Week to give away (Monday date, YYYY-MM-DD) |
| `target_faculty_id` | UUID | Yes | Faculty accepting the swap |
| `target_week` | string (date) | No | Week to receive (for one-to-one swap) |
| `swap_type` | string | Yes | Type: `one_to_one` or `absorb` |
| `reason` | string | Yes | Reason for the swap |

### Swap Types

| Type | Description |
|------|-------------|
| `one_to_one` | Exchange weeks between two faculty (both give and receive) |
| `absorb` | One faculty gives away week, other faculty absorbs (no exchange) |

### Response

**Success (200 OK)**

```json
{
  "success": true,
  "swap_id": "550e8400-e29b-41d4-a716-446655440002",
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

**Validation Failed (200 OK with success=false)**

```json
{
  "success": false,
  "swap_id": null,
  "message": "Swap validation failed",
  "validation": {
    "valid": false,
    "errors": [
      "Back-to-back weeks detected: FAC-PD would have weeks 2024-07-01 and 2024-07-08"
    ],
    "warnings": [
      "Faculty will have 3 FMIT weeks in 4-week period"
    ],
    "back_to_back_conflict": true,
    "external_conflict": false
  }
}
```

### Validation Rules

The system validates swaps against:

| Rule | Description | Severity |
|------|-------------|----------|
| **Back-to-back weeks** | No faculty should have consecutive FMIT weeks | Error |
| **External conflicts** | Check against leave, TDY, deployments | Error |
| **Target week limits** | Faculty shouldn't exceed target week allocation | Warning |
| **Excessive alternating** | Avoid week-on/week-off patterns | Warning |

### Example Requests

**cURL - One-to-One Swap**

```bash
curl -X POST http://localhost:8000/api/v1/swaps/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2024-07-08",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "target_week": "2024-07-15",
    "swap_type": "one_to_one",
    "reason": "Family commitment"
  }'
```

**cURL - Absorb Swap**

```bash
curl -X POST http://localhost:8000/api/v1/swaps/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2024-07-08",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "swap_type": "absorb",
    "reason": "Medical leave"
  }'
```

**Python**

```python
import requests

swap_data = {
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2024-07-08",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "target_week": "2024-07-15",
    "swap_type": "one_to_one",
    "reason": "Vacation conflict"
}

response = requests.post(
    "http://localhost:8000/api/v1/swaps/execute",
    headers={"Authorization": f"Bearer {token}"},
    json=swap_data
)

result = response.json()
if result['success']:
    print(f"✅ Swap executed: {result['swap_id']}")
else:
    print(f"❌ Swap failed: {result['message']}")
    for error in result['validation']['errors']:
        print(f"  - {error}")
```

---

## Validate Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/validate`

Validate a proposed swap without executing it.

Use this to check if a swap is possible before attempting execution.

### Request Body

```json
{
  "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_week": "2024-07-08",
  "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
  "target_week": "2024-07-15",
  "swap_type": "one_to_one"
}
```

### Response

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Target faculty will have 3 FMIT weeks in 4-week period (above recommended 2)"
  ],
  "back_to_back_conflict": false,
  "external_conflict": false
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/swaps/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_week": "2024-07-08",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
    "target_week": "2024-07-15",
    "swap_type": "one_to_one"
  }'
```

**Python - Validate Before Executing**

```python
import requests

swap_data = {
    "source_faculty_id": source_id,
    "source_week": "2024-07-08",
    "target_faculty_id": target_id,
    "target_week": "2024-07-15",
    "swap_type": "one_to_one"
}

# Validate first
validation = requests.post(
    "http://localhost:8000/api/v1/swaps/validate",
    headers={"Authorization": f"Bearer {token}"},
    json=swap_data
).json()

if validation['valid']:
    print("✅ Validation passed")

    # Show warnings
    if validation['warnings']:
        print("⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")

    # Confirm execution
    confirm = input("Execute swap? (yes/no): ")
    if confirm.lower() == "yes":
        swap_data['reason'] = "Approved after validation"
        response = requests.post(
            "http://localhost:8000/api/v1/swaps/execute",
            headers={"Authorization": f"Bearer {token}"},
            json=swap_data
        )
        print(f"Swap executed: {response.json()['swap_id']}")
else:
    print("❌ Validation failed:")
    for error in validation['errors']:
        print(f"  - {error}")
```

---

## Get Swap History

<span class="endpoint-badge get">GET</span> `/api/v1/swaps/history`

Get swap history with optional filters and pagination.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `faculty_id` | UUID | No | Filter by source or target faculty |
| `status` | string | No | Filter by status: `pending`, `executed`, `rolled_back`, `failed` |
| `start_date` | string (date) | No | Filter swaps with source_week >= start_date |
| `end_date` | string (date) | No | Filter swaps with source_week <= end_date |
| `page` | integer | No | Page number (1-indexed, default: 1) |
| `page_size` | integer | No | Items per page (default: 20) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
      "source_faculty_name": "FAC-PD",
      "source_week": "2024-07-08",
      "target_faculty_id": "550e8400-e29b-41d4-a716-446655440002",
      "target_faculty_name": "FAC-APD",
      "target_week": "2024-07-15",
      "swap_type": "one_to_one",
      "status": "executed",
      "reason": "Family commitment",
      "requested_at": "2024-06-25T10:00:00Z",
      "executed_at": "2024-06-25T10:05:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### Swap Statuses

| Status | Description |
|--------|-------------|
| `pending` | Swap requested but not yet executed |
| `executed` | Swap successfully executed |
| `rolled_back` | Swap was executed then rolled back |
| `failed` | Swap execution failed |

### Example Requests

**All swaps**

```bash
curl "http://localhost:8000/api/v1/swaps/history" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Swaps for specific faculty**

```bash
curl "http://localhost:8000/api/v1/swaps/history?faculty_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Executed swaps in date range**

```bash
curl "http://localhost:8000/api/v1/swaps/history?status=executed&start_date=2024-07-01&end_date=2024-07-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python - Get Faculty Swap History**

```python
import requests

params = {
    "faculty_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "executed",
    "page": 1,
    "page_size": 50
}

response = requests.get(
    "http://localhost:8000/api/v1/swaps/history",
    headers={"Authorization": f"Bearer {token}"},
    params=params
)

history = response.json()
print(f"Total swaps: {history['total']}")
for swap in history['items']:
    print(f"{swap['requested_at']}: {swap['source_faculty_name']} ↔ {swap['target_faculty_name']}")
    print(f"  Weeks: {swap['source_week']} ↔ {swap['target_week']}")
```

---

## Get Swap Details

<span class="endpoint-badge get">GET</span> `/api/v1/swaps/{swap_id}`

Get detailed information about a specific swap.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `swap_id` | UUID | Swap record ID |

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source_faculty_id": "550e8400-e29b-41d4-a716-446655440001",
  "source_faculty_name": "FAC-PD",
  "source_week": "2024-07-08",
  "target_faculty_id": "550e8400-e29b-41d4-a716-446655440002",
  "target_faculty_name": "FAC-APD",
  "target_week": "2024-07-15",
  "swap_type": "one_to_one",
  "status": "executed",
  "reason": "Family commitment",
  "requested_at": "2024-06-25T10:00:00Z",
  "executed_at": "2024-06-25T10:05:00Z"
}
```

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Swap with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/swaps/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Rollback Swap

<span class="endpoint-badge post">POST</span> `/api/v1/swaps/{swap_id}/rollback`

Rollback an executed swap within the allowed window.

**Rollback Window**: Swaps can only be rolled back within **24 hours** of execution.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `swap_id` | UUID | Swap record ID |

### Request Body

```json
{
  "reason": "Faculty changed mind, reverting to original schedule"
}
```

### Response

**Success (200 OK)**

```json
{
  "success": true,
  "message": "Swap rolled back successfully"
}
```

**Error (400 Bad Request)**

```json
{
  "detail": "Swap cannot be rolled back (either not found, already rolled back, or outside rollback window)"
}
```

### Example

```bash
curl -X POST http://localhost:8000/api/v1/swaps/550e8400-e29b-41d4-a716-446655440000/rollback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Faculty requested reversal"
  }'
```

**Python - Check Rollback Eligibility**

```python
import requests
from datetime import datetime, timedelta

# Get swap details
swap = requests.get(
    f"http://localhost:8000/api/v1/swaps/{swap_id}",
    headers={"Authorization": f"Bearer {token}"}
).json()

# Check if within rollback window
executed_at = datetime.fromisoformat(swap['executed_at'].replace('Z', '+00:00'))
hours_since_execution = (datetime.now() - executed_at).total_seconds() / 3600

if hours_since_execution > 24:
    print(f"❌ Cannot rollback: {hours_since_execution:.1f} hours since execution (max: 24)")
elif swap['status'] != 'executed':
    print(f"❌ Cannot rollback: swap status is '{swap['status']}' (must be 'executed')")
else:
    print(f"✅ Rollback eligible ({24 - hours_since_execution:.1f} hours remaining)")

    # Perform rollback
    response = requests.post(
        f"http://localhost:8000/api/v1/swaps/{swap_id}/rollback",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Requested by faculty"}
    )

    if response.status_code == 200:
        print("Swap rolled back successfully")
```

---

## Common Use Cases

### 1. Execute Simple Swap with Validation

```python
import requests

def execute_swap_with_validation(source_id, source_week, target_id, target_week, reason, token):
    """Execute a swap with pre-validation."""
    swap_data = {
        "source_faculty_id": source_id,
        "source_week": source_week,
        "target_faculty_id": target_id,
        "target_week": target_week,
        "swap_type": "one_to_one"
    }

    # Validate first
    validation = requests.post(
        "http://localhost:8000/api/v1/swaps/validate",
        headers={"Authorization": f"Bearer {token}"},
        json=swap_data
    ).json()

    if not validation['valid']:
        print("❌ Validation failed:")
        for error in validation['errors']:
            print(f"  - {error}")
        return None

    # Execute
    swap_data['reason'] = reason
    response = requests.post(
        "http://localhost:8000/api/v1/swaps/execute",
        headers={"Authorization": f"Bearer {token}"},
        json=swap_data
    )

    result = response.json()
    if result['success']:
        print(f"✅ Swap executed: {result['swap_id']}")
        return result['swap_id']
    else:
        print(f"❌ Execution failed: {result['message']}")
        return None

# Usage
swap_id = execute_swap_with_validation(
    source_id="550e8400-e29b-41d4-a716-446655440000",
    source_week="2024-07-08",
    target_id="550e8400-e29b-41d4-a716-446655440001",
    target_week="2024-07-15",
    reason="Family vacation",
    token=token
)
```

### 2. View Faculty Swap History

```python
def get_faculty_swap_count(faculty_id, token):
    """Get total swaps for a faculty member."""
    response = requests.get(
        "http://localhost:8000/api/v1/swaps/history",
        headers={"Authorization": f"Bearer {token}"},
        params={"faculty_id": faculty_id}
    )

    history = response.json()
    return history['total']

# Check swap counts
faculty_ids = {
    "FAC-PD": "550e8400-e29b-41d4-a716-446655440000",
    "FAC-APD": "550e8400-e29b-41d4-a716-446655440001"
}

for name, fac_id in faculty_ids.items():
    count = get_faculty_swap_count(fac_id, token)
    print(f"{name}: {count} total swaps")
```

### 3. Absorb Week (Emergency Coverage)

```python
# One faculty gives away week, another absorbs
absorb_data = {
    "source_faculty_id": "550e8400-e29b-41d4-a716-446655440000",  # Person with emergency
    "source_week": "2024-07-08",
    "target_faculty_id": "550e8400-e29b-41d4-a716-446655440001",  # Covering person
    "swap_type": "absorb",  # No week exchange
    "reason": "Medical emergency - no exchange required"
}

response = requests.post(
    "http://localhost:8000/api/v1/swaps/execute",
    headers={"Authorization": f"Bearer {token}"},
    json=absorb_data
)
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `SWAP_NOT_FOUND` | 404 | Swap record does not exist |
| `FACULTY_NOT_FOUND` | 404 | Faculty member does not exist |
| `VALIDATION_FAILED` | 200 (success=false) | Swap validation failed (errors in validation object) |
| `BACK_TO_BACK_CONFLICT` | 200 (success=false) | Swap would create consecutive weeks |
| `EXTERNAL_CONFLICT` | 200 (success=false) | Swap conflicts with leave/TDY |
| `ROLLBACK_WINDOW_EXPIRED` | 400 | Swap cannot be rolled back (>24 hours) |
| `ALREADY_ROLLED_BACK` | 400 | Swap has already been rolled back |
| `INVALID_SWAP_STATUS` | 400 | Swap status doesn't allow rollback |

---

## See Also

- [Schedule API](schedules.md) - Find swap candidates
- [Persons API](persons.md) - Faculty management
- [Absences API](../absences.md) - External conflict detection
- [Authentication](../authentication.md) - Token management
