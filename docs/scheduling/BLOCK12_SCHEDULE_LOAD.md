# Block 12 Schedule Load — Import Log

> **Date:** 2026-02-18 (dry run), 2026-02-__ (handjam)
> **Block:** 12 (May 7 – Jun 3, 2026), AY 2025
> **Source:** Excel handjam (TBD) + Excel "Block Schedule" sheet (dry run)
> **Branch:** `feat/block12-schedule-load`

---

## Pre-Flight Checklist

- [x] DB backup taken (`checkpoint.sh pre_dry_run`)
- [ ] Latest Excel version confirmed with coordinator (Block 12 tab doesn't exist yet)
- [x] `NAME_MAP` covers all Excel names (27 entries: 17 residents + 10 faculty)
- [x] `CODE_MAP` covers all activity codes (50+ from Block 11)
- [ ] TAMC-LD vs KAP-LD distinguished per rotation site
- [x] `block_assignments` table populated (corrected from Excel Block Schedule)
- [x] Split-block residents have `secondary_rotation_template_id` set (2 of 6 split-blocks)
- [x] Memorial Day (May 25) flagged in blocks table
- [x] Deployed faculty assignments removed from B12 and B13
- [x] Pre-flight script passes 7/7 for Block 12
- [x] Pre-flight integrated into import_block12.py

---

## Session Log

> Append timestamped entries during interactive handjam session.
> Format: what was attempted, what happened, whether it was a gotcha.

| Time | Action | Result | Gotcha? |
|------|--------|--------|---------|
| 2026-02-18 18:41 | DB checkpoint pre_dry_run | 2.9MB dump saved | No |
| 2026-02-18 18:44 | Dry run: fix block_assignments | 16 stale deleted, 16 correct created | YES — #1 |
| 2026-02-18 18:44 | Dry run: remove graduated R3 assignments | 40 stale assignments deleted | YES — #2 |
| 2026-02-18 18:44 | Dry run: remove deployed faculty supervising | 24 deployed-faculty assignments deleted | YES — #3 |
| 2026-02-18 18:44 | Dry run: rebuild assignments | 896 resident assignments created (16 × 56) | No |
| 2026-02-18 18:44 | DB checkpoint post_dry_run | 2.9MB dump saved | No |
| 2026-02-18 21:00 | Pre-handjam: flag Memorial Day | 2 blocks flagged (AM/PM on 2026-05-25) | YES — #4 |
| 2026-02-18 21:00 | Pre-handjam: audit deployed faculty | Deployed faculty had 22 stale B13 assignments, deleted | YES — #3 ext |
| 2026-02-18 21:00 | Pre-handjam: check Block 13 staleness | B13 has 16 block_assignments, Excel cols blank (not scheduled yet) | No |
| 2026-02-18 21:01 | Pre-handjam: create preflight script | 7-check reusable validator, B12 passes 7/7, B13 passes 5/7 | No |
| 2026-02-18 21:01 | Pre-handjam: wire preflight into import | import_block12.py now runs preflight before parse_excel | No |
| 2026-02-18 21:36 | DB checkpoint pre_hda_expansion | 2.9MB dump saved | No |
| 2026-02-18 21:37 | HDA expansion: BlockAssignmentExpansionService | 882 HDAs created (607 with activity, 277 NULL pending handjam) | YES — #8 |
| 2026-02-18 21:37 | Fix: rotation_type attribute bug | expansion service referenced nonexistent `activity_type` column | YES — #9 |
| 2026-02-18 21:38 | DB checkpoint post_hda_expansion | 2.9MB dump saved | No |
| 2026-02-19 17:20 | Clone laptop DB to Mini | 2.9MB dump via Tailscale, labeled "Cloned from laptop 2026-02-19" | No |
| 2026-02-19 17:55 | Add 6 missing activities | C40, CAST, ER, PEDS-ER, RAD, TNG inserted | YES — #8 |
| 2026-02-19 18:00 | Apply ML predictions (--min-conf 0.5) | 192 NULL HDAs filled (source='solver'), 85 remain | YES — #9 |

---

## Gotcha Catalog

> Failures and surprises discovered during Block 12 import.
> Reference: Block 11 found 8 gotchas — see `BEST_PRACTICES_AND_GOTCHAS.md:1080-1092`.

| # | Gotcha | Impact | Fix | Status |
|---|--------|--------|-----|--------|
| 1 | block_assignments 100% stale | All 16 residents had wrong rotations (Block 11 data in Block 12 slots) | Deleted and re-inserted from Excel Block Schedule | Fixed (dry run) |
| 2 | Graduated R3 not in Block 12 | DB had graduated resident as ELEC with 40 assignments but Excel shows blank after Block 10 | Deleted stale assignments; excluded from Block 12 | Fixed (dry run) |
| 3 | Deployed faculty assigned | Faculty deployed Feb 21 – Jun 30 but had 24+22 supervising assignments (B12+B13) | Deleted supervision assignments for Block 12 (dry run) and Block 13 (pre-handjam) | Fixed |
| 4 | Memorial Day not flagged | May 25, 2026 (Mon) not marked as holiday in blocks table | Flagged via fix_memorial_day.py using holidays.py validation | Fixed (pre-handjam) |
| 5 | Name discrepancies Excel vs DB | 7 names differ between Excel legal names and DB preferred names | NAME_MAP handles mapping | Documented |
| 6 | Block 13 Juneteenth not flagged | Jun 19, 2026 not marked as holiday in blocks table | Detected by preflight script, fix deferred to B13 import | Documented |
| 7 | Graduated R3 stale in Block 13 | 38 primary assignments in B13 but no block_assignment | Detected by preflight script, fix deferred to B13 import | Documented |
| 8 | ML predictions reference missing activities | 6 activity codes from archive (C40, CAST, ER, PEDS-ER, RAD, TNG) not in `activities` table | Added 6 activity records before applying predictions | Fixed |
| 9 | `source='predicted'` violates check constraint | `ck_half_day_assignments_check_half_day_source` only allows preload\|manual\|solver\|template | Used `source='solver'` for ML predictions. Extend constraint in future migration if dedicated source needed. | Fixed (workaround) |

---

## DB Checkpoints

| Label | Timestamp | File |
|-------|-----------|------|
| pre-dry-run | 2026-02-18T18:41:38 | `/tmp/block12_pre_dry_run_*.dump` |
| post-dry-run | 2026-02-18T18:44:28 | `/tmp/block12_post_dry_run_*.dump` |
| laptop-clone | 2026-02-19T17:20:00 | `/tmp/residency_scheduler_laptop_2026-02-19.dump` (on Mini) |
| pre-import | | `/tmp/block12_pre_import_*.dump` |
| post-hda-sync | | |
| post-assignments-fix | | |
| post-absence-sync | | |

---

## What Was Done

### 0. Dry Run (2026-02-18) — Template-Derived, No Handjam

**Source:** Excel "Block Schedule" sheet (col 24-25) + DB rotation_templates
**Script:** `scripts/data/block12_import/dry_run.py`

**Rotation assignments corrected (all 16 were wrong):**

| Resident | PGY | Was (DB) | Now (Excel) | Split NF? |
|----------|-----|---------|-------------|-----------|
| R1-A | 1 | NF-PEDS-PG | NF-PEDS-PG | Combined template |
| R1-B | 1 | TAMC-LD | NF-FMIT-PG | Combined template |
| R1-C | 1 | PROC | MSK-SEL | No |
| R1-D | 1 | KAPI-LD-PG | FMIT-PGY2 / NF | Split day 15 |
| R1-E | 1 | NF-AM | PEDS-WARD- / NF-PEDS-PG | Split day 15 |
| R1-F | 1 | NF-AM | NBN | No |
| R2-A | 2 | PEDS-SUB | NF-LD | No |
| R2-B | 2 | FMIT-PGY1 | ELEC | No |
| R2-C | 2 | DERM | FMC | No |
| R2-D | 2 | NF-LD | ELEC | No |
| R2-E | 2 | NF-LD | NF-DERM-PG | Combined template |
| R2-F | 2 | ELEC | NF-CARDIO | Combined template |
| R3-A | 3 | NF-AM | PEDS-EM | No |
| R3-B | 3 | NF-AM | FMIT-PGY3 | No |
| R3-C | 3 | FMC | HILO-PGY3 | No |
| R3-D | 3 | ELEC | JAPAN | No |

**Counts:**
| Metric | Value |
|--------|-------|
| block_assignments fixed | 16 (all wrong → all correct) |
| Stale assignments deleted | 776 (712 residents + 40 graduated R3 + 24 deployed faculty) |
| Assignments rebuilt | 896 (16 residents × 56 slots) |
| Expected HDAs (template) | ~842 (minus absence days) |

### 0.5. ML Prediction Pre-Fill (2026-02-19) — APPLIED

**Source:** Historical pattern learning from 65 blocks (AY 2021-2025) + Current AY Blocks 8-10
**Script:** `~/schedule-vision/predict_block12.py` → `scripts/data/block12_import/load_predictions.py`

**Training data:**
- Archive: 137,609 features from 65 blocks across 5 academic years
- Current AY: 4,831 features from Blocks 8-10 (actual handjam data)
- Combined training set: 13,928 features (archive B1-7 + current B8-10)

**LOBO accuracy (within-AY):**
- Overall: ~38-41% (weighted across all strategies)
- `rot_pgy_dow_half`: ~57% (best strategy, rotation + PGY level + day + half)
- `person_dow_half`: ~25-30% (person patterns, less reliable across rotations)

**Predictions generated:**
| Metric | Count |
|--------|-------|
| Total prediction slots | 2,520 (45 people × 56 half-days) |
| DB-ready (mapped people) | 1,288 (23 people) |
| High confidence (≥80%) | 344 |
| Medium confidence (50-79%) | 496 |
| Low confidence (<50%) | 448 |

**CODE_MAP additions:** 11 new codes (HOL, PedW, TNG, P ER, ER, US, C-I, C40, Rad, Cast, TENT)

**Activities added to DB:** 6 new activity records (C40, CAST, ER, PEDS-ER, RAD, TNG) — required
for predictions that referenced codes not yet in the `activities` table.

**Applied (2026-02-19, --min-conf 0.5, source='solver'):**

| Metric | Count |
|--------|-------|
| NULL HDAs pre-filled | 192 of 277 (69%) |
| Already filled (template/preload) | 500 |
| No HDA row (unmapped people) | 148 |
| Remaining NULL for handjam | 85 |

**Block 12 HDA final state after predictions:**

| Source | Count |
|--------|-------|
| solver (template expansion + ML) | 563 |
| preload | 236 |
| NULL (awaiting handjam) | 85 |
| **Total** | **884** |

**Remaining 85 NULL HDAs — why unpredictable:**

| Person | PGY | Rotation (`rotation_templates.name`) | NULLs | Root Cause |
|--------|-----|--------------------------------------|-------|------------|
| R2-C | 2 | Family Medicine Clinic | 27 | FMC weekday `activity_category='clinical'` codes split between `fm_clinic`, `US`, `LV`, `lec` at 21-33% confidence. The coordinator manually assigns clinic vs ultrasound vs lecture days — no repeating pattern across blocks. |
| R1-B | 1 | NF-FMIT-PG (`is_block_half_rotation=True`) | 24 | Night float combined template: daytime codes (`off`/`NF`/`lec`) cycle irregularly. Weekday AM is 35% `off` (post-call recovery, `activity_category='time_off'`) vs 35% lecture (`is_protected=True`). |
| R2-E | 2 | NF-DERM-PG (`is_block_half_rotation=True`) | 24 | Same NF combined template pattern as R1-B. Day-side schedule is coordinator-crafted per block, not pattern-driven. |
| R1-C | 1 | MSK-SEL | 6 | Weekend slots where `HOL` (`activity_category='time_off'`) and `sm_clinic` (`activity_category='clinical'`) are each 25%. Ref: Block 11 gotcha #6 — holiday vs weekend priority ambiguity. |
| R3-A | 3 | PEDS-EM | 3 | Thursday PM: `lec` (`is_protected=True`) at 38% — depends on teaching calendar, not rotation. |
| R3-D | 3 | ELEC | 1 | Single Thursday PM `lec` slot at 38%. Same teaching calendar dependency. |

**Key finding:** Three structural patterns resist ML prediction:
1. **FMC rotation** — `fm_clinic`/`US`/`lec` day assignments are coordinator-discretionary, not algorithmic
2. **Night float day-side** — post-call `off` vs `lec` vs `NF` cycling is hand-scheduled per block
3. **Thursday PM lecture** — `lec` (`is_protected=True`) depends on the GME teaching calendar, an external input

**To re-run (if DB is reset):**
```bash
# Dry run first
backend/.venv/bin/python scripts/data/block12_import/load_predictions.py --dry-run \
    --predictions ~/schedule-vision/data/block12_db_ready.json
# Apply medium+ confidence predictions
backend/.venv/bin/python scripts/data/block12_import/load_predictions.py --min-conf 0.5 \
    --predictions ~/schedule-vision/data/block12_db_ready.json
```

### 1. Excel Parsing & HDA Sync

- Source Excel: _(awaiting Block 12 handjam tab)_
- Sheet: _(Block 12 tab doesn't exist yet)_
- NAME_MAP: 27 entries pre-filled from Block 11 Import
- CODE_MAP: 61 entries (50 from Block 11 + 11 from ML predictions)

### 2. Assignments Table Fix

- Stale assignments deleted: 776
- Correct assignments rebuilt: 896
- Split-block residents handled: 2 residents with primary/secondary split at day 15
- Combined NF templates used: 4 residents with whole-block combined templates

### 3. HDA Block Assignment Linkage

- Resident HDAs with `block_assignment_id`: 0 (no HDAs generated yet)
- Faculty HDAs (NULL, expected): 2 (preloads)

### 4. Faculty Weekly Templates

- Template rows updated: _(pending handjam)_
- Template rows created: _(pending handjam)_

### 5. Absence Sync

| Person | Type | Dates | Notes |
|--------|------|-------|-------|
| R2-C | vacation | May 29 – Jun 4 | Block 12 |
| Faculty-A | vacation | May 18 – May 21 | FMIT starts May 22 |
| Faculty-B | deployment | Feb 21 – Jun 30 | Full block deployed |
| Faculty-C | vacation | May 26 – May 29 | Leave |
| R3-A | vacation | May 27 – Jun 2 | Block 12 |
| R2-D | vacation | May 14 – May 18 | Block 12 |
| R2-D | vacation | Jun 2 – Jun 7 | Block 12-13 overlap |
| R1-F | vacation | May 24 – May 30 | Block 12 |

---

## Verification Checklist

- [x] Features extracted from 65+ blocks (2021-2025 archive + current AY)
- [x] LOBO accuracy measured (~57% for rot_pgy_dow_half)
- [x] 277 NULL HDAs have prediction candidates with confidence scores
- [x] ML predictions file generated (block12_db_ready.json)
- [x] Prediction loader script created (load_predictions.py)
- [x] 6 missing activities added to DB (C40, CAST, ER, PEDS-ER, RAD, TNG)
- [x] Predictions loaded into DB (192 of 277 NULLs filled, source='solver', min-conf=0.5)
- [x] 85 remaining NULLs analyzed — FMC variability, NF day-side, Thu PM lecture
- [ ] HDA count matches Excel (days x 2 x people)
- [ ] 100% activity code match between Excel and DB
- [x] Assignments rebuilt with correct rotation templates (dry run)
- [ ] HDA `block_assignment_id` populated for residents
- [ ] Faculty weekly templates have `activity_id` on all slots
- [ ] Absences match Excel leave/TDY/deployment data
- [ ] Schedule scored after handjam import
- [ ] No CRITICAL ACGME conflicts
- [ ] GUI renders Block 12 schedule correctly

---

## Final State

| Table | Count | Status |
|-------|-------|--------|
| `half_day_assignments` | 884 (799 filled, 85 NULL) | ML pre-filled, 85 await handjam |
| `assignments` | 896 (residents) | Dry run complete |
| `block_assignments` | 16 | Corrected from Excel |
| `activities` | 80 (74 original + 6 ML-added) | C40, CAST, ER, PEDS-ER, RAD, TNG added |
| `faculty_weekly_templates` | | Pending handjam |
| `absences` (Block 12) | 8 | From existing DB records |

---

## Lessons Learned

> Post-session — what was different from Block 11, what should change for Block 13.

1. **block_assignments were 100% wrong** — the solver/prior import populated Block 12 with Block 11 rotation data. Always cross-reference with the coordinator's Excel "Block Schedule" sheet before trusting DB block_assignments.
2. **Dry run can auto-derive ~80% of the schedule** from Block Schedule + rotation templates, but faculty codes, call schedule, and day-specific overrides require the handjam Excel.
3. **7 name discrepancies** between Excel (legal names) and DB (preferred names). NAME_MAP is essential.
4. **Graduated R3** had no Block 12 assignment but had stale DB data. Always verify against Block Schedule for PGY-3 residents who may be completing early.
5. **Deployed faculty** — deployment absences need to cascade to removing supervision assignments.
6. **ML pre-fill reduced manual handjam by 69%** (192 of 277 NULLs). The 7-level hierarchical lookup trained on 13,928 features outperformed both pure rules and RandomForest (which needs `fill_rgb` visual features unavailable at prediction time).
7. **`source` check constraint** — DB only allows `preload|manual|solver|template`. ML predictions use `source='solver'` since `'predicted'` is not in the constraint. If a dedicated source is needed, add a migration to extend `ck_half_day_assignments_check_half_day_source`. (Ref: Block 11 gotcha #1)
8. **Three structural prediction limits** — FMC weekday assignments, NF day-side scheduling, and Thursday PM lectures are coordinator-discretionary or calendar-dependent. These will always require manual handjam regardless of training data volume.
9. **Block Schedule tab format varies** — current AY workbook uses "block N" text in row 1 (not integers). `extract.py` `parse_block_schedule()` must check both row 1 and row 2 for text patterns.
10. **Within-AY accuracy >> cross-AY** — `rot_pgy_dow_half` hits ~57% within same AY but degrades across years as people and rotation assignments change. For Block 13, retrain with B1-12 data (not just B1-10).
