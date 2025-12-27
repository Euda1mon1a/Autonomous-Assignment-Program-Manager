***REMOVED*** Primary Duty Clinic Constraints

> **Version:** 1.0
> **Created:** 2025-12-27
> **Status:** Implemented

This document describes the Airtable-driven faculty clinic constraints that use primary duty configuration data for per-faculty scheduling rules.

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Data Source](***REMOVED***data-source)
3. [Constraint Classes](***REMOVED***constraint-classes)
4. [Configuration Fields](***REMOVED***configuration-fields)
5. [Integration with Solver](***REMOVED***integration-with-solver)
6. [Usage Examples](***REMOVED***usage-examples)
7. [Testing](***REMOVED***testing)

---

***REMOVED******REMOVED*** Overview

The primary duty constraint system provides **per-faculty clinic scheduling rules** that are more granular than the role-based defaults in `FacultyRoleClinicConstraint`.

***REMOVED******REMOVED******REMOVED*** Why Primary Duties?

| Approach | Granularity | Source |
|----------|-------------|--------|
| Role-based (`FacultyRoleClinicConstraint`) | Per role (PD, APD, Core, etc.) | Hardcoded in Person model |
| Primary Duty-based (this system) | Per individual faculty member | Airtable export JSON |

Primary duties allow:
- **Individual min/max targets** that differ from role defaults
- **Day-of-week availability** per faculty member
- **Clinic template restrictions** (only certain clinics allowed)

---

***REMOVED******REMOVED*** Data Source

***REMOVED******REMOVED******REMOVED*** Airtable Export Location

```
docs/schedules/sanitized_primary_duties.json
```

***REMOVED******REMOVED******REMOVED*** Data Structure

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

***REMOVED******REMOVED******REMOVED*** Sanitization

The file uses NATO phonetic alphabet identifiers (Alpha, Bravo, Charlie...) instead of real faculty names per OPSEC/PERSEC requirements.

---

***REMOVED******REMOVED*** Constraint Classes

***REMOVED******REMOVED******REMOVED*** 1. FacultyPrimaryDutyClinicConstraint (Hard)

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
***REMOVED*** Automatically loads from docs/schedules/sanitized_primary_duties.json
```

***REMOVED******REMOVED******REMOVED*** 2. FacultyDayAvailabilityConstraint (Hard)

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

***REMOVED******REMOVED******REMOVED*** 3. FacultyClinicEquitySoftConstraint (Soft)

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

***REMOVED******REMOVED*** Configuration Fields

***REMOVED******REMOVED******REMOVED*** PrimaryDutyConfig Dataclass

```python
@dataclass
class PrimaryDutyConfig:
    duty_id: str                    ***REMOVED*** Airtable record ID
    duty_name: str                  ***REMOVED*** e.g., "Faculty Alpha"
    clinic_min_per_week: int        ***REMOVED*** Minimum clinic half-days (default: 0)
    clinic_max_per_week: int        ***REMOVED*** Maximum clinic half-days (default: 10)
    available_days: set[int]        ***REMOVED*** Weekdays available (0=Mon, 4=Fri)
    allowed_clinic_templates: set[str]  ***REMOVED*** Allowed Airtable template IDs
    faculty_ids: list[str]          ***REMOVED*** Linked faculty Airtable IDs
```

***REMOVED******REMOVED******REMOVED*** Field Mapping from Airtable

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

***REMOVED******REMOVED*** Integration with Solver

***REMOVED******REMOVED******REMOVED*** Automatic Registration

The constraints are automatically registered in `ConstraintManager.create_default()`:

```python
***REMOVED*** backend/app/scheduling/constraints/manager.py

manager.add(FacultyPrimaryDutyClinicConstraint())
manager.add(FacultyDayAvailabilityConstraint())
manager.add(FacultyClinicEquitySoftConstraint(weight=15.0))
```

***REMOVED******REMOVED******REMOVED*** Solver Variables

The constraints work with `template_assignments` variables:

```python
template_vars = variables.get("template_assignments", {})
***REMOVED*** template_vars[(faculty_idx, block_idx, template_idx)] = binary variable
```

***REMOVED******REMOVED******REMOVED*** Clinic Template Identification

Clinic templates are identified by `activity_type == "outpatient"`:

```python
clinic_template_ids = {
    t.id
    for t in context.templates
    if hasattr(t, "activity_type") and t.activity_type == "outpatient"
}
```

***REMOVED******REMOVED******REMOVED*** Faculty Lookup

Faculty are linked to duty configs via the `primary_duty` field on Person model:

```python
***REMOVED*** Person model has primary_duty: str field
***REMOVED*** Constraint looks up: duty_configs.get(faculty.primary_duty)
```

---

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** Loading Configurations

```python
from app.scheduling.constraints.primary_duty import (
    load_primary_duties_config,
    PrimaryDutyConfig,
)

***REMOVED*** Load from default path
configs = load_primary_duties_config()

***REMOVED*** Load from custom path
configs = load_primary_duties_config("/path/to/custom.json")

***REMOVED*** Access specific duty
faculty_alpha = configs.get("Faculty Alpha")
print(f"Min: {faculty_alpha.clinic_min_per_week}")
print(f"Max: {faculty_alpha.clinic_max_per_week}")
```

***REMOVED******REMOVED******REMOVED*** Custom Configuration

```python
from app.scheduling.constraints import FacultyPrimaryDutyClinicConstraint

***REMOVED*** Create with custom configs (not from file)
custom_configs = {
    "Dr. Smith Duty": PrimaryDutyConfig(
        duty_id="custom1",
        duty_name="Dr. Smith Duty",
        clinic_min_per_week=3,
        clinic_max_per_week=5,
        available_days={0, 1, 3, 4},  ***REMOVED*** No Wednesday
    )
}

constraint = FacultyPrimaryDutyClinicConstraint(duty_configs=custom_configs)
```

***REMOVED******REMOVED******REMOVED*** Validation Only

```python
from app.scheduling.constraints import FacultyPrimaryDutyClinicConstraint

constraint = FacultyPrimaryDutyClinicConstraint()
result = constraint.validate(assignments, context)

if not result.satisfied:
    for violation in result.violations:
        print(f"{violation.message}")
```

---

***REMOVED******REMOVED*** Testing

***REMOVED******REMOVED******REMOVED*** Test File Location

```
backend/tests/scheduling/test_primary_duty_constraint.py
```

***REMOVED******REMOVED******REMOVED*** Test Classes

| Test Class | Coverage |
|------------|----------|
| `TestPrimaryDutyConfig` | Airtable record parsing |
| `TestLoadPrimaryDutiesConfig` | JSON file loading |
| `TestFacultyPrimaryDutyClinicConstraint` | Min/max enforcement |
| `TestFacultyDayAvailabilityConstraint` | Day blocking |
| `TestFacultyClinicEquitySoftConstraint` | Penalty calculation |

***REMOVED******REMOVED******REMOVED*** Running Tests

```bash
cd backend
pytest tests/scheduling/test_primary_duty_constraint.py -v
```

---

***REMOVED******REMOVED*** Relationship to Other Constraints

***REMOVED******REMOVED******REMOVED*** Constraint Hierarchy

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

***REMOVED******REMOVED******REMOVED*** Interaction Notes

1. **FacultyRoleClinicConstraint** uses hardcoded limits from `Person.weekly_clinic_limit`
2. **FacultyPrimaryDutyClinicConstraint** uses JSON config limits
3. Both can be enabled simultaneously - the stricter constraint wins
4. **FacultyDayAvailabilityConstraint** complements both by blocking specific days

---

***REMOVED******REMOVED*** Updating Primary Duty Data

***REMOVED******REMOVED******REMOVED*** When to Update

Update the JSON file when:
- Faculty primary duties change
- Clinic min/max requirements change
- Day availability changes
- New faculty join the program

***REMOVED******REMOVED******REMOVED*** Update Process

1. Export from Airtable (primary_duties table)
2. Sanitize real names → NATO phonetic alphabet
3. Save to `docs/schedules/sanitized_primary_duties.json`
4. Verify with tests:
   ```bash
   pytest tests/scheduling/test_primary_duty_constraint.py -v
   ```

***REMOVED******REMOVED******REMOVED*** Airtable Field Requirements

Ensure these fields exist in the Airtable primary_duties table:
- `primaryDuty` (text)
- `Clinic Minimum Half-Days Per Week` (number)
- `Clinic Maximum Half-Days Per Week` (number)
- `availableMonday` through `availableFriday` (checkbox)
- `attendingClinicTemplates` (linked records)
- `Faculty` (linked records)

---

***REMOVED******REMOVED*** Future Enhancements

***REMOVED******REMOVED******REMOVED*** Planned

1. **Template Restriction Enforcement**: Use `allowed_clinic_templates` to restrict which clinics a faculty can be assigned to
2. **Inpatient Constraints**: Extend to `Inpatient Weeks Minimum/Maximum`
3. **GME Constraints**: Extend to `Graduate Medical Education Half-Days`
4. **Database Sync**: Load from database instead of JSON file

***REMOVED******REMOVED******REMOVED*** Under Consideration

1. **Block-level flexibility**: Allow APD/OIC to have 0 one week, 4 another (block total = 8)
2. **Preference integration**: Use primary duty data for soft preferences
3. **Real-time Airtable sync**: Webhook-triggered config updates

---

***REMOVED******REMOVED*** References

- [FACULTY_SCHEDULING_SPECIFICATION.md](FACULTY_SCHEDULING_SPECIFICATION.md) - Role definitions
- [clinic-constraints.md](clinic-constraints.md) - Clinic capacity constraints
- `backend/app/scheduling/constraints/primary_duty.py` - Implementation
- `backend/tests/scheduling/test_primary_duty_constraint.py` - Tests
