# Certifications API

The Certifications API provides endpoints for managing personnel certifications (BLS, ACLS, PALS, N95 Fit Testing, etc.) with expiration tracking, compliance monitoring, and automated reminder workflows.

## Base URL

```
/certifications
```

## Endpoints Overview

| Endpoint | Method | Purpose | Authentication |
|----------|--------|---------|----------------|
| **Certification Types** ||||
| `/certifications/types` | GET | List certification types | No |
| `/certifications/types/{cert_type_id}` | GET | Get certification type | No |
| `/certifications/types` | POST | Create certification type | Required |
| `/certifications/types/{cert_type_id}` | PUT | Update certification type | Required |
| **Person Certifications** ||||
| `/certifications/by-person/{person_id}` | GET | List person's certifications | No |
| `/certifications/{cert_id}` | GET | Get certification | No |
| `/certifications` | POST | Create certification | Required |
| `/certifications/{cert_id}` | PUT | Update certification | Required |
| `/certifications/{cert_id}/renew` | POST | Renew certification | Required |
| `/certifications/{cert_id}` | DELETE | Delete certification | Required |
| **Compliance & Expiration** ||||
| `/certifications/expiring` | GET | Get expiring certifications | No |
| `/certifications/compliance` | GET | Overall compliance summary | No |
| `/certifications/compliance/{person_id}` | GET | Person compliance status | No |
| **Admin** ||||
| `/certifications/admin/send-reminders` | POST | Trigger reminder emails | Admin only |

---

## Certification Type Endpoints

### List Certification Types

**Purpose:** Get all certification types (BLS, ACLS, PALS, etc.) with their requirements.

```http
GET /certifications/types?active_only=true
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | true | Only show active certification types |

#### Response

**Status:** 200 OK

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "BLS",
      "full_name": "Basic Life Support",
      "description": "AHA Basic Life Support for Healthcare Providers",
      "renewal_period_months": 24,
      "required_for_residents": true,
      "required_for_faculty": true,
      "required_for_specialties": null,
      "reminder_days_180": true,
      "reminder_days_90": true,
      "reminder_days_30": true,
      "reminder_days_14": true,
      "reminder_days_7": true,
      "is_active": true,
      "created_at": "2024-01-01T10:00:00.000000",
      "updated_at": "2024-01-01T10:00:00.000000"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "ACLS",
      "full_name": "Advanced Cardiovascular Life Support",
      "description": "AHA Advanced Cardiovascular Life Support",
      "renewal_period_months": 24,
      "required_for_residents": true,
      "required_for_faculty": true,
      "required_for_specialties": "Cardiology,Emergency Medicine,Internal Medicine",
      "reminder_days_180": true,
      "reminder_days_90": true,
      "reminder_days_30": true,
      "reminder_days_14": false,
      "reminder_days_7": false,
      "is_active": true,
      "created_at": "2024-01-01T10:00:00.000000",
      "updated_at": "2024-01-01T10:00:00.000000"
    }
  ],
  "total": 2
}
```

**Schema:** `CertificationTypeListResponse`

#### Common Certification Types

| Type | Full Name | Renewal Period |
|------|-----------|----------------|
| BLS | Basic Life Support | 24 months |
| ACLS | Advanced Cardiovascular Life Support | 24 months |
| PALS | Pediatric Advanced Life Support | 24 months |
| NRP | Neonatal Resuscitation Program | 24 months |
| N95_FIT | N95 Respirator Fit Test | 12 months |
| HIPAA | HIPAA Training | 12 months |
| BBP | Bloodborne Pathogens Training | 12 months |

---

### Get Certification Type

**Purpose:** Get details of a specific certification type.

```http
GET /certifications/types/{cert_type_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `cert_type_id` | UUID | Certification type UUID |

#### Response

**Status:** 200 OK

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "BLS",
  "full_name": "Basic Life Support",
  "description": "AHA Basic Life Support for Healthcare Providers",
  "renewal_period_months": 24,
  "required_for_residents": true,
  "required_for_faculty": true,
  "required_for_specialties": null,
  "reminder_days_180": true,
  "reminder_days_90": true,
  "reminder_days_30": true,
  "reminder_days_14": true,
  "reminder_days_7": true,
  "is_active": true,
  "created_at": "2024-01-01T10:00:00.000000",
  "updated_at": "2024-01-01T10:00:00.000000"
}
```

**Schema:** `CertificationTypeResponse`

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Certification type not found"
}
```

---

### Create Certification Type

**Purpose:** Create a new certification type.

```http
POST /certifications/types
```

**Authentication:** Required (JWT)

#### Request Body

```json
{
  "name": "BLS",
  "full_name": "Basic Life Support",
  "description": "AHA Basic Life Support for Healthcare Providers",
  "renewal_period_months": 24,
  "required_for_residents": true,
  "required_for_faculty": true,
  "required_for_specialties": null,
  "reminder_days_180": true,
  "reminder_days_90": true,
  "reminder_days_30": true,
  "reminder_days_14": true,
  "reminder_days_7": true,
  "is_active": true
}
```

**Schema:** `CertificationTypeCreate`

#### Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | 1-100 chars | Short name (e.g., "BLS") |
| `full_name` | string | No | 1-200 chars | Full certification name |
| `description` | string | No | 1-1000 chars | Detailed description |
| `renewal_period_months` | integer | No | 1-120 | Renewal period (default: 24) |
| `required_for_residents` | boolean | No | - | Required for residents (default: true) |
| `required_for_faculty` | boolean | No | - | Required for faculty (default: true) |
| `required_for_specialties` | string | No | 1-500 chars | Comma-separated specialty list |
| `reminder_days_180` | boolean | No | - | Send 180-day reminder (default: true) |
| `reminder_days_90` | boolean | No | - | Send 90-day reminder (default: true) |
| `reminder_days_30` | boolean | No | - | Send 30-day reminder (default: true) |
| `reminder_days_14` | boolean | No | - | Send 14-day reminder (default: true) |
| `reminder_days_7` | boolean | No | - | Send 7-day reminder (default: true) |
| `is_active` | boolean | No | - | Active status (default: true) |

#### Response

**Status:** 201 Created

Same as `CertificationTypeResponse`

---

### Update Certification Type

**Purpose:** Update an existing certification type.

```http
PUT /certifications/types/{cert_type_id}
```

**Authentication:** Required (JWT)

#### Request Body

All fields optional (only include fields to update):

```json
{
  "renewal_period_months": 12,
  "reminder_days_14": false
}
```

**Schema:** `CertificationTypeUpdate`

#### Response

**Status:** 200 OK

Same as `CertificationTypeResponse`

---

## Person Certification Endpoints

### List Certifications for Person

**Purpose:** Get all certifications for a specific person.

```http
GET /certifications/by-person/{person_id}?include_expired=true
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person UUID |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_expired` | boolean | true | Include expired certifications |

#### Response

**Status:** 200 OK

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "person_id": "880e8400-e29b-41d4-a716-446655440003",
      "certification_type_id": "550e8400-e29b-41d4-a716-446655440000",
      "certification_number": "BLS-2024-12345",
      "issued_date": "2024-01-15",
      "expiration_date": "2026-01-15",
      "status": "current",
      "verified_by": "Training Coordinator",
      "verified_date": "2024-01-16",
      "document_url": "https://storage.example.com/certs/bls-12345.pdf",
      "notes": "Completed at AHA Training Center",
      "days_until_expiration": 730,
      "is_expired": false,
      "is_expiring_soon": false,
      "created_at": "2024-01-16T10:00:00.000000",
      "updated_at": "2024-01-16T10:00:00.000000"
    }
  ],
  "total": 1
}
```

**Schema:** `PersonCertificationListResponse`

#### Certification Status Values

| Status | Description | Criteria |
|--------|-------------|----------|
| `current` | Valid certification | > 90 days until expiration |
| `expiring_soon` | Expiring soon | 1-90 days until expiration |
| `expired` | Expired | Expiration date passed |
| `pending` | Awaiting verification | Not yet verified |

---

### Get Person Certification

**Purpose:** Get details of a specific person's certification.

```http
GET /certifications/{cert_id}
```

#### Response

**Status:** 200 OK

Same as individual item in `PersonCertificationListResponse`

**Schema:** `PersonCertificationResponse`

---

### Create Person Certification

**Purpose:** Add a certification for a person.

```http
POST /certifications
```

**Authentication:** Required (JWT)

#### Request Body

```json
{
  "person_id": "880e8400-e29b-41d4-a716-446655440003",
  "certification_type_id": "550e8400-e29b-41d4-a716-446655440000",
  "certification_number": "BLS-2024-12345",
  "issued_date": "2024-01-15",
  "expiration_date": "2026-01-15",
  "status": "current",
  "verified_by": "Training Coordinator",
  "verified_date": "2024-01-16",
  "document_url": "https://storage.example.com/certs/bls-12345.pdf",
  "notes": "Completed at AHA Training Center"
}
```

**Schema:** `PersonCertificationCreate`

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person UUID |
| `certification_type_id` | UUID | Yes | Certification type UUID |
| `certification_number` | string | No | Cert number/ID (max 100 chars) |
| `issued_date` | date | Yes | Date certification was issued |
| `expiration_date` | date | Yes | Date certification expires |
| `status` | string | No | Status (default: "current") |
| `verified_by` | string | No | Person who verified (max 200 chars) |
| `verified_date` | date | No | Date verified |
| `document_url` | string | No | URL to cert document (max 500 chars) |
| `notes` | string | No | Additional notes (max 2000 chars) |

#### Validation Rules

- `expiration_date` must be after `issued_date`
- `status` must be one of: "current", "expiring_soon", "expired", "pending"
- Dates must be within reasonable range (not > 10 years in future)

#### Response

**Status:** 201 Created

Same as `PersonCertificationResponse`

---

### Update Person Certification

**Purpose:** Update an existing certification.

```http
PUT /certifications/{cert_id}
```

**Authentication:** Required (JWT)

#### Request Body

All fields optional:

```json
{
  "status": "expired",
  "notes": "Certification has expired - renewal in progress"
}
```

**Schema:** `PersonCertificationUpdate`

#### Response

**Status:** 200 OK

Same as `PersonCertificationResponse`

---

### Renew Certification

**Purpose:** Renew a certification with new dates (convenience endpoint for renewal workflow).

```http
POST /certifications/{cert_id}/renew
```

**Authentication:** Required (JWT)

#### Request Body

```json
{
  "new_issued_date": "2026-01-15",
  "new_expiration_date": "2028-01-15",
  "new_certification_number": "BLS-2026-67890"
}
```

**Schema:** `RenewalRequest`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_issued_date` | date | Yes | New issue date |
| `new_expiration_date` | date | Yes | New expiration date |
| `new_certification_number` | string | No | New cert number (optional) |

#### Response

**Status:** 200 OK

Returns updated certification with:
- `issued_date` = `new_issued_date`
- `expiration_date` = `new_expiration_date`
- `certification_number` = `new_certification_number` (if provided)
- `status` = "current"
- `days_until_expiration` recalculated

Same as `PersonCertificationResponse`

#### Notes
- Automatically sets status to "current"
- Updates `updated_at` timestamp
- Preserves other fields (verified_by, document_url, notes)

---

### Delete Person Certification

**Purpose:** Delete a person's certification record.

```http
DELETE /certifications/{cert_id}
```

**Authentication:** Required (JWT)

#### Response

**Status:** 204 No Content

---

## Compliance & Expiration Endpoints

### Get Expiring Certifications

**Purpose:** Get all certifications expiring within N days.

```http
GET /certifications/expiring?days=180
```

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 180 | Days to look ahead (default: 6 months) |

#### Response

**Status:** 200 OK

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "person": {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "name": "Dr. Jane Smith",
        "type": "FACULTY",
        "email": "jane.smith@example.com"
      },
      "certification_type": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "BLS",
        "full_name": "Basic Life Support"
      },
      "expiration_date": "2024-03-15",
      "days_until_expiration": 45,
      "status": "expiring_soon"
    }
  ],
  "total": 1,
  "days_threshold": 180
}
```

**Schema:** `ExpiringCertificationsListResponse`

#### Notes
- Sorted by expiration date (soonest first)
- Useful for proactive renewal planning
- Common thresholds: 180 days (6 months), 90 days (3 months), 30 days

---

### Get Compliance Summary

**Purpose:** Get overall certification compliance statistics.

```http
GET /certifications/compliance
```

#### Response

**Status:** 200 OK

```json
{
  "total": 150,
  "current": 120,
  "expiring_soon": 20,
  "expired": 10,
  "compliance_rate": 80.0
}
```

**Schema:** `ComplianceSummaryResponse`

| Field | Description |
|-------|-------------|
| `total` | Total certifications tracked |
| `current` | Valid certifications (> 90 days) |
| `expiring_soon` | Expiring within 90 days |
| `expired` | Expired certifications |
| `compliance_rate` | Percentage current (current / total × 100) |

#### Notes
- Compliance rate target: > 90%
- Use for dashboard widgets and compliance reports

---

### Get Person Compliance

**Purpose:** Get certification compliance status for a specific person.

```http
GET /certifications/compliance/{person_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person UUID |

#### Response

**Status:** 200 OK

```json
{
  "person": {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "name": "Dr. Jane Smith",
    "type": "FACULTY",
    "email": "jane.smith@example.com"
  },
  "total_required": 5,
  "total_current": 4,
  "expired": 1,
  "expiring_soon": 0,
  "missing": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "name": "ACLS",
      "full_name": "Advanced Cardiovascular Life Support"
    }
  ],
  "is_compliant": false
}
```

**Schema:** `PersonComplianceResponse`

#### Compliance Determination

A person is compliant if:
- All required certifications are present
- No certifications are expired
- `is_compliant` = true

#### Notes
- Use for pre-assignment validation (slot-type invariants)
- Flag non-compliant personnel before scheduling

---

## Admin Endpoints

### Trigger Certification Reminders

**Purpose:** Manually run the certification expiration check and send reminder emails.

```http
POST /certifications/admin/send-reminders
```

**Authentication:** Required (Admin role only)

#### Response

**Status:** 200 OK

```json
{
  "status": "success",
  "statuses_updated": 15,
  "expiring_count": 25,
  "expired_count": 5,
  "message": "Certification check completed. Email reminders require SMTP configuration."
}
```

#### What This Does

1. Updates all certification statuses based on expiration dates
2. Identifies certifications expiring in 180, 90, 30, 14, 7 days
3. Sends email reminders (if SMTP is configured)
4. Returns counts of updated statuses

#### Notes
- This job normally runs automatically daily at 6:00 AM
- Use this endpoint to trigger manually for testing or urgent updates
- Requires admin role to prevent unauthorized access

---

## Common Workflows

### Onboarding New Personnel

```bash
# 1. Create person (via /persons API)

# 2. Add required certifications
POST /certifications
{
  "person_id": "{person_id}",
  "certification_type_id": "{bls_type_id}",
  "issued_date": "2024-01-15",
  "expiration_date": "2026-01-15"
}

# 3. Verify compliance
GET /certifications/compliance/{person_id}
```

### Renewal Process

```bash
# 1. Identify expiring certifications
GET /certifications/expiring?days=90

# 2. Notify person to renew

# 3. After renewal, update certification
POST /certifications/{cert_id}/renew
{
  "new_issued_date": "2024-01-15",
  "new_expiration_date": "2026-01-15",
  "new_certification_number": "BLS-2024-67890"
}
```

### Compliance Audit

```bash
# 1. Get overall compliance
GET /certifications/compliance

# 2. Identify non-compliant personnel
GET /certifications/expiring?days=0  # Expired only

# 3. Review individual compliance
GET /certifications/compliance/{person_id}
```

### Dashboard Widget Data

```bash
# Get data for certification dashboard
GET /certifications/compliance          # Overall stats
GET /certifications/expiring?days=30    # Urgent renewals
GET /certifications/expiring?days=90    # Planning renewals
```

---

## Reminder Email Schedule

When SMTP is configured, the system sends automatic reminders:

| Days Until Expiration | Email Sent | Configurable |
|----------------------|------------|--------------|
| 180 days (6 months) | Yes | `reminder_days_180` |
| 90 days (3 months) | Yes | `reminder_days_90` |
| 30 days (1 month) | Yes | `reminder_days_30` |
| 14 days (2 weeks) | Yes | `reminder_days_14` |
| 7 days (1 week) | Yes | `reminder_days_7` |

Configure per certification type using the reminder flags.

---

## Integration with Scheduling

### Slot-Type Invariants

Certifications integrate with the scheduling system via **slot-type invariants**:

```python
# Example: Inpatient call requires valid certifications
invariant_catalog = {
    "inpatient_call": {
        "hard": ["BLS", "ACLS", "N95_Fit"],
        "soft": [{"name": "expiring_soon", "window_days": 14}]
    }
}
```

**Hard Constraints:** Person cannot be assigned if certifications are missing/expired

**Soft Constraints:** Warning if certifications expiring soon (penalty applied in solver)

### Pre-Assignment Validation

Before creating an assignment:
```bash
# Check person is compliant for slot type
GET /certifications/compliance/{person_id}

# Verify no hard constraint failures
# Proceed with assignment if is_compliant = true
```

---

## Error Codes Summary

| Status | Error | Common Cause |
|--------|-------|--------------|
| 400 | Bad Request | expiration_date before issued_date |
| 401 | Unauthorized | Missing/invalid JWT |
| 403 | Forbidden | Admin endpoint, non-admin user |
| 404 | Not Found | Certification or person not found |
| 422 | Validation Error | Invalid date format, status value |

---

## Related Documentation

- `backend/app/api/routes/certifications.py` - Implementation
- `backend/app/controllers/certification_controller.py` - Business logic
- `backend/app/services/certification_service.py` - Service layer
- `backend/app/schemas/certification.py` - Request/response schemas
- `docs/architecture/SLOT_TYPE_INVARIANTS.md` - Slot-type certification requirements
- `CLAUDE.md` - Slot-type invariants section
