# ML Rotation Pattern Mining Results — Context for Advisory

## System Overview

Medical residency scheduling system for a family medicine program (~33 people: ~19 residents across PGY 1-3, ~14 faculty). Each academic block is ~4 weeks. Each person gets 56 half-day assignments per block (28 days x AM/PM). The constraint programming solver (Google OR-Tools CP-SAT) fills unlocked slots based on rotation_activity_requirements.

### Database Schema (relevant tables)

- **half_day_assignments**: person_id, date, time_of_day (AM/PM), activity_id, source (preload|manual|solver|template)
- **rotation_templates**: 87 defined, with rotation_type, template_category, is_block_half_rotation
- **rotation_activity_requirements**: rotation_template_id, activity_id, min_halfdays, max_halfdays, target_halfdays, prefer_full_days, priority (0-100), applicable_weeks (JSONB)
- **block_assignments**: resident_id, block_number, rotation_template_id, secondary_rotation_template_id (for split-blocks)
- **weekly_patterns**: rotation_template_id, day_of_week, time_of_day, activity_id, is_protected

### Data Volume

- 17,464 half-day assignments across blocks 2-12 (AY 2025)
- 87 rotation templates, 182 activity requirements, 513 weekly patterns, 218 block assignments
- ~49 distinct foreground activity codes, ~26 background/administrative codes

---

## Phase 1: Rotation Profile Mining

**Method**: Group HDAs by (person, block) → one rotation profile per combination. Separate foreground activities (rotation-defining: FMIT, Night Float, KAP-LD, etc.) from background (fm_clinic, lectures, conferences, PI, weekends, leave, holidays).

**Results**: 386 profiles total, 276 meaningful (excluding background-only blocks)

| Category | Count | Description |
|----------|-------|-------------|
| mono_rotation | 68 | Single dominant foreground activity >60% of HDAs |
| focused | 137 | 2-3 foreground activities |
| mixed | 71 | 4+ diverse foreground activities |
| background_only | 110 | Leave/holiday blocks, no real rotation |

**Top dominant foreground codes across all profiles:**

| Code | Profiles | Description |
|------|----------|-------------|
| FMIT | 69 | Family Medicine Inpatient Team (all PGY + faculty) |
| CV | 26 | Curriculum Vitae / academic time (faculty) |
| NF | 19 | Night Float |
| TDY | 16 | Temporary Duty (off-site) |
| sm_clinic | 16 | Sports Medicine clinic |
| TNG | 16 | Training |
| KAP-LD | 14 | Kapiolani Labor & Delivery |
| ADM | 12 | Admissions |

**PGY-level patterns:**
- PGY-1: FMIT (13), ADM (10), KAP-LD (9), aSM (7), IMW (6)
- PGY-2: FMIT (11), NF (8), ER (5), PEDS-S (5), KAP-LD (5)
- PGY-3: NF (10), FMIT (10), TDY (9), VA (5), NICU (3)
- Faculty: FMIT (35), CV (17), DOFM (8), sm_clinic (6), TDY (5)

**Split-block rate**: 123/276 = 45% of meaningful profiles show a foreground code change mid-block

**Template coverage**: Only 185/386 profiles (48%) have an assigned rotation template in block_assignments

---

## Phase 2: HDBSCAN Clustering

**Method**: Code-frequency feature vectors (77 foreground codes normalized by total HDAs) + 6 context features (foreground_pct, is_split, PGY one-hot, faculty flag). StandardScaler → PCA (15 components, 42% variance) → HDBSCAN (min_cluster_size=5, min_samples=3).

**Results**: 15 clusters + 150 noise points (54% noise rate)

| Cluster | Label | Size | Dominant Code | PGY | Template Match |
|---------|-------|------|---------------|-----|----------------|
| 0 | PR-dominant | 5 | PR (procedures) | PGY-1 | Procedures (80%) |
| 1 | split-block | 6 | NF/NICU mix | PGY-3 | Low (17%) |
| 2 | sm_clinic | 5 | Sports Med | PGY-2 | Low (20%) |
| 3 | FMIT-mono | 7 | FMIT | PGY-3 | Night Float AM (43%) — MISLABELED |
| 4 | KAP-LD-mono | 10 | KAP-LD + IMW | PGY-1 | KAP-LD PGY-1 (40%) |
| 5 | TDY-mono | 7 | TDY | PGY-3 | Hilo PGY-3 (57%) |
| 6 | FMIT-mono | 8 | FMIT | PGY-2 | FM Clinic (25%) — MISLABELED |
| 7 | GYN-mixed | 9 | GYN/elective/ER | PGY-2 | ER (22%) |
| 8 | FMIT+aSM split | 15 | FMIT + aSM | PGY-1 | Low (7%) |
| 9 | NBN-mono | 5 | NBN | PGY-1 | Newborn Nursery (80%) |
| 10 | ADM-focused | 8 | ADM | PGY-1 | NO MATCH |
| 11 | sm_clinic-faculty | 5 | sm_clinic | Faculty | NO MATCH |
| 12 | FMIT-faculty-split | 16 | FMIT + CV | Faculty | NO MATCH |
| 13 | FMIT-faculty-mono | 8 | FMIT | Faculty | NO MATCH |
| 14 | CV-faculty | 12 | CV | Faculty | NO MATCH |

**Key observations:**
- Faculty clusters (11-14) have NO template matches — faculty scheduling not captured in templates
- Some cluster→template mappings are wrong (FMIT cluster matched to Night Float template)
- 42% PCA variance is low — the 77-code space is very sparse
- Noise rate suggests many profiles are genuinely unique (one-off electives, unusual combinations)

---

## Phase 3: Inverse Constraint Learning

**Method**: For each rotation template with block_assignments, find all historical person-blocks assigned to that template. Compute per-activity-code statistics: 5th percentile (learned_min), median (learned_target), 95th percentile (learned_max).

**Results**: Learned constraints for 32 templates (of 87 total)

### Constraint Diff Summary

| Category | Count | Description |
|----------|-------|-------------|
| Matched | 2 | Existing DB constraint matches historical data |
| Wider needed | 50 | Existing constraint range too tight |
| New pairs | 66 | Activity-template pair exists in data but not in DB |
| Orphaned | 30 | Exists in DB but never observed in historical data |

### Examples of Key Findings

**Family Medicine Inpatient Team PGY-2 (4 instances):**
- FMIT: NEW — learned min=24, max=52, target=50 (100% presence)
- The template has no FMIT requirement despite being the inpatient team rotation

**Kapiolani Labor & Delivery PGY-1 (5 instances):**
- KAP-LD: NEW — learned min=36, max=37, target=36 (100% presence)
- fm_clinic: existing min=3, learned min=1 (needs wider)
- lec: existing min=4, learned min=1 (needs wider)

**Newborn Nursery (6 instances):**
- NBN: NEW — learned min=33, max=39, target=36 (100% presence)
- lec: existing min=5, learned min=0 (needs much wider)

**Internal Medicine Ward (5 instances):**
- IMW: NEW — learned min=45, max=47, target=46 (100% presence)
- lec: existing min=4, learned min=1 (needs wider)

**Intensive Care Unit Intern (3 instances):**
- ICU: NEW — learned min=47, max=50, target=48 (100% presence)
- C40: NEW — learned min=0, max=4, target=4 (67% presence)

**Procedures (7 instances):**
- PR: existing min=2, max=4. Learned min=4, max=9, target=8 (wider)
- VASC: NEW — learned min=0, max=1, target=1 (71% presence)
- VAS: existing max=2. Learned max=3, target=2 (wider)

**Widespread pattern — lecture requirements too strict:**
Nearly every template has `lec` (lectures) set at min=4-5, max=4-5 (exact). Historical data shows actual range is 0-3. The fixed requirement forces the solver to schedule exactly 4-5 lecture slots, but in practice residents attend fewer.

**Widespread pattern — fm_clinic ranges too narrow:**
Most templates set fm_clinic to exactly 3. Historical data shows ranges from 0-12 depending on the rotation. FMIT residents get 0-2 clinic days, while outpatient rotations get 6-12.

### Full Learned Constraints (32 templates)

```
Template                                        Instances  FG Activities  BG Activities
Cardiology                                      3          11             11
Dermatology                                     2          5              6
Elective                                        7          5              9
Emergency Medicine                              3          5              7
Family Medicine Clinic                          11         5              11
Family Medicine Inpatient Team PGY-1            16         3              8
Family Medicine Inpatient Team PGY-2            4          4              4
Family Medicine Inpatient Team PGY-3            2          1              2
Geriatrics                                      4          13             11
Gynecology                                      5          1              8
Hilo PGY-3                                      5          3              5
Intensive Care Unit Intern                      3          5              3
Internal Medicine Ward                          5          5              3
Japan Off-Site Rotation                         5          4              6
Kapiolani Labor & Delivery PGY-1               5          1              6
Medical Selective                               3          9              8
Musculoskeletal Selective                        6          6              6
NICU                                            2          6              7
Newborn Nursery                                 6          2              6
Night Float + Dermatology PGY-2                 2          5              9
Night Float AM                                  13         3              8
Night Float Labor & Delivery                    6          2              10
Night Float Pediatrics PGY-1                    3          5              7
Pediatric Emergency Medicine                    2          5              8
Pediatrics Clinic                               4          4              8
Pediatrics Subspecialty                          4          10             11
Pediatrics Ward PGY-1                           3          5              6
Procedures                                      7          7              9
Psychiatry                                      4          13             11
Sports Medicine PM                              3          14             12
Surgical Experience                             4          13             9
TAMC Labor and Delivery                         5          2              6
```

---

## Phase 4: Association Rule Mining (Apriori)

**Method**: Each person-week = one transaction with activity codes + context tags (_PGY1, _FACULTY, _RESIDENT). Apriori with min_support=0.03, min_confidence=0.6.

**Results**: 1,658 deduplicated co-occurrence rules

### Top Activity Co-occurrence Rules

| Antecedent | Consequent | Confidence | Lift | Type |
|-----------|------------|------------|------|------|
| VAS (vasectomy) | VASC (vascular) | 75% | 20.7 | Universal |
| VASC | VAS | 90% | 20.7 | Universal |
| PGY-1 + recovery | ADM (admissions) | 87% | 11.4 | PGY-specific |
| sm_clinic | LV + aSM | 68% | 11.1 | Universal |
| LV + aSM | sm_clinic | 88% | 11.1 | Universal |
| elective | ITE (in-training exam) | 80% | 11.0 | Resident |
| C30 + split-block | NF (night float) | 100% | 11.0 | Universal |
| CV + DO | PCAT (attending call) | 93% | 10.8 | Universal |
| ORIENT + PR | FLX (flex time) | 77% | 9.7 | Universal |
| aSM + fm_clinic | sm_clinic | 80% | 10.0 | Universal |

### Rule Classification

| Type | Count |
|------|-------|
| Universal (no PGY/role filter) | 2,756 |
| Resident-general | 710 |
| PGY-specific | 527 |
| Faculty-specific | 396 |

### Interesting Implicit Rules (not in any template)

1. **VAS ↔ VASC always paired** — Procedures rotation always includes both vasectomy and vascular surgery
2. **PGY-1 post-recovery → ADM** — After recovery day, PGY-1s always get admissions
3. **CV + DO → PCAT** — Faculty academic/duty officer weeks always include attending call
4. **C30 continuity in split blocks → Night Float** — The C30 clinic visit in split blocks always pairs with NF
5. **Elective blocks → ITE** — In-training exam always scheduled during elective blocks
6. **aSM + fm_clinic → sm_clinic** — Sports medicine assistant role always co-occurs with sports med clinic

---

## Current Architecture

```
Coordinator manually creates schedule (97% of data)
    ↓
half_day_assignments table (17,464 rows, ground truth)
    ↓
ML Mining Pipeline (what we just built)
    ↓
Learned constraints (66 new, 50 corrections, 30 orphans)
    ↓
rotation_activity_requirements table (currently 182 rows, needs calibration)
    ↓
CP-SAT Activity Solver (reads requirements, fills unlocked slots)
    ↓
Generated schedule (currently only used for blocks 10, 12)
```

### Solver Pipeline

1. SyncPreloadService locks known slots (absences, FMIT, call, institutional events)
2. CP-SAT solver assigns activities to unlocked slots using rotation_activity_requirements
3. Solver respects: min/max/target halfdays, faculty clinic caps, supervision ratios, equity constraints
4. If rotation_activity_requirements are wrong → solver output diverges from coordinator style

---

## Open Questions

1. How to safely calibrate 182 existing + 66 new constraint rows from small samples (2-16 instances per template)?
2. Is 54% HDBSCAN noise expected, or should we try different approaches?
3. What solver agreement rate is realistic when re-solving a historical block with calibrated constraints?
4. How to handle variable split-block transition points (not always at day 14)?
5. Should ML models predict constraints dynamically or is static calibration sufficient for ~33 people?
6. What other ML techniques would yield high value on this dataset?
