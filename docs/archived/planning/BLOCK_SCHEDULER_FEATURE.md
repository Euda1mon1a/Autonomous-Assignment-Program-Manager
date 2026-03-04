# Block Scheduler Feature: Leave-Eligible Rotation Matching

> **Status:** Implemented
> **Created:** 2025-12-30
> **Implemented:** 2025-12-30
> **Priority:** High (operational requirement)
> **Related:** Rotation Template GUI (completed)

---

## Overview

A block scheduler that factors in resident leave requests and matches them with leave-eligible rotations. This ensures residents taking leave are assigned to rotations where coverage can be managed without disrupting critical services.

---

## Problem Statement

Currently:
1. Residents submit leave requests
2. Leave is approved/denied based on manual review
3. Rotation assignments may conflict with leave periods
4. FMIT/inpatient rotations require coverage when someone is on leave

**Need:** Automated matching of residents to leave-eligible rotations when they have approved leave during a block.

---

## Core Requirements

### 1. Leave-Eligible Rotation Matching

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BLOCK SCHEDULER LOGIC                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Residents with approved leave in Block N                              │
│  ├── Rotation templates (with leave_eligible flag)                         │
│  └── Block constraints (ACGME, capacity, specialty requirements)           │
│                                                                             │
│  PROCESSING:                                                                │
│  ├── For each resident with leave:                                         │
│  │   ├── Filter rotations where leave_eligible = True                      │
│  │   ├── Check capacity constraints                                        │
│  │   ├── Check specialty/PGY requirements                                  │
│  │   └── Assign to best-fit leave-eligible rotation                        │
│  │                                                                          │
│  ├── For remaining residents:                                              │
│  │   ├── Assign to any eligible rotation (including leave_eligible=False)  │
│  │   └── Balance coverage for FMIT/inpatient                               │
│  │                                                                          │
│  └── Validate ACGME compliance                                             │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── Block assignments for all residents                                   │
│  ├── Coverage gaps identified                                              │
│  └── Leave conflict warnings                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2. Leave Types to Consider

| Leave Type | Priority | Scheduling Impact |
|------------|----------|-------------------|
| **Annual Leave** | Standard | Must be on leave-eligible rotation |
| **Sick Leave** | Emergency | Generate coverage alert |
| **Conference** | Scheduled | Must be on leave-eligible rotation |
| **Military TDY** | High | Extended absence, may span blocks |
| **Maternity/Paternity** | Protected | Multi-block planning needed |
| **Bereavement** | Emergency | Generate coverage alert |

### 3. Rotation Categories

**Leave-Eligible (leave_eligible = True):**
- Elective rotations
- Outpatient specialty clinics
- Non-critical clinic time
- Research blocks

**Not Leave-Eligible (leave_eligible = False):**
- FMIT (Family Medicine Inpatient Teaching)
- Night Float
- OB coverage
- ICU rotations
- Any 24/7 coverage requirement

---

## Data Model Considerations

### Existing Fields

Already have in `RotationTemplate`:
```python
leave_eligible = Column(Boolean, default=True, nullable=False)
```

### May Need

```python
# Absence model may need:
class Absence:
    # ... existing fields ...
    block_id: UUID  # Link to specific block
    rotation_preference: str  # Resident's preferred rotation during leave block
    auto_assigned: bool  # Was this auto-matched by block scheduler?

# New table for block assignments
class BlockAssignment:
    id: UUID
    block_number: int  # 1-13
    academic_year: int
    resident_id: UUID
    rotation_template_id: UUID
    has_leave: bool  # Does resident have leave during this block?
    leave_days: int  # Number of leave days in block
    assignment_reason: str  # "leave_eligible_match", "manual", "balanced"
    created_at: datetime
```

---

## Algorithm Sketch

```python
def schedule_block(block_number: int, residents: list[Resident]) -> list[BlockAssignment]:
    """
    Schedule all residents for a single block.

    Priority order:
    1. Residents with approved leave -> leave-eligible rotations
    2. Residents with specialty requirements -> matching rotations
    3. Remaining residents -> balance across all rotations
    4. Validate ACGME compliance
    """

    assignments = []

    # 1. Get residents with leave in this block
    residents_with_leave = get_residents_with_leave(block_number, residents)

    # 2. Get leave-eligible rotations with capacity
    leave_eligible_rotations = get_rotations(leave_eligible=True)

    # 3. Match residents with leave to leave-eligible rotations
    for resident in residents_with_leave:
        best_rotation = find_best_match(
            resident,
            leave_eligible_rotations,
            criteria=[
                "specialty_match",
                "pgy_level",
                "capacity_available",
                "preference_score"
            ]
        )
        assignments.append(BlockAssignment(
            resident=resident,
            rotation=best_rotation,
            has_leave=True,
            assignment_reason="leave_eligible_match"
        ))
        update_capacity(best_rotation)

    # 4. Assign remaining residents
    remaining = [r for r in residents if r not in residents_with_leave]
    all_rotations = get_rotations()  # Including non-leave-eligible

    for resident in remaining:
        # Prioritize FMIT/inpatient coverage
        best_rotation = find_best_match(
            resident,
            all_rotations,
            criteria=[
                "coverage_need",  # FMIT needs coverage first
                "specialty_match",
                "pgy_level",
                "capacity_available"
            ]
        )
        assignments.append(BlockAssignment(
            resident=resident,
            rotation=best_rotation,
            has_leave=False,
            assignment_reason="balanced"
        ))

    # 5. Validate
    validate_acgme_compliance(assignments)
    validate_coverage(assignments)

    return assignments
```

---

## UI Considerations

### Block Scheduler Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  BLOCK 5 SCHEDULER                                      Jan 27 - Feb 23    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEAVE REQUESTS THIS BLOCK: 4                                               │
│  ├── Dr. Smith: Jan 30 - Feb 3 (Annual Leave)                              │
│  ├── Dr. Jones: Feb 10-12 (Conference)                                     │
│  ├── Dr. Lee: Feb 15-17 (TDY)                                              │
│  └── Dr. Patel: Feb 1 (Sick - coverage needed)                             │
│                                                                             │
│  ROTATION CAPACITY                                                          │
│  ─────────────────                                                          │
│  │ FMIT           │ ████████░░ │ 4/5 assigned │ NEEDS COVERAGE             │
│  │ Sports Med     │ ██████░░░░ │ 3/5 assigned │ Leave-eligible ✓           │
│  │ Derm Elective  │ ████░░░░░░ │ 2/5 assigned │ Leave-eligible ✓           │
│  │ Research       │ ██░░░░░░░░ │ 1/5 assigned │ Leave-eligible ✓           │
│                                                                             │
│  [Auto-Assign with Leave Priority] [Manual Override] [Validate]            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Integration with Rotation Template GUI

The `leave_eligible` toggle in the Rotation Template GUI directly affects:
- Which rotations appear as options for residents with leave
- Coverage planning for non-leave-eligible rotations
- Automated block scheduling priority

---

## Implementation Phases

### Phase 1: Data Foundation ✅
- [x] Add block assignment tracking (`BlockAssignment` model)
- [x] Link absences to blocks (via date overlap detection)
- [x] Query for leave-eligible rotation availability

### Phase 2: Matching Algorithm ✅
- [x] Implement resident-to-rotation matching (`BlockSchedulerService`)
- [x] Add capacity tracking (`RotationSlot` with available/is_full)
- [x] Add coverage gap detection

### Phase 3: API Integration ✅
- [x] Block scheduler dashboard endpoint (`/block-scheduler/dashboard`)
- [x] Schedule preview/execute endpoint (`/block-scheduler/schedule`)
- [x] Coverage gap alerts in response

### Phase 4: Future Enhancements
- [ ] Auto-assign on leave approval (webhook integration)
- [ ] Frontend UI components
- [ ] Swap suggestions when conflicts arise

---

## Dependencies

- **Rotation Template GUI** (current session) - Provides `leave_eligible` toggle
- **Absence Management** - Source of leave requests
- **ACGME Validator** - Compliance checking
- **Schedule Generator** - Integration for full schedule optimization

---

## Questions for Future Session

1. Should auto-assignment happen immediately on leave approval, or batch at block start?
2. How to handle leave requests that span multiple blocks?
3. Priority when multiple residents with leave compete for same rotation?
4. Should residents be able to request specific leave-eligible rotations?
5. How to handle last-minute leave (sick, emergency) vs. planned leave?

---

## Related Files

### Core Implementation
- `backend/app/models/block_assignment.py` - BlockAssignment model
- `backend/app/schemas/block_assignment.py` - Pydantic schemas
- `backend/app/repositories/block_assignment.py` - Data access layer
- `backend/app/services/block_scheduler_service.py` - Leave-eligible matching algorithm
- `backend/app/controllers/block_scheduler_controller.py` - Request handling
- `backend/app/api/routes/block_scheduler.py` - API endpoints

### Migration
- `backend/alembic/versions/20251230_add_block_assignments.py` - Database migration

### Tests
- `backend/tests/services/test_block_scheduler_service.py` - Unit tests

### Dependencies
- `backend/app/models/rotation_template.py` - `leave_eligible` field
- `backend/app/models/absence.py` - Leave request model
- `backend/app/scheduling/` - Scheduling engine
