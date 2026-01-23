# Session 108: Stealth Launch Block 10 - COMPLETE

**Date:** 2026-01-14/15
**Branch:** `feat/tamc-v15-cleanup`
**Status:** Pipeline working, ready for stealth launch

---

## Mission

**Goal:** Generate Block 10 xlsx indistinguishable from 4-8 hours of hand-jamming.
**Result:** SUCCESS - Pipeline generates correct patterns with 0 automated errors.

---

## Key Accomplishments

### 1. Verified DB Data
- Block 10 AY 2025: 17 residents with rotations
- Dates: 2026-03-12 to 2026-04-08
- Container: `scheduler-local-db` (not `residency-scheduler-backend`)
- Table: `block_assignments` with `block_number`, `academic_year`

### 2. Fixed Pattern Issues in `schedule_xml_exporter.py`

**Changes made:**

```python
# 1. Added Hilo/TDY to INPATIENT_ROTATIONS (line ~90)
INPATIENT_ROTATIONS = frozenset([
    ...
    "TDY",
    "Hilo",
])

# 2. Added TDY to _get_inpatient_weekend_codes (line ~368)
elif rotation in ("TDY", "Hilo"):
    return ("TDY", "TDY")

# 3. Added ENDO pattern (line ~76)
"ENDO": ("ENDO", "C"),
"Endocrinology": ("ENDO", "C"),

# 4. Added aSM for SM on Wed AM (line ~384)
if rotation in ("SM", "Sports Medicine", "Sports Medicine AM"):
    return "aSM"
```

### 3. Clarified Data Source (DB vs ROSETTA)

| Question | Answer |
|----------|--------|
| Wilhelm/Byrnes mid-block | User will fix by hand (~65 cells) |
| FMIT continuity clinic | Correct as C (not FMIT all day) |
| Hernandez NF→ENDO | Correct per DB |
| You NEURO Wed AM | Correct as NEURO (not C) |

**Result:** 33 "mismatches" vs ROSETTA are test data differences, not errors.

---

## Files Generated

| File | Purpose |
|------|---------|
| `Block10_FINAL_PIPELINE.xlsx` | Final output with correct patterns |
| `/tmp/Block10_FINAL.xml` | XML intermediate (in container) |

---

## Pipeline Summary

```
DB (block_assignments)
    → parse_rotation() [maps full names to codes, handles mid-block]
    → ScheduleXMLExporter [applies patterns: KAP, LDNF, FMIT, etc.]
    → XML
    → Template overlay [fills Block Template2 structure]
    → Block10_FINAL_PIPELINE.xlsx
```

---

## Rotation Name to Code Mapping

```python
ROTATION_NAME_TO_CODE = {
    'Family Medicine Clinic': 'FMC',
    'Family Medicine Inpatient Team PGY-2': 'FMIT',
    'Night Float Labor & Delivery': 'LDNF',
    'Point of Care Ultrasound': 'POCUS',
    'Surgical Experience': 'Surg Exp',
    'Gynecology': 'GYN',
    'Sports Medicine AM': 'SM',
    'Pediatrics Ward PGY-1': 'PedW',
    'Kapiolani Labor & Delivery PGY-1': 'KAP',
    'Internal Medicine PGY-1': 'IM',
    'Night Float Pediatrics PGY-1': 'PedNF',
    'Procedure AM': 'PROC',
    'Hilo PGY-3': 'Hilo',
    'Night Float': 'NF',
    'Endocrinology': 'ENDO',
    'Neurology': 'NEURO',
}
```

---

## Patterns Verified Correct

| Resident | Rotation | Key Pattern |
|----------|----------|-------------|
| Connolly | Hilo | TDY all days including weekends |
| Headid | LDNF | Fri AM = C (not Wed!), Mon-Thu = OFF/LDNF |
| Travis | KAP | Mon=KAP/OFF, Tue=OFF/OFF, Wed=C/LEC |
| Monsivais | IM | Works weekends, Wed AM = C (intern continuity) |
| Cook | SM | Wed AM = aSM (Academic Sports Med) |
| Hernandez | NF→ENDO | Week 1-2 = OFF/NF, Week 3-4 = ENDO/C |

---

## Manual Fixes Required

**Wilhelm, Clara:** PedW → PedNF mid-block (column 28+)
**Byrnes, Katherine:** PedNF → PedW mid-block (column 28+)

~65 cells total - user will fix by hand.

---

## Commands to Resume

```bash
# Copy exporter to container (if changes made)
docker cp backend/app/services/schedule_xml_exporter.py scheduler-local-backend:/app/app/services/schedule_xml_exporter.py

# Generate XML in container
docker exec scheduler-local-backend python -c "
from datetime import date
from app.services.schedule_xml_exporter import ScheduleXMLExporter
# ... (see session code)
"

# Run ROSETTA validation
python3 scripts/validate_rosetta_complete.py
```

---

## Next Steps

1. User applies manual mid-block fixes to Wilhelm/Byrnes
2. Visual review in Excel
3. Deploy for alpha test
4. Count actual manual corrections needed

---

## Session Metrics

- DB queries: Fixed container name, table schema
- Pattern fixes: 4 (Hilo, TDY weekends, ENDO, aSM)
- Mismatches resolved: 280 → 33 (ROSETTA differences, not errors)
- Final automated errors: **0**
