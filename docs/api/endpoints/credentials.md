# Credentials API

> **Last Updated:** 2025-12-16

Endpoints for managing faculty procedure credentials - tracking which faculty members are qualified to supervise specific medical procedures.

## Overview

The credentials system ensures that procedures requiring supervision are only assigned to faculty with valid credentials. Credentials have:
- **Status**: `active`, `expired`, `suspended`, `pending`
- **Competency Level**: `trainee`, `qualified`, `expert`, `master`
- **Expiration tracking** with configurable alerts
- **Supervision limits** (concurrent residents, per week, per academic year)

## Base URL

```
/api/credentials
```

---

## Endpoints

### List Expiring Credentials

```http
GET /api/credentials/expiring
```

List credentials expiring within a specified timeframe.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 30 | Number of days to look ahead |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "person_id": "uuid",
      "procedure_id": "uuid",
      "status": "active",
      "competency_level": "qualified",
      "issued_date": "2024-01-15",
      "expiration_date": "2025-01-15",
      "last_verified_date": "2024-06-15",
      "max_concurrent_residents": 2,
      "max_per_week": 10,
      "max_per_academic_year": 200,
      "notes": null,
      "is_valid": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-06-15T14:30:00Z"
    }
  ],
  "total": 1
}
```

---

### List Credentials by Person

```http
GET /api/credentials/by-person/{person_id}
```

Get all credentials for a specific faculty member.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Faculty member's ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter by status (`active`, `expired`, `suspended`, `pending`) |
| `include_expired` | boolean | false | Include expired credentials |

**Response:** `200 OK` - Returns `CredentialListResponse`

---

### List Credentials by Procedure

```http
GET /api/credentials/by-procedure/{procedure_id}
```

Get all credentials for a specific procedure (who can supervise it).

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | null | Filter by status |
| `include_expired` | boolean | false | Include expired credentials |

**Response:** `200 OK` - Returns `CredentialListResponse`

---

### Get Qualified Faculty

```http
GET /api/credentials/qualified-faculty/{procedure_id}
```

Get all faculty members currently qualified to supervise a specific procedure.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Response:** `200 OK`

```json
{
  "procedure_id": "uuid",
  "procedure_name": "Joint Injection",
  "qualified_faculty": [
    {
      "id": "uuid",
      "name": "Dr. Smith",
      "type": "faculty"
    }
  ],
  "total": 1
}
```

---

### Check Qualification

```http
GET /api/credentials/check/{person_id}/{procedure_id}
```

Check if a faculty member is qualified to supervise a specific procedure.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Faculty member's ID |
| `procedure_id` | UUID | Procedure's ID |

**Response:** `200 OK`

```json
{
  "qualified": true,
  "credential_id": "uuid",
  "competency_level": "expert",
  "expiration_date": "2025-06-15"
}
```

---

### Get Faculty Credential Summary

```http
GET /api/credentials/summary/{person_id}
```

Get a summary of a faculty member's credentials.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Faculty member's ID |

**Response:** `200 OK`

```json
{
  "person_id": "uuid",
  "person_name": "Dr. Smith",
  "total_credentials": 5,
  "active_credentials": 4,
  "expiring_soon": 1,
  "procedures": [
    {
      "id": "uuid",
      "name": "Joint Injection",
      "specialty": "Sports Medicine",
      "category": "office"
    }
  ]
}
```

---

### Get Credential

```http
GET /api/credentials/{credential_id}
```

Get a specific credential by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `credential_id` | UUID | Credential's ID |

**Response:** `200 OK` - Returns `CredentialResponse`

---

### Create Credential

```http
POST /api/credentials
```

Create a new credential for a faculty member. **Requires authentication.**

**Request Body:**

```json
{
  "person_id": "uuid",
  "procedure_id": "uuid",
  "status": "active",
  "competency_level": "qualified",
  "issued_date": "2024-01-15",
  "expiration_date": "2026-01-15",
  "max_concurrent_residents": 2,
  "max_per_week": 10,
  "max_per_academic_year": 200,
  "notes": "Completed advanced training course"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Faculty member to credential |
| `procedure_id` | UUID | Yes | Procedure being credentialed for |
| `status` | string | No | Default: `active` |
| `competency_level` | string | No | Default: `qualified` |
| `issued_date` | date | No | When credential was issued |
| `expiration_date` | date | No | When credential expires |
| `max_concurrent_residents` | integer | No | Max residents supervised at once |
| `max_per_week` | integer | No | Max procedures per week |
| `max_per_academic_year` | integer | No | Max procedures per year |
| `notes` | string | No | Additional notes |

**Response:** `201 Created` - Returns `CredentialResponse`

---

### Update Credential

```http
PUT /api/credentials/{credential_id}
```

Update an existing credential. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `credential_id` | UUID | Credential's ID |

**Request Body:** Same fields as create, all optional.

**Response:** `200 OK` - Returns `CredentialResponse`

---

### Delete Credential

```http
DELETE /api/credentials/{credential_id}
```

Delete a credential. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `credential_id` | UUID | Credential's ID |

**Response:** `204 No Content`

---

### Suspend Credential

```http
POST /api/credentials/{credential_id}/suspend
```

Suspend a credential. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `credential_id` | UUID | Credential's ID |

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notes` | string | Suspension reason/notes |

**Response:** `200 OK` - Returns `CredentialResponse` with `status: "suspended"`

---

### Activate Credential

```http
POST /api/credentials/{credential_id}/activate
```

Activate a credential (from suspended/pending). **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `credential_id` | UUID | Credential's ID |

**Response:** `200 OK` - Returns `CredentialResponse` with `status: "active"`

---

### Verify Credential

```http
POST /api/credentials/{credential_id}/verify
```

Mark a credential as verified today. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `credential_id` | UUID | Credential's ID |

**Response:** `200 OK` - Returns `CredentialResponse` with updated `last_verified_date`

---

## Schemas

### CredentialResponse

```json
{
  "id": "uuid",
  "person_id": "uuid",
  "procedure_id": "uuid",
  "status": "active",
  "competency_level": "qualified",
  "issued_date": "2024-01-15",
  "expiration_date": "2026-01-15",
  "last_verified_date": "2024-06-15",
  "max_concurrent_residents": 2,
  "max_per_week": 10,
  "max_per_academic_year": 200,
  "notes": "string",
  "is_valid": true,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-06-15T14:30:00Z"
}
```

### Status Values

| Status | Description |
|--------|-------------|
| `active` | Credential is valid and can be used |
| `expired` | Credential has passed its expiration date |
| `suspended` | Credential is temporarily disabled |
| `pending` | Credential is awaiting approval/verification |

### Competency Levels

| Level | Description |
|-------|-------------|
| `trainee` | Still learning, requires additional supervision |
| `qualified` | Fully qualified to supervise independently |
| `expert` | Advanced expertise, can train others |
| `master` | Highest level, program lead for procedure |

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| `400` | Invalid request (validation error) |
| `401` | Authentication required |
| `403` | Insufficient permissions |
| `404` | Credential/person/procedure not found |
| `409` | Conflict (e.g., duplicate credential) |

---

## Related Endpoints

- [Procedures API](./procedures.md) - Manage procedure definitions
- [Certifications API](./certifications.md) - Personal certifications (BLS, ACLS)
- [People API](./people.md) - Faculty and resident management
