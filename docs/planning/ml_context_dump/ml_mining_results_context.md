# ML Rotation Pattern Mining & Constraint Calibration — Full Context

## System Overview

Medical residency scheduling system for a family medicine program (~33 people: ~19 residents across PGY 1-3, ~14 faculty). Each academic block is ~4 weeks. Each person gets 56 half-day assignments per block (28 days x AM/PM). The constraint programming solver (Google OR-Tools CP-SAT) fills unlocked slots based on rotation_activity_requirements.

### Database Schema (relevant tables)

- **half_day_assignments**: person_id, date, time_of_day (AM/PM), activity_id, source (preload|manual|solver|template)
- **rotation_templates**: 87 defined, with rotation_type, template_category, is_block_half_rotation
- **rotation_activity_requirements**: rotation_template_id, activity_id, min_halfdays, max_halfdays, target_halfdays, prefer_full_days, priority (0-100), applicable_weeks (JSONB), applicable_weeks_hash (UUID unique constraint)
- **block_assignments**: resident_id, block_number, rotation_template_id, secondary_rotation_template_id (for split-blocks)
- **weekly_patterns**: rotation_template_id, day_of_week, time_of_day, activity_id, is_protected
- **people**: name, type (resident/faculty), pgy_level (1-3, null for faculty), min/max_clinic_halfdays_per_week, target_clinical_blocks, fmit_weeks_count

### Data Volume

- 17,464 half-day assignments across blocks 2-12 (AY 2025)
- 87 rotation templates, 195 activity requirements (was 182 before calibration), 513 weekly patterns, 218 block assignments
- ~49 distinct foreground activity codes, ~26 background/administrative codes

---

## Phase 1: Rotation Profile Mining

**Script:** `mine_rotation_patterns.py`
**Method**: Group HDAs by (person, block) -> one rotation profile per combination. Separate foreground activities from background. **v2 addition:** `split_week_hdas` field partitions code_counts into weeks_1_2 and weeks_3_4 for split-block-aware learning.

**Results**: 386 profiles total, 276 meaningful (excluding background-only blocks)

| Category | Count | Description |
|----------|-------|-------------|
| mono_rotation | 68 | Single dominant foreground activity >60% of HDAs |
| focused | 137 | 2-3 foreground activities |
| mixed | 71 | 4+ diverse foreground activities |
| background_only | 110 | Leave/holiday blocks, no real rotation |

**Split-block rate**: 123/276 = 45% of meaningful profiles show a foreground code change mid-block

**Template coverage**: Only 185/386 profiles (48%) have an assigned rotation template in block_assignments

---

## Phase 2: HDBSCAN Clustering

**Script:** `cluster_rotations.py`
**Results**: 15 clusters + 150 noise points (54% noise rate). Faculty clusters (11-14) have NO template matches. 42% PCA variance is low (77-code space very sparse). Noise rate suggests many profiles are genuinely unique.

---

## Phase 3: Inverse Constraint Learning (v1)

**Script:** `learn_constraints.py` (v1)
**Results**: Learned constraints for 32 templates

| Category | Count | Description |
|----------|-------|-------------|
| Matched | 2 | Existing DB constraint matches historical data |
| Wider needed | 50 | Existing constraint range too tight |
| New pairs | 66 | Activity-template pair exists in data but not in DB |
| Orphaned | 30 | Exists in DB but never observed in historical data |

**Key findings:**
- **lec (lectures) universally over-constrained:** Nearly every template has lec set at min=4-5, but historical data shows actual range 0-3
- **fm_clinic ranges too narrow:** Most templates set to exactly 3, data shows 0-12 depending on rotation
- **ADV orphaned across 27 templates:** Set in DB but never observed in data
- **Split-block contamination:** Dermatology (n=2) learned FMIT min=2 max=46 because profiles span two rotations (primary + secondary template HDAs mixed together)

---

## Phase 4: Association Rule Mining

**Script:** `mine_rules.py` (upgraded from Apriori to FP-Growth)
**Results**: 4,389 classified co-occurrence rules (was 1,658 with v1 profiles)

Top activity co-occurrence rules by lift: VAS<->VASC always paired (procedures), PGY-1 post-recovery -> ADM, CV+DO -> PCAT (faculty), C30 in split blocks -> NF, elective blocks -> ITE.

---

## Phase 5: Constraint Calibration (DEPLOYED)

### v2 Upgrades (council recommendations implemented)

**1. Split-block-aware learning** (`learn_constraints.py` v2):
- For profiles where `is_split_block=True`, partitions HDAs by week:
  - Weeks 1-2 HDAs -> learn constraints for primary template
  - Weeks 3-4 HDAs -> learn constraints for secondary template
  - Uses `applicable_weeks: [1,2]` or `[3,4]` on split-block constraints
- This fixed Dermatology learning FMIT min=2 max=46

**2. Confidence tiers:**
```
n >= 8  -> "high"    (auto-apply, no padding)
n = 4-7 -> "medium"  (auto-apply with +/-2 halfday padding on bounds)
n = 2-3 -> "low"     (flag only, written to needs_review.md)
```

**3. Anomaly detection:** Per-template z-score check. Flags any instance where activity count is >2 sigma from template mean.

**4. Cross-validation** (`validate_calibration.py`):
Leave-one-block-out validation across blocks 2-11:

| Metric | Value |
|--------|-------|
| Overall containment | 88.9% |
| High-confidence containment | 93.5% |
| Medium-confidence containment | 94.5% |
| Low-confidence containment | 75.6% |
| Foreground containment | 86.0% |
| Background containment | 91.7% |
| Non-split containment | 89.5% |
| Split-block containment | 87.2% |
| Overall MAE (target error) | 1.8 halfdays |

**5. DB Calibration** (`calibrate_constraints.py`):
Applied to production DB with transaction wrapping and pg_dump backups:

| Operation | Count |
|-----------|-------|
| New constraints inserted | 13 |
| Constraints updated (widened) | 28 |
| Universal lec min->0 fixes | 75 templates |
| Universal ADV min->0 fixes | 27 templates |
| Low-confidence flagged | 158 items (not applied) |
| Total requirements after | 195 (was 182) |
| SQL backups | 4 in /tmp/aapm_backups/ |

---

## CP-SAT Solver Architecture

The solver that CONSUMES these constraints has this architecture:

### Two-Pass Design
1. **Rotation Solver** (pass 1): Assigns rotation templates to block slots. Handles capacity, FMIT distribution, longitudinal clinics, split-blocks.
2. **Activity Solver** (pass 2): Fills unlocked half-day slots within each assigned rotation. Reads `rotation_activity_requirements` and generates per-slot activity assignments.

### Activity Solver Constraint Loading (`_load_activity_requirements()`)
- Queries `rotation_activity_requirements` joined with rotation_templates and activities
- Gates on `applicable_weeks`: null means "all weeks", non-null skips non-matching weeks
- `BLOCK_HALF_DAY = 14`: days 1-14 use primary template, 15+ use secondary
- All min/max requirements use **soft slack variables** (not hard constraints)
- The only hard constraint is the PGY-1 FM clinic floor (min 2 clinic halfdays/week)

### Penalty Weights (soft constraint priorities)
```python
ACTIVITY_MIN_SHORTFALL = 10    # per halfday below min
CLINIC_MIN_SHORTFALL = 25      # clinic-specific min penalty (2.5x)
ACTIVITY_MAX_OVERAGE = 20      # per halfday above max
CLINIC_MAX_OVERAGE = 40        # clinic-specific max penalty (2x)
AT_COVERAGE_SHORTFALL = 50     # attending coverage gap
```

### Other Constraint Categories (74+ total, 14 categories)
Beyond rotation_activity_requirements, the solver enforces:

| Category | Examples | ML-Learnable? |
|----------|----------|---------------|
| **Person-level fields** | `min/max_clinic_halfdays_per_week`, `fmit_weeks_count` | Yes - mine from HDAs |
| **Resident weekly requirements** | `fm_clinic_min/max_per_week`, protected slots | Yes - mine from weekly patterns |
| **Faculty weekly templates** | Day/time/activity grids with `is_locked` | Yes - mine from faculty HDAs |
| **Faculty preferences** | Clinic/call day preferences, weights | Partially |
| **Weekly pattern constraints** | `is_protected` slot constraints | Yes |
| **Call equity** | Sunday/weekday call counts, spacing | Yes - mine from call_assignments |
| **FMIT constraints** | Max weeks/year, consecutive limits | Yes |
| **ACGME hard constraints** | 80-hour rule, 1-in-7, supervision ratios | Validate only (regulatory) |
| **Capacity limits** | `max_residents` per template | Physical, not learnable |
| **Solver penalty weights** | 20+ constants (above) | Tunable via grid search |
| **Absence blocking** | Leave/holiday blocks | Always hard |
| **Supervision ratios** | Faculty-to-resident ratios | Policy, not learnable |
| **Equity constraints** | Balanced call distribution | Yes |
| **Continuity constraints** | Longitudinal clinic scheduling | Yes |

---

## Current Architecture

```
Coordinator manually creates schedule (97% of data)
    |
half_day_assignments table (17,464 rows, ground truth)
    |
ML Mining Pipeline (5 scripts)
    |
    +-> rotation_profiles_v2.json (276 meaningful profiles)
    +-> learned_constraints_v2.json (33 templates, confidence-tiered)
    +-> validation_results.json (88.9% containment)
    +-> association_rules_v2.json (4,389 rules)
    +-> needs_review.md (158 low-confidence items)
    |
calibrate_constraints.py --apply-all
    |
rotation_activity_requirements table (195 rows, calibrated)
    |
CP-SAT Activity Solver (reads requirements, fills unlocked slots)
    |
Generated schedule (currently used for blocks 10, 12)
```

### Pipeline Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `mine_rotation_patterns.py` | Extract rotation profiles from HDAs | DB | rotation_profiles_v2.json |
| `cluster_rotations.py` | HDBSCAN clustering | profiles | cluster visualization |
| `learn_constraints.py` v2 | Split-block-aware constraint learning | profiles + DB | learned_constraints_v2.json |
| `validate_calibration.py` | Leave-one-block-out cross-validation | profiles + DB | validation_results.json |
| `calibrate_constraints.py` | Safe DB writer (dry-run/apply modes) | learned JSON + DB | DB updates + backups |
| `mine_rules.py` | FP-Growth co-occurrence rules | profiles | association_rules_v2.json |

---

## What's Done vs What's Next

### Completed
- Phase 1: Rotation profile mining with split_week_hdas
- Phase 2: HDBSCAN clustering (informational)
- Phase 3+5: Inverse constraint learning v2 (split-block aware, confidence tiers, anomaly detection)
- Phase 4: Association rule mining (FP-Growth, 4,389 rules)
- Cross-validation: 88.9% overall, 93.5% high-confidence
- DB calibration: 195 requirements applied with backups
- Universal fixes: lec min->0 (75 templates), ADV min->0 (27 templates)
- Phase 6: E2E solver validation (validate_e2e.py) — RUN on blocks 6, 8, 10

### Phase 6 E2E Results (Feb 20, 2026)

**Method**: Temporarily unlock all manual slots → solver fills outpatient rotation slots → compare to coordinator → rollback. DB never modified.

| Block | Outpatient Slots | Solver Status | Runtime | Constraint Sat. | Jaccard (filled) | Slot Match (filled) |
|-------|-----------------|---------------|---------|-----------------|------------------|---------------------|
| 6 | 623/1742 (36%) | FEASIBLE | 180.7s | 24.4% | 0.186 | 9.6% |
| 8 | 636/1664 (38%) | OPTIMAL | 1.6s | 17.8% | 0.153 | 14.0% |
| 10 | 961/1681 (57%) | FEASIBLE | 180.4s | 24.6% | 0.137 | 12.7% |

**Key findings**:
1. Solver scope is narrow — only fills outpatient rotation slots (36-57%). Inpatient, NF, off, education not handled.
2. Constraint satisfaction 17-25% — solver's own output violates DB constraints (lec, ADV, fm_clinic still too tight)
3. Slot match 10-14% — expected, many valid permutations exist. Not a solver quality issue.
4. Massive weekly clamping — constraints calibrated at block-level but applied at weekly level
5. Block 8 OPTIMAL in 1.6s, blocks 6/10 FEASIBLE at timeout — constraint complexity varies significantly
6. **Bottleneck is constraint tightness, NOT solver quality** — confirms Phase 7 (weekly calibration) is next priority

### Council Consensus (Perplexity — GPT-5.2, Claude Opus 4.6, Gemini 3.1 Pro)
- 88.9% containment is production-ready (unanimous)
- Association rules: validation/anomaly detection only, not solver constraints (unanimous)
- Periodic batch re-calibration sufficient (annual at AY boundary)
- Penalty weight tuning via Bayesian optimization (Optuna) after E2E baseline

### Execution Roadmap (Council-Recommended)
1. Phase 6: E2E solver validation on blocks 6, 8, 10 (DONE — see above)
2. Phase 6b: Weight sensitivity with 4 configs (BUILT, not yet run — constraint fix needed first)
3. Phase 7: Resident weekly FM clinic calibration
4. Phase 8: Bayesian penalty weight optimization (Optuna)
5. Phase 8b: ML predictions as solver hints (warm-start)
6. Phase 9: Faculty clinic caps calibration
7. Phase 10: Template-family sharing for low-confidence constraints
8. Phase 11: ML penalty terms in solver objective

### Pipeline Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `mine_rotation_patterns.py` | Extract rotation profiles from HDAs | DB | rotation_profiles_v2.json |
| `cluster_rotations.py` | HDBSCAN clustering | profiles | cluster visualization |
| `learn_constraints.py` v2 | Split-block-aware constraint learning | profiles + DB | learned_constraints_v2.json |
| `validate_calibration.py` | Leave-one-block-out cross-validation | profiles + DB | validation_results.json |
| `calibrate_constraints.py` | Safe DB writer (dry-run/apply modes) | learned JSON + DB | DB updates + backups |
| `mine_rules.py` | FP-Growth co-occurrence rules | profiles | association_rules_v2.json |
| `validate_e2e.py` | E2E solver validation + weight sensitivity | DB (solver run) | e2e_validation_results.json |
