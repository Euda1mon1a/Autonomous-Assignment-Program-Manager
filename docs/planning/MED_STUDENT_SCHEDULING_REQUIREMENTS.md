# Medical Student & Rotating Intern Scheduling Requirements

> **Status:** Draft - Pending Implementation
> **Created:** 2025-12-23
> **Source:** Med Student Coordinator Interview
> **Rotation:** Family Medicine

---

## Overview

Support scheduling for up to **7 concurrent medical students** plus rotating interns on Family Medicine rotation. These learners have different constraints than FM residents:

### Learner Types

| Type | Abbreviation | FMIT Required | Notes |
|------|--------------|---------------|-------|
| Medical Student | MS | Yes (1 week) | MS3/MS4 on FM clerkship |
| Transitional Year Intern | TY | No | Non-FM intern rotating through |
| Psychiatry Intern | PSYCH | No | Non-FM intern rotating through |

### Key Scheduling Concept

**Learners do NOT have their own clinic slots.** They are **paired with existing attending/resident clinic sessions**:

- Attending has clinic → assign 1-2 learners to shadow/see patients with them
- Learners "help see clinic" - e.g., 2 med students each see 2 patients in attending's clinic
- This is an **overlay** on existing schedule, not separate slots

Med students have different constraints than residents:

- No LCME hour tracking (unlike ACGME for residents)
- Max 2 learners per physician (supervision ratio)
- Prefer attendings over residents for clinic supervision (soft constraint)
- Need exposure to variety of faculty/residents (staggered templates)

---

## Glossary

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **FMIT** | Family Medicine Inpatient Team | Inpatient rotation; med students do 1 week with overnight call Thursday |
| **PC** | Post Call | Day after overnight call; lighter duties or recovery |
| **ASM** | Academic Sports Medicine | Wednesday AM didactic/clinic session for all med students |
| **LCME** | Liaison Committee on Medical Education | Accrediting body for med schools (does NOT track hours like ACGME) |
| **TY** | Transitional Year Intern | Non-FM intern rotating through; same schedule as MS but no FMIT |
| **PSYCH** | Psychiatry Intern | Psychiatry intern rotating through; same schedule as MS but no FMIT |
| **MS** | Medical Student | MS3 or MS4 on Family Medicine clerkship |

---

## Block Structure

### Duration
- **4-week blocks** (same as resident blocks)
- **Half-day granularity**: AM and PM sessions

### Block Boundaries

| Day | Session | Activity |
|-----|---------|----------|
| **First day of block** | AM | Inprocessing |
| **First day of block** | PM | Normal schedule begins |
| **Last Friday of block** | AM | Normal schedule |
| **Last Friday of block** | PM | Studying / Outprocessing |

---

## Weekly Schedule Template

### Standard Week (Non-FMIT)

| Day | AM | PM | Notes |
|-----|----|----|-------|
| Monday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |
| Tuesday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |
| Wednesday | **ASM** | Normal template | ASM is fixed for all med students |
| Thursday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |
| Friday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |

### FMIT Week (1 week per block)

| Day | AM | PM | Notes |
|-----|----|----|-------|
| Monday | FMIT | FMIT | Inpatient team |
| Tuesday | FMIT | FMIT | Inpatient team |
| Wednesday | **ASM** | FMIT | ASM still required |
| Thursday | FMIT | FMIT | **Overnight call starts** |
| Thursday Night | Call | Call | Overnight on inpatient |
| Friday | **PC** | **PC** | Post Call - recovery day |

---

## Constraints

### Hard Constraints

1. **ASM Wednesday AM**: All learners have Wednesday AM blocked for ASM
2. **Wednesday PM Didactics**: Same afternoon didactics as residents
3. **4th Wednesday Inverted**: On the 4th Wednesday of the block, schedule is inverted (TBD: AM/PM swap?)
4. **Max 2 learners per physician**: Any attending or PGY-2/3 resident can supervise max 2 learners
5. **FM Interns cannot supervise**: PGY-1 FM interns get 0 learners assigned to them
6. **Procedures conflict**: Learner NOT in procedures if FM intern (PGY-1) is assigned there
7. **Inprocessing**: First AM of block is unavailable (orientation)
8. **Outprocessing**: Last Friday PM is unavailable (studying/checkout)
9. **Weekends**: Learners only work weekends during FMIT week (follows resident schedule)
10. **Night coverage**: Only FMIT Thursday overnight - no separate night float rotations

### Soft Constraints

1. **Attending preference**: Prefer scheduling med students with attendings (not residents) in clinic
2. **Variety exposure**: Stagger templates so each med student works with different faculty/residents across the block
3. **FMIT week placement**: Can be any week of the 4-week block (flexible for staggering)

---

## Learner Track System

### Concept: Generic Tracks

Instead of creating templates tied to specific people, use **7 generic learner tracks** that actual learners get assigned to:

```
Track 1  ──→  [Block assignments for Track 1]  ──→  "Jane Doe (MS3)" assigned to Track 1
Track 2  ──→  [Block assignments for Track 2]  ──→  "John Smith (TY)" assigned to Track 2
...
Track 7  ──→  [Block assignments for Track 7]  ──→  (unassigned)
```

### Backend Requirements

1. **Track entity**: `LearnerTrack` with ID 1-7 (or A-G)
2. **Track schedule**: Each track has block assignments (clinic pairings, FMIT week, etc.)
3. **Person assignment**: Assign actual learner (Person) to a track for a date range
4. **Add/remove flexibility**:
   - Can add new block assignments to a track
   - Can remove block assignments (with warning: "This will affect assigned learners")

### Frontend GUI Workflow

1. Coordinator views Track 1's schedule for Block 5
2. Adds/modifies half-day assignments (pair with Dr. Smith AM, procedures PM, etc.)
3. Assigns "Jane Doe" to Track 1 for Block 5-6 date range
4. Jane sees her schedule populated from Track 1

### Staggered FMIT Distribution

| Track | FMIT Week | Notes |
|-------|-----------|-------|
| Track 1 | Week 1 | |
| Track 2 | Week 2 | |
| Track 3 | Week 3 | |
| Track 4 | Week 4 | |
| Track 5 | Week 1 | Offset clinic assignments from Track 1 |
| Track 6 | Week 2 | Offset clinic assignments from Track 2 |
| Track 7 | Week 3 | Offset clinic assignments from Track 3 |

> **Note**: TY/PSYCH interns use same tracks but skip FMIT week (substitute with clinic/procedures).

---

## Data Model Changes Required

### Person Model

Add learner types to valid person types:

```python
# Current constraint
CheckConstraint("type IN ('resident', 'faculty')", name="check_person_type")

# New constraint - add learner types
CheckConstraint(
    "type IN ('resident', 'faculty', 'med_student', 'rotating_intern')",
    name="check_person_type"
)
```

### New Fields for Learners

```python
# Learner-specific fields (med students and rotating interns)
learner_type = Column(String(50))  # 'MS', 'TY', 'PSYCH' (for rotating_intern type)
med_school = Column(String(255))  # e.g., "USUHS", "Harvard" (for med_students)
ms_year = Column(Integer)  # 3 or 4 (MS3, MS4) - null for rotating interns
rotation_start_date = Column(Date)  # When their FM rotation starts
rotation_end_date = Column(Date)  # When their FM rotation ends
requires_fmit = Column(Boolean, default=True)  # True for MS, False for TY/PSYCH
```

### Learner Assignment Model (NEW)

Since learners are **paired with existing clinic assignments** (not their own slots), we need a separate assignment model:

```python
class LearnerAssignment(Base):
    """
    Pairs a learner (med student, TY, PSYCH) with an existing clinic assignment.

    This is an OVERLAY on the main schedule - learners don't have their own
    clinic slots, they are assigned to work with someone who already has one.
    """
    __tablename__ = "learner_assignments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # The learner being assigned
    learner_id = Column(GUID(), ForeignKey("people.id"), nullable=False)

    # The existing assignment they're paired with (attending/resident's clinic)
    parent_assignment_id = Column(GUID(), ForeignKey("assignments.id"), nullable=False)

    # Or for non-clinic activities (FMIT, ASM, procedures)
    block_id = Column(GUID(), ForeignKey("blocks.id"))
    activity_type = Column(String(50))  # 'FMIT', 'ASM', 'procedures', 'clinic'

    # Relationships
    learner = relationship("Person", foreign_keys=[learner_id])
    parent_assignment = relationship("Assignment")
    block = relationship("Block")

    __table_args__ = (
        # Max 2 learners per parent assignment
        # (enforced at application level, not DB constraint)
    )
```

### Learner Track Model (NEW)

Generic tracks that learners get assigned to:

```python
class LearnerTrack(Base):
    """
    A generic learner track (1-7) that actual learners are assigned to.

    Tracks have their own schedule templates. When a learner is assigned
    to a track, they inherit that track's schedule for their rotation period.
    """
    __tablename__ = "learner_tracks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    track_number = Column(Integer, nullable=False, unique=True)  # 1-7
    name = Column(String(50))  # "Track 1" or "Track A" - display name

    # Default FMIT week for this track (1-4), null for TY/PSYCH tracks
    default_fmit_week = Column(Integer)

    # Relationships
    assignments = relationship("LearnerTrackAssignment", back_populates="track")
    learner_assignments = relationship("LearnerToTrack", back_populates="track")


class LearnerToTrack(Base):
    """
    Assigns a specific learner (Person) to a track for a date range.
    """
    __tablename__ = "learner_to_tracks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    learner_id = Column(GUID(), ForeignKey("people.id"), nullable=False)
    track_id = Column(GUID(), ForeignKey("learner_tracks.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Override FMIT requirement (False for TY/PSYCH even on MS track)
    requires_fmit = Column(Boolean, default=True)

    # Relationships
    learner = relationship("Person")
    track = relationship("LearnerTrack", back_populates="learner_assignments")
```

---

## Supervision Tracking

### Supervision Rules

| Supervisor Type | Max Learners | Notes |
|-----------------|--------------|-------|
| Attending (any) | 2 | Can supervise MS, TY, PSYCH |
| PGY-2/PGY-3 Resident | 2 | Can supervise, but prefer attendings |
| PGY-1 FM Intern | **0** | Cannot supervise any learners |

### Learner Counting

When assigning a learner to a clinic session, validate supervisor capacity:

```python
def can_supervise_learners(person: Person) -> bool:
    """Check if this person can supervise learners."""
    if person.is_faculty:
        return True
    if person.is_resident and person.pgy_level >= 2:
        return True  # PGY-2/3 can supervise
    return False  # PGY-1 cannot supervise


def count_learners_with_supervisor(block_id: UUID, supervisor_id: UUID) -> int:
    """Count learners currently assigned to this supervisor in this block."""
    return db.query(LearnerAssignment).filter(
        LearnerAssignment.parent_assignment.has(
            Assignment.block_id == block_id,
            Assignment.person_id == supervisor_id
        )
    ).count()


def can_assign_learner(block_id: UUID, supervisor_id: UUID) -> bool:
    """Check if supervisor has capacity for another learner."""
    supervisor = get_person(supervisor_id)
    if not can_supervise_learners(supervisor):
        return False
    return count_learners_with_supervisor(block_id, supervisor_id) < 2
```

---

## Conflict Detection

### Procedures Conflict

```python
def check_procedures_conflict(block_id: UUID, med_student_id: UUID) -> bool:
    """
    Med student cannot be in procedures if an intern is there.

    Returns True if conflict exists (intern already in procedures).
    """
    intern_in_procedures = db.query(Assignment).filter(
        Assignment.block_id == block_id,
        Assignment.rotation_template.has(activity_type="procedure"),
        Assignment.person.has(type="resident", pgy_level=1)
    ).first()

    return intern_in_procedures is not None
```

---

## UI Considerations

### Schedule View

- Med students should appear in a separate section/color from residents
- Show current learner count per attending in clinic view
- Highlight conflicts (procedures with intern)

### Reporting

- Block summary: Show med student assignments alongside residents
- Attending workload: Include med student supervision in learner counts

---

## Implementation Phases

### Phase 1: Data Model
- [ ] Add `med_student` to Person type constraint
- [ ] Add med student specific fields
- [ ] Create Alembic migration
- [ ] Create 7 rotation templates

### Phase 2: Constraints
- [ ] Implement ASM Wednesday AM hard constraint
- [ ] Implement max 2 learners per physician
- [ ] Implement procedures/intern conflict detection
- [ ] Implement inprocessing/outprocessing blocks

### Phase 3: Scheduling Logic
- [ ] Create med student schedule generator
- [ ] Implement template staggering algorithm
- [ ] Add attending preference soft constraint

### Phase 4: API & UI
- [ ] Create med student CRUD endpoints
- [ ] Add med student schedule view
- [ ] Add conflict warnings to UI

---

## Open Questions

1. ~~**Weekend coverage**: Do med students ever work weekends?~~ ✅ Only during FMIT week
2. ~~**Night float**: Do med students participate in night float, or just FMIT overnight?~~ ✅ FMIT overnight only
3. **4th Wednesday "inverted"**: What exactly is inverted? AM/PM swap? Different activities?
4. **Clinic locations**: Which specific clinics do med students rotate through? Same as residents?
5. **Leave requests**: Can med students request time off during the 4-week block?

---

## References

- Existing template structure: `backend/app/models/rotation_template.py`
- FMIT constraints: `backend/app/scheduling/constraints/fmit.py`
- Block model: `backend/app/models/block.py`
- Faculty scheduling spec: `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md`
