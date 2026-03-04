# Constraint Diff Report

**Summary:** 2 matched, 0 tighter, 50 wider, 66 new (missing from DB), 30 orphaned (in DB, not observed)

Comparing **learned** constraints (from historical HDAs) to **existing** rotation_activity_requirements.

> **Phase 7 Actions (2026-02-20):**
> - 30 orphaned constraints **REMOVED** from DB (Phase 7a-4)
> - 66 NEW constraints **APPLIED** via `calibrate_constraints.py --apply-all` (Phase 7c-1)
> - 50 wider constraints **UPDATED** to learned bounds (Phase 7c-1)
> - Total requirements: 174 → 356 (+181 INSERTs, +43 UPDATEs)


### Cardiology (n=3)
  - `CLC`: **NEW** — min=0, max=1, target=1 (67% presence, n=3)
  - `CV`: **NEW** — min=0, max=6, target=1 (67% presence, n=3)
  - `FLX`: **NEW** — min=0, max=2, target=1 (67% presence, n=3)
  - `aSM`: **NEW** — min=0, max=2, target=2 (67% presence, n=3)
  - `fm_clinic`: min: 3→5, max: 3→13, target: 3→8 (wider, 100% presence, n=3)
  - `lec`: min: 4→2, max: 4→3, target: 4→3 (wider, 100% presence, n=3)
  - `sm_clinic`: **NEW** — min=0, max=7, target=5 (67% presence, n=3)

### Dermatology (n=2)
  - `C30`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `DERM`: **NEW** — min=0, max=9, target=4 (50% presence, n=2)
  - `FMIT`: **NEW** — min=2, max=46, target=24 (50% presence, n=2)
  - `NF`: **NEW** — min=1, max=22, target=12 (50% presence, n=2)
  - `V2`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `fm_clinic`: min: 3→4, max: 3→5, target: 3→4 (wider, 100% presence, n=2)
  - `lec`: min: 4→2, target: 4→3 (wider, 100% presence, n=2)

### Elective (n=7)
  - `CLC`: **NEW** — min=0, max=1, target=1 (57% presence, n=7)
  - `elective`: **NEW** — min=0, max=31, target=1 (57% presence, n=7)
  - `fm_clinic`: min: 2→0, max: 5→12, target: 3→11 (wider, 71% presence, n=7)
  - `lec`: min: 4→2, max: 4→3, target: 4→3 (wider, 100% presence, n=7)

### Emergency Medicine (n=3)
  - `FMIT`: **NEW** — min=1, max=48, target=10 (67% presence, n=3)
  - `lec`: min: 4→0, target: 4→2 (wider, 67% presence, n=3)

### Family Medicine Clinic (n=11)
  - `PR`: max: 2→4, target: 1→2 (wider, 82% presence, n=11)
  - `fm_clinic`: min: 4→0, max: 6→12, target: 5→6 (wider, 73% presence, n=11)
  - `lec`: min: 4→0, max: 4→3, target: 4→2 (wider, 82% presence, n=11)

### Family Medicine Inpatient Team PGY-1 (n=16)
  - `FMIT`: **NEW** — min=0, max=50, target=14 (56% presence, n=16)
  - `fm_clinic`: min: 3→0, max: 3→6, target: 3→2 (wider, 62% presence, n=16)
  - `lec`: min: 4→0, target: 4→2 (wider, 81% presence, n=16)

### Family Medicine Inpatient Team PGY-2 (n=4)
  - `FMIT`: **NEW** — min=24, max=52, target=50 (100% presence, n=4)
  - `fm_clinic`: min: 4→0, max: 4→3, target: 4→0 (wider, 25% presence, n=4)

### Family Medicine Inpatient Team PGY-3 (n=2)
  - `FMIT`: **NEW** — min=48, max=51, target=50 (100% presence, n=2)

### Geriatrics (n=4)
  - `ADM`: **NEW** — min=0, max=3, target=2 (75% presence, n=4)
  - `CV`: **NEW** — min=0, max=1, target=0 (50% presence, n=4)
  - `HV`: **NEW** — min=0, max=2, target=0 (50% presence, n=4)
  - `PR`: **NEW** — min=0, max=4, target=0 (50% presence, n=4)
  - `TDY`: **NEW** — min=0, max=43, target=2 (50% presence, n=4)
  - `VA`: **NEW** — min=0, max=12, target=4 (50% presence, n=4)
  - `fm_clinic`: min: 3→2, max: 3→10, target: 3→4 (wider, 100% presence, n=4)
  - `lec`: min: 4→1, max: 4→3, target: 4→2 (wider, 100% presence, n=4)

### Gynecology (n=5)
  - `fm_clinic`: min: 3→0, max: 3→12, target: 3→10 (wider, 80% presence, n=5)
  - `lec`: min: 4→0, target: 4→2 (wider, 80% presence, n=5)

### Hilo PGY-3 (n=5)
  - `ADM`: **NEW** — min=0, max=4, target=1 (80% presence, n=5)
  - `TDY`: **NEW** — min=0, max=46, target=24 (60% presence, n=5)
  - `lec`: min: 5→0, max: 5→3, target: 5→1 (wider, 80% presence, n=5)

### Intensive Care Unit Intern (n=3)
  - `C40`: **NEW** — min=0, max=4, target=4 (67% presence, n=3)
  - `ICU`: **NEW** — min=47, max=50, target=48 (100% presence, n=3)
  - `lec`: min: 5→1, max: 5→3, target: 5→2 (wider, 100% presence, n=3)

### Internal Medicine Ward (n=5)
  - `C30`: **NEW** — min=0, max=1, target=1 (80% presence, n=5)
  - `IMW`: **NEW** — min=45, max=47, target=46 (100% presence, n=5)
  - `lec`: min: 4→1, target: 4→2 (wider, 100% presence, n=5)

### Japan Off-Site Rotation (n=5)
  - `C30`: **NEW** — min=0, max=1, target=1 (60% presence, n=5)
  - `NF`: **NEW** — min=0, max=23, target=23 (60% presence, n=5)

### Kapiolani Labor & Delivery PGY-1 (n=5)
  - `KAP-LD`: **NEW** — min=36, max=37, target=36 (100% presence, n=5)
  - `fm_clinic`: min: 3→1 (wider, 80% presence, n=5)
  - `lec`: min: 4→1, max: 4→3, target: 4→2 (wider, 100% presence, n=5)

### Medical Selective (n=3)
  - `HV`: **NEW** — min=0, max=2, target=1 (67% presence, n=3)
  - `LSCO`: **NEW** — min=0, max=1, target=1 (67% presence, n=3)
  - `fm_clinic`: min: 3→6, max: 3→22, target: 3→6 (wider, 100% presence, n=3)
  - `lec`: min: 4→2, max: 4→2, target: 4→2 (wider, 100% presence, n=3)

### Musculoskeletal Selective (n=6)
  - `CAST`: **NEW** — min=0, max=3, target=2 (83% presence, n=6)
  - `RAD`: **NEW** — min=0, max=4, target=4 (83% presence, n=6)
  - `aSM`: **NEW** — min=0, max=4, target=2 (83% presence, n=6)
  - `fm_clinic`: min: 3→0, max: 3→8, target: 3→0 (wider, 33% presence, n=6)
  - `lec`: min: 4→0, max: 4→6, target: 4→2 (wider, 83% presence, n=6)
  - `sm_clinic`: **NEW** — min=0, max=11, target=8 (67% presence, n=6)

### NICU (n=2)
  - `ADHD`: **NEW** — min=0, max=4, target=2 (50% presence, n=2)
  - `MM`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `MULTID`: **NEW** — min=0, max=5, target=2 (50% presence, n=2)
  - `NF`: **NEW** — min=20, max=22, target=21 (100% presence, n=2)
  - `NICU`: **NEW** — min=1, max=23, target=12 (50% presence, n=2)
  - `PSY`: **NEW** — min=0, max=4, target=2 (50% presence, n=2)
  - `lec`: min: 5→1, max: 5→2, target: 5→2 (wider, 100% presence, n=2)

### Newborn Nursery (n=6)
  - `NBN`: **NEW** — min=33, max=39, target=36 (100% presence, n=6)
  - `lec`: min: 5→0, max: 5→3, target: 5→2 (wider, 67% presence, n=6)

### Night Float + Dermatology PGY-2 (n=2)
  - `C-N`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `CLC`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `DERM`: **NEW** — min=0, max=8, target=4 (50% presence, n=2)
  - `NF`: **NEW** — min=1, max=18, target=10 (50% presence, n=2)
  - `PEDS-ER`: **NEW** — min=2, max=38, target=20 (50% presence, n=2)
  - `lec`: min: 5→0, max: 5→1, target: 5→0 (wider, 50% presence, n=2)

### Night Float AM (n=13)
  - `lec`: min: 5→0, max: 5→3, target: 5→1 (wider, 62% presence, n=13)

### Night Float Labor & Delivery (n=6)
  - `lec`: min: 5→0, max: 5→2, target: 5→0 (wider, 50% presence, n=6)

### Night Float Pediatrics PGY-1 (n=3)
  - `PEDSW`: **NEW** — min=2, max=44, target=21 (67% presence, n=3)
  - `lec`: min: 5→0, max: 5→1, target: 5→1 (wider, 67% presence, n=3)

### Pediatric Emergency Medicine (n=2)
  - `C30`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `CV`: **NEW** — min=0, max=1, target=0 (50% presence, n=2)
  - `ER`: **NEW** — min=1, max=17, target=9 (50% presence, n=2)
  - `NF`: **NEW** — min=1, max=10, target=6 (50% presence, n=2)
  - `PER`: **NEW** — min=1, max=28, target=14 (50% presence, n=2)

### Pediatrics Clinic (n=4)
  - `C40`: **NEW** — min=0, max=6, target=2 (50% presence, n=4)
  - `PEDC`: **NEW** — min=3, max=21, target=20 (75% presence, n=4)
  - `fm_clinic`: min: 3→0, max: 3→5, target: 3→0 (wider, 50% presence, n=4)
  - `lec`: min: 4→2, target: 4→2 (wider, 100% presence, n=4)

### Pediatrics Subspecialty (n=4)
  - `CLC`: **NEW** — min=0, max=1, target=0 (50% presence, n=4)
  - `PEDS-S`: min: 4→0, max: 6→15, target: 5→0 (wider, 25% presence, n=4)
  - `fm_clinic`: min: 2→4, max: 4→10, target: 3→9 (wider, 100% presence, n=4)
  - `lec`: min: 4→0, max: 4→3, target: 4→2 (wider, 75% presence, n=4)

### Pediatrics Ward PGY-1 (n=3)
  - `PEDSW`: **NEW** — min=21, max=41, target=26 (100% presence, n=3)
  - `fm_clinic`: min: 3→0, target: 3→1 (wider, 67% presence, n=3)
  - `lec`: min: 4→0, max: 4→1, target: 4→0 (wider, 33% presence, n=3)

### Procedures (n=7)
  - `ADM`: **NEW** — min=0, max=2, target=1 (57% presence, n=7)
  - `FLX`: **NEW** — min=0, max=3, target=1 (57% presence, n=7)
  - `PR`: min: 2→4, max: 4→9, target: 3→8 (wider, 100% presence, n=7)
  - `SIM`: min: 0→1, max: 2→3, target: 1→2 (wider, 100% presence, n=7)
  - `VAS`: max: 2→3, target: 1→2 (wider, 86% presence, n=7)
  - `VASC`: **NEW** — min=0, max=1, target=1 (71% presence, n=7)
  - `fm_clinic`: max: 4→10, target: 3→10 (wider, 86% presence, n=7)
  - `lec`: min: 4→1, max: 4→3, target: 4→2 (wider, 100% presence, n=7)

### Psychiatry (n=4)
  - `ADM`: **NEW** — min=0, max=2, target=0 (50% presence, n=4)
  - `TDY`: **NEW** — min=0, max=7, target=0 (50% presence, n=4)

### Sports Medicine PM (n=3)
  - `fm_clinic`: min: 3→4, max: 3→10, target: 3→8 (wider, 100% presence, n=3)
  - `lec`: min: 4→0, max: 4→3, target: 4→1 (wider, 67% presence, n=3)

### Surgical Experience (n=4)
  - `CLC`: **NEW** — min=0, max=1, target=0 (50% presence, n=4)
  - `fm_clinic`: min: 3→5, max: 3→10, target: 3→8 (wider, 100% presence, n=4)
  - `lec`: min: 4→0, max: 4→3, target: 4→3 (wider, 75% presence, n=4)

### Tripler Army Medical Center Labor and Delivery (n=5)
  - `KAP-LD`: **NEW** — min=6, max=37, target=32 (80% presence, n=5)
  - `fm_clinic`: min: 3→0, target: 3→0 (wider, 40% presence, n=5)
  - `lec`: min: 4→1, target: 4→3 (wider, 100% presence, n=5)

### Orphaned Requirements (in DB, not in data) — REMOVED 2026-02-20
  - `Cardiology` → `ADV`: exists in DB but never observed in data
  - `Dermatology` → `ADV`: exists in DB but never observed in data
  - `Elective` → `ADV`: exists in DB but never observed in data
  - `Elective` → `aSM`: exists in DB but never observed in data
  - `Elective` → `sm_clinic`: exists in DB but never observed in data
  - `Emergency Medicine` → `ADV`: exists in DB but never observed in data
  - `Family Medicine Clinic` → `ADV`: exists in DB but never observed in data
  - `Family Medicine Clinic` → `VAS`: exists in DB but never observed in data
  - `Family Medicine Clinic` → `VASC`: exists in DB but never observed in data
  - `Family Medicine Clinic` → `elective`: exists in DB but never observed in data
  - `Family Medicine Inpatient Team PGY-1` → `ADV`: exists in DB but never observed in data
  - `Family Medicine Inpatient Team PGY-2` → `ADV`: exists in DB but never observed in data
  - `Family Medicine Inpatient Team PGY-2` → `lec`: exists in DB but never observed in data
  - `Family Medicine Inpatient Team PGY-3` → `ADV`: exists in DB but never observed in data
  - `Family Medicine Inpatient Team PGY-3` → `C-I`: exists in DB but never observed in data
  - `Family Medicine Inpatient Team PGY-3` → `lec`: exists in DB but never observed in data
  - `Geriatrics` → `ADV`: exists in DB but never observed in data
  - `Gynecology` → `ADV`: exists in DB but never observed in data
  - `Internal Medicine Ward` → `ADV`: exists in DB but never observed in data
  - `Internal Medicine Ward` → `fm_clinic`: exists in DB but never observed in data
  ... and 10 more
