# Persons API Endpoints

Complete reference for managing residents, faculty, and their credentials.

---

## Overview

The Persons API provides endpoints for:
- Listing residents and faculty
- Creating and updating person records
- Managing procedure credentials
- Tracking faculty qualifications

**Base Path**: `/api/v1/people`

**Authentication**: All endpoints require JWT authentication.

---

## List People

<span class="endpoint-badge get">GET</span> `/api/v1/people`

List all people (residents and faculty) with optional filters.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `resident` or `faculty` |
| `pgy_level` | integer | No | Filter residents by PGY level (1, 2, or 3) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "PGY1-01",
      "type": "resident",
      "pgy_level": 1,
      "email": "pgy1-01@example.com",
      "phone": null,
      "specialty": null,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "FAC-PD",
      "type": "faculty",
      "pgy_level": null,
      "email": "pd@example.com",
      "phone": "+1-808-555-1234",
      "specialty": "Family Medicine",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 21
}
```

### Example Requests

**All people**

```bash
curl "http://localhost:8000/api/v1/people" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Only residents**

```bash
curl "http://localhost:8000/api/v1/people?type=resident" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Only faculty**

```bash
curl "http://localhost:8000/api/v1/people?type=faculty" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Residents filtered by PGY level**

```bash
curl "http://localhost:8000/api/v1/people?type=resident&pgy_level=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python example**

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/people",
    headers={"Authorization": f"Bearer {token}"},
    params={"type": "resident", "pgy_level": 2}
)

people = response.json()
print(f"Total PGY-2 residents: {people['total']}")
for person in people['items']:
    print(f"  - {person['name']}")
```

---

## List Residents

<span class="endpoint-badge get">GET</span> `/api/v1/people/residents`

List all residents, optionally filtered by PGY level.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "PGY1-01",
      "type": "resident",
      "pgy_level": 1,
      "email": "pgy1-01@example.com",
      "phone": null,
      "specialty": null,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 9
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/people/residents?pgy_level=1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## List Faculty

<span class="endpoint-badge get">GET</span> `/api/v1/people/faculty`

List all faculty, optionally filtered by specialty.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `specialty` | string | No | Filter by specialty (e.g., "Sports Medicine") |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "FAC-PD",
      "type": "faculty",
      "pgy_level": null,
      "email": "pd@example.com",
      "phone": "+1-808-555-1234",
      "specialty": "Family Medicine",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 12
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/people/faculty?specialty=Sports+Medicine" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Person

<span class="endpoint-badge get">GET</span> `/api/v1/people/{person_id}`

Get a specific person by ID.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person ID |

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "PGY1-01",
  "type": "resident",
  "pgy_level": 1,
  "email": "pgy1-01@example.com",
  "phone": null,
  "specialty": null,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "assignments": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "block_id": "550e8400-e29b-41d4-a716-446655440002",
      "role": "resident",
      "activity_name": "Clinic",
      "abbreviation": "CLN"
    }
  ]
}
```

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Person with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Create Person

<span class="endpoint-badge post">POST</span> `/api/v1/people`

Create a new person (resident or faculty).

### Request Body

**Resident**

```json
{
  "name": "PGY1-04",
  "type": "resident",
  "pgy_level": 1,
  "email": "pgy1-04@example.com",
  "phone": "+1-808-555-5678",
  "is_active": true
}
```

**Faculty**

```json
{
  "name": "FAC-CORE-02",
  "type": "faculty",
  "email": "core-02@example.com",
  "phone": "+1-808-555-9876",
  "specialty": "Sports Medicine",
  "is_active": true
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Person's name or identifier |
| `type` | string | Yes | Type: `resident` or `faculty` |
| `pgy_level` | integer | Conditional | PGY level (1-3, required for residents) |
| `email` | string | No | Email address |
| `phone` | string | No | Phone number |
| `specialty` | string | No | Specialty (for faculty) |
| `is_active` | boolean | No | Active status (default: true) |

### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "PGY1-04",
  "type": "resident",
  "pgy_level": 1,
  "email": "pgy1-04@example.com",
  "phone": "+1-808-555-5678",
  "specialty": null,
  "is_active": true,
  "created_at": "2024-07-01T10:00:00Z",
  "updated_at": "2024-07-01T10:00:00Z"
}
```

### Example Requests

**cURL**

```bash
curl -X POST http://localhost:8000/api/v1/people \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PGY1-04",
    "type": "resident",
    "pgy_level": 1,
    "email": "pgy1-04@example.com"
  }'
```

**Python**

```python
import requests

data = {
    "name": "FAC-CORE-02",
    "type": "faculty",
    "email": "core-02@example.com",
    "specialty": "Sports Medicine"
}

response = requests.post(
    "http://localhost:8000/api/v1/people",
    headers={"Authorization": f"Bearer {token}"},
    json=data
)

person = response.json()
print(f"Created person: {person['id']}")
```

---

## Update Person

<span class="endpoint-badge put">PUT</span> `/api/v1/people/{person_id}`

Update an existing person.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person ID |

### Request Body

```json
{
  "name": "PGY2-01",
  "pgy_level": 2,
  "email": "pgy2-01@example.com",
  "phone": "+1-808-555-9999",
  "is_active": true
}
```

### Request Parameters

All fields are optional. Only include fields you want to update.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Person's name |
| `pgy_level` | integer | PGY level (residents only) |
| `email` | string | Email address |
| `phone` | string | Phone number |
| `specialty` | string | Specialty (faculty only) |
| `is_active` | boolean | Active status |

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "PGY2-01",
  "type": "resident",
  "pgy_level": 2,
  "email": "pgy2-01@example.com",
  "phone": "+1-808-555-9999",
  "specialty": null,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-07-01T10:30:00Z"
}
```

### Example

```bash
curl -X PUT http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pgy_level": 2,
    "email": "pgy2-01@example.com"
  }'
```

---

## Delete Person

<span class="endpoint-badge delete">DELETE</span> `/api/v1/people/{person_id}`

Delete a person.

**Warning**: This operation cascades to related records (assignments, absences, etc.).

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person ID |

### Response (204 No Content)

No response body.

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Person with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Conflict (409)**

```json
{
  "detail": "Cannot delete person with active assignments. Delete assignments first or set is_active=false."
}
```

### Example

```bash
curl -X DELETE http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Person Credentials

<span class="endpoint-badge get">GET</span> `/api/v1/people/{person_id}/credentials`

Get all procedure credentials for a faculty member.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Faculty member ID |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter by status: `active`, `expired`, `revoked` |
| `include_expired` | boolean | No | Include expired credentials (default: false) |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "faculty_id": "550e8400-e29b-41d4-a716-446655440001",
      "procedure_id": "550e8400-e29b-41d4-a716-446655440002",
      "credential_type": "BLS",
      "status": "active",
      "certified_date": "2024-01-01",
      "expiration_date": "2026-01-01",
      "certification_number": "BLS-123456",
      "issuing_organization": "American Heart Association",
      "notes": "Recertified 2024",
      "procedure": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "Basic Life Support",
        "code": "BLS",
        "category": "resuscitation"
      }
    }
  ],
  "total": 5
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000/credentials?status=active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Person Credential Summary

<span class="endpoint-badge get">GET</span> `/api/v1/people/{person_id}/credentials/summary`

Get a summary of a faculty member's credentials.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Faculty member ID |

### Response

```json
{
  "faculty_id": "550e8400-e29b-41d4-a716-446655440000",
  "faculty_name": "FAC-PD",
  "total_credentials": 8,
  "active_credentials": 6,
  "expired_credentials": 2,
  "expiring_soon": 1,
  "credentials_by_category": {
    "resuscitation": 3,
    "procedures": 2,
    "certifications": 3
  },
  "upcoming_expirations": [
    {
      "credential_type": "ACLS",
      "procedure_name": "Advanced Cardiac Life Support",
      "expiration_date": "2024-08-15",
      "days_until_expiration": 45
    }
  ]
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000/credentials/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Get Person Procedures

<span class="endpoint-badge get">GET</span> `/api/v1/people/{person_id}/procedures`

Get all procedures a faculty member is qualified to supervise.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Faculty member ID |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Basic Life Support",
      "code": "BLS",
      "category": "resuscitation",
      "description": "CPR and basic emergency care",
      "required_credentials": ["BLS"],
      "supervision_required": false,
      "faculty_credential": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "status": "active",
        "expiration_date": "2026-01-01"
      }
    }
  ],
  "total": 8
}
```

### Example

```bash
curl "http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000/procedures" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Common Use Cases

### 1. Add New Resident to Program

```python
import requests

# Create resident
data = {
    "name": "PGY1-05",
    "type": "resident",
    "pgy_level": 1,
    "email": "pgy1-05@example.com"
}

response = requests.post(
    "http://localhost:8000/api/v1/people",
    headers={"Authorization": f"Bearer {token}"},
    json=data
)

resident = response.json()
print(f"Created resident: {resident['name']} (ID: {resident['id']})")
```

### 2. Promote Resident to Next PGY Level

```python
# Promote all PGY-1 residents to PGY-2
residents = requests.get(
    "http://localhost:8000/api/v1/people/residents",
    headers={"Authorization": f"Bearer {token}"},
    params={"pgy_level": 1}
).json()

for resident in residents['items']:
    update = {"pgy_level": 2}
    response = requests.put(
        f"http://localhost:8000/api/v1/people/{resident['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json=update
    )
    print(f"Promoted {resident['name']} to PGY-2")
```

### 3. Find Faculty with Expiring Credentials

```python
import requests

# Get all faculty
faculty = requests.get(
    "http://localhost:8000/api/v1/people/faculty",
    headers={"Authorization": f"Bearer {token}"}
).json()

# Check credential summaries
for fac in faculty['items']:
    summary = requests.get(
        f"http://localhost:8000/api/v1/people/{fac['id']}/credentials/summary",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    if summary['expiring_soon'] > 0:
        print(f"⚠️  {fac['name']} has {summary['expiring_soon']} expiring credentials")
        for exp in summary['upcoming_expirations']:
            print(f"    - {exp['credential_type']}: expires {exp['expiration_date']}")
```

### 4. Deactivate Person Instead of Deleting

```python
# Soft delete by setting is_active=false
response = requests.put(
    f"http://localhost:8000/api/v1/people/{person_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={"is_active": false}
)

if response.status_code == 200:
    print("Person deactivated (soft delete)")
```

---

## Validation Rules

### Name Validation

- **Required**: Yes
- **Min Length**: 1 character
- **Max Length**: 100 characters
- **Pattern**: Any characters allowed (supports codes like "PGY1-01" or real names)

### Email Validation

- **Format**: Valid email format (user@domain.com)
- **Unique**: Must be unique across all people

### PGY Level Validation

- **Type**: `resident` only
- **Range**: 1, 2, or 3
- **Required**: Yes for residents, must be null for faculty

### Specialty Validation

- **Type**: `faculty` only
- **Examples**: "Family Medicine", "Sports Medicine", "Pediatrics"

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `PERSON_NOT_FOUND` | 404 | Person does not exist |
| `EMAIL_ALREADY_EXISTS` | 422 | Email is already in use |
| `INVALID_PGY_LEVEL` | 422 | PGY level must be 1, 2, or 3 |
| `PGY_LEVEL_REQUIRED` | 422 | Residents must have pgy_level |
| `PGY_LEVEL_FORBIDDEN` | 422 | Faculty cannot have pgy_level |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `DELETE_CONFLICT` | 409 | Cannot delete person with active assignments |

---

## See Also

- [Assignments API](assignments.md) - Assign people to schedules
- [Credentials API](../credentials.md) - Manage procedure credentials
- [Authentication](../authentication.md) - Token management
