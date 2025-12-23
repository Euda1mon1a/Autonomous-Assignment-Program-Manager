***REMOVED*** Medical Student Scheduling Requirements

> **Status:** Draft - Pending Implementation
> **Created:** 2025-12-23
> **Source:** Med Student Coordinator Interview
> **Rotation:** Family Medicine

---

***REMOVED******REMOVED*** Overview

Support scheduling for up to **7 concurrent medical students** on Family Medicine rotation. Med students have different constraints than residents:

- No LCME hour tracking (unlike ACGME for residents)
- Max 2 learners per physician (supervision ratio)
- Prefer attendings over residents for clinic supervision (soft constraint)
- Need exposure to variety of faculty/residents (staggered templates)

---

***REMOVED******REMOVED*** Glossary

| Abbreviation | Full Name | Description |
|--------------|-----------|-------------|
| **FMIT** | Family Medicine Inpatient Team | Inpatient rotation; med students do 1 week with overnight call Thursday |
| **PC** | Post Call | Day after overnight call; lighter duties or recovery |
| **ASM** | Academic Sports Medicine | Wednesday AM didactic/clinic session for all med students |
| **LCME** | Liaison Committee on Medical Education | Accrediting body for med schools (does NOT track hours like ACGME) |

---

***REMOVED******REMOVED*** Block Structure

***REMOVED******REMOVED******REMOVED*** Duration
- **4-week blocks** (same as resident blocks)
- **Half-day granularity**: AM and PM sessions

***REMOVED******REMOVED******REMOVED*** Block Boundaries

| Day | Session | Activity |
|-----|---------|----------|
| **First day of block** | AM | Inprocessing |
| **First day of block** | PM | Normal schedule begins |
| **Last Friday of block** | AM | Normal schedule |
| **Last Friday of block** | PM | Studying / Outprocessing |

---

***REMOVED******REMOVED*** Weekly Schedule Template

***REMOVED******REMOVED******REMOVED*** Standard Week (Non-FMIT)

| Day | AM | PM | Notes |
|-----|----|----|-------|
| Monday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |
| Tuesday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |
| Wednesday | **ASM** | Normal template | ASM is fixed for all med students |
| Thursday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |
| Friday | Clinic/Procedures | Clinic/Procedures | Prefer attending supervision |

***REMOVED******REMOVED******REMOVED*** FMIT Week (1 week per block)

| Day | AM | PM | Notes |
|-----|----|----|-------|
| Monday | FMIT | FMIT | Inpatient team |
| Tuesday | FMIT | FMIT | Inpatient team |
| Wednesday | **ASM** | FMIT | ASM still required |
| Thursday | FMIT | FMIT | **Overnight call starts** |
| Thursday Night | Call | Call | Overnight on inpatient |
| Friday | **PC** | **PC** | Post Call - recovery day |

---

***REMOVED******REMOVED*** Constraints

***REMOVED******REMOVED******REMOVED*** Hard Constraints

1. **ASM Wednesday AM**: All med students must have Wednesday AM blocked for ASM
2. **Max 2 learners per physician**: Cannot assign >2 med students + residents to same attending
3. **Procedures conflict**: Med student NOT in procedures if intern (PGY-1) is assigned there
4. **Inprocessing**: First AM of block is unavailable (orientation)
5. **Outprocessing**: Last Friday PM is unavailable (studying/checkout)

***REMOVED******REMOVED******REMOVED*** Soft Constraints

1. **Attending preference**: Prefer scheduling med students with attendings (not residents) in clinic
2. **Variety exposure**: Stagger templates so each med student works with different faculty/residents across the block
3. **FMIT week placement**: Can be any week of the 4-week block (flexible for staggering)

---

***REMOVED******REMOVED*** 7 Template Design

Need 7 distinct rotation templates for up to 7 concurrent med students. Templates should be **staggered** to:

1. Minimize conflicts (not all in same clinic/procedure at once)
2. Maximize exposure (each student works with different attendings/residents)
3. Distribute FMIT weeks across the block

***REMOVED******REMOVED******REMOVED*** Proposed Template Staggering

| Template | FMIT Week | Mon AM | Mon PM | Tue AM | Tue PM | Wed AM | Wed PM | Thu AM | Thu PM | Fri AM | Fri PM |
|----------|-----------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| MS-1 | Week 1 | Varies by FMIT week | | | | ASM | | | | | |
| MS-2 | Week 2 | | | | | ASM | | | | | |
| MS-3 | Week 3 | | | | | ASM | | | | | |
| MS-4 | Week 4 | | | | | ASM | | | | | |
| MS-5 | Week 1 | Offset from MS-1 | | | | ASM | | | | | |
| MS-6 | Week 2 | Offset from MS-2 | | | | ASM | | | | | |
| MS-7 | Week 3 | Offset from MS-3 | | | | ASM | | | | | |

> **TODO**: Define specific half-day assignments for each template based on clinic capacity and attending availability.

---

***REMOVED******REMOVED*** Data Model Changes Required

***REMOVED******REMOVED******REMOVED*** Person Model

Add `med_student` as valid person type:

```python
***REMOVED*** Current constraint
CheckConstraint("type IN ('resident', 'faculty')", name="check_person_type")

***REMOVED*** New constraint
CheckConstraint("type IN ('resident', 'faculty', 'med_student')", name="check_person_type")
```

***REMOVED******REMOVED******REMOVED*** New Fields for Med Students

```python
***REMOVED*** Med student specific fields
med_school = Column(String(255))  ***REMOVED*** e.g., "USUHS", "Harvard"
ms_year = Column(Integer)  ***REMOVED*** 3 or 4 (MS3, MS4)
rotation_start_date = Column(Date)  ***REMOVED*** When their FM rotation starts
rotation_end_date = Column(Date)  ***REMOVED*** When their FM rotation ends
```

***REMOVED******REMOVED******REMOVED*** Rotation Templates

Create 7 new templates:

```python
MED_STUDENT_TEMPLATES = [
    {"name": "Med Student Template 1", "abbreviation": "MS-1", "activity_type": "med_student"},
    {"name": "Med Student Template 2", "abbreviation": "MS-2", "activity_type": "med_student"},
    ***REMOVED*** ... etc
]
```

---

***REMOVED******REMOVED*** Supervision Tracking

***REMOVED******REMOVED******REMOVED*** Learner Counting

When assigning a med student to a clinic session, count total learners with that attending:

```python
def count_learners_with_attending(block_id: UUID, attending_id: UUID) -> int:
    """Count residents + med students assigned to this attending in this block."""
    ***REMOVED*** Query assignments where supervising_person_id == attending_id
    ***REMOVED*** Sum residents + med_students
    pass

def can_assign_med_student(block_id: UUID, attending_id: UUID) -> bool:
    """Check if attending has capacity for another learner."""
    return count_learners_with_attending(block_id, attending_id) < 2
```

---

***REMOVED******REMOVED*** Conflict Detection

***REMOVED******REMOVED******REMOVED*** Procedures Conflict

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

***REMOVED******REMOVED*** UI Considerations

***REMOVED******REMOVED******REMOVED*** Schedule View

- Med students should appear in a separate section/color from residents
- Show current learner count per attending in clinic view
- Highlight conflicts (procedures with intern)

***REMOVED******REMOVED******REMOVED*** Reporting

- Block summary: Show med student assignments alongside residents
- Attending workload: Include med student supervision in learner counts

---

***REMOVED******REMOVED*** Implementation Phases

***REMOVED******REMOVED******REMOVED*** Phase 1: Data Model
- [ ] Add `med_student` to Person type constraint
- [ ] Add med student specific fields
- [ ] Create Alembic migration
- [ ] Create 7 rotation templates

***REMOVED******REMOVED******REMOVED*** Phase 2: Constraints
- [ ] Implement ASM Wednesday AM hard constraint
- [ ] Implement max 2 learners per physician
- [ ] Implement procedures/intern conflict detection
- [ ] Implement inprocessing/outprocessing blocks

***REMOVED******REMOVED******REMOVED*** Phase 3: Scheduling Logic
- [ ] Create med student schedule generator
- [ ] Implement template staggering algorithm
- [ ] Add attending preference soft constraint

***REMOVED******REMOVED******REMOVED*** Phase 4: API & UI
- [ ] Create med student CRUD endpoints
- [ ] Add med student schedule view
- [ ] Add conflict warnings to UI

---

***REMOVED******REMOVED*** Open Questions

1. **Clinic locations**: Which specific clinics do med students rotate through? Same as residents?
2. **Template details**: What are the specific half-day assignments for non-FMIT, non-ASM slots?
3. **Weekend coverage**: Do med students ever work weekends?
4. **Night float**: Do med students participate in night float, or just FMIT overnight?
5. **Leave requests**: Can med students request time off during the 4-week block?

---

***REMOVED******REMOVED*** References

- Existing template structure: `backend/app/models/rotation_template.py`
- FMIT constraints: `backend/app/scheduling/constraints/fmit.py`
- Block model: `backend/app/models/block.py`
- Faculty scheduling spec: `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md`
