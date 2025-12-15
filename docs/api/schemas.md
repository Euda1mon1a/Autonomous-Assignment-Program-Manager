# API Schemas Reference

This document provides detailed information about all request and response schemas used in the Residency Scheduler API, including TypeScript type definitions for frontend integration.

## Table of Contents

- [Authentication Schemas](#authentication-schemas)
- [Person Schemas](#person-schemas)
- [Block Schemas](#block-schemas)
- [Rotation Template Schemas](#rotation-template-schemas)
- [Absence Schemas](#absence-schemas)
- [Assignment Schemas](#assignment-schemas)
- [Schedule Schemas](#schedule-schemas)
- [Settings Schemas](#settings-schemas)
- [Common Types](#common-types)

---

## Authentication Schemas

### Token

JWT authentication token response.

**Schema:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**TypeScript:**
```typescript
interface Token {
  access_token: string;
  token_type: string;
}
```

**Fields:**
- `access_token` (string, required) - JWT token for authentication
- `token_type` (string, required) - Always "bearer"

---

### UserLogin

Request schema for JSON-based login.

**Schema:**
```json
{
  "username": "admin",
  "password": "SecurePassword123"
}
```

**TypeScript:**
```typescript
interface UserLogin {
  username: string;
  password: string;
}
```

**Validation:**
- `username` - Required, non-empty string
- `password` - Required, non-empty string

---

### UserCreate

Request schema for creating a new user.

**Schema:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "role": "coordinator"
}
```

**TypeScript:**
```typescript
interface UserCreate {
  username: string;
  email: string; // Must be valid email format
  password: string;
  role?: "admin" | "coordinator" | "faculty"; // Default: "coordinator"
}
```

**Validation:**
- `username` - Required, unique
- `email` - Required, valid email format, unique
- `password` - Required, minimum 8 characters recommended
- `role` - Optional, defaults to "coordinator"

**Roles:**
- `admin` - Full system access
- `coordinator` - Scheduling and management access
- `faculty` - Limited read access (planned)

---

### UserResponse

Response schema for user data (password excluded).

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true
}
```

**TypeScript:**
```typescript
interface UserResponse {
  id: string; // UUID
  username: string;
  email: string;
  role: "admin" | "coordinator" | "faculty";
  is_active: boolean;
}
```

---

## Person Schemas

### PersonCreate

Request schema for creating a person (resident or faculty).

**Resident Example:**
```json
{
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@example.com",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null
}
```

**Faculty Example:**
```json
{
  "name": "Dr. John Doe",
  "type": "faculty",
  "email": "john.doe@example.com",
  "pgy_level": null,
  "performs_procedures": true,
  "specialties": ["cardiology", "internal medicine"],
  "primary_duty": "teaching"
}
```

**TypeScript:**
```typescript
type PersonType = "resident" | "faculty";
type PGYLevel = 1 | 2 | 3;

interface PersonCreate {
  name: string;
  type: PersonType;
  email?: string | null;
  pgy_level?: PGYLevel | null; // Required for residents
  performs_procedures?: boolean; // Default: false
  specialties?: string[] | null;
  primary_duty?: string | null;
}
```

**Validation Rules:**
- `name` - Required, non-empty string
- `type` - Required, must be "resident" or "faculty"
- `email` - Optional, must be valid email format if provided
- `pgy_level` - Required for residents, must be 1, 2, or 3
- `pgy_level` - Not applicable for faculty (should be null)
- `performs_procedures` - Boolean, defaults to false
- `specialties` - Array of specialty names (for faculty)
- `primary_duty` - Free text field

---

### PersonUpdate

Request schema for updating a person.

**Schema:**
```json
{
  "name": "Dr. Jane Smith",
  "email": "jane.newemail@example.com",
  "pgy_level": 3,
  "performs_procedures": true
}
```

**TypeScript:**
```typescript
interface PersonUpdate {
  name?: string;
  email?: string | null;
  pgy_level?: PGYLevel | null;
  performs_procedures?: boolean;
  specialties?: string[] | null;
  primary_duty?: string | null;
}
```

**Note:** All fields are optional. Only provided fields will be updated.

---

### PersonResponse

Response schema for person data.

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Dr. Jane Smith",
  "type": "resident",
  "email": "jane.smith@example.com",
  "pgy_level": 2,
  "performs_procedures": false,
  "specialties": null,
  "primary_duty": null,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

**TypeScript:**
```typescript
interface PersonResponse {
  id: string; // UUID
  name: string;
  type: PersonType;
  email: string | null;
  pgy_level: PGYLevel | null;
  performs_procedures: boolean;
  specialties: string[] | null;
  primary_duty: string | null;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}
```

---

### PersonListResponse

Response schema for list of persons.

**Schema:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Dr. Jane Smith",
      "type": "resident",
      "pgy_level": 2,
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
    }
  ],
  "total": 1
}
```

**TypeScript:**
```typescript
interface PersonListResponse {
  items: PersonResponse[];
  total: number;
}
```

---

## Block Schemas

### BlockCreate

Request schema for creating a block.

**Schema:**
```json
{
  "date": "2024-01-01",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**TypeScript:**
```typescript
type TimeOfDay = "AM" | "PM";

interface BlockCreate {
  date: string; // ISO 8601 date (YYYY-MM-DD)
  time_of_day: TimeOfDay;
  block_number: number; // Academic block number (1-13 typically)
  is_weekend?: boolean; // Default: false
  is_holiday?: boolean; // Default: false
  holiday_name?: string | null;
}
```

**Validation Rules:**
- `date` - Required, valid date in YYYY-MM-DD format
- `time_of_day` - Required, must be "AM" or "PM"
- `block_number` - Required, positive integer
- `is_weekend` - Auto-calculated based on date if not provided
- `is_holiday` - Boolean, defaults to false
- `holiday_name` - Optional, name of the holiday

---

### BlockResponse

Response schema for block data.

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "date": "2024-01-01",
  "time_of_day": "AM",
  "block_number": 1,
  "is_weekend": false,
  "is_holiday": false,
  "holiday_name": null
}
```

**TypeScript:**
```typescript
interface BlockResponse {
  id: string; // UUID
  date: string; // ISO 8601 date
  time_of_day: TimeOfDay;
  block_number: number;
  is_weekend: boolean;
  is_holiday: boolean;
  holiday_name: string | null;
}
```

---

### BlockListResponse

Response schema for list of blocks.

**TypeScript:**
```typescript
interface BlockListResponse {
  items: BlockResponse[];
  total: number;
}
```

---

## Rotation Template Schemas

### RotationTemplateCreate

Request schema for creating a rotation template.

**Schema:**
```json
{
  "name": "Cardiology Clinic",
  "activity_type": "clinic",
  "abbreviation": "CARD",
  "clinic_location": "Building A",
  "max_residents": 4,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4
}
```

**TypeScript:**
```typescript
type ActivityType = "clinic" | "inpatient" | "procedure" | "conference";

interface RotationTemplateCreate {
  name: string;
  activity_type: ActivityType;
  abbreviation?: string | null;
  clinic_location?: string | null;
  max_residents?: number | null;
  requires_specialty?: string | null;
  requires_procedure_credential?: boolean; // Default: false
  supervision_required?: boolean; // Default: true
  max_supervision_ratio?: number; // Default: 4
}
```

**Validation Rules:**
- `name` - Required, unique rotation name
- `activity_type` - Required, one of: "clinic", "inpatient", "procedure", "conference"
- `abbreviation` - Optional, short code for display
- `clinic_location` - Optional, physical location
- `max_residents` - Optional, maximum residents per block
- `requires_specialty` - Optional, specialty requirement
- `requires_procedure_credential` - Boolean, defaults to false
- `supervision_required` - Boolean, defaults to true
- `max_supervision_ratio` - Integer, defaults to 4 (e.g., 1:4 ratio)

**Activity Types:**
- `clinic` - Outpatient clinic
- `inpatient` - Inpatient ward/service
- `procedure` - Procedure-based rotation
- `conference` - Educational conference

---

### RotationTemplateUpdate

Request schema for updating a rotation template.

**TypeScript:**
```typescript
interface RotationTemplateUpdate {
  name?: string;
  activity_type?: ActivityType;
  abbreviation?: string | null;
  clinic_location?: string | null;
  max_residents?: number | null;
  requires_specialty?: string | null;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number;
}
```

---

### RotationTemplateResponse

Response schema for rotation template data.

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Cardiology Clinic",
  "activity_type": "clinic",
  "abbreviation": "CARD",
  "clinic_location": "Building A",
  "max_residents": 4,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 4,
  "created_at": "2024-01-01T12:00:00"
}
```

**TypeScript:**
```typescript
interface RotationTemplateResponse {
  id: string; // UUID
  name: string;
  activity_type: ActivityType;
  abbreviation: string | null;
  clinic_location: string | null;
  max_residents: number | null;
  requires_specialty: string | null;
  requires_procedure_credential: boolean;
  supervision_required: boolean;
  max_supervision_ratio: number;
  created_at: string; // ISO 8601 datetime
}
```

---

### RotationTemplateListResponse

**TypeScript:**
```typescript
interface RotationTemplateListResponse {
  items: RotationTemplateResponse[];
  total: number;
}
```

---

## Absence Schemas

### AbsenceCreate

Request schema for creating an absence.

**Schema:**
```json
{
  "person_id": "123e4567-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Pre-planned vacation"
}
```

**TypeScript:**
```typescript
type AbsenceType =
  | "vacation"
  | "deployment"
  | "tdy"
  | "medical"
  | "family_emergency"
  | "conference";

interface AbsenceCreate {
  person_id: string; // UUID
  start_date: string; // ISO 8601 date
  end_date: string; // ISO 8601 date
  absence_type: AbsenceType;
  deployment_orders?: boolean; // Default: false
  tdy_location?: string | null;
  replacement_activity?: string | null;
  notes?: string | null;
}
```

**Validation Rules:**
- `person_id` - Required, valid UUID of existing person
- `start_date` - Required, valid date in YYYY-MM-DD format
- `end_date` - Required, must be >= start_date
- `absence_type` - Required, valid absence type
- `deployment_orders` - Boolean, true if official deployment orders exist
- `tdy_location` - Optional, location for TDY assignments
- `replacement_activity` - Optional, alternate activity during absence
- `notes` - Optional, additional information

**Absence Types:**
- `vacation` - Planned time off
- `deployment` - Military deployment
- `tdy` - Temporary duty (TDY) assignment
- `medical` - Medical leave
- `family_emergency` - Family emergency leave
- `conference` - Conference attendance

---

### AbsenceUpdate

Request schema for updating an absence.

**TypeScript:**
```typescript
interface AbsenceUpdate {
  start_date?: string;
  end_date?: string;
  absence_type?: AbsenceType;
  deployment_orders?: boolean;
  tdy_location?: string | null;
  replacement_activity?: string | null;
  notes?: string | null;
}
```

---

### AbsenceResponse

Response schema for absence data.

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "person_id": "456e7890-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "absence_type": "vacation",
  "deployment_orders": false,
  "tdy_location": null,
  "replacement_activity": null,
  "notes": "Pre-planned vacation",
  "created_at": "2024-01-01T12:00:00"
}
```

**TypeScript:**
```typescript
interface AbsenceResponse {
  id: string; // UUID
  person_id: string; // UUID
  start_date: string; // ISO 8601 date
  end_date: string; // ISO 8601 date
  absence_type: AbsenceType;
  deployment_orders: boolean;
  tdy_location: string | null;
  replacement_activity: string | null;
  notes: string | null;
  created_at: string; // ISO 8601 datetime
}
```

---

## Assignment Schemas

### AssignmentCreate

Request schema for creating an assignment.

**Schema:**
```json
{
  "block_id": "123e4567-e89b-12d3-a456-426614174000",
  "person_id": "456e7890-e89b-12d3-a456-426614174000",
  "rotation_template_id": "789e0123-e89b-12d3-a456-426614174000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": "Approved by Program Director"
}
```

**TypeScript:**
```typescript
type AssignmentRole = "primary" | "supervising" | "backup";

interface AssignmentCreate {
  block_id: string; // UUID
  person_id: string; // UUID
  rotation_template_id?: string | null; // UUID
  role: AssignmentRole;
  activity_override?: string | null;
  notes?: string | null;
  override_reason?: string | null; // For acknowledging ACGME violations
  created_by?: string | null; // Auto-filled by API
}
```

**Validation Rules:**
- `block_id` - Required, valid UUID of existing block
- `person_id` - Required, valid UUID of existing person
- `rotation_template_id` - Optional, UUID of rotation template
- `role` - Required, must be "primary", "supervising", or "backup"
- `activity_override` - Optional, override template activity name
- `notes` - Optional, additional notes
- `override_reason` - Optional, reason for ACGME violation override

**Role Types:**
- `primary` - Primary assignee for the block
- `supervising` - Supervising faculty member
- `backup` - Backup coverage

---

### AssignmentUpdate

Request schema for updating an assignment.

**Schema:**
```json
{
  "role": "supervising",
  "notes": "Changed to supervising role",
  "override_reason": "Approved by Program Director",
  "updated_at": "2024-01-01T12:00:00"
}
```

**TypeScript:**
```typescript
interface AssignmentUpdate {
  rotation_template_id?: string | null;
  role?: AssignmentRole;
  activity_override?: string | null;
  notes?: string | null;
  override_reason?: string | null;
  acknowledge_override?: boolean; // Set to true to timestamp override
  updated_at: string; // Required for optimistic locking
}
```

**Note:** The `updated_at` field is required for optimistic locking to prevent concurrent modifications.

---

### AssignmentResponse

Response schema for assignment data.

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "block_id": "456e7890-e89b-12d3-a456-426614174000",
  "person_id": "789e0123-e89b-12d3-a456-426614174000",
  "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": null,
  "created_by": "admin",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "override_acknowledged_at": null
}
```

**TypeScript:**
```typescript
interface AssignmentResponse {
  id: string; // UUID
  block_id: string; // UUID
  person_id: string; // UUID
  rotation_template_id: string | null; // UUID
  role: AssignmentRole;
  activity_override: string | null;
  notes: string | null;
  override_reason: string | null;
  created_by: string | null;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
  override_acknowledged_at: string | null; // ISO 8601 datetime
}
```

---

### AssignmentWithWarnings

Extended assignment response with ACGME validation warnings.

**Schema:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "block_id": "456e7890-e89b-12d3-a456-426614174000",
  "person_id": "789e0123-e89b-12d3-a456-426614174000",
  "rotation_template_id": "012e3456-e89b-12d3-a456-426614174000",
  "role": "primary",
  "activity_override": null,
  "notes": null,
  "override_reason": null,
  "created_by": "admin",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00",
  "override_acknowledged_at": null,
  "acgme_warnings": [
    "HIGH: Resident exceeds 80-hour work week average"
  ],
  "is_compliant": false
}
```

**TypeScript:**
```typescript
interface AssignmentWithWarnings extends AssignmentResponse {
  acgme_warnings: string[];
  is_compliant: boolean;
}
```

---

## Schedule Schemas

### ScheduleRequest

Request schema for schedule generation.

**Schema:**
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-28",
  "pgy_levels": [1, 2, 3],
  "rotation_template_ids": null,
  "algorithm": "greedy",
  "timeout_seconds": 60.0
}
```

**TypeScript:**
```typescript
type SchedulingAlgorithm = "greedy" | "cp_sat" | "pulp" | "hybrid";

interface ScheduleRequest {
  start_date: string; // ISO 8601 date
  end_date: string; // ISO 8601 date
  pgy_levels?: number[] | null; // Filter by PGY levels [1, 2, 3]
  rotation_template_ids?: string[] | null; // Filter by template UUIDs
  algorithm?: SchedulingAlgorithm; // Default: "greedy"
  timeout_seconds?: number; // Default: 60, range: 5-300
}
```

**Validation Rules:**
- `start_date` - Required, must be <= end_date
- `end_date` - Required, must be >= start_date
- `pgy_levels` - Optional, array of PGY levels to include
- `rotation_template_ids` - Optional, specific templates to use
- `algorithm` - Optional, defaults to "greedy"
- `timeout_seconds` - Optional, range 5-300 seconds

**Algorithm Options:**
- `greedy` - Fast heuristic algorithm
- `cp_sat` - OR-Tools constraint programming (optimal)
- `pulp` - PuLP linear programming (fast for large problems)
- `hybrid` - Combines CP-SAT and PuLP

---

### Violation

Schema for a single ACGME violation.

**Schema:**
```json
{
  "type": "80_HOUR",
  "severity": "CRITICAL",
  "person_id": "123e4567-e89b-12d3-a456-426614174000",
  "person_name": "Dr. Jane Smith",
  "block_id": null,
  "message": "Resident exceeds 80-hour work week average",
  "details": {
    "avg_hours": 85.5,
    "week_range": "2024-01-08 to 2024-02-04"
  }
}
```

**TypeScript:**
```typescript
type ViolationType = "80_HOUR" | "1_IN_7" | "SUPERVISION_RATIO";
type ViolationSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

interface Violation {
  type: ViolationType;
  severity: ViolationSeverity;
  person_id?: string | null; // UUID
  person_name?: string | null;
  block_id?: string | null; // UUID
  message: string;
  details?: Record<string, any> | null;
}
```

**Violation Types:**
- `80_HOUR` - Exceeds 80-hour weekly average (4-week rolling)
- `1_IN_7` - Missing 1-in-7 days off requirement
- `SUPERVISION_RATIO` - Inadequate supervision ratio

**Severity Levels:**
- `CRITICAL` - Immediate attention required
- `HIGH` - Should be addressed soon
- `MEDIUM` - Minor concern
- `LOW` - Informational

---

### ValidationResult

Schema for ACGME validation results.

**Schema:**
```json
{
  "valid": true,
  "total_violations": 0,
  "violations": [],
  "coverage_rate": 93.75,
  "statistics": {
    "total_residents": 12,
    "total_blocks": 160,
    "avg_hours_per_week": 68.5
  }
}
```

**TypeScript:**
```typescript
interface ValidationResult {
  valid: boolean;
  total_violations: number;
  violations: Violation[];
  coverage_rate: number; // Percentage (0-100)
  statistics?: Record<string, any> | null;
}
```

---

### SolverStatistics

Statistics from the solver run.

**Schema:**
```json
{
  "total_blocks": 160,
  "total_residents": 12,
  "coverage_rate": 93.75,
  "branches": 1024,
  "conflicts": 45
}
```

**TypeScript:**
```typescript
interface SolverStatistics {
  total_blocks?: number | null;
  total_residents?: number | null;
  coverage_rate?: number | null; // Percentage
  branches?: number | null; // CP-SAT specific
  conflicts?: number | null; // CP-SAT specific
}
```

---

### ScheduleResponse

Response schema for schedule generation.

**Schema:**
```json
{
  "status": "success",
  "message": "Schedule generated successfully",
  "total_blocks_assigned": 150,
  "total_blocks": 160,
  "validation": {
    "valid": true,
    "total_violations": 0,
    "violations": [],
    "coverage_rate": 93.75,
    "statistics": {}
  },
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "solver_stats": {
    "total_blocks": 160,
    "total_residents": 12,
    "coverage_rate": 93.75,
    "branches": 1024,
    "conflicts": 45
  },
  "acgme_override_count": 0
}
```

**TypeScript:**
```typescript
type ScheduleStatus = "success" | "partial" | "failed";

interface ScheduleResponse {
  status: ScheduleStatus;
  message: string;
  total_blocks_assigned: number;
  total_blocks: number;
  validation: ValidationResult;
  run_id?: string | null; // UUID
  solver_stats?: SolverStatistics | null;
  acgme_override_count?: number; // Default: 0
}
```

**Status Values:**
- `success` - Complete success, all assignments created
- `partial` - Partial success, some assignments with warnings
- `failed` - Failed to generate schedule

---

### EmergencyRequest

Request schema for emergency coverage.

**Schema:**
```json
{
  "person_id": "123e4567-e89b-12d3-a456-426614174000",
  "start_date": "2024-02-15",
  "end_date": "2024-02-20",
  "reason": "Family emergency",
  "is_deployment": false
}
```

**TypeScript:**
```typescript
interface EmergencyRequest {
  person_id: string; // UUID
  start_date: string; // ISO 8601 date
  end_date: string; // ISO 8601 date
  reason: string;
  is_deployment?: boolean; // Default: false
}
```

---

### EmergencyResponse

Response schema for emergency coverage.

**Schema:**
```json
{
  "status": "success",
  "replacements_found": 8,
  "coverage_gaps": 2,
  "requires_manual_review": true,
  "details": [
    {
      "date": "2024-02-15",
      "time_of_day": "AM",
      "original_person": "Dr. Jane Smith",
      "replacement_person": "Dr. John Doe",
      "rotation": "Cardiology Clinic"
    }
  ]
}
```

**TypeScript:**
```typescript
interface EmergencyResponse {
  status: string;
  replacements_found: number;
  coverage_gaps: number;
  requires_manual_review: boolean;
  details: Record<string, any>[];
}
```

---

## Settings Schemas

### SettingsBase / SettingsResponse

Schema for application settings.

**Schema:**
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

**TypeScript:**
```typescript
interface SettingsResponse {
  scheduling_algorithm: string; // "greedy", "min_conflicts", "cp_sat"
  work_hours_per_week: number; // Range: 40-100
  max_consecutive_days: number; // Range: 1-7
  min_days_off_per_week: number; // Range: 1-3
  pgy1_supervision_ratio: string; // e.g., "1:2"
  pgy2_supervision_ratio: string; // e.g., "1:4"
  pgy3_supervision_ratio: string; // e.g., "1:4"
  enable_weekend_scheduling: boolean;
  enable_holiday_scheduling: boolean;
  default_block_duration_hours: number; // Range: 1-12
}
```

**Validation Rules:**
- `work_hours_per_week` - Integer, range 40-100
- `max_consecutive_days` - Integer, range 1-7
- `min_days_off_per_week` - Integer, range 1-3
- `default_block_duration_hours` - Integer, range 1-12

---

### SettingsUpdate

Schema for partial settings update.

**TypeScript:**
```typescript
interface SettingsUpdate {
  scheduling_algorithm?: string;
  work_hours_per_week?: number;
  max_consecutive_days?: number;
  min_days_off_per_week?: number;
  pgy1_supervision_ratio?: string;
  pgy2_supervision_ratio?: string;
  pgy3_supervision_ratio?: string;
  enable_weekend_scheduling?: boolean;
  enable_holiday_scheduling?: boolean;
  default_block_duration_hours?: number;
}
```

---

## Common Types

### UUID

All ID fields use UUID version 4 format.

**Example:** `123e4567-e89b-12d3-a456-426614174000`

**TypeScript:**
```typescript
type UUID = string; // UUID v4 format
```

---

### ISO 8601 Date

Date fields use ISO 8601 format (YYYY-MM-DD).

**Example:** `2024-01-01`

**TypeScript:**
```typescript
type ISODate = string; // YYYY-MM-DD
```

---

### ISO 8601 DateTime

DateTime fields use ISO 8601 format with timezone.

**Example:** `2024-01-01T12:00:00` or `2024-01-01T12:00:00.000Z`

**TypeScript:**
```typescript
type ISODateTime = string; // ISO 8601 datetime
```

---

### List Response Pattern

All list endpoints follow a consistent pattern.

**TypeScript:**
```typescript
interface ListResponse<T> {
  items: T[];
  total: number;
}
```

---

## Complete TypeScript Definitions

For convenience, here's a complete TypeScript definitions file you can use in your frontend application:

```typescript
// ============================================================================
// Common Types
// ============================================================================

type UUID = string;
type ISODate = string; // YYYY-MM-DD
type ISODateTime = string; // ISO 8601

interface ListResponse<T> {
  items: T[];
  total: number;
}

// ============================================================================
// Authentication
// ============================================================================

interface Token {
  access_token: string;
  token_type: string;
}

interface UserLogin {
  username: string;
  password: string;
}

interface UserCreate {
  username: string;
  email: string;
  password: string;
  role?: "admin" | "coordinator" | "faculty";
}

interface UserResponse {
  id: UUID;
  username: string;
  email: string;
  role: "admin" | "coordinator" | "faculty";
  is_active: boolean;
}

// ============================================================================
// Person
// ============================================================================

type PersonType = "resident" | "faculty";
type PGYLevel = 1 | 2 | 3;

interface PersonCreate {
  name: string;
  type: PersonType;
  email?: string | null;
  pgy_level?: PGYLevel | null;
  performs_procedures?: boolean;
  specialties?: string[] | null;
  primary_duty?: string | null;
}

interface PersonUpdate {
  name?: string;
  email?: string | null;
  pgy_level?: PGYLevel | null;
  performs_procedures?: boolean;
  specialties?: string[] | null;
  primary_duty?: string | null;
}

interface PersonResponse {
  id: UUID;
  name: string;
  type: PersonType;
  email: string | null;
  pgy_level: PGYLevel | null;
  performs_procedures: boolean;
  specialties: string[] | null;
  primary_duty: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
}

type PersonListResponse = ListResponse<PersonResponse>;

// ============================================================================
// Block
// ============================================================================

type TimeOfDay = "AM" | "PM";

interface BlockCreate {
  date: ISODate;
  time_of_day: TimeOfDay;
  block_number: number;
  is_weekend?: boolean;
  is_holiday?: boolean;
  holiday_name?: string | null;
}

interface BlockResponse {
  id: UUID;
  date: ISODate;
  time_of_day: TimeOfDay;
  block_number: number;
  is_weekend: boolean;
  is_holiday: boolean;
  holiday_name: string | null;
}

type BlockListResponse = ListResponse<BlockResponse>;

// ============================================================================
// Rotation Template
// ============================================================================

type ActivityType = "clinic" | "inpatient" | "procedure" | "conference";

interface RotationTemplateCreate {
  name: string;
  activity_type: ActivityType;
  abbreviation?: string | null;
  clinic_location?: string | null;
  max_residents?: number | null;
  requires_specialty?: string | null;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number;
}

interface RotationTemplateUpdate {
  name?: string;
  activity_type?: ActivityType;
  abbreviation?: string | null;
  clinic_location?: string | null;
  max_residents?: number | null;
  requires_specialty?: string | null;
  requires_procedure_credential?: boolean;
  supervision_required?: boolean;
  max_supervision_ratio?: number;
}

interface RotationTemplateResponse {
  id: UUID;
  name: string;
  activity_type: ActivityType;
  abbreviation: string | null;
  clinic_location: string | null;
  max_residents: number | null;
  requires_specialty: string | null;
  requires_procedure_credential: boolean;
  supervision_required: boolean;
  max_supervision_ratio: number;
  created_at: ISODateTime;
}

type RotationTemplateListResponse = ListResponse<RotationTemplateResponse>;

// ============================================================================
// Absence
// ============================================================================

type AbsenceType =
  | "vacation"
  | "deployment"
  | "tdy"
  | "medical"
  | "family_emergency"
  | "conference";

interface AbsenceCreate {
  person_id: UUID;
  start_date: ISODate;
  end_date: ISODate;
  absence_type: AbsenceType;
  deployment_orders?: boolean;
  tdy_location?: string | null;
  replacement_activity?: string | null;
  notes?: string | null;
}

interface AbsenceUpdate {
  start_date?: ISODate;
  end_date?: ISODate;
  absence_type?: AbsenceType;
  deployment_orders?: boolean;
  tdy_location?: string | null;
  replacement_activity?: string | null;
  notes?: string | null;
}

interface AbsenceResponse {
  id: UUID;
  person_id: UUID;
  start_date: ISODate;
  end_date: ISODate;
  absence_type: AbsenceType;
  deployment_orders: boolean;
  tdy_location: string | null;
  replacement_activity: string | null;
  notes: string | null;
  created_at: ISODateTime;
}

// ============================================================================
// Assignment
// ============================================================================

type AssignmentRole = "primary" | "supervising" | "backup";

interface AssignmentCreate {
  block_id: UUID;
  person_id: UUID;
  rotation_template_id?: UUID | null;
  role: AssignmentRole;
  activity_override?: string | null;
  notes?: string | null;
  override_reason?: string | null;
  created_by?: string | null;
}

interface AssignmentUpdate {
  rotation_template_id?: UUID | null;
  role?: AssignmentRole;
  activity_override?: string | null;
  notes?: string | null;
  override_reason?: string | null;
  acknowledge_override?: boolean;
  updated_at: ISODateTime;
}

interface AssignmentResponse {
  id: UUID;
  block_id: UUID;
  person_id: UUID;
  rotation_template_id: UUID | null;
  role: AssignmentRole;
  activity_override: string | null;
  notes: string | null;
  override_reason: string | null;
  created_by: string | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  override_acknowledged_at: ISODateTime | null;
}

interface AssignmentWithWarnings extends AssignmentResponse {
  acgme_warnings: string[];
  is_compliant: boolean;
}

// ============================================================================
// Schedule
// ============================================================================

type SchedulingAlgorithm = "greedy" | "cp_sat" | "pulp" | "hybrid";

interface ScheduleRequest {
  start_date: ISODate;
  end_date: ISODate;
  pgy_levels?: number[] | null;
  rotation_template_ids?: UUID[] | null;
  algorithm?: SchedulingAlgorithm;
  timeout_seconds?: number;
}

type ViolationType = "80_HOUR" | "1_IN_7" | "SUPERVISION_RATIO";
type ViolationSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

interface Violation {
  type: ViolationType;
  severity: ViolationSeverity;
  person_id?: UUID | null;
  person_name?: string | null;
  block_id?: UUID | null;
  message: string;
  details?: Record<string, any> | null;
}

interface ValidationResult {
  valid: boolean;
  total_violations: number;
  violations: Violation[];
  coverage_rate: number;
  statistics?: Record<string, any> | null;
}

interface SolverStatistics {
  total_blocks?: number | null;
  total_residents?: number | null;
  coverage_rate?: number | null;
  branches?: number | null;
  conflicts?: number | null;
}

type ScheduleStatus = "success" | "partial" | "failed";

interface ScheduleResponse {
  status: ScheduleStatus;
  message: string;
  total_blocks_assigned: number;
  total_blocks: number;
  validation: ValidationResult;
  run_id?: UUID | null;
  solver_stats?: SolverStatistics | null;
  acgme_override_count?: number;
}

interface EmergencyRequest {
  person_id: UUID;
  start_date: ISODate;
  end_date: ISODate;
  reason: string;
  is_deployment?: boolean;
}

interface EmergencyResponse {
  status: string;
  replacements_found: number;
  coverage_gaps: number;
  requires_manual_review: boolean;
  details: Record<string, any>[];
}

// ============================================================================
// Settings
// ============================================================================

interface SettingsResponse {
  scheduling_algorithm: string;
  work_hours_per_week: number;
  max_consecutive_days: number;
  min_days_off_per_week: number;
  pgy1_supervision_ratio: string;
  pgy2_supervision_ratio: string;
  pgy3_supervision_ratio: string;
  enable_weekend_scheduling: boolean;
  enable_holiday_scheduling: boolean;
  default_block_duration_hours: number;
}

interface SettingsUpdate {
  scheduling_algorithm?: string;
  work_hours_per_week?: number;
  max_consecutive_days?: number;
  min_days_off_per_week?: number;
  pgy1_supervision_ratio?: string;
  pgy2_supervision_ratio?: string;
  pgy3_supervision_ratio?: string;
  enable_weekend_scheduling?: boolean;
  enable_holiday_scheduling?: boolean;
  default_block_duration_hours?: number;
}
```

Save this file as `types/api.ts` in your frontend project for full type safety when working with the API.
