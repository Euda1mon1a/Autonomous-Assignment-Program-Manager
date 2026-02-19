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

---

## DB Checkpoints

| Label | Timestamp | File |
|-------|-----------|------|
| pre-dry-run | 2026-02-18T18:41:38 | `/tmp/block12_pre_dry_run_*.dump` |
| post-dry-run | 2026-02-18T18:44:28 | `/tmp/block12_post_dry_run_*.dump` |
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

### 1. Excel Parsing & HDA Sync

- Source Excel: _(awaiting Block 12 handjam tab)_
- Sheet: _(Block 12 tab doesn't exist yet)_
- NAME_MAP: 27 entries pre-filled from Block 11 Import
- CODE_MAP: 50+ entries carried from Block 11

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

- [ ] HDA count matches Excel (days x 2 x people)
- [ ] 100% activity code match between Excel and DB
- [x] Assignments rebuilt with correct rotation templates (dry run)
- [ ] HDA `block_assignment_id` populated for residents
- [ ] Faculty weekly templates have `activity_id` on all slots
- [ ] Absences match Excel leave/TDY/deployment data
- [ ] GUI renders Block 12 schedule correctly
- [ ] PR passes Codex review (all P1/P2 addressed)

---

## Final State

| Table | Count | Status |
|-------|-------|--------|
| `half_day_assignments` | 2 (preloads only) | Pending handjam |
| `assignments` | 896 (residents) | Dry run complete |
| `block_assignments` | 16 | Corrected from Excel |
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
