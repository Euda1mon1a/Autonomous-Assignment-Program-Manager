# Rotation Types Reference

This document defines the rotation types (categories) and how the scheduling engine handles each.

---

## Overview

Rotation templates are classified by `rotation_type` to determine whether the solver manages them or they are preserved as immutable pre-seeded assignments. For **rotation templates**, `rotation_type` is **only** `inpatient` or `outpatient`.

| Rotation Type | Solver Manages? | Description |
|---------------|-----------------|-------------|
| `outpatient` | **Yes** | Outpatient rotations (includes procedure templates) |
| `inpatient` | No - Preserved | Hospital rotations - pre-seeded from block schedule |
| `off` | No - Preserved | Off-site rotations - different hospitals |
| `education` | No - Preserved | Orientation, GME, lectures |
| `absence` | No - Preserved | Leave, weekend |
| `recovery` | No - Preserved | Post-call recovery |

---

## Solver-Managed Types

### `outpatient`

Outpatient rotations that the solver optimizes for coverage and equity. This
includes **procedure** templates (PROC/VAS/etc.), which are outpatient rotations
in the rotation_type model.

```
Clinic AM                    CLI-AM
Clinic PM                    CLI-PM
Sports Medicine AM           SPM-AM
Sports Medicine PM           SPM-PM
Academic Sports Medicine AM  ASM-AM
Colposcopy AM               COL-AM
Colposcopy PM               COL-PM
Houseless Clinic AM         HLC-AM
Houseless Clinic PM         HLC-PM
PCAT AM                     PCAT-AM
Resident Supervision AM     RSU-AM
Resident Supervision PM     RSU-PM
Advising PM                 ADV-PM
Direct Observation PM       DOB-PM
Department of Family Medicine AM  DFM-AM
Department of Family Medicine PM  DFM-PM
```

## Preserved Types (Immutable)

These are pre-seeded from Airtable block schedule data and must NOT be overwritten by the solver.

### `inpatient` (23 templates)

Hospital-based rotations. Pre-seeded per block from block schedule.

**FMIT (Family Medicine Inpatient Teaching):**
```
FMIT AM                                    FMIT-AM
FMIT PM                                    FMIT-PM
Family Medicine Inpatient Team Intern      FMI
Family Medicine Inpatient Team Resident    FMIT-R
Family Medicine Inpatient Team Pre-Attending  FMIT-PA
```

**Night Float:**
```
Night Float AM                 NF-AM
Night Float PM                 NF-PM
Night Float + Cardiology       NF+C
Night Float + Dermatology      NF-DERM
Night Float + Medical Selective NF-MED
Night Float + NICU             NF-NICU
Night Float Intern + FMIT      NFI
Cardiology + Night Float       C+NF
Dermatology + Night Float      D+NF
Pediatrics Night Float Intern  PNF
```

**ICU/NICU:**
```
NICU                           NICU
NICU + Night Float             NICU-NF
Intensive Care Unit Intern     ICU
```

**L&D:**
```
Labor and Delivery Intern      LD-I
Labor and Delivery Night Float LDNF
```

**Other:**
```
Internal Medicine Intern       IM-INT
Pediatrics Ward Intern         PEDS-W
Newborn Nursery               NBN
```

### `off` (5 templates)

Off-site rotations at different hospitals. Excluded from local scheduling.

```
Hilo       HILO
Kapiolani  KAPI
Okinawa    OKI
OFF AM     OFF-AM
OFF PM     OFF-PM
```

### `education` (5 templates)

Orientation and educational sessions.

```
Family Medicine Orientation     FMO
Graduate Medical Education AM   GME-AM
Graduate Medical Education PM   GME-PM
Lecture AM                     LEC-AM
Lecture PM                     LEC-PM
```

### `absence` (4 templates)

Leave and protected time.

```
Leave AM    LEA-AM
Leave PM    LEA-PM
Weekend AM  WKD-AM
Weekend PM  WKD-PM
```

### `recovery` (1 template)

Post-call recovery day.

```
Post-Call Recovery  PCR
```

---

## Engine Behavior

### Loading Preserved Assignments

The engine loads preserved assignments using rotation type filters:

```python
# backend/app/scheduling/engine.py

# Inpatient rotations
self._load_fmit_assignments()           # FMIT for faculty
self._load_resident_inpatient_assignments()  # All resident inpatient

# Other preserved types
self._load_absence_assignments()        # Leave, Weekend
self._load_offsite_assignments()        # Hilo, Kapiolani, Okinawa
self._load_recovery_assignments()       # Post-Call
self._load_education_assignments()      # FMO, GME, Lectures
```

### Conflict Filtering

Solver output is filtered against preserved slots:

```python
occupied_slots: set[tuple[UUID, UUID]] = set()
for a in existing_assignments:
    occupied_slots.add((a.person_id, a.block_id))

# Skip if slot is occupied by preserved assignment
if (person_id, block_id) in occupied_slots:
    continue  # Do not create this assignment
```

---

## Template Naming Conventions

| Pattern | Meaning |
|---------|---------|
| `* AM` | Morning half-day |
| `* PM` | Afternoon half-day |
| `*-AM`, `*-PM` | Abbreviation with time suffix |
| `* + *` | Combined rotation (e.g., Night Float + Cardiology) |
| `* Intern` | PGY-1 specific rotation |
| `* Resident` | PGY-2/3 rotation |

---

## Database Schema

```sql
CREATE TABLE rotation_templates (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    abbreviation VARCHAR,
    rotation_type VARCHAR,  -- 'outpatient', 'inpatient', 'off', etc.
    ...
);
```

The `rotation_type` field determines how the engine handles the rotation during schedule generation.

---

## Related Documentation

- [Engine Assignment Flow](ENGINE_ASSIGNMENT_FLOW.md) - How preserved assignments flow through the engine
- [FMIT Constraints](FMIT_CONSTRAINTS.md) - FMIT-specific constraint rules
- [Seed Rotation Templates Script](../../scripts/seed_rotation_templates.py) - Template seeding
