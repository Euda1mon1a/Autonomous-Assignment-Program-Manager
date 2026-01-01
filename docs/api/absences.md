# Absence API Endpoints

Complete reference for managing faculty and resident absences, including vacation, leave, deployments, and TDY assignments.

---

## Overview

The Absences API provides endpoints for:
- Creating and managing absence records
- Tracking military deployments and TDY
- Conflict detection with swap requests
- Leave approval workflows
- Absence reporting and analytics

**Base Path**: `/api/v1/absences`

**Authentication**: All endpoints require JWT authentication.

---

## List Absences

<span class="endpoint-badge get">GET</span> `/api/v1/absences`

List all absences with optional filters and pagination.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | UUID | No | Filter by specific person |
| `start_date` | string (date) | No | Filter from this date (YYYY-MM-DD) |
| `end_date` | string (date) | No | Filter until this date (YYYY-MM-DD) |
| `type` | string | No | Filter by type: `vacation`, `sick`, `deployment`, `tdy`, `conference`, `other` |
| `status` | string | No | Filter by status: `pending`, `approved`, `denied`, `cancelled` |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "person_id": "550e8400-e29b-41d4-a716-446655440001",
      "person_name": "FAC-PD",
      "type": "vacation",
      "start_date": "2025-01-15",
      "end_date": "2025-01-20",
      "status": "approved",
      "notes": "Annual vacation - Hawaii",
      "approved_by": "admin@example.com",
      "approved_at": "2024-12-01T10:00:00Z",
      "created_at": "2024-11-25T14:30:00Z",
      "updated_at": "2024-12-01T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "person_id": "550e8400-e29b-41d4-a716-446655440003",
      "person_name": "PGY2-03",
      "type": "deployment",
      "start_date": "2025-02-01",
      "end_date": "2025-05-01",
      "status": "approved",
      "notes": "Military deployment - 90 days",
      "approved_by": "admin@example.com",
      "approved_at": "2024-12-15T09:00:00Z",
      "created_at": "2024-12-10T16:00:00Z",
      "updated_at": "2024-12-15T09:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### Absence Types

| Type | Description | Typical Duration | Approval Required |
|------|-------------|------------------|-------------------|
| `vacation` | Planned vacation/leave | 3-14 days | Yes |
| `sick` | Sick leave | 1-7 days | Auto-approved for < 3 days |
| `deployment` | Military deployment | 30-180 days | Yes (command) |
| `tdy` | Temporary duty assignment | 7-30 days | Yes |
| `conference` | Professional conference | 2-5 days | Yes |
| `other` | Other absences | Varies | Yes |

### Absence Status

| Status | Description |
|--------|-------------|
| `pending` | Awaiting approval |
| `approved` | Approved by supervisor/admin |
| `denied` | Request denied |
| `cancelled` | Cancelled by requester |

### Example Requests

**All absences**

```bash
curl "http://localhost:8000/api/v1/absences" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by person**

```bash
curl "http://localhost:8000/api/v1/absences?person_id=550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by date range**

```bash
curl "http://localhost:8000/api/v1/absences?start_date=2025-01-01&end_date=2025-03-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Filter by type**

```bash
curl "http://localhost:8000/api/v1/absences?type=deployment&status=approved" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python Example**

```python
import requests

params = {
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "status": "approved"
}

response = requests.get(
    "http://localhost:8000/api/v1/absences",
    headers={"Authorization": f"Bearer {token}"},
    params=params
)

absences = response.json()
print(f"Total absences: {absences['total']}")
for absence in absences['items']:
    print(f"{absence['person_name']}: {absence['type']} ({absence['start_date']} to {absence['end_date']})")
```

---

## Get Absence

<span class="endpoint-badge get">GET</span> `/api/v1/absences/{absence_id}`

Get a specific absence by ID.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `absence_id` | UUID | Absence ID |

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "FAC-PD",
    "type": "faculty",
    "email": "pd@example.com"
  },
  "type": "vacation",
  "start_date": "2025-01-15",
  "end_date": "2025-01-20",
  "status": "approved",
  "notes": "Annual vacation - Hawaii",
  "approved_by": "admin@example.com",
  "approved_at": "2024-12-01T10:00:00Z",
  "created_at": "2024-11-25T14:30:00Z",
  "updated_at": "2024-12-01T10:00:00Z",
  "conflicts": [
    {
      "type": "fmit_assignment",
      "date": "2025-01-18",
      "description": "FMIT week assignment during absence"
    }
  ]
}
```

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Absence with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/absences/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Create Absence

<span class="endpoint-badge post">POST</span> `/api/v1/absences`

Create a new absence record.

**Authorization**: Any authenticated user can create absences for themselves. Coordinators and admins can create for anyone.

### Request Body

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "type": "vacation",
  "start_date": "2025-01-15",
  "end_date": "2025-01-20",
  "notes": "Annual vacation - Hawaii"
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person taking absence |
| `type` | string | Yes | Absence type (see types above) |
| `start_date` | string (date) | Yes | Start date (YYYY-MM-DD) |
| `end_date` | string (date) | Yes | End date (YYYY-MM-DD) |
| `notes` | string | No | Additional notes/reason |

### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_name": "FAC-PD",
  "type": "vacation",
  "start_date": "2025-01-15",
  "end_date": "2025-01-20",
  "status": "pending",
  "notes": "Annual vacation - Hawaii",
  "approved_by": null,
  "approved_at": null,
  "created_at": "2024-11-25T14:30:00Z",
  "updated_at": "2024-11-25T14:30:00Z",
  "conflicts": [
    {
      "type": "fmit_assignment",
      "date": "2025-01-18",
      "description": "FMIT week assignment during absence",
      "severity": "high"
    }
  ],
  "warnings": [
    "Absence conflicts with FMIT week. Consider requesting swap first."
  ]
}
```

### Conflict Detection

The system automatically detects conflicts with:
- FMIT week assignments
- On-call schedules
- Clinic sessions
- Existing absences (overlaps)

Conflicts are returned in the response but do not block creation. The absence status will be `pending` and require supervisor approval.

### Example Requests

**cURL**

```bash
curl -X POST http://localhost:8000/api/v1/absences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "type": "vacation",
    "start_date": "2025-01-15",
    "end_date": "2025-01-20",
    "notes": "Annual vacation"
  }'
```

**Python**

```python
import requests

absence_data = {
    "person_id": "550e8400-e29b-41d4-a716-446655440001",
    "type": "vacation",
    "start_date": "2025-01-15",
    "end_date": "2025-01-20",
    "notes": "Annual vacation - Hawaii"
}

response = requests.post(
    "http://localhost:8000/api/v1/absences",
    headers={"Authorization": f"Bearer {token}"},
    json=absence_data
)

result = response.json()
print(f"Created absence: {result['id']}")
print(f"Status: {result['status']}")

if result.get('conflicts'):
    print(f"⚠️  {len(result['conflicts'])} conflicts detected:")
    for conflict in result['conflicts']:
        print(f"  - {conflict['description']}")
```

---

## Update Absence

<span class="endpoint-badge put">PUT</span> `/api/v1/absences/{absence_id}`

Update an existing absence.

**Authorization**: Users can update their own pending absences. Coordinators and admins can update any absence.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `absence_id` | UUID | Absence ID |

### Request Body

```json
{
  "type": "vacation",
  "start_date": "2025-01-16",
  "end_date": "2025-01-21",
  "notes": "Extended by one day"
}
```

### Request Parameters

All fields are optional. Only include fields you want to update.

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Absence type |
| `start_date` | string (date) | Start date |
| `end_date` | string (date) | End date |
| `notes` | string | Notes |
| `status` | string | Status (coordinator/admin only) |

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440001",
  "person_name": "FAC-PD",
  "type": "vacation",
  "start_date": "2025-01-16",
  "end_date": "2025-01-21",
  "status": "pending",
  "notes": "Extended by one day",
  "created_at": "2024-11-25T14:30:00Z",
  "updated_at": "2024-11-26T09:15:00Z"
}
```

### Example

```bash
curl -X PUT http://localhost:8000/api/v1/absences/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "end_date": "2025-01-21",
    "notes": "Extended by one day"
  }'
```

---

## Approve/Deny Absence

<span class="endpoint-badge post">POST</span> `/api/v1/absences/{absence_id}/approve`

<span class="endpoint-badge post">POST</span> `/api/v1/absences/{absence_id}/deny`

Approve or deny a pending absence request.

**Authorization**: Requires coordinator or admin role.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `absence_id` | UUID | Absence ID |

### Request Body (optional for approve)

```json
{
  "notes": "Approved - coverage arranged"
}
```

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "approved_by": "admin@example.com",
  "approved_at": "2024-12-01T10:00:00Z",
  "notes": "Approved - coverage arranged"
}
```

### Example

**Approve**

```bash
curl -X POST http://localhost:8000/api/v1/absences/550e8400-e29b-41d4-a716-446655440000/approve \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Approved - coverage arranged"
  }'
```

**Deny**

```bash
curl -X POST http://localhost:8000/api/v1/absences/550e8400-e29b-41d4-a716-446655440000/deny \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Insufficient coverage - please reschedule"
  }'
```

---

## Delete Absence

<span class="endpoint-badge delete">DELETE</span> `/api/v1/absences/{absence_id}`

Delete an absence record.

**Authorization**: Users can delete their own pending absences. Coordinators and admins can delete any absence.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `absence_id` | UUID | Absence ID |

### Response (204 No Content)

No response body.

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Absence with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Forbidden (403)**

```json
{
  "detail": "Cannot delete approved absence. Please contact coordinator."
}
```

### Example

```bash
curl -X DELETE http://localhost:8000/api/v1/absences/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Common Use Cases

### 1. Request Vacation

```python
import requests

def request_vacation(token, person_id, start_date, end_date, reason):
    """Request vacation and check for conflicts."""
    data = {
        "person_id": person_id,
        "type": "vacation",
        "start_date": start_date,
        "end_date": end_date,
        "notes": reason
    }

    response = requests.post(
        "http://localhost:8000/api/v1/absences",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )

    result = response.json()

    print(f"Vacation requested: {result['id']}")
    print(f"Status: {result['status']}")

    if result.get('conflicts'):
        print(f"\n⚠️  Conflicts detected:")
        for conflict in result['conflicts']:
            print(f"  - {conflict['date']}: {conflict['description']}")
        print("\nConsider requesting swaps for conflicting assignments.")

    return result

# Usage
absence = request_vacation(
    token=token,
    person_id="550e8400-e29b-41d4-a716-446655440001",
    start_date="2025-07-15",
    end_date="2025-07-22",
    reason="Family vacation"
)
```

### 2. Track Deployments

```python
def get_active_deployments(token):
    """Get all active military deployments."""
    params = {
        "type": "deployment",
        "status": "approved",
        "start_date": date.today().isoformat()
    }

    response = requests.get(
        "http://localhost:8000/api/v1/absences",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    deployments = response.json()['items']

    print(f"Active Deployments: {len(deployments)}")
    for deployment in deployments:
        print(f"  - {deployment['person_name']}: {deployment['start_date']} to {deployment['end_date']}")

    return deployments

deployments = get_active_deployments(token)
```

### 3. Approve Pending Requests

```python
def approve_pending_absences(token):
    """Approve all pending vacation requests under 7 days."""
    params = {
        "status": "pending",
        "type": "vacation"
    }

    response = requests.get(
        "http://localhost:8000/api/v1/absences",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    pending = response.json()['items']

    for absence in pending:
        start = date.fromisoformat(absence['start_date'])
        end = date.fromisoformat(absence['end_date'])
        duration = (end - start).days + 1

        # Auto-approve if < 7 days and no conflicts
        if duration <= 7 and not absence.get('conflicts'):
            approve_response = requests.post(
                f"http://localhost:8000/api/v1/absences/{absence['id']}/approve",
                headers={"Authorization": f"Bearer {token}"},
                json={"notes": "Auto-approved - under 7 days, no conflicts"}
            )

            if approve_response.status_code == 200:
                print(f"✅ Approved: {absence['person_name']} ({duration} days)")
            else:
                print(f"❌ Failed to approve: {absence['person_name']}")
        else:
            print(f"⚠️  Requires manual review: {absence['person_name']} ({duration} days)")

approve_pending_absences(token)
```

### 4. Check Person's Absence History

```python
def get_absence_summary(token, person_id, year):
    """Get absence summary for a person for the year."""
    params = {
        "person_id": person_id,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "status": "approved"
    }

    response = requests.get(
        "http://localhost:8000/api/v1/absences",
        headers={"Authorization": f"Bearer {token}"},
        params=params
    )

    absences = response.json()['items']

    # Calculate totals by type
    totals = {}
    for absence in absences:
        start = date.fromisoformat(absence['start_date'])
        end = date.fromisoformat(absence['end_date'])
        days = (end - start).days + 1

        absence_type = absence['type']
        totals[absence_type] = totals.get(absence_type, 0) + days

    print(f"Absence Summary for {year}:")
    for absence_type, days in totals.items():
        print(f"  {absence_type}: {days} days")
    print(f"  Total: {sum(totals.values())} days")

    return totals

summary = get_absence_summary(token, person_id="550e8400-e29b-41d4-a716-446655440001", year=2025)
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `ABSENCE_NOT_FOUND` | 404 | Absence does not exist |
| `PERSON_NOT_FOUND` | 404 | Person does not exist |
| `INVALID_DATE_RANGE` | 422 | start_date must be before end_date |
| `OVERLAPPING_ABSENCE` | 422 | Person already has absence for these dates |
| `INSUFFICIENT_PERMISSIONS` | 403 | Cannot modify this absence |
| `CANNOT_DELETE_APPROVED` | 403 | Cannot delete approved absence |
| `VALIDATION_ERROR` | 422 | Invalid request data |

---

## Best Practices

### 1. Always Check Conflicts

When creating absences, always check the `conflicts` array in the response:

```python
result = create_absence(data)

if result.get('conflicts'):
    # Handle conflicts before finalizing
    for conflict in result['conflicts']:
        if conflict['type'] == 'fmit_assignment':
            # Request swap for FMIT week
            request_swap(conflict['date'])
```

### 2. Request Absences Early

Request absences at least 14 days in advance to allow time for:
- Conflict resolution
- Swap requests
- Approval workflow
- Coverage planning

### 3. Deployment Coordination

For military deployments:
1. Create deployment absence ASAP
2. Check conflicts with FMIT/call
3. Request swaps for conflicting weeks
4. Notify program director

### 4. Track Absence Quota

Monitor total absence days per year:

```python
summary = get_absence_summary(person_id, year=2025)
total_days = sum(summary.values())

if total_days > 30:
    print(f"⚠️  Warning: {total_days} absence days (quota: 30)")
```

---

## See Also

- [Swaps API](SWAPS_API.md) - Schedule swap management
- [Persons API](endpoints/persons.md) - Person management
- [Schedule API](endpoints/schedules.md) - Emergency coverage handling
- [Authentication](authentication.md) - Token management
- [Pagination](pagination.md) - Pagination patterns
