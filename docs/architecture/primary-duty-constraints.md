# Primary Duty Clinic Constraints

> **Version:** 1.0
> **Created:** 2025-12-27
> **Status:** Implemented

This document describes the Airtable-driven faculty clinic constraints that use primary duty configuration data for per-faculty scheduling rules.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Source](#data-source)
3. [Constraint Classes](#constraint-classes)
4. [Configuration Fields](#configuration-fields)
5. [Integration with Solver](#integration-with-solver)
6. [Usage Examples](#usage-examples)
7. [Testing](#testing)

---

## Overview

The primary duty constraint system provides **per-faculty clinic scheduling rules** that are more granular than the role-based defaults in `FacultyRoleClinicConstraint`.

### Why Primary Duties?

| Approach | Granularity | Source |
|----------|-------------|--------|
| Role-based (`FacultyRoleClinicConstraint`) | Per role (PD, APD, Core, etc.) | Hardcoded in Person model |
| Primary Duty-based (this system) | Per individual faculty member | Airtable export JSON |

Primary duties allow:
- **Individual min/max targets** that differ from role defaults
- **Day-of-week availability** per faculty member
- **Clinic template restrictions** (only certain clinics allowed)

---

## Data Source

### Airtable Export Location

```
docs/schedules/sanitized_primary_duties.json
```

### Data Structure

The JSON contains an array of Airtable records:

```json
{
  "fetched_at": "2025-12-25T20:46:40.568434",
  "table_name": "primary_duties",
  "record_count": 25,
  "records": [
    {
      "id": "recgREn5x6J5HN5pz",
      "fields": {
        "primaryDuty": "Faculty Alpha",
        "Clinic Minimum Half-Days Per Week": 2,
        "Clinic Maximum Half-Days Per Week": 4,
        "availableMonday": true,
        "availableTuesday": true,
        "availableWednesday": true,
        "availableThursday": true,
        "availableFriday": true,
        "attendingClinicTemplates": ["recA", "recB", ...],
        "Faculty": ["recWg0eLb8COLXaGh"]
      }
    }
  ]
}
```

### Sanitization

The file uses NATO phonetic alphabet identifiers (Alpha, Bravo, Charlie...) instead of real faculty names per OPSEC/PERSEC requirements.

---

## Constraint Classes

### 1. FacultyPrimaryDutyClinicConstraint (Hard)

**Purpose:** Enforces minimum and maximum clinic half-days per week based on primary duty configuration.

**Priority:** HIGH (ConstraintPriority.HIGH)

**Constraint Type:** CAPACITY

**Behavior:**
- **Minimum requirement**: Faculty must have at least `clinic_min_per_week` clinic sessions
- **Maximum limit**: Faculty cannot exceed `clinic_max_per_week` clinic sessions
- **Scope**: Enforced per calendar week (Monday-Sunday)

**Violations:**
- `severity: HIGH` when below minimum
- `severity: HIGH` when exceeding maximum

```python
from app.scheduling.constraints import FacultyPrimaryDutyClinicConstraint

constraint = FacultyPrimaryDutyClinicConstraint()
# Automatically loads from docs/schedules/sanitized_primary_duties.json
```

### 2. FacultyDayAvailabilityConstraint (Hard)

**Purpose:** Prevents clinic assignments on days when faculty are unavailable.

**Priority:** CRITICAL (ConstraintPriority.CRITICAL)

**Constraint Type:** AVAILABILITY

**Behavior:**
- Reads `availableMonday` through `availableFriday` flags
- Blocks all clinic assignments on unavailable days
- Does not affect non-clinic assignments

**Example:**
- Faculty Alpha has `availableWednesday: false`
- Any Wednesday clinic assignment for Faculty Alpha is blocked

```python
from app.scheduling.constraints import FacultyDayAvailabilityConstraint

constraint = FacultyDayAvailabilityConstraint()
```

### 3. FacultyClinicEquitySoftConstraint (Soft)

**Purpose:** Optimizes toward target clinic coverage (midpoint of min/max).

**Priority:** MEDIUM (ConstraintPriority.MEDIUM)

**Constraint Type:** EQUITY

**Weight:** 15.0 (default)

**Behavior:**
- Calculates target as `(min + max) // 2`
- Penalizes deviation from target
- Does not make schedule infeasible (soft constraint)

```python
from app.scheduling.constraints import FacultyClinicEquitySoftConstraint

constraint = FacultyClinicEquitySoftConstraint(weight=15.0)
```

---

## Configuration Fields

### PrimaryDutyConfig Dataclass

```python
@dataclass
class PrimaryDutyConfig:
    duty_id: str                    # Airtable record ID
    duty_name: str                  # e.g., "Faculty Alpha"
    clinic_min_per_week: int        # Minimum clinic half-days (default: 0)
    clinic_max_per_week: int        # Maximum clinic half-days (default: 10)
    available_days: set[int]        # Weekdays available (0=Mon, 4=Fri)
    allowed_clinic_templates: set[str]  # Allowed Airtable template IDs
    faculty_ids: list[str]          # Linked faculty Airtable IDs
```

### Field Mapping from Airtable

| Airtable Field | Python Field | Notes |
|----------------|--------------|-------|
| `primaryDuty` | `duty_name` | Human-readable name |
| `Duty ID` | `duty_id` | Same as record ID |
| `Clinic Minimum Half-Days Per Week` | `clinic_min_per_week` | 0 if not set |
| `Clinic Maximum Half-Days Per Week` | `clinic_max_per_week` | 10 if not set |
| `availableMonday` | `available_days` | 0 if true |
| `availableTuesday` | `available_days` | 1 if true |
| `availableWednesday` | `available_days` | 2 if true |
| `availableThursday` | `available_days` | 3 if true |
| `availableFriday` | `available_days` | 4 if true |
| `attendingClinicTemplates` | `allowed_clinic_templates` | Set of template IDs |
| `Faculty` | `faculty_ids` | List of faculty record IDs |

---

## Integration with Solver

### Automatic Registration

The constraints are automatically registered in `ConstraintManager.create_default()`:

```python
# backend/app/scheduling/constraints/manager.py

manager.add(FacultyPrimaryDutyClinicConstraint())
manager.add(FacultyDayAvailabilityConstraint())
manager.add(FacultyClinicEquitySoftConstraint(weight=15.0))
```

### Solver Variables

The constraints work with `template_assignments` variables:

```python
template_vars = variables.get("template_assignments", {})
# template_vars[(faculty_idx, block_idx, template_idx)] = binary variable
```

### Clinic Template Identification

Clinic templates are identified by `rotation_type == "outpatient"`:

```python
clinic_template_ids = {
    t.id
    for t in context.templates
    if hasattr(t, "rotation_type") and t.rotation_type == "outpatient"
}
```

### Faculty Lookup

Faculty are linked to duty configs via the `primary_duty` field on Person model:

```python
# Person model has primary_duty: str field
# Constraint looks up: duty_configs.get(faculty.primary_duty)
```

---

## Usage Examples

### Loading Configurations

```python
from app.scheduling.constraints.primary_duty import (
    load_primary_duties_config,
    PrimaryDutyConfig,
)

# Load from default path
configs = load_primary_duties_config()

# Load from custom path
configs = load_primary_duties_config("/path/to/custom.json")

# Access specific duty
faculty_alpha = configs.get("Faculty Alpha")
print(f"Min: {faculty_alpha.clinic_min_per_week}")
print(f"Max: {faculty_alpha.clinic_max_per_week}")
```

### Custom Configuration

```python
from app.scheduling.constraints import FacultyPrimaryDutyClinicConstraint

# Create with custom configs (not from file)
custom_configs = {
    "Dr. Smith Duty": PrimaryDutyConfig(
        duty_id="custom1",
        duty_name="Dr. Smith Duty",
        clinic_min_per_week=3,
        clinic_max_per_week=5,
        available_days={0, 1, 3, 4},  # No Wednesday
    )
}

constraint = FacultyPrimaryDutyClinicConstraint(duty_configs=custom_configs)
```

### Validation Only

```python
from app.scheduling.constraints import FacultyPrimaryDutyClinicConstraint

constraint = FacultyPrimaryDutyClinicConstraint()
result = constraint.validate(assignments, context)

if not result.satisfied:
    for violation in result.violations:
        print(f"{violation.message}")
```

---

## Testing

### Test File Location

```
backend/tests/scheduling/test_primary_duty_constraint.py
```

### Test Classes

| Test Class | Coverage |
|------------|----------|
| `TestPrimaryDutyConfig` | Airtable record parsing |
| `TestLoadPrimaryDutiesConfig` | JSON file loading |
| `TestFacultyPrimaryDutyClinicConstraint` | Min/max enforcement |
| `TestFacultyDayAvailabilityConstraint` | Day blocking |
| `TestFacultyClinicEquitySoftConstraint` | Penalty calculation |

### Running Tests

```bash
cd backend
pytest tests/scheduling/test_primary_duty_constraint.py -v
```

---

## Relationship to Other Constraints

### Constraint Hierarchy

```
Faculty Clinic Scheduling Constraints
├── FacultyRoleClinicConstraint (hardcoded role limits)
│   └── Based on FacultyRole enum (PD, APD, Core, etc.)
│
├── FacultyPrimaryDutyClinicConstraint (Airtable-driven)  ← NEW
│   └── Based on primary_duty field → JSON config
│
├── FacultyDayAvailabilityConstraint (Airtable-driven)    ← NEW
│   └── Blocks unavailable days from primary duty config
│
├── SMFacultyClinicConstraint (specialty-specific)
│   └── Sports Medicine faculty → no regular clinic
│
└── FacultyClinicEquitySoftConstraint (optimization)       ← NEW
    └── Soft penalty for deviation from target
```

### Interaction Notes

1. **FacultyRoleClinicConstraint** uses hardcoded limits from `Person.weekly_clinic_limit`
2. **FacultyPrimaryDutyClinicConstraint** uses JSON config limits
3. Both can be enabled simultaneously - the stricter constraint wins
4. **FacultyDayAvailabilityConstraint** complements both by blocking specific days

---

## Updating Primary Duty Data

### When to Update

Update the JSON file when:
- Faculty primary duties change
- Clinic min/max requirements change
- Day availability changes
- New faculty join the program

### Update Process

1. Export from Airtable (primary_duties table)
2. Sanitize real names → NATO phonetic alphabet
3. Save to `docs/schedules/sanitized_primary_duties.json`
4. Verify with tests:
   ```bash
   pytest tests/scheduling/test_primary_duty_constraint.py -v
   ```

### Airtable Field Requirements

Ensure these fields exist in the Airtable primary_duties table:
- `primaryDuty` (text)
- `Clinic Minimum Half-Days Per Week` (number)
- `Clinic Maximum Half-Days Per Week` (number)
- `availableMonday` through `availableFriday` (checkbox)
- `attendingClinicTemplates` (linked records)
- `Faculty` (linked records)

---

## Future Enhancements

### Planned

1. **Template Restriction Enforcement**: Use `allowed_clinic_templates` to restrict which clinics a faculty can be assigned to
2. **Inpatient Constraints**: Extend to `Inpatient Weeks Minimum/Maximum`
3. **GME Constraints**: Extend to `Graduate Medical Education Half-Days`
4. **Database Sync**: Load from database instead of JSON file

### Under Consideration

1. **Block-level flexibility**: Allow APD/OIC to have 0 one week, 4 another (block total = 8)
2. **Preference integration**: Use primary duty data for soft preferences
3. **Real-time Airtable sync**: Webhook-triggered config updates

---

## References

- [FACULTY_SCHEDULING_SPECIFICATION.md](FACULTY_SCHEDULING_SPECIFICATION.md) - Role definitions
- [clinic-constraints.md](clinic-constraints.md) - Clinic capacity constraints
- `backend/app/scheduling/constraints/primary_duty.py` - Implementation
- `backend/tests/scheduling/test_primary_duty_constraint.py` - Tests
