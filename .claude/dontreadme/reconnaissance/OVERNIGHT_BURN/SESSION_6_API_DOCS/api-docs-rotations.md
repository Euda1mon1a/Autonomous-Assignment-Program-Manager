# Rotation API Documentation

**Status:** Complete API Documentation
**Last Updated:** 2025-12-30
**Endpoint Base:** `/api/rotation-templates`
**Authentication:** Required (JWT via httpOnly cookie)

---

## Table of Contents

1. [Overview](#overview)
2. [Core Endpoints](#core-endpoints)
3. [Data Models](#data-models)
4. [Scheduling Integration](#scheduling-integration)
5. [Constraint Management](#constraint-management)
6. [Leave Eligibility](#leave-eligibility)
7. [Template Management Patterns](#template-management-patterns)
8. [Error Handling](#error-handling)
9. [Examples](#examples)

---

## Overview

The Rotation API manages reusable activity patterns that structure the academic year schedule. Rotations define:

- **Activity Type**: clinic, inpatient, procedure, conference
- **Capacity Constraints**: Max residents per rotation
- **Supervision Requirements**: ACGME-compliant ratios
- **Leave Eligibility**: Whether leave can be scheduled during this rotation
- **Specialty Requirements**: Certifications or qualifications needed
- **Visual Styling**: Colors and abbreviations for schedule displays

### Key Architectural Concepts

**Leave-Eligible vs Non-Leave-Eligible Rotations:**
- **Leave-Eligible** (e.g., electives, specialty clinic): Residents can take approved leave during these rotations. The BlockSchedulerService automatically assigns residents with pending leave to these rotations to avoid disrupting critical coverage.
- **Non-Leave-Eligible** (e.g., FMIT inpatient, call coverage): Leave is not normally allowed. Emergency absences still generate conflict alerts regardless of this setting.

**Template-Based Composition:**
- Templates define half-day requirements (FM Clinic: 4 days, Specialty: 5 days, Academics: 1 day)
- The solver uses these to optimize schedule composition
- Weekly patterns (7x2 AM/PM grid) define slot-level activities

---

## Core Endpoints

### List Rotation Templates

```http
GET /api/rotation-templates
```

**Query Parameters:**
- `activity_type` (optional): Filter by activity type (clinic, inpatient, procedure, conference)

**Response:** `RotationTemplateListResponse`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "PGY-1 Clinic",
      "activity_type": "clinic",
      "abbreviation": "C1",
      "font_color": "text-blue-600",
      "background_color": "bg-blue-50",
      "leave_eligible": true,
      "clinic_location": "Main Clinic",
      "max_residents": 4,
      "requires_specialty": null,
      "requires_procedure_credential": false,
      "supervision_required": true,
      "max_supervision_ratio": 4,
      "created_at": "2025-12-01T10:00:00Z"
    }
  ],
  "total": 15
}
```

**Use Cases:**
- Frontend: Populate rotation selection dropdowns
- Scheduling: Enumerate available templates for assignment
- Admin: Display rotation catalog for review

---

### Get Rotation Template by ID

```http
GET /api/rotation-templates/{template_id}
```

**Path Parameters:**
- `template_id` (UUID): Rotation template identifier

**Response:** `RotationTemplateResponse`

```json
{
  "id": "uuid",
  "name": "FMIT Inpatient",
  "activity_type": "inpatient",
  "abbreviation": "FMIT",
  "font_color": "text-red-600",
  "background_color": "bg-red-50",
  "leave_eligible": false,
  "clinic_location": null,
  "max_residents": null,
  "requires_specialty": null,
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 2,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Error Responses:**
- `404 Not Found`: Template does not exist
- `422 Unprocessable Entity`: Invalid UUID format

---

### Create Rotation Template

```http
POST /api/rotation-templates
Content-Type: application/json
```

**Request Body:** `RotationTemplateCreate`

```json
{
  "name": "Neurology Specialty",
  "activity_type": "clinic",
  "abbreviation": "NEURO",
  "font_color": "text-purple-600",
  "background_color": "bg-purple-50",
  "clinic_location": "Neurology Building",
  "max_residents": 3,
  "requires_specialty": "Neurology",
  "requires_procedure_credential": false,
  "supervision_required": true,
  "max_supervision_ratio": 3,
  "leave_eligible": true
}
```

**Response:** `RotationTemplateResponse` (HTTP 201)

**Required Fields:**
- `name`: String, max 255 characters
- `activity_type`: One of [clinic, inpatient, procedure, conference]

**Optional Fields:**
- `abbreviation`: String, max 10 (for Excel exports)
- `font_color`: Tailwind CSS text color class (e.g., text-blue-600)
- `background_color`: Tailwind CSS background class (e.g., bg-blue-50)
- `clinic_location`: String, max 255
- `max_residents`: Integer (null = unlimited)
- `requires_specialty`: String, specialty name
- `requires_procedure_credential`: Boolean (default: false)
- `supervision_required`: Boolean (default: true)
- `max_supervision_ratio`: Integer (default: 4)
- `leave_eligible`: Boolean (default: true)

**Validation Rules:**
- `activity_type` must be a valid enum value
- `max_residents` must be >= 0 if provided
- `max_supervision_ratio` must be > 0 if supervision_required is true

**Business Logic:**
- New templates are immediately available for schedule assignments
- Templates with `max_residents` set will be validated during schedule generation (capacity constraint)

---

### Update Rotation Template

```http
PUT /api/rotation-templates/{template_id}
Content-Type: application/json
```

**Path Parameters:**
- `template_id` (UUID): Template to update

**Request Body:** `RotationTemplateUpdate` (all fields optional)

```json
{
  "name": "Updated Name",
  "max_residents": 5,
  "leave_eligible": false
}
```

**Response:** `RotationTemplateResponse` (HTTP 200)

**Behavior:**
- Only provided fields are updated (partial updates supported)
- `id` and `created_at` are immutable
- Existing assignments are not cascaded (data consistency maintained)

**Warning:**
Changing `leave_eligible` from `true` to `false` may cause conflicts if residents with pending leave are already assigned. Use with caution.

---

### Delete Rotation Template

```http
DELETE /api/rotation-templates/{template_id}
```

**Path Parameters:**
- `template_id` (UUID): Template to delete

**Response:** HTTP 204 No Content

**Cascade Behavior:**
- Deletes associated `rotation_preferences` (soft constraints)
- Deletes associated `rotation_halfday_requirements` (composition rules)
- Deletes associated `weekly_patterns` (grid definitions)
- Does NOT delete `assignments` (foreign key constraint prevents deletion if assignments exist)

**Error Handling:**
- `404 Not Found`: Template does not exist
- `409 Conflict`: Template has active assignments (try updating assignments first)

---

## Data Models

### RotationTemplate (ORM Model)

**Database Table:** `rotation_templates`

```python
class RotationTemplate(Base):
    id: UUID = Column(GUID, primary_key=True)
    name: str = Column(String(255), nullable=False)
    activity_type: str = Column(String(255), nullable=False)
    abbreviation: str | None = Column(String(10))
    font_color: str | None = Column(String(50))
    background_color: str | None = Column(String(50))

    # Leave eligibility - core concept
    leave_eligible: bool = Column(Boolean, default=True)

    # Clinic constraints
    clinic_location: str | None = Column(String(255))
    max_residents: int | None = Column(Integer)
    requires_specialty: str | None = Column(String(255))
    requires_procedure_credential: bool = Column(Boolean, default=False)

    # ACGME supervision
    supervision_required: bool = Column(Boolean, default=True)
    max_supervision_ratio: int = Column(Integer, default=4)

    # Timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assignments: list[Assignment]
    halfday_requirements: RotationHalfDayRequirement  # One-to-one
    preferences: list[RotationPreference]
    weekly_patterns: list[WeeklyPattern]
```

**Indexes:**
- Primary key: `id`
- Foreign keys: `rotation_templates.id` referenced by assignments, preferences, patterns

**Computed Properties:**

```python
@property
def has_capacity_limit(self) -> bool:
    """True if max_residents is set and > 0."""
    return self.max_residents is not None and self.max_residents > 0

@property
def requires_specialty_faculty(self) -> bool:
    """True if requires_specialty is set."""
    return self.requires_specialty is not None
```

---

### RotationHalfDayRequirement (ORM Model)

**Database Table:** `rotation_halfday_requirements`

Defines per-block composition (how 10 half-days should be structured):

```python
class RotationHalfDayRequirement(Base):
    id: UUID = Column(GUID, primary_key=True)
    rotation_template_id: UUID = Column(ForeignKey("rotation_templates.id"))

    # Activity breakdown per block (sums to 10)
    fm_clinic_halfdays: int = Column(Integer, default=4)
    specialty_halfdays: int = Column(Integer, default=5)
    specialty_name: str | None = Column(String(255))  # "Neurology", "Dermatology"
    academics_halfdays: int = Column(Integer, default=1)  # Wed AM
    elective_halfdays: int = Column(Integer, default=0)  # Buffer/flex time

    # Solver constraints
    min_consecutive_specialty: int = Column(Integer, default=1)
    prefer_combined_clinic_days: bool = Column(Boolean, default=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, onupdate=datetime.utcnow)
```

**Computed Properties:**

```python
@property
def total_halfdays(self) -> int:
    """Sum of all activity half-days."""
    return (self.fm_clinic_halfdays + self.specialty_halfdays
            + self.academics_halfdays + (self.elective_halfdays or 0))

@property
def is_balanced(self) -> bool:
    """True if total equals standard block (10)."""
    return self.total_halfdays == 10
```

**Example Composition:**
- FM Clinic: 4 half-days
- Specialty (e.g., Neurology): 5 half-days
- Academics (Wed AM): 1 half-day
- Total: 10 half-days per block

---

### RotationPreference (ORM Model)

**Database Table:** `rotation_preferences`

Soft scheduling constraints (optimization objectives, not hard rules):

```python
class RotationPreference(Base):
    id: UUID = Column(GUID, primary_key=True)
    rotation_template_id: UUID = Column(ForeignKey("rotation_templates.id"))

    preference_type: str  # full_day_grouping, consecutive_specialty, etc.
    weight: str = "medium"  # low, medium, high, required
    config_json: dict  # Type-specific configuration
    is_active: bool = Column(Boolean, default=True)
    description: str | None

    created_at: datetime
    updated_at: datetime
```

**Preference Types and Weights:**

| Type | Default Weight | Purpose | Config Example |
|------|---|---|---|
| `full_day_grouping` | medium | Prefer AM+PM same activity (full FM day) | `{}` |
| `consecutive_specialty` | high | Group specialty sessions together | `{"min_consecutive": 2}` |
| `avoid_isolated` | low | Avoid single orphaned half-day | `{"penalty_multiplier": 1.5}` |
| `preferred_days` | medium | Prefer specific activities on specific days | `{"activity": "fm_clinic", "days": [1,2,5]}` |
| `avoid_friday_pm` | low | Keep Friday PM open for travel | `{}` |
| `balance_weekly` | medium | Distribute activities evenly | `{"max_same_per_day": 1}` |

**Weight Multipliers (Solver Impact):**
- `low`: 1x penalty (nice to have)
- `medium`: 2x penalty (moderate priority)
- `high`: 4x penalty (strong preference)
- `required`: 8x penalty (soft but strongly enforced)

---

### WeeklyPattern (ORM Model)

**Database Table:** `weekly_patterns`

Defines 7x2 (AM/PM) grid for weekly rotation structure:

```python
class WeeklyPattern(Base):
    id: UUID = Column(GUID, primary_key=True)
    rotation_template_id: UUID = Column(ForeignKey("rotation_templates.id"))

    day_of_week: int  # 0=Sunday, 6=Saturday
    time_of_day: str  # "AM" or "PM"
    activity_type: str  # fm_clinic, specialty, elective, conference, inpatient, call, procedure, off
    linked_template_id: UUID | None  # For split rotations (reference to other template)
    is_protected: bool = False  # Wednesday academics protected time
    notes: str | None

    created_at: datetime
    updated_at: datetime
```

**Activity Types:**
- `fm_clinic`: Family Medicine clinic session
- `specialty`: Specialty rotation activity
- `elective`: Elective or flexible activity
- `conference`: Educational conference/didactic
- `inpatient`: Inpatient/hospital ward
- `call`: Call shift (on-call duties)
- `procedure`: Procedure-based activity
- `off`: Time off (scheduled leave/personal time)

**Protected Time:**
- Wednesday AM is typically marked `is_protected=True` for academics
- Solver respects protected slots and doesn't modify them

---

## Scheduling Integration

### Leave-Eligible Rotation Matching Algorithm

The `BlockSchedulerService` uses rotation templates to intelligently assign residents:

```python
class BlockSchedulerService:
    """Resident-to-rotation scheduling algorithm."""

    def find_best_leave_eligible_rotation(
        self,
        resident: Person,
        capacities: dict[UUID, RotationSlot],
        already_assigned: set[UUID]
    ) -> UUID | None:
        """
        Find best leave-eligible rotation for resident with pending leave.

        Logic:
        1. Filter to leave_eligible=True rotations only
        2. Skip already-assigned rotations
        3. Prefer rotations with available capacity (not overcrowded)
        4. Consider PGY level (some rotations may be better for certain levels)

        Returns: rotation_template_id or None if no suitable rotation found
        """
```

**Scheduling Priority Order:**
1. Residents with approved leave → `leave_eligible=True` rotations
2. Remaining residents → coverage needs first (non-leave-eligible), then balanced distribution
3. Coverage gaps identified for rotations needing staffing

**Block Structure:**
- Academic year: 13 blocks of 28 days each
- Each block has 14 half-days per resident (7 days × 2 periods)
- Block dates calculated: Block N starts `(N-1) * 28` days after July 1

### Capacity Constraints

**Max Residents Enforcement:**

```python
@dataclass
class RotationSlot:
    template: RotationTemplate
    max_capacity: int | None
    current_count: int = 0

    @property
    def is_full(self) -> bool:
        """Check if rotation is at capacity."""
        if self.max_capacity is None:
            return False
        return self.current_count >= self.max_capacity

    @property
    def available(self) -> int | None:
        """Get available slots (None if unlimited)."""
        if self.max_capacity is None:
            return None
        return max(0, self.max_capacity - self.current_count)
```

**Validation:**
- At schedule generation time, solver validates `max_residents` constraint
- If exceeded, schedule generation fails with capacity conflict alert
- Admin must either increase capacity or reduce resident assignments

### Supervision Ratio Enforcement

ACGME supervision requirements integrated into scheduling constraints:

```python
Template Settings:
- supervision_required: bool
- max_supervision_ratio: int (default 4, meaning 1 faculty : N residents)

PGY Level Specific:
- PGY-1: typically 1:2 ratio (tighter supervision)
- PGY-2/3: typically 1:4 ratio (looser supervision)
```

**Validation:**
- Solver checks supervision ratios during assignment
- Fails if assigning more residents than supervision allows
- Configuration is template-specific for flexibility

---

## Constraint Management

### Leave Eligibility Rules

**leave_eligible = true** (e.g., electives, specialty clinic)
- Residents can take approved leave during these rotations
- `BlockSchedulerService` auto-assigns residents with pending leave to these rotations
- Avoids disrupting critical coverage (FMIT, inpatient)

**leave_eligible = false** (e.g., FMIT inpatient, call coverage)
- Leave is not normally allowed
- Only emergency absences permitted
- Absence during these rotations generates conflict alerts
- System prevents/penalizes assignment to residents with pending leave

**Implementation in BlockSchedulerService:**

```python
def find_best_leave_eligible_rotation(
    self, resident, capacities, already_assigned
) -> UUID | None:
    """Find best rotation for resident with approved leave."""
    for rotation_id, slot in capacities.items():
        # Skip non-leave-eligible rotations
        if not slot.template.leave_eligible:
            continue

        # Skip if already assigned to this rotation
        if rotation_id in already_assigned:
            continue

        # Skip if rotation is full
        if slot.is_full:
            continue

        # Prefer rotations with available capacity
        return rotation_id
```

### Absence Conflict Detection

**Algorithm:**
1. When absence is created/approved: Check if overlap with non-leave-eligible rotation
2. If overlap found: Generate `LeaveConflict` alert
3. Alert severity depends on rotation type (FMIT = CRITICAL, elective = LOW)

**Conflict Resolution:**
- User must either:
  - Cancel/modify the absence
  - Request swap to leave-eligible rotation
  - Escalate for administrative override

---

## Template Management Patterns

### Activity Type Patterns

**Clinic Rotations (activity_type = "clinic")**
```json
{
  "name": "PGY-1 Continuity Clinic",
  "activity_type": "clinic",
  "abbreviation": "C1",
  "clinic_location": "Main Clinic Building",
  "max_residents": 4,
  "leave_eligible": true,
  "supervision_required": true,
  "max_supervision_ratio": 4
}
```

**Inpatient Rotations (activity_type = "inpatient")**
```json
{
  "name": "FMIT Inpatient",
  "activity_type": "inpatient",
  "abbreviation": "FMIT",
  "leave_eligible": false,
  "supervision_required": true,
  "max_supervision_ratio": 2,
  "max_residents": null
}
```

**Procedure Rotations (activity_type = "procedure")**
```json
{
  "name": "Joint Injection Procedure",
  "activity_type": "procedure",
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": true,
  "leave_eligible": true
}
```

**Conference Rotations (activity_type = "conference")**
```json
{
  "name": "Grand Rounds & Didactics",
  "activity_type": "conference",
  "supervision_required": false,
  "leave_eligible": true
}
```

### Split and Mirrored Rotations

**Split Rotation:** Two sequential rotations (e.g., Block 1: Neurology then Elective)

```json
{
  "name": "Neurology → Elective (Part A)",
  "activity_type": "clinic",
  "abbreviation": "NEURO-A",
  "paired_template_id": "uuid-of-part-b"
}
```

**Mirrored Rotation:** Two cohorts swap halfway through (Cohort A: FMIT→Elective, Cohort B: Elective→FMIT)

```json
{
  "name": "FMIT/Elective (Cohort A)",
  "activity_type": "inpatient",
  "pattern_type": "mirrored",
  "is_mirror_primary": true,
  "split_day": 14,
  "paired_template_id": "uuid-of-cohort-b"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET, PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Malformed JSON |
| 401 | Unauthorized | Missing/invalid JWT |
| 404 | Not Found | Template doesn't exist |
| 409 | Conflict | Delete template with active assignments |
| 422 | Validation Error | Invalid field values |
| 500 | Server Error | Database connection failure |

### Error Response Format

```json
{
  "detail": "Rotation template not found"
}
```

**Validation Error Example:**

```json
{
  "detail": [
    {
      "loc": ["body", "activity_type"],
      "msg": "Input should be 'clinic', 'inpatient', 'procedure', or 'conference'",
      "type": "enum"
    }
  ]
}
```

### Common Error Scenarios

**Cannot Delete Template with Active Assignments**
```
DELETE /api/rotation-templates/{id} → 409 Conflict

Reason: Foreign key constraint prevents deletion.
Solution: First update/delete all assignments using this template.
```

**Invalid UUID Format**
```
GET /api/rotation-templates/not-a-uuid → 422 Unprocessable Entity

Reason: UUID must be valid RFC 4122 format.
Solution: Use valid UUID, e.g., 550e8400-e29b-41d4-a716-446655440000
```

**Capacity Exceeded During Scheduling**
```
POST /api/schedule/generate → 409 Conflict

Reason: More residents assigned than max_residents allows.
Solution: Either increase max_residents or reduce assignments.
```

---

## Examples

### Example 1: Create a Specialty Clinic Template

```bash
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "name": "Sports Medicine Clinic",
    "activity_type": "clinic",
    "abbreviation": "SM",
    "font_color": "text-green-600",
    "background_color": "bg-green-50",
    "clinic_location": "Sports Medicine Center",
    "max_residents": 3,
    "requires_specialty": "Sports Medicine",
    "requires_procedure_credential": true,
    "supervision_required": true,
    "max_supervision_ratio": 3,
    "leave_eligible": true
  }'
```

**Response (201):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Sports Medicine Clinic",
  "activity_type": "clinic",
  "abbreviation": "SM",
  "font_color": "text-green-600",
  "background_color": "bg-green-50",
  "clinic_location": "Sports Medicine Center",
  "max_residents": 3,
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": true,
  "supervision_required": true,
  "max_supervision_ratio": 3,
  "leave_eligible": true,
  "created_at": "2025-12-30T15:45:00Z"
}
```

---

### Example 2: Update Template to Reduce Capacity

**Scenario:** Sports clinic at capacity, temporarily reduce max_residents

```bash
curl -X PUT http://localhost:8000/api/rotation-templates/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "max_residents": 2
  }'
```

**Response (200):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "Sports Medicine Clinic",
  "activity_type": "clinic",
  "abbreviation": "SM",
  "font_color": "text-green-600",
  "background_color": "bg-green-50",
  "clinic_location": "Sports Medicine Center",
  "max_residents": 2,
  "requires_specialty": "Sports Medicine",
  "requires_procedure_credential": true,
  "supervision_required": true,
  "max_supervision_ratio": 3,
  "leave_eligible": true,
  "created_at": "2025-12-30T15:45:00Z"
}
```

---

### Example 3: Filter Rotations by Activity Type

**Get all inpatient rotations:**

```bash
curl -X GET "http://localhost:8000/api/rotation-templates?activity_type=inpatient" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "fmit-uuid-1234",
      "name": "FMIT Inpatient",
      "activity_type": "inpatient",
      "abbreviation": "FMIT",
      "font_color": "text-red-600",
      "background_color": "bg-red-50",
      "leave_eligible": false,
      "clinic_location": null,
      "max_residents": null,
      "requires_specialty": null,
      "requires_procedure_credential": false,
      "supervision_required": true,
      "max_supervision_ratio": 2,
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": "night-float-uuid",
      "name": "Night Float",
      "activity_type": "inpatient",
      "abbreviation": "NF",
      "font_color": "text-blue-600",
      "background_color": "bg-blue-50",
      "leave_eligible": false,
      "clinic_location": null,
      "max_residents": null,
      "requires_specialty": null,
      "requires_procedure_credential": false,
      "supervision_required": true,
      "max_supervision_ratio": 1,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

---

### Example 4: Delete Template

**Warning: Template must have no active assignments**

```bash
curl -X DELETE http://localhost:8000/api/rotation-templates/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response (204):** Empty body, deletion successful

**If Template Has Assignments (409):**
```json
{
  "detail": "Cannot delete rotation template with active assignments"
}
```

---

### Example 5: Leave Eligibility Conflict Scenario

**Scenario:** Resident has approved leave during FMIT (non-leave-eligible) block

**Data Setup:**
```json
{
  "rotation": {
    "name": "FMIT Inpatient",
    "leave_eligible": false
  },
  "resident": {
    "name": "PGY-1-03",
    "approved_absence": {
      "start_date": "2025-07-15",
      "end_date": "2025-07-21",
      "type": "vacation"
    }
  },
  "block": {
    "number": 1,
    "start": "2025-07-01",
    "end": "2025-07-28"
  }
}
```

**BlockSchedulerService Logic:**
```python
# Step 1: Identify residents with leave in block
residents_with_leave = get_residents_with_leave_in_block(block=1)
# Result: [PGY-1-03 with 7 days leave]

# Step 2: Find leave-eligible rotations for this resident
leave_eligible_rotations = [
  "Continuity Clinic",  # leave_eligible=true
  "Elective",           # leave_eligible=true
  "Grand Rounds"        # leave_eligible=true
]

# Step 3: Assign resident to best available rotation
assignment = find_best_leave_eligible_rotation(
  resident=PGY-1-03,
  capacities=rotation_capacities,
  already_assigned=set()
)
# Result: Assign to "Continuity Clinic" (has capacity)

# Step 4: Remaining residents → fill coverage needs
remaining_residents = all_residents - residents_with_leave
for resident in remaining_residents:
    # Try to assign to coverage-critical rotations (FMIT, Night Float)
    # Then balance across other rotations
```

**Conflict Alert (if manually assigned to FMIT):**
```json
{
  "conflict_id": "uuid",
  "type": "leave_conflict",
  "severity": "critical",
  "resident_id": "pgy1-03-uuid",
  "rotation_id": "fmit-uuid",
  "date_range": {
    "start": "2025-07-15",
    "end": "2025-07-21"
  },
  "message": "Resident PGY-1-03 has approved leave during FMIT (non-leave-eligible rotation)",
  "resolution_options": [
    "Modify or cancel absence",
    "Reassign to leave-eligible rotation",
    "Override (requires admin approval)"
  ]
}
```

---

### Example 6: Half-Day Requirements Integration

**Create template with detailed half-day breakdown:**

```bash
curl -X POST http://localhost:8000/api/rotation-templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "name": "Neurology Rotation",
    "activity_type": "clinic",
    "abbreviation": "NEURO",
    "leave_eligible": true,
    "supervision_required": true,
    "max_supervision_ratio": 3,
    "halfday_requirement": {
      "fm_clinic_halfdays": 4,
      "specialty_halfdays": 5,
      "specialty_name": "Neurology",
      "academics_halfdays": 1,
      "elective_halfdays": 0,
      "min_consecutive_specialty": 2,
      "prefer_combined_clinic_days": true
    }
  }'
```

**Solver Uses This to:**
- Allocate 4 FM Clinic half-days per block
- Allocate 5 Neurology specialty half-days per block
- Allocate 1 Wednesday AM academic half-day
- Try to keep specialty sessions in groups of 2+ (min_consecutive_specialty=2)
- Prefer full days of same activity over half-day splits

---

## Advanced: Rotation Preferences (Soft Constraints)

**Create preference for full-day grouping:**

```bash
curl -X POST http://localhost:8000/api/rotation-templates/neuro-uuid/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "preference_type": "full_day_grouping",
    "weight": "medium",
    "description": "Prefer full days of FM clinic (AM+PM together)",
    "is_active": true
  }'
```

**Solver Behavior:**
- Tries to assign both AM and PM of FM clinic same day
- If not possible, applies 2x penalty to objective function
- Can violate if necessary to satisfy other constraints

---

## Summary

The Rotation API provides a flexible system for:
1. **Defining activity patterns** (clinic, inpatient, procedure, conference)
2. **Managing leave eligibility** to prevent coverage conflicts
3. **Specifying capacity and supervision constraints** for ACGME compliance
4. **Configuring soft preferences** for schedule optimization
5. **Supporting split/mirrored rotations** for complex scheduling patterns

Key integration points:
- **BlockSchedulerService**: Auto-assigns residents with leave to leave-eligible rotations
- **SchedulingConstraints**: Validates capacity and supervision ratios
- **AbsenceConflictDetection**: Alerts when approved leave conflicts with non-leave-eligible rotations

All endpoints require authentication and support full CRUD operations with proper validation and error handling.

