# Request and Response Schemas

This document provides detailed schema definitions for all API requests and responses.

## Common Data Types

| Type | Format | Example |
|------|--------|---------|
| UUID | UUID v4 | `550e8400-e29b-41d4-a716-446655440000` |
| Date | ISO 8601 | `2024-01-15` |
| DateTime | ISO 8601 with TZ | `2024-01-15T10:30:00Z` |
| Boolean | JSON boolean | `true` / `false` |
| Integer | JSON number | `42` |
| String | JSON string | `"example"` |

## Authentication Schemas

### UserLogin

Login request body.

```json
{
  "username": "string",
  "password": "string"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | User's username |
| `password` | string | Yes | User's password |

### UserCreate

User registration request body.

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "admin|coordinator|faculty"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Valid email address (unique) |
| `password` | string | Yes | User password |
| `role` | string | No | User role (default: `coordinator`) |

### Token

Authentication response.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT access token |
| `token_type` | string | Token type (always `bearer`) |

### UserResponse

User information response.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "email": "john.doe@hospital.org",
  "role": "coordinator",
  "is_active": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | User's unique identifier |
| `username` | string | Username |
| `email` | string | Email address |
| `role` | string | User role |
| `is_active` | boolean | Account active status |

## Person Schemas

### PersonCreate

Create person request body.

```json
{
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@hospital.org",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": ["Sports Medicine"],
  "primary_duty": null
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | Max 255 characters |
| `type` | string | Yes | `resident` or `faculty` |
| `email` | string | No | Valid email format |
| `pgy_level` | integer | Yes (residents) | 1, 2, or 3 |
| `performs_procedures` | boolean | No | Default: `false` |
| `specialties` | string[] | No | Array of specialty names |
| `primary_duty` | string | No | Primary duty assignment |

### PersonUpdate

Update person request body (all fields optional).

```json
{
  "name": "Dr. Jane Smith-Jones",
  "email": "jane.jones@hospital.org",
  "pgy_level": 3,
  "performs_procedures": true
}
```

### PersonResponse

Person response object.

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@hospital.org",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Person's unique identifier |
| `name` | string | Full name |
| `type` | string | `resident` or `faculty` |
| `email` | string | Email address |
| `pgy_level` | integer | PGY level (residents only) |
| `performs_procedures` | boolean | Can perform procedures |
| `specialties` | string[] | List of specialties |
| `primary_duty` | string | Primary duty assignment |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

### PersonListResponse

List of persons response.

```json
{
  "items": [
    {
      "id": "...",
      "name": "Dr. Jane Smith",
      "type": "resident",
      ...
    }
  ],
  "total": 24
}
```

## Block Schemas

### BlockCreate

Create block request body.

```json
{
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 5,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `date` | date | Yes | YYYY-MM-DD format |
| `time_of_day` | string | Yes | `AM` or `PM` |
| `block_number` | integer | Yes | Academic block number |
| `is_weekend` | boolean | No | Default: `false` |
| `is_holiday` | boolean | No | Default: `false` |
| `holiday_name` | string | No | Holiday name if applicable |

### BlockResponse

Block response object.

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "date": "2024-01-15",
  "time_of_day": "AM",
  "block_number": 5,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

### BlockGenerateParams

Parameters for bulk block generation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Start date (YYYY-MM-DD) |
| `end_date` | date | Yes | End date (YYYY-MM-DD) |
| `base_block_number` | integer | No | Starting block number (default: 1) |

## Rotation Template Schemas

### RotationTemplateCreate

Create rotation template request body.

```json
{
  "name": "Sports Medicine Clinic",
  "activity_type": "clinic",
  "abbreviation": "SM",
  "clinic_location": "Building A, Room 102",
  "max_residents": 4,
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique template name |
| `activity_type` | string | Yes | `clinic`, `inpatient`, `procedure`, `conference` |
| `abbreviation` | string | No | Short code (max 10 chars) |
| `clinic_location` | string | No | Physical location |
| `max_residents` | integer | No | Max residents per session |
| `requires_specialty` | string | No | Required faculty specialty |
| `requires_procedure_credential` | boolean | No | Default: `false` |
| `supervision_required` | boolean | No | Default: `true` |
| `max_supervision_ratio` | integer | No | Default: 4 (1:4 ratio) |

### RotationTemplateResponse

Rotation template response object.

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "name": "Sports Medicine Clinic",
  "activity_type": "clinic",
  "abbreviation": "SM",
  "clinic_location": "Building A, Room 102",
  "max_residents": 4,
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Assignment Schemas

### AssignmentCreate

Create assignment request body.

```json
{
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "primary",
  "activity_override": null,
  "notes": "Coverage for Dr. Jones",
  "override_reason": null
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `block_id` | UUID | Yes | Must exist |
| `person_id` | UUID | Yes | Must exist |
| `rotation_template_id` | UUID | No | Template reference |
| `role` | string | Yes | `primary`, `supervising`, `backup` |
| `activity_override` | string | No | Override activity name |
| `notes` | string | No | Assignment notes |
| `override_reason` | string | No | Reason for ACGME override |

### AssignmentUpdate

Update assignment request body.

```json
{
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440001",
  "role": "backup",
  "notes": "Reassigned due to conflict",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Note:** `updated_at` is required for optimistic locking to prevent concurrent modification conflicts.

### AssignmentResponse

Assignment response object.

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "block_id": "660e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "rotation_template_id": "770e8400-e29b-41d4-a716-446655440000",
  "role": "primary",
  "activity_override": null,
  "notes": "Coverage for Dr. Jones",
  "created_by": "coordinator@hospital.org",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "override_acknowledged_at": null
}
```

### AssignmentWithWarnings

Assignment response with ACGME validation.

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "block_id": "...",
  "person_id": "...",
  "role": "primary",
  "acgme_warnings": [
    "Approaching 80-hour limit for this week"
  ],
  "is_compliant": true
}
```

## Absence Schemas

### AbsenceCreate

Create absence request body.

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-15",
  "absence_type": "deployment",
  "deployment_orders": true,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Annual training deployment"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `person_id` | UUID | Yes | Must exist |
| `start_date` | date | Yes | YYYY-MM-DD |
| `end_date` | date | Yes | Must be >= start_date |
| `absence_type` | string | Yes | See valid types below |
| `deployment_orders` | boolean | No | Has deployment orders |
| `tdy_location` | string | No | TDY location |
| `replacement_activity` | string | No | Replacement activity |
| `notes` | string | No | Additional notes |

**Valid Absence Types:**
- `vacation` - Personal vacation time
- `deployment` - Military deployment
- `tdy` - Temporary duty assignment
- `medical` - Medical leave
- `family_emergency` - Family emergency leave
- `conference` - Conference attendance

### AbsenceResponse

Absence response object.

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-15",
  "absence_type": "deployment",
  "deployment_orders": true,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Annual training deployment",
  "created_at": "2024-01-15T00:00:00Z"
}
```

## Schedule Schemas

### ScheduleRequest

Schedule generation request body.

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-06-30",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": ["770e8400-e29b-41d4-a716-446655440000"],
  "algorithm": "greedy",
  "timeout_seconds": 60.0
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `start_date` | date | Yes | YYYY-MM-DD |
| `end_date` | date | Yes | Must be > start_date |
| `pgy_levels` | integer[] | No | Filter by PGY levels [1, 2, 3] |
| `rotation_template_ids` | UUID[] | No | Specific templates |
| `algorithm` | string | No | `greedy`, `cp_sat`, `pulp`, `hybrid` |
| `timeout_seconds` | float | No | 5.0 to 300.0 (default: 60.0) |

### ScheduleResponse

Schedule generation response.

```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 2920,
  "total_blocks": 3650,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 80.0,
    "statistics": {
      "total_assignments": 2920,
      "total_blocks": 3650,
      "residents_scheduled": 24
    }
  },
  "run_id": "aa0e8400-e29b-41d4-a716-446655440000",
  "solver_stats": {
    "total_blocks": 3650,
    "total_residents": 24,
    "coverage_rate": 80.0,
    "branches": 1250,
    "conflicts": 45
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success`, `partial`, `failed` |
| `message` | string | Status message |
| `total_blocks_assigned` | integer | Number of blocks with assignments |
| `total_blocks` | integer | Total blocks in range |
| `validation` | object | ACGME validation results |
| `run_id` | UUID | Schedule generation run ID |
| `solver_stats` | object | Solver performance statistics |

### ValidationResult

ACGME validation response.

```json
{
  "valid": false,
  "total_violations": 2,
  "violations": [
    {
      "type": "80_HOUR_VIOLATION",
      "severity": "CRITICAL",
      "person_id": "550e8400-e29b-41d4-a716-446655440000",
      "person_name": "Dr. Jane Smith",
      "block_id": null,
      "message": "Dr. Jane Smith: 82.5 hours/week (limit: 80)",
      "details": {
        "window_start": "2024-01-01",
        "window_end": "2024-01-28",
        "average_weekly_hours": 82.5
      }
    }
  ],
  "coverage_rate": 95.5,
  "statistics": {
    "total_assignments": 3500,
    "total_blocks": 3650,
    "residents_scheduled": 24
  }
}
```

### Violation

ACGME violation object.

```json
{
  "type": "80_HOUR_VIOLATION",
  "severity": "CRITICAL",
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_name": "Dr. Jane Smith",
  "block_id": null,
  "message": "Dr. Jane Smith: 82.5 hours/week (limit: 80)",
  "details": {
    "window_start": "2024-01-01",
    "window_end": "2024-01-28",
    "average_weekly_hours": 82.5
  }
}
```

**Violation Types:**
| Type | Severity | Description |
|------|----------|-------------|
| `80_HOUR_VIOLATION` | CRITICAL | Exceeds 80-hour weekly limit |
| `1_IN_7_VIOLATION` | HIGH | Missing required day off |
| `SUPERVISION_RATIO_VIOLATION` | CRITICAL | Insufficient supervision |
| `CONSECUTIVE_DUTY_VIOLATION` | HIGH | Too many consecutive days |

### EmergencyRequest

Emergency coverage request body.

```json
{
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-01-20",
  "end_date": "2024-01-25",
  "reason": "Family emergency",
  "is_deployment": false
}
```

### EmergencyResponse

Emergency coverage response.

```json
{
  "status": "partial",
  "replacements_found": 8,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2024-01-20",
      "time_of_day": "AM",
      "original_assignment": "Sports Medicine Clinic",
      "replacement": {
        "person_id": "550e8400-e29b-41d4-a716-446655440002",
        "person_name": "Dr. Bob Wilson"
      },
      "status": "covered"
    }
  ]
}
```

## Settings Schema

### Settings

System settings object.

```json
{
  "scheduling_algorithm": "greedy",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `scheduling_algorithm` | string | `greedy`, `cp_sat`, `pulp` | `greedy` |
| `work_hours_per_week` | integer | 40-100 | 80 |
| `max_consecutive_days` | integer | 1-7 | 6 |
| `min_days_off_per_week` | integer | 1-3 | 1 |
| `pgy1_supervision_ratio` | string | Format: "1:N" | `1:2` |
| `pgy2_supervision_ratio` | string | Format: "1:N" | `1:4` |
| `pgy3_supervision_ratio` | string | Format: "1:N" | `1:4` |
| `enable_weekend_scheduling` | boolean | - | `true` |
| `enable_holiday_scheduling` | boolean | - | `false` |
| `default_block_duration_hours` | integer | 1-12 | 4 |

## Common Response Wrappers

### List Response

All list endpoints return this format:

```json
{
  "items": [...],
  "total": 100
}
```

| Field | Type | Description |
|-------|------|-------------|
| `items` | array | Array of resource objects |
| `total` | integer | Total count of resources |

### Error Response

All errors return this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Response

Validation errors may include field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

---

*See also: [Error Handling](./errors.md) for error response details*
