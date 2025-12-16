# Certifications API

> **Last Updated:** 2025-12-16

Endpoints for managing personnel certifications (BLS, ACLS, PALS, etc.) with expiration tracking and compliance monitoring.

## Overview

The certifications system tracks required professional certifications for all personnel:
- **Certification Types**: Define what certifications exist (BLS, ACLS, PALS)
- **Person Certifications**: Track individual certification records
- **Expiration Alerts**: Automatic tracking of upcoming expirations
- **Compliance Reports**: Program-wide compliance monitoring

## Base URL

```
/api/certifications
```

---

## Certification Type Endpoints

### List Certification Types

```http
GET /api/certifications/types
```

List all certification types (BLS, ACLS, PALS, etc.).

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | true | Only show active certification types |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "BLS",
      "description": "Basic Life Support",
      "validity_months": 24,
      "is_required": true,
      "required_for_types": ["resident", "faculty"],
      "is_active": true
    }
  ],
  "total": 1
}
```

---

### Get Certification Type

```http
GET /api/certifications/types/{cert_type_id}
```

Get a certification type by ID.

**Response:** `200 OK` - Returns `CertificationTypeResponse`

---

### Create Certification Type

```http
POST /api/certifications/types
```

Create a new certification type. **Requires authentication.**

**Request Body:**

```json
{
  "name": "ACLS",
  "description": "Advanced Cardiac Life Support",
  "validity_months": 24,
  "is_required": true,
  "required_for_types": ["resident", "faculty"]
}
```

**Response:** `201 Created` - Returns `CertificationTypeResponse`

---

### Update Certification Type

```http
PUT /api/certifications/types/{cert_type_id}
```

Update a certification type. **Requires authentication.**

**Response:** `200 OK` - Returns `CertificationTypeResponse`

---

## Expiration & Compliance Endpoints

### Get Expiring Certifications

```http
GET /api/certifications/expiring
```

Get all certifications expiring within N days.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 180 | Days to look ahead (default 6 months) |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": "uuid",
      "person_id": "uuid",
      "person_name": "Dr. Smith",
      "certification_type_id": "uuid",
      "certification_name": "BLS",
      "expiration_date": "2025-02-15",
      "days_until_expiration": 60,
      "status": "expiring_soon"
    }
  ],
  "total": 5,
  "by_timeframe": {
    "30_days": 2,
    "60_days": 3,
    "90_days": 4,
    "180_days": 5
  }
}
```

---

### Get Compliance Summary

```http
GET /api/certifications/compliance
```

Get overall certification compliance summary for the program.

**Response:** `200 OK`

```json
{
  "total_personnel": 50,
  "fully_compliant": 45,
  "missing_required": 3,
  "expired": 2,
  "expiring_soon": 5,
  "compliance_rate": 90.0,
  "by_certification_type": [
    {
      "name": "BLS",
      "compliant": 48,
      "non_compliant": 2,
      "compliance_rate": 96.0
    }
  ]
}
```

---

### Get Person Compliance

```http
GET /api/certifications/compliance/{person_id}
```

Get certification compliance for a specific person.

**Response:** `200 OK`

```json
{
  "person_id": "uuid",
  "person_name": "Dr. Smith",
  "is_compliant": true,
  "certifications": [
    {
      "type_name": "BLS",
      "is_required": true,
      "status": "current",
      "expiration_date": "2025-06-15"
    }
  ],
  "missing_required": [],
  "expired": []
}
```

---

## Person Certification Endpoints

### List Certifications for Person

```http
GET /api/certifications/by-person/{person_id}
```

List all certifications for a specific person.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_expired` | boolean | true | Include expired certifications |

**Response:** `200 OK` - Returns `PersonCertificationListResponse`

---

### Get Person Certification

```http
GET /api/certifications/{cert_id}
```

Get a specific person certification by ID.

**Response:** `200 OK` - Returns `PersonCertificationResponse`

---

### Create Person Certification

```http
POST /api/certifications
```

Add a certification for a person. **Requires authentication.**

**Request Body:**

```json
{
  "person_id": "uuid",
  "certification_type_id": "uuid",
  "certification_number": "BLS-123456",
  "issued_date": "2024-01-15",
  "expiration_date": "2026-01-15",
  "issuing_organization": "American Heart Association"
}
```

**Response:** `201 Created` - Returns `PersonCertificationResponse`

---

### Update Person Certification

```http
PUT /api/certifications/{cert_id}
```

Update a person's certification. **Requires authentication.**

**Response:** `200 OK` - Returns `PersonCertificationResponse`

---

### Renew Certification

```http
POST /api/certifications/{cert_id}/renew
```

Renew a certification with new dates. **Requires authentication.**

**Request Body:**

```json
{
  "new_issued_date": "2025-01-15",
  "new_expiration_date": "2027-01-15",
  "new_certification_number": "BLS-789012"
}
```

**Response:** `200 OK` - Returns `PersonCertificationResponse`

---

### Delete Person Certification

```http
DELETE /api/certifications/{cert_id}
```

Delete a person's certification. **Requires authentication.**

**Response:** `204 No Content`

---

## Admin Endpoints

### Trigger Certification Reminders

```http
POST /api/certifications/admin/send-reminders
```

Manually trigger certification expiration check and send reminders. **Requires authentication.**

This runs the same job that normally runs daily at 6 AM.

**Response:** `200 OK`

```json
{
  "status": "success",
  "statuses_updated": 5,
  "expiring_count": 10,
  "expired_count": 2,
  "message": "Certification check completed. Email reminders require SMTP configuration."
}
```

---

## Schemas

### PersonCertificationResponse

```json
{
  "id": "uuid",
  "person_id": "uuid",
  "certification_type_id": "uuid",
  "certification_number": "BLS-123456",
  "issued_date": "2024-01-15",
  "expiration_date": "2026-01-15",
  "issuing_organization": "American Heart Association",
  "status": "current",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Status Values

| Status | Description |
|--------|-------------|
| `current` | Valid and not expiring soon |
| `expiring_soon` | Expiring within warning period |
| `expired` | Past expiration date |

---

## Error Responses

| Status Code | Description |
|-------------|-------------|
| `400` | Invalid request (validation error) |
| `401` | Authentication required |
| `403` | Insufficient permissions |
| `404` | Certification not found |
| `409` | Conflict (e.g., duplicate certification) |

---

## Related Endpoints

- [Credentials API](./credentials.md) - Procedure-specific credentials
- [Procedures API](./procedures.md) - Medical procedures
- [People API](./people.md) - Personnel management
