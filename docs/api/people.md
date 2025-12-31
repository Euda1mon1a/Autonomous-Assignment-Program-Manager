# People API Endpoints

Complete reference for managing residents, faculty, and other personnel in the residency program.

---

## Overview

The People API provides endpoints for:
- Managing resident and faculty rosters
- Tracking PGY levels and specialties
- Role assignment and permissions
- Personnel onboarding and offboarding
- Credential tracking and renewals

**Base Path**: `/api/v1/people`

**Authentication**: All endpoints require JWT authentication. Admin and coordinator roles required for write operations.

---

## List People

<span class="endpoint-badge get">GET</span> `/api/v1/people`

List all personnel with optional filters and pagination.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by type: `resident`, `faculty`, `staff` |
| `role` | string | No | Filter by role: `admin`, `coordinator`, `faculty`, `resident`, `clinical_staff`, `rn`, `lpn`, `msa` |
| `pgy_level` | integer | No | Filter by PGY level (1, 2, or 3) |
| `specialty` | string | No | Filter by medical specialty |
| `active` | boolean | No | Filter by active status (default: true) |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50) |

### Person Types

| Type | Description | Typical Roles |
|------|-------------|---------------|
| `resident` | Medical resident in training | Resident |
| `faculty` | Attending physician/instructor | Faculty, Admin, Coordinator |
| `staff` | Administrative or clinical staff | Clinical Staff, RN, LPN, MSA |

### Roles (RBAC)

| Role | Permissions | Description |
|------|-------------|-------------|
| `admin` | Full system access | System administrators |
| `coordinator` | Schedule management, approvals | Program coordinators |
| `faculty` | View schedules, request swaps | Attending physicians |
| `resident` | View own schedule, request leave | Medical residents |
| `clinical_staff` | Limited clinical access | Nurses, pharmacists |
| `rn` | Registered nurse access | RN staff |
| `lpn` | Licensed practical nurse access | LPN staff |
| `msa` | Medical support assistant access | MSA staff |

### Response

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Doe, John",
      "email": "john.doe@example.com",
      "type": "resident",
      "role": "resident",
      "pgy_level": 2,
      "specialty": "Family Medicine",
      "active": true,
      "start_date": "2024-07-01",
      "credentials": {
        "medical_license": "MD123456",
        "dea": null,
        "board_certified": false
      },
      "created_at": "2024-06-15T10:00:00Z",
      "updated_at": "2024-12-01T14:30:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Smith, Jane",
      "email": "jane.smith@example.com",
      "type": "faculty",
      "role": "faculty",
      "pgy_level": null,
      "specialty": "Family Medicine",
      "active": true,
      "start_date": "2020-01-15",
      "credentials": {
        "medical_license": "MD789012",
        "dea": "AS1234567",
        "board_certified": true
      },
      "created_at": "2020-01-01T08:00:00Z",
      "updated_at": "2024-11-15T09:20:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 50,
  "pages": 1
}
```

### Example Requests

**All active people**

```bash
curl "http://localhost:8000/api/v1/people?active=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Residents only**

```bash
curl "http://localhost:8000/api/v1/people?type=resident" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**PGY-2 residents**

```bash
curl "http://localhost:8000/api/v1/people?type=resident&pgy_level=2" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Faculty in Family Medicine**

```bash
curl "http://localhost:8000/api/v1/people?type=faculty&specialty=Family+Medicine" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Python Example**

```python
import requests

params = {
    "type": "resident",
    "active": True,
    "page": 1,
    "page_size": 50
}

response = requests.get(
    "http://localhost:8000/api/v1/people",
    headers={"Authorization": f"Bearer {token}"},
    params=params
)

people = response.json()
print(f"Total residents: {people['total']}")
for person in people['items']:
    pgy = f"PGY-{person['pgy_level']}" if person['pgy_level'] else "N/A"
    print(f"{person['name']}: {pgy}, {person['specialty']}")
```

---

## Get Person

<span class="endpoint-badge get">GET</span> `/api/v1/people/{person_id}`

Get detailed information about a specific person.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person ID |

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Doe, John",
  "email": "john.doe@example.com",
  "type": "resident",
  "role": "resident",
  "pgy_level": 2,
  "specialty": "Family Medicine",
  "active": true,
  "start_date": "2024-07-01",
  "end_date": null,
  "credentials": {
    "medical_license": "MD123456",
    "license_expiry": "2026-12-31",
    "dea": null,
    "board_certified": false
  },
  "contact": {
    "phone": "+1-555-0123",
    "emergency_contact": "Jane Doe (spouse): +1-555-0124"
  },
  "assignments_count": 248,
  "absences_count": 5,
  "swaps_count": 3,
  "created_at": "2024-06-15T10:00:00Z",
  "updated_at": "2024-12-01T14:30:00Z"
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

Create a new person record.

**Authorization**: Requires admin or coordinator role.

### Request Body

```json
{
  "name": "Brown, Alice",
  "email": "alice.brown@example.com",
  "type": "resident",
  "role": "resident",
  "pgy_level": 1,
  "specialty": "Family Medicine",
  "start_date": "2025-07-01",
  "credentials": {
    "medical_license": "MD345678",
    "license_expiry": "2027-12-31"
  },
  "contact": {
    "phone": "+1-555-0125"
  }
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Full name (Last, First format) |
| `email` | string | Yes | Email address (must be unique) |
| `type` | string | Yes | Person type: `resident`, `faculty`, `staff` |
| `role` | string | Yes | System role (see roles table above) |
| `pgy_level` | integer | Conditional | Required for residents (1, 2, or 3) |
| `specialty` | string | Yes | Medical specialty |
| `start_date` | string (date) | Yes | Program start date (YYYY-MM-DD) |
| `end_date` | string (date) | No | Program end date (optional) |
| `credentials` | object | No | Credentials object (license, DEA, etc.) |
| `contact` | object | No | Contact information |

### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Brown, Alice",
  "email": "alice.brown@example.com",
  "type": "resident",
  "role": "resident",
  "pgy_level": 1,
  "specialty": "Family Medicine",
  "active": true,
  "start_date": "2025-07-01",
  "created_at": "2025-01-10T09:00:00Z",
  "updated_at": "2025-01-10T09:00:00Z"
}
```

### Validation Rules

- **Email uniqueness**: Email must not already exist in system
- **PGY level**: Required for residents, must be 1, 2, or 3
- **Specialty**: Must match known specialties (configurable)
- **Role-type alignment**: Role must be compatible with type (e.g., residents can't have `admin` role)

### Example Requests

**cURL**

```bash
curl -X POST http://localhost:8000/api/v1/people \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Brown, Alice",
    "email": "alice.brown@example.com",
    "type": "resident",
    "role": "resident",
    "pgy_level": 1,
    "specialty": "Family Medicine",
    "start_date": "2025-07-01"
  }'
```

**Python**

```python
import requests

person_data = {
    "name": "Brown, Alice",
    "email": "alice.brown@example.com",
    "type": "resident",
    "role": "resident",
    "pgy_level": 1,
    "specialty": "Family Medicine",
    "start_date": "2025-07-01",
    "credentials": {
        "medical_license": "MD345678",
        "license_expiry": "2027-12-31"
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/people",
    headers={"Authorization": f"Bearer {admin_token}"},
    json=person_data
)

result = response.json()
print(f"Created person: {result['id']}")
print(f"Name: {result['name']}, PGY: {result['pgy_level']}")
```

---

## Update Person

<span class="endpoint-badge put">PUT</span> `/api/v1/people/{person_id}`

Update an existing person record.

**Authorization**: Requires admin or coordinator role.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person ID |

### Request Body

All fields are optional. Only include fields you want to update.

```json
{
  "pgy_level": 3,
  "specialty": "Emergency Medicine",
  "credentials": {
    "board_certified": true,
    "board_cert_date": "2025-06-15"
  }
}
```

### Common Updates

**Promote resident to next PGY level:**
```json
{
  "pgy_level": 3
}
```

**Mark as inactive (offboard):**
```json
{
  "active": false,
  "end_date": "2025-06-30"
}
```

**Update credentials:**
```json
{
  "credentials": {
    "medical_license": "MD123456",
    "license_expiry": "2027-12-31",
    "dea": "AS1234567",
    "board_certified": true
  }
}
```

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Doe, John",
  "email": "john.doe@example.com",
  "type": "resident",
  "role": "resident",
  "pgy_level": 3,
  "specialty": "Emergency Medicine",
  "active": true,
  "updated_at": "2025-01-10T10:30:00Z"
}
```

### Example

```bash
curl -X PUT http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pgy_level": 3,
    "credentials": {"board_certified": true}
  }'
```

---

## Delete Person

<span class="endpoint-badge delete">DELETE</span> `/api/v1/people/{person_id}`

**CAUTION**: This is a soft delete. Person is marked inactive but not removed from database.

**Authorization**: Requires admin role.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person ID |

### Response (204 No Content)

No response body. Person is marked `active=false`.

### Error Responses

**Not Found (404)**

```json
{
  "detail": "Person with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Forbidden (403)**

```json
{
  "detail": "Cannot delete person with active assignments. Remove assignments first."
}
```

### Example

```bash
curl -X DELETE http://localhost:8000/api/v1/people/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Common Use Cases

### 1. Onboard New Resident

```python
import requests
from datetime import date

def onboard_resident(token, name, email, pgy_level, start_date):
    """Onboard a new resident to the program."""
    data = {
        "name": name,
        "email": email,
        "type": "resident",
        "role": "resident",
        "pgy_level": pgy_level,
        "specialty": "Family Medicine",
        "start_date": start_date,
        "active": True
    }

    response = requests.post(
        "http://localhost:8000/api/v1/people",
        headers={"Authorization": f"Bearer {token}"},
        json=data
    )

    result = response.json()
    print(f"✅ Onboarded: {result['name']} (PGY-{result['pgy_level']})")
    print(f"   ID: {result['id']}")
    print(f"   Email: {result['email']}")

    return result

# Usage
new_resident = onboard_resident(
    token=admin_token,
    name="Williams, Sarah",
    email="sarah.williams@example.com",
    pgy_level=1,
    start_date="2025-07-01"
)
```

### 2. Promote Residents to Next PGY Level

```python
def promote_residents(token):
    """Promote all residents to next PGY level (run annually)."""
    # Get all active residents
    response = requests.get(
        "http://localhost:8000/api/v1/people",
        headers={"Authorization": f"Bearer {token}"},
        params={"type": "resident", "active": True}
    )

    residents = response.json()['items']

    for resident in residents:
        current_pgy = resident['pgy_level']

        if current_pgy == 3:
            # Graduate PGY-3s
            requests.put(
                f"http://localhost:8000/api/v1/people/{resident['id']}",
                headers={"Authorization": f"Bearer {token}"},
                json={"active": False, "end_date": date.today().isoformat()}
            )
            print(f"🎓 Graduated: {resident['name']}")
        else:
            # Promote to next level
            new_pgy = current_pgy + 1
            requests.put(
                f"http://localhost:8000/api/v1/people/{resident['id']}",
                headers={"Authorization": f"Bearer {token}"},
                json={"pgy_level": new_pgy}
            )
            print(f"⬆️  Promoted: {resident['name']} (PGY-{current_pgy} → PGY-{new_pgy})")

# Run annually on July 1
promote_residents(admin_token)
```

### 3. Generate Resident Roster Report

```python
def generate_roster_report(token):
    """Generate current resident roster with counts by PGY."""
    response = requests.get(
        "http://localhost:8000/api/v1/people",
        headers={"Authorization": f"Bearer {token}"},
        params={"type": "resident", "active": True}
    )

    residents = response.json()['items']

    # Count by PGY level
    pgy_counts = {1: 0, 2: 0, 3: 0}
    for resident in residents:
        pgy_counts[resident['pgy_level']] += 1

    print("=== RESIDENT ROSTER REPORT ===")
    print(f"Total Residents: {len(residents)}")
    print(f"  PGY-1: {pgy_counts[1]}")
    print(f"  PGY-2: {pgy_counts[2]}")
    print(f"  PGY-3: {pgy_counts[3]}")
    print()

    # List by PGY
    for pgy in [1, 2, 3]:
        print(f"PGY-{pgy} Residents:")
        for resident in sorted(residents, key=lambda r: r['name']):
            if resident['pgy_level'] == pgy:
                print(f"  - {resident['name']} ({resident['email']})")
        print()

generate_roster_report(token)
```

### 4. Track Credential Expiration

```python
from datetime import datetime, timedelta

def check_expiring_credentials(token, days_warning=30):
    """Check for credentials expiring soon."""
    response = requests.get(
        "http://localhost:8000/api/v1/people",
        headers={"Authorization": f"Bearer {token}"},
        params={"active": True}
    )

    people = response.json()['items']
    cutoff_date = datetime.now() + timedelta(days=days_warning)

    print(f"=== CREDENTIALS EXPIRING IN {days_warning} DAYS ===")

    for person in people:
        creds = person.get('credentials', {})
        license_expiry = creds.get('license_expiry')

        if license_expiry:
            expiry_date = datetime.fromisoformat(license_expiry)
            if expiry_date <= cutoff_date:
                days_remaining = (expiry_date - datetime.now()).days
                print(f"⚠️  {person['name']}: Medical license expires in {days_remaining} days")
                print(f"   License: {creds.get('medical_license')}")
                print(f"   Expiry: {license_expiry}")
                print()

check_expiring_credentials(admin_token, days_warning=60)
```

---

## Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `PERSON_NOT_FOUND` | 404 | Person does not exist |
| `EMAIL_ALREADY_EXISTS` | 422 | Email is already registered |
| `INVALID_PGY_LEVEL` | 422 | PGY level must be 1, 2, or 3 |
| `INVALID_PERSON_TYPE` | 422 | Type must be resident, faculty, or staff |
| `INVALID_ROLE` | 422 | Role not recognized or incompatible with type |
| `CANNOT_DELETE_WITH_ASSIGNMENTS` | 403 | Person has active assignments |
| `INSUFFICIENT_PERMISSIONS` | 403 | Admin or coordinator role required |

---

## Best Practices

### 1. Use Email as Unique Identifier

Emails are unique and immutable. Use email for external integrations:

```python
# Look up by email instead of ID
params = {"email": "john.doe@example.com"}
response = requests.get("http://localhost:8000/api/v1/people", params=params)
person = response.json()['items'][0]
```

### 2. Soft Delete for Historical Records

Never hard delete people - use soft delete to preserve:
- Historical schedule assignments
- Swap history
- Compliance audit trails

### 3. Credential Renewal Reminders

Set up automated reminders for credential renewals:

```python
# Check monthly for credentials expiring in 60 days
if datetime.now().day == 1:
    check_expiring_credentials(admin_token, days_warning=60)
```

### 4. Validate PGY Levels on Promotion

Ensure PGY transitions happen only once per year:

```python
# Only promote on July 1
if datetime.now().month == 7 and datetime.now().day == 1:
    promote_residents(admin_token)
```

### 5. Role-Type Consistency

Always ensure role matches type:
- Residents → `resident` role
- Faculty → `faculty`, `coordinator`, or `admin` roles
- Staff → `clinical_staff`, `rn`, `lpn`, or `msa` roles

---

## See Also

- [Assignments API](endpoints/assignments.md) - Person assignment management
- [Absences API](absences.md) - Leave and deployment tracking
- [Authentication](authentication.md) - Role-based access control
- [Pagination](pagination.md) - Pagination patterns
- [User Management Guide](../guides/user-workflows.md) - Personnel workflows
