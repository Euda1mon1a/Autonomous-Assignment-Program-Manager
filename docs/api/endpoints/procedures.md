# Procedures API

> **Last Updated:** 2025-12-16

Endpoints for managing medical procedures that require credentialed supervision.

## Overview

Procedures define medical activities that require faculty supervision, including:
- Complexity levels determining required training
- Minimum PGY level for residents
- Supervision ratios for safety
- Active/inactive status for scheduling

## Base URL

```
/api/procedures
```

---

## Endpoints

### List Procedures

```http
GET /api/procedures
```

List all procedures with optional filters.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `specialty` | string | Filter by specialty (e.g., "Sports Medicine") |
| `category` | string | Filter by category (e.g., "surgical", "office") |
| `is_active` | boolean | Filter by active status |
| `complexity_level` | string | Filter by complexity (`basic`, `standard`, `advanced`, `complex`) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Joint Injection",
      "description": "Intra-articular injection of corticosteroid",
      "category": "office",
      "specialty": "Sports Medicine",
      "supervision_ratio": 2,
      "requires_certification": true,
      "complexity_level": "standard",
      "min_pgy_level": 1,
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Get Specialties

```http
GET /api/procedures/specialties
```

Get all unique specialties from procedures.

**Response:** `200 OK`

```json
["Sports Medicine", "OB/GYN", "Family Medicine", "Internal Medicine"]
```

---

### Get Categories

```http
GET /api/procedures/categories
```

Get all unique categories from procedures.

**Response:** `200 OK`

```json
["surgical", "office", "obstetric", "clinic"]
```

---

### Get Procedure by Name

```http
GET /api/procedures/by-name/{name}
```

Get a procedure by its name.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Procedure name (URL-encoded) |

**Response:** `200 OK` - Returns `ProcedureResponse`

---

### Get Procedure

```http
GET /api/procedures/{procedure_id}
```

Get a procedure by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Response:** `200 OK` - Returns `ProcedureResponse`

---

### Create Procedure

```http
POST /api/procedures
```

Create a new procedure. **Requires authentication.**

**Request Body:**

```json
{
  "name": "Joint Injection",
  "description": "Intra-articular injection of corticosteroid",
  "category": "office",
  "specialty": "Sports Medicine",
  "supervision_ratio": 2,
  "requires_certification": true,
  "complexity_level": "standard",
  "min_pgy_level": 1,
  "is_active": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Unique procedure name |
| `description` | string | No | null | Detailed description |
| `category` | string | No | null | Category (surgical, office, etc.) |
| `specialty` | string | No | null | Medical specialty |
| `supervision_ratio` | integer | No | 1 | Residents per supervisor |
| `requires_certification` | boolean | No | true | Requires credential to supervise |
| `complexity_level` | string | No | standard | Complexity level |
| `min_pgy_level` | integer | No | 1 | Minimum resident year (1-3) |
| `is_active` | boolean | No | true | Available for scheduling |

**Response:** `201 Created` - Returns `ProcedureResponse`

---

### Update Procedure

```http
PUT /api/procedures/{procedure_id}
```

Update an existing procedure. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Request Body:** Same fields as create, all optional.

**Response:** `200 OK` - Returns `ProcedureResponse`

---

### Delete Procedure

```http
DELETE /api/procedures/{procedure_id}
```

Delete a procedure. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Response:** `204 No Content`

---

### Deactivate Procedure

```http
POST /api/procedures/{procedure_id}/deactivate
```

Soft-delete a procedure (mark as inactive). **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Response:** `200 OK` - Returns `ProcedureResponse` with `is_active: false`

---

### Activate Procedure

```http
POST /api/procedures/{procedure_id}/activate
```

Activate a previously deactivated procedure. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `procedure_id` | UUID | Procedure's ID |

**Response:** `200 OK` - Returns `ProcedureResponse` with `is_active: true`

---

## Schemas

### ProcedureResponse

```json
{
  "id": "uuid",
  "name": "Joint Injection",
  "description": "Intra-articular injection of corticosteroid",
  "category": "office",
  "specialty": "Sports Medicine",
  "supervision_ratio": 2,
  "requires_certification": true,
  "complexity_level": "standard",
  "min_pgy_level": 1,
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Complexity Levels

| Level | Description |
|-------|-------------|
| `basic` | Simple procedures, minimal training required |
| `standard` | Standard procedures, typical residency training |
| `advanced` | Complex procedures, additional training needed |
| `complex` | High-risk procedures, extensive experience required |

### Categories

Common procedure categories:
- `surgical` - Operative procedures
- `office` - Office-based procedures
- `obstetric` - Obstetric procedures
- `clinic` - Clinic-based procedures

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| `400` | Invalid request (validation error) |
| `401` | Authentication required |
| `403` | Insufficient permissions |
| `404` | Procedure not found |
| `409` | Conflict (e.g., duplicate name) |

---

## Related Endpoints

- [Credentials API](./credentials.md) - Faculty procedure credentials
- [Certifications API](./certifications.md) - Personal certifications (BLS, ACLS)
- [Rotation Templates](./rotation-templates.md) - Include procedures in rotations
