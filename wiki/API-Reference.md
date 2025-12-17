# API Reference

This document provides a reference for the Residency Scheduler REST API.

---

## Overview

### Base URL

```
Production: https://your-domain.com/api
Development: http://localhost:8000/api
```

### Authentication

All endpoints except `/auth/login` and `/auth/register` require authentication.

Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Response Format

All responses are JSON:

```json
{
  "data": { ... },
  "message": "Success",
  "status": 200
}
```

Error responses:

```json
{
  "detail": "Error description",
  "status": 400
}
```

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Authentication

### Register User

```http
POST /api/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe",
  "role": "admin"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "is_active": true
}
```

### Login

```http
POST /api/auth/login
```

**Request Body (form data):**
```
username=user@example.com
password=secure_password
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /api/auth/me
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "is_active": true
}
```

### Logout

```http
POST /api/auth/logout
```

Invalidates the current token.

---

## People

### List People

```http
GET /api/people
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `role` | string | Filter by role (resident/faculty) |
| `pgy_level` | int | Filter by PGY level |
| `specialty` | string | Filter by specialty |
| `is_active` | bool | Filter by active status |
| `page` | int | Page number (default: 1) |
| `size` | int | Page size (default: 50) |

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "role": "resident",
      "pgy_level": 2,
      "specialty": "Internal Medicine",
      "is_active": true
    }
  ],
  "total": 50,
  "page": 1,
  "size": 50,
  "pages": 1
}
```

### Get Person

```http
GET /api/people/{id}
```

### Create Person

```http
POST /api/people
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "role": "resident",
  "pgy_level": 2,
  "specialty": "Internal Medicine"
}
```

### Update Person

```http
PUT /api/people/{id}
```

### Delete Person

```http
DELETE /api/people/{id}
```

### Get Residents

```http
GET /api/people/residents
```

Returns only residents.

### Get Faculty

```http
GET /api/people/faculty
```

Returns only faculty members.

---

## Schedule

### Generate Schedule

```http
POST /api/schedule/generate
```

**Request Body:**
```json
{
  "start_date": "2025-07-01",
  "end_date": "2026-06-30",
  "algorithm": "hybrid",
  "options": {
    "prioritize_fairness": true,
    "respect_preferences": true
  }
}
```

**Response:**
```json
{
  "schedule_run_id": 123,
  "status": "processing",
  "message": "Schedule generation started"
}
```

### Get Schedule Status

```http
GET /api/schedule/status/{schedule_run_id}
```

**Response:**
```json
{
  "id": 123,
  "status": "completed",
  "created_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:35:00Z",
  "total_assignments": 730,
  "violations_count": 0
}
```

### Validate Schedule

```http
POST /api/schedule/validate
```

Validates ACGME compliance for a schedule.

**Request Body:**
```json
{
  "schedule_run_id": 123
}
```

**Response:**
```json
{
  "is_valid": true,
  "violations": [],
  "warnings": [
    {
      "type": "preference_conflict",
      "person_id": 5,
      "message": "Assignment conflicts with stated preference"
    }
  ]
}
```

### Emergency Coverage

```http
POST /api/schedule/emergency-coverage
```

**Request Body:**
```json
{
  "assignment_id": 456,
  "reason": "medical_emergency",
  "notes": "Resident hospitalized"
}
```

**Response:**
```json
{
  "suggested_replacements": [
    {
      "person_id": 7,
      "person_name": "Jane Smith",
      "availability_score": 0.95,
      "workload_impact": "minimal"
    }
  ]
}
```

---

## Assignments

### List Assignments

```http
GET /api/assignments
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | int | Filter by person |
| `block_id` | int | Filter by block |
| `date` | date | Filter by date |
| `start_date` | date | Filter range start |
| `end_date` | date | Filter range end |
| `template_id` | int | Filter by rotation template |

### Get Assignment

```http
GET /api/assignments/{id}
```

### Create Assignment

```http
POST /api/assignments
```

**Request Body:**
```json
{
  "person_id": 1,
  "block_id": 100,
  "template_id": 5,
  "notes": "Additional notes"
}
```

### Update Assignment

```http
PUT /api/assignments/{id}
```

### Delete Assignment

```http
DELETE /api/assignments/{id}
```

---

## Blocks

### List Blocks

```http
GET /api/blocks
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | date | Filter by start date |
| `end_date` | date | Filter by end date |
| `session` | string | AM or PM |

### Get Block

```http
GET /api/blocks/{id}
```

### Get Academic Blocks

```http
GET /api/blocks/academic
```

Returns blocks for the current academic year.

---

## Absences

### List Absences

```http
GET /api/absences
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | int | Filter by person |
| `type` | string | Filter by absence type |
| `start_date` | date | Filter by start date |
| `end_date` | date | Filter by end date |

### Get Absence

```http
GET /api/absences/{id}
```

### Create Absence

```http
POST /api/absences
```

**Request Body:**
```json
{
  "person_id": 1,
  "absence_type": "vacation",
  "start_date": "2025-03-01",
  "end_date": "2025-03-07",
  "notes": "Spring break"
}
```

**Absence Types:**
- `vacation`
- `medical`
- `deployment`
- `tdy`
- `conference`
- `family_emergency`
- `bereavement`

### Update Absence

```http
PUT /api/absences/{id}
```

### Delete Absence

```http
DELETE /api/absences/{id}
```

---

## Rotation Templates

### List Templates

```http
GET /api/rotation-templates
```

### Get Template

```http
GET /api/rotation-templates/{id}
```

### Create Template

```http
POST /api/rotation-templates
```

**Request Body:**
```json
{
  "name": "ICU Rotation",
  "type": "clinical",
  "duration_blocks": 14,
  "capacity": 4,
  "min_pgy_level": 2,
  "supervision_ratio": 0.25,
  "description": "Intensive care unit rotation"
}
```

### Update Template

```http
PUT /api/rotation-templates/{id}
```

### Delete Template

```http
DELETE /api/rotation-templates/{id}
```

---

## Swaps

### List Swaps

```http
GET /api/swaps
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `requester_id` | int | Filter by requester |

### Get Swap

```http
GET /api/swaps/{id}
```

### Request Swap

```http
POST /api/swaps/request
```

**Request Body:**
```json
{
  "assignment_id": 456,
  "preferred_dates": ["2025-03-15", "2025-03-16"],
  "notes": "Need to attend family event"
}
```

### Auto-Match Swaps

```http
POST /api/swaps/auto-match
```

Triggers the automatic swap matching algorithm.

**Request Body:**
```json
{
  "swap_request_id": 789
}
```

**Response:**
```json
{
  "matches": [
    {
      "potential_swap_id": 790,
      "match_score": 0.87,
      "factors": {
        "availability": 1.0,
        "preferences": 0.8,
        "specialization": 0.9,
        "pgy_balance": 0.85,
        "coverage_impact": 0.8
      }
    }
  ]
}
```

### Accept Swap

```http
POST /api/swaps/{id}/accept
```

### Decline Swap

```http
POST /api/swaps/{id}/decline
```

### Cancel Swap

```http
POST /api/swaps/{id}/cancel
```

---

## Compliance

### Get Violations

```http
GET /api/compliance/violations
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | int | Filter by person |
| `severity` | string | Filter by severity |
| `rule_type` | string | Filter by rule type |
| `resolved` | bool | Filter by resolution status |

**Response:**
```json
{
  "violations": [
    {
      "id": 1,
      "person_id": 5,
      "person_name": "John Doe",
      "rule_type": "80_hour",
      "severity": "critical",
      "message": "Exceeded 80-hour weekly limit",
      "week_hours": 85.5,
      "created_at": "2025-01-15T08:00:00Z",
      "resolved": false
    }
  ],
  "summary": {
    "total": 5,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 1
  }
}
```

### Monitor Compliance

```http
GET /api/compliance/monitor
```

Real-time compliance status.

**Response:**
```json
{
  "overall_score": 0.95,
  "status": "compliant",
  "metrics": {
    "80_hour_compliance": 0.98,
    "1_in_7_compliance": 1.0,
    "supervision_compliance": 0.92
  },
  "active_violations": 3
}
```

---

## Conflicts

### List Conflicts

```http
GET /api/conflicts
```

### Auto-Resolve Conflicts

```http
POST /api/conflicts/auto-resolve
```

**Request Body:**
```json
{
  "conflict_ids": [1, 2, 3],
  "strategy": "coverage_prioritized"
}
```

**Strategies:**
- `preference_based`
- `coverage_prioritized`
- `fairness_optimized`
- `minimum_displacement`
- `escalate_to_admin`

---

## Analytics

### Coverage Analytics

```http
GET /api/analytics/coverage
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `start_date` | date | Period start |
| `end_date` | date | Period end |

### Fairness Analytics

```http
GET /api/analytics/fairness
```

**Response:**
```json
{
  "gini_coefficient": 0.12,
  "variance": 2.5,
  "distribution": {
    "person_1": 45,
    "person_2": 47,
    "person_3": 43
  }
}
```

### Workload Analytics

```http
GET /api/analytics/workload
```

---

## Calendar

The Calendar API provides ICS file export and WebCal subscription functionality for integrating schedules with external calendar applications (Google Calendar, Microsoft Outlook, Apple Calendar).

### ICS Export Endpoints

#### Export All Schedules

```http
GET /api/calendar/export/ics
```

Export complete schedule as ICS file with optional filters.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Export range start (YYYY-MM-DD) |
| `end_date` | date | Yes | Export range end (YYYY-MM-DD) |
| `person_ids` | list[UUID] | No | Filter by specific people |
| `rotation_ids` | list[UUID] | No | Filter by specific rotations |
| `include_types` | list[string] | No | Filter by activity types (clinical, administrative, call) |

**Response:** ICS file download (`text/calendar`)

**Example:**
```http
GET /api/calendar/export/ics?start_date=2025-01-01&end_date=2025-06-30&include_types=clinical
```

#### Export Person Schedule

```http
GET /api/calendar/export/ics/{person_id}
GET /api/calendar/export/person/{person_id}
```

Export individual's schedule as ICS file.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | UUID | Person UUID |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Export range start |
| `end_date` | date | Yes | Export range end |
| `include_types` | list[string] | No | Filter by activity types |

**Response:** ICS file download

#### Export Rotation Schedule

```http
GET /api/calendar/export/rotation/{rotation_id}
```

Export all assignments for a rotation.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `rotation_id` | UUID | Rotation template UUID |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Export range start |
| `end_date` | date | Yes | Export range end |

### WebCal Subscription Endpoints

WebCal subscriptions provide live-updating calendar feeds that calendar applications can subscribe to.

#### Create Subscription

```http
POST /api/calendar/subscribe
```

Create a secure webcal subscription URL. **Requires authentication.**

**Request Body:**
```json
{
  "person_id": "123e4567-e89b-12d3-a456-426614174000",
  "label": "My Work Calendar",
  "expires_days": 365
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Person to subscribe to |
| `label` | string | No | Friendly label for the subscription |
| `expires_days` | int | No | Days until subscription expires (null = never) |

**Response:**
```json
{
  "token": "abc123def456...",
  "subscription_url": "https://domain.com/api/calendar/subscribe/abc123...",
  "webcal_url": "webcal://domain.com/api/calendar/subscribe/abc123...",
  "person_id": "123e4567-e89b-12d3-a456-426614174000",
  "label": "My Work Calendar",
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2026-01-15T10:30:00Z",
  "last_accessed_at": null,
  "is_active": true
}
```

#### Get Calendar Feed

```http
GET /api/calendar/subscribe/{token}
```

Retrieve the ICS calendar feed. **No authentication required** - the token serves as authentication. This is the endpoint calendar apps poll for updates.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `token` | string | Subscription token |

**Response:** ICS calendar content with:
- Assignments from today through 6 months ahead
- VTIMEZONE component for America/New_York
- Cache-Control: private, max-age=900 (15-minute refresh)

**Calendar App Integration:**
- **Google Calendar:** Settings → Add calendar → From URL → paste `webcal://` URL
- **Apple Calendar:** File → New Calendar Subscription → paste URL
- **Outlook:** Add calendar → From Internet → paste URL

#### List Subscriptions

```http
GET /api/calendar/subscriptions
```

List all subscriptions created by the current user. **Requires authentication.**

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `person_id` | UUID | None | Filter by person |
| `active_only` | bool | true | Only return active subscriptions |

**Response:**
```json
{
  "subscriptions": [
    {
      "token": "abc123...",
      "subscription_url": "https://...",
      "webcal_url": "webcal://...",
      "person_id": "...",
      "label": "My Calendar",
      "created_at": "2025-01-15T10:30:00Z",
      "expires_at": null,
      "last_accessed_at": "2025-01-16T08:00:00Z",
      "is_active": true
    }
  ],
  "total": 1
}
```

#### Revoke Subscription

```http
DELETE /api/calendar/subscribe/{token}
```

Permanently disable a subscription token. **Requires authentication.**

**Response:**
```json
{
  "success": true,
  "message": "Subscription revoked successfully"
}
```

### ICS File Format

Generated ICS files comply with RFC 5545 and include:

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Residency Scheduler//Calendar Export//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:John Doe - Schedule
X-WR-TIMEZONE:America/New_York
BEGIN:VTIMEZONE
TZID:America/New_York
...
END:VTIMEZONE
BEGIN:VEVENT
UID:assignment-uuid@residency-scheduler
DTSTART:20250115T080000
DTEND:20250115T120000
SUMMARY:ICU Rotation (Primary)
LOCATION:Building A, Room 101
DESCRIPTION:Role: Primary\nBlock: Week 1 AM\nType: Clinical
END:VEVENT
END:VCALENDAR
```

**Block Time Mapping:**
| Block | Start | End |
|-------|-------|-----|
| AM | 8:00 AM | 12:00 PM |
| PM | 1:00 PM | 5:00 PM |

**Role Modifiers in SUMMARY:**
- Primary: `Activity Name`
- Supervising: `Activity Name (Supervising)`
- Backup: `Activity Name (Backup)`

---

## Export

### Export to Excel

```http
GET /api/export/excel
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | schedule, people, absences |
| `start_date` | date | Export range start |
| `end_date` | date | Export range end |

Returns an Excel file download.

### Export to PDF

```http
GET /api/export/pdf
```

Returns a PDF file download.

---

## Daily Manifest

### Get Today's Manifest

```http
GET /api/daily-manifest
```

### Get Manifest for Date

```http
GET /api/daily-manifest/{date}
```

**Response:**
```json
{
  "date": "2025-01-15",
  "assignments": [
    {
      "id": 100,
      "person_name": "John Doe",
      "rotation": "ICU",
      "session": "AM",
      "supervisor": "Dr. Smith"
    }
  ],
  "absences": [
    {
      "person_name": "Jane Doe",
      "type": "vacation"
    }
  ],
  "coverage_status": "adequate"
}
```

---

## Resilience

### Health Check

```http
GET /api/resilience/health-check
```

**Response:**
```json
{
  "status": "healthy",
  "defense_level": "GREEN",
  "utilization": 0.65,
  "metrics": {
    "coverage_ratio": 0.98,
    "fairness_score": 0.87,
    "stability_index": 0.92
  }
}
```

### Contingency Analysis

```http
GET /api/resilience/contingency
```

Performs N-1/N-2 failure scenario analysis.

### Crisis Mode

```http
POST /api/resilience/crisis
```

Activates crisis management protocols.

---

## Certifications

### List Certifications

```http
GET /api/certifications
```

### Get Expiring Certifications

```http
GET /api/certifications/expiring
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `days` | int | Days until expiration (default: 30) |

### Create Certification

```http
POST /api/certifications
```

**Request Body:**
```json
{
  "person_id": 1,
  "type": "BLS",
  "issue_date": "2024-01-15",
  "expiration_date": "2026-01-15",
  "issuing_body": "American Heart Association"
}
```

---

## Procedures

### List Procedures

```http
GET /api/procedures
```

### Get Procedure Credentials

```http
GET /api/procedures/credentials
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `person_id` | int | Filter by person |
| `procedure_id` | int | Filter by procedure |
| `competency_level` | string | Filter by level |

---

## Audit

### Get Audit Logs

```http
GET /api/audit/logs
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `entity_type` | string | Filter by entity type |
| `entity_id` | int | Filter by entity ID |
| `user_id` | int | Filter by user |
| `action` | string | create, update, delete |
| `start_date` | datetime | Filter by date range |
| `end_date` | datetime | Filter by date range |

### Get Audit Statistics

```http
GET /api/audit/statistics
```

### Export Audit Logs

```http
GET /api/audit/export
```

Returns CSV/Excel file of audit logs.

---

## Health Check

### Basic Health

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Detailed Health

```http
GET /health/ready
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "celery": "running"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Rate Limiting

API requests are rate-limited:

| Endpoint Type | Limit |
|--------------|-------|
| Authentication | 10/minute |
| Read operations | 100/minute |
| Write operations | 30/minute |
| Schedule generation | 5/hour |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642256400
```

---

## Pagination

List endpoints support pagination:

```http
GET /api/people?page=2&size=25
```

**Response includes:**
```json
{
  "items": [...],
  "total": 100,
  "page": 2,
  "size": 25,
  "pages": 4
}
```

---

## Related Documentation

- [Architecture](Architecture) - System design
- [Configuration](Configuration) - Environment setup
- [Development](Development) - Contributing guide
