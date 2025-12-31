***REMOVED*** People API Reference

**Endpoint Prefix:** `/api/people`

***REMOVED******REMOVED*** Overview

The People API manages residents and faculty members, including their roles, credentials, and procedure qualifications. This API integrates with the scheduling system to ensure ACGME compliance and proper credential verification.

***REMOVED******REMOVED******REMOVED*** Key Features

- **Person Management**: Create, read, update, delete residents and faculty
- **Role-Based Filtering**: Filter by person type (resident/faculty) and PGY level
- **Credential Tracking**: Manage faculty certifications and training records
- **Procedure Qualifications**: Track which faculty can supervise specific procedures
- **Specialty Management**: Organize faculty by specialty

***REMOVED******REMOVED******REMOVED*** Data Model

```
Person (base class)
├── Resident
│   ├── PGY Level (1-3)
│   └── Assigned Rotations
└── Faculty
    ├── Specialty
    ├── Credentials
    └── Qualified Procedures
```

---

***REMOVED******REMOVED*** Endpoints

***REMOVED******REMOVED******REMOVED*** GET /

List all people with optional filtering.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people?type=resident&pgy_level=2' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `type` (optional): Filter by type - `'resident'` or `'faculty'`
- `pgy_level` (optional): Filter residents by PGY level (1, 2, or 3)

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Dr. Jane Smith",
      "email": "jane.smith@medical.edu",
      "type": "resident",
      "pgy_level": 2,
      "specialty": "Internal Medicine",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-12-31T14:20:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "name": "Dr. John Doe",
      "email": "john.doe@medical.edu",
      "type": "resident",
      "pgy_level": 2,
      "specialty": "Internal Medicine",
      "is_active": true,
      "created_at": "2025-01-16T09:00:00Z",
      "updated_at": "2025-12-31T13:15:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

**Error Responses:**

- **401 Unauthorized**: Missing authentication
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

---

***REMOVED******REMOVED******REMOVED*** GET /residents

List all residents with optional PGY level filtering.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people/residents?pgy_level=1' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `pgy_level` (optional): Filter by PGY level (1, 2, or 3)

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "PGY1-01",
      "email": "pgyi01@medical.edu",
      "type": "resident",
      "pgy_level": 1,
      "specialty": "Internal Medicine",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-12-31T14:20:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

---

***REMOVED******REMOVED******REMOVED*** GET /faculty

List all faculty with optional specialty filtering.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people/faculty?specialty=Cardiology' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
- `specialty` (optional): Filter by specialty name

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "name": "Dr. Sarah Johnson",
      "email": "sarah.johnson@medical.edu",
      "type": "faculty",
      "specialty": "Cardiology",
      "role": "attending",
      "is_active": true,
      "created_at": "2025-01-10T08:00:00Z",
      "updated_at": "2025-12-31T15:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

---

***REMOVED******REMOVED******REMOVED*** GET /{person_id}

Get a person by ID.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `person_id` (required, UUID): Person ID to retrieve

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Dr. Jane Smith",
  "email": "jane.smith@medical.edu",
  "phone": "+1-555-0123",
  "type": "resident",
  "pgy_level": 2,
  "specialty": "Internal Medicine",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-12-31T14:20:00Z"
}
```

**Error Responses:**

- **404 Not Found**: Person doesn't exist
  ```json
  {
    "detail": "Person not found"
  }
  ```

---

***REMOVED******REMOVED******REMOVED*** POST /

Create a new person (resident or faculty).

**Request:**
```bash
curl -X POST http://localhost:8000/api/people \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "name": "Dr. Michael Chen",
    "email": "michael.chen@medical.edu",
    "phone": "+1-555-0456",
    "type": "resident",
    "pgy_level": 1,
    "specialty": "Internal Medicine"
  }'
```

**Request Body:**

For **Resident**:
```json
{
  "name": "string (required)",
  "email": "string (required, valid email)",
  "phone": "string (optional)",
  "type": "resident",
  "pgy_level": 1,
  "specialty": "string (optional)"
}
```

For **Faculty**:
```json
{
  "name": "string (required)",
  "email": "string (required, valid email)",
  "phone": "string (optional)",
  "type": "faculty",
  "specialty": "string (required for faculty)",
  "role": "attending | fellow | resident (optional)"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440050",
  "name": "Dr. Michael Chen",
  "email": "michael.chen@medical.edu",
  "phone": "+1-555-0456",
  "type": "resident",
  "pgy_level": 1,
  "specialty": "Internal Medicine",
  "is_active": true,
  "created_at": "2025-12-31T16:30:00Z",
  "updated_at": "2025-12-31T16:30:00Z"
}
```

**Error Responses:**

- **400 Bad Request**: Invalid request data
  ```json
  {
    "detail": "Invalid person data"
  }
  ```

- **400 Bad Request**: Email already exists
  ```json
  {
    "detail": "Person with this email already exists"
  }
  ```

---

***REMOVED******REMOVED******REMOVED*** PUT /{person_id}

Update an existing person.

**Request:**
```bash
curl -X PUT 'http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "phone": "+1-555-0789",
    "specialty": "Emergency Medicine",
    "is_active": true
  }'
```

**Path Parameters:**
- `person_id` (required, UUID): Person ID to update

**Request Body:**
```json
{
  "name": "string (optional)",
  "email": "string (optional)",
  "phone": "string (optional)",
  "specialty": "string (optional)",
  "is_active": "boolean (optional)",
  "pgy_level": "number (optional, for residents)"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Dr. Jane Smith",
  "email": "jane.smith@medical.edu",
  "phone": "+1-555-0789",
  "type": "resident",
  "pgy_level": 2,
  "specialty": "Emergency Medicine",
  "is_active": true,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-12-31T16:45:00Z"
}
```

**Error Responses:**

- **404 Not Found**: Person doesn't exist
  ```json
  {
    "detail": "Person not found"
  }
  ```

- **400 Bad Request**: Invalid update data
  ```json
  {
    "detail": "Invalid person data"
  }
  ```

---

***REMOVED******REMOVED******REMOVED*** DELETE /{person_id}

Delete a person.

**Request:**
```bash
curl -X DELETE 'http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440001' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `person_id` (required, UUID): Person ID to delete

**Response (204):**
No content returned.

**Error Responses:**

- **404 Not Found**: Person doesn't exist
  ```json
  {
    "detail": "Person not found"
  }
  ```

---

***REMOVED******REMOVED*** Credential Management

***REMOVED******REMOVED******REMOVED*** GET /{person_id}/credentials

Get all credentials for a faculty member.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440010/credentials?status=active&include_expired=false' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `person_id` (required, UUID): Faculty member ID

**Query Parameters:**
- `status` (optional): Filter by status - `'active'`, `'expired'`, `'pending'`
- `include_expired` (optional, default: false): Include expired credentials

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440100",
      "person_id": "550e8400-e29b-41d4-a716-446655440010",
      "credential_type": "BLS",
      "issuer": "American Heart Association",
      "issue_date": "2024-01-15",
      "expiration_date": "2026-01-15",
      "status": "active",
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440101",
      "person_id": "550e8400-e29b-41d4-a716-446655440010",
      "credential_type": "ACLS",
      "issuer": "American Heart Association",
      "issue_date": "2023-06-01",
      "expiration_date": "2026-06-01",
      "status": "active",
      "created_at": "2023-06-01T10:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

**Credential Types:**
- BLS (Basic Life Support)
- ACLS (Advanced Cardiac Life Support)
- PALS (Pediatric Advanced Life Support)
- NRP (Neonatal Resuscitation Program)
- HIPAA Training
- Cyber Security Training
- N95 Fit Test
- Chaperone Training
- Bloodborne Pathogen Training
- Sharps Safety

---

***REMOVED******REMOVED******REMOVED*** GET /{person_id}/credentials/summary

Get a summary of a faculty member's credentials.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440010/credentials/summary' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `person_id` (required, UUID): Faculty member ID

**Response (200):**
```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440010",
  "person_name": "Dr. Sarah Johnson",
  "total_credentials": 8,
  "active_credentials": 7,
  "expired_credentials": 1,
  "expiring_within_30_days": 2,
  "credentials_by_type": {
    "BLS": {
      "status": "active",
      "expiration_date": "2026-01-15"
    },
    "ACLS": {
      "status": "active",
      "expiration_date": "2026-06-01"
    }
  },
  "compliance_status": "compliant",
  "next_expiration": "2026-01-15"
}
```

**Response Fields:**

- `compliance_status` (string): `'compliant'` (all required credentials active) or `'non-compliant'`
- `expiring_within_30_days` (number): Count of credentials expiring in the next 30 days
- `total_credentials` (number): Total number of credentials
- `active_credentials` (number): Number of currently valid credentials
- `expired_credentials` (number): Number of expired credentials

---

***REMOVED******REMOVED******REMOVED*** GET /{person_id}/procedures

Get all procedures a faculty member is qualified to supervise.

**Request:**
```bash
curl -X GET 'http://localhost:8000/api/people/550e8400-e29b-41d4-a716-446655440010/procedures' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Path Parameters:**
- `person_id` (required, UUID): Faculty member ID

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440200",
      "name": "Echocardiography",
      "specialty": "Cardiology",
      "required_credentials": [
        "ACLS",
        "BLS"
      ],
      "faculty_certified": true,
      "certification_date": "2023-06-01"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440201",
      "name": "Coronary Angiography",
      "specialty": "Cardiology",
      "required_credentials": [
        "ACLS",
        "BLS"
      ],
      "faculty_certified": true,
      "certification_date": "2023-06-01"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

---

***REMOVED******REMOVED*** Data Models

***REMOVED******REMOVED******REMOVED*** Person Response

```json
{
  "id": "string (UUID)",
  "name": "string",
  "email": "string",
  "phone": "string or null",
  "type": "resident | faculty",
  "pgy_level": "number or null (for residents only)",
  "specialty": "string or null",
  "is_active": "boolean",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

***REMOVED******REMOVED******REMOVED*** Credential Response

```json
{
  "id": "string (UUID)",
  "person_id": "string (UUID)",
  "credential_type": "string",
  "issuer": "string",
  "issue_date": "string (YYYY-MM-DD)",
  "expiration_date": "string (YYYY-MM-DD)",
  "status": "active | expired | pending",
  "created_at": "string (ISO 8601)"
}
```

***REMOVED******REMOVED******REMOVED*** Procedure Response

```json
{
  "id": "string (UUID)",
  "name": "string",
  "specialty": "string",
  "required_credentials": ["string"],
  "faculty_certified": "boolean",
  "certification_date": "string (ISO 8601) or null"
}
```

---

***REMOVED******REMOVED*** Common Use Cases

***REMOVED******REMOVED******REMOVED*** 1. List All PGY-2 Residents

```bash
curl -X GET 'http://localhost:8000/api/people/residents?pgy_level=2' \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.items'
```

***REMOVED******REMOVED******REMOVED*** 2. Find Faculty by Specialty

```bash
curl -X GET 'http://localhost:8000/api/people/faculty?specialty=Cardiology' \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

***REMOVED******REMOVED******REMOVED*** 3. Verify Faculty Credentials Before Assignment

```bash
***REMOVED*** Check credentials summary
curl -X GET 'http://localhost:8000/api/people/{faculty_id}/credentials/summary' \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.compliance_status'

***REMOVED*** Check specific procedures
curl -X GET 'http://localhost:8000/api/people/{faculty_id}/procedures' \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq '.items[] | select(.name == "Echocardiography")'
```

***REMOVED******REMOVED******REMOVED*** 4. Create New Resident

```bash
curl -X POST http://localhost:8000/api/people \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "name": "PGY1-01",
    "email": "pgyi01@medical.edu",
    "type": "resident",
    "pgy_level": 1,
    "specialty": "Internal Medicine"
  }' | jq '.id'
```

***REMOVED******REMOVED******REMOVED*** 5. Update Resident Status

```bash
curl -X PUT 'http://localhost:8000/api/people/{resident_id}' \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "is_active": false
  }'
```

---

***REMOVED******REMOVED*** Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request format or validation error |
| 401 | Unauthorized | Authentication required or invalid token |
| 404 | Not Found | Person, credential, or procedure not found |
| 409 | Conflict | Email already exists or other conflict |
| 500 | Internal Server Error | Server error |

---

***REMOVED******REMOVED*** Related Documentation

- [Scheduling API](SCHEDULE_API.md)
- [Assignment API](ASSIGNMENTS_API.md)
- [Credential Management Guide](../user-guide/credentials.md)
