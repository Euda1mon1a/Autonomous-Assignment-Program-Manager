# Block 12 Dry Run Postmortem

> **Date:** 2026-02-18
> **Block:** 12 (May 7 – Jun 3, 2026), AY 2025
> **Type:** Dry run — auto-derived from Excel Block Schedule + DB, no coordinator handjam
> **Trigger:** User request to test how much of the handjam can be automated before the interactive session

---

## Executive Summary

A dry run of the Block 12 schedule import was performed using the Excel "Block Schedule" master grid and DB rotation templates — without the coordinator's daily handjam Excel (which doesn't exist yet for Block 12). The dry run uncovered that **all 16 block_assignments were stale** (containing Block 11 rotation data), corrected them to match the coordinator's master schedule, and rebuilt 896 resident assignments.

| Metric | Pre-Dry-Run | Post-Dry-Run |
|--------|------------|--------------|
| block_assignments | 16 (all wrong) | 16 (all correct) |
| Resident assignments (primary) | 752 (wrong rotations) | 896 (correct rotations) |
| Faculty assignments (supervising) | 240 | 216 (removed deployed faculty) |
| Half-day assignments | 2 (preloads) | 2 (unchanged — needs handjam) |
| Absences overlapping B12 | 8 | 8 (unchanged) |
| Stale data removed | — | 776 assignments + 40 graduated R3 |

---

## Timeline

| Time (HST) | Action | Duration |
|------------|--------|----------|
| 18:30 | Spawned 2 agents: Excel explorer + DB state checker | — |
| 18:35 | DB agent returned: 16 stale block_assignments, 992 assignments, 8 absences | 5 min |
| 18:37 | Excel agent returned: 10 sheets, Block 12 tab absent, Block Schedule has rotation grid | 7 min |
| 18:38 | Queried Excel Block Schedule col 24-25 for Block 12 rotation assignments | 1 min |
| 18:39 | Cross-referenced Excel vs DB — discovered 15 of 16 are wrong | 1 min |
| 18:40 | Queried rotation template IDs for mapping | 1 min |
| 18:41 | DB checkpoint: `pre_dry_run` (2.9MB) | <1 min |
| 18:42 | Created `dry_run.py`, ran — hit column-order bug in rotation lookup | 2 min |
| 18:43 | Fixed bug (SELECT column order vs unpack order), restored DB, re-ran | 1 min |
| 18:44 | Dry run completed: 16 block_assignments created, 896 assignments rebuilt | <1 min |
| 18:44 | DB checkpoint: `post_dry_run` (2.9MB) | <1 min |
| 18:45 | Updated `import_block12.py` with NAME_MAP (27 entries) and EXCEL_PATH | 1 min |
| 18:46 | Updated `BLOCK12_SCHEDULE_LOAD.md` with full dry run results | 2 min |
| **Total** | | **~20 min** |

---

## What Was Discovered

### 1. block_assignments Were 100% Stale (Critical)

Every single Block 12 block_assignment in the DB contained the wrong rotation. The data appeared to be from an earlier solver run that either duplicated Block 11 data or used a prior iteration of the block schedule.

All 16 residents had mismatched rotations — e.g., residents assigned to TAMC-LD in DB were actually on NF-FMIT-PG per Excel, PROC assignments should have been MSK-SEL, etc. Only 1 of 16 happened to match by coincidence.

**Root cause:** The solver generates block_assignments as part of schedule generation. Since Block 12 hadn't been officially scheduled yet, the existing data was from a prior run with stale rotation mappings. The coordinator's Excel "Block Schedule" sheet is the authoritative source, but it was never synced to the DB for Block 12.

**Lesson:** Always cross-reference `block_assignments` against the Excel Block Schedule before running any import. Add a pre-flight check to the import script that compares DB vs Excel and flags mismatches.

### 2. Graduated R3 Not in Block 12

The Excel Block Schedule shows a graduated R3 assigned through Block 10 with blocks 11-12 blank. However, the DB had 40 stale assignment records for this resident in Block 12 as ELEC/primary, plus no block_assignment record.

**Fix:** Deleted the 40 stale assignments. Excluded from Block 12 roster.

### 3. Deployed Faculty Assigned

A deployed faculty member (deployment Feb 21 – Jun 30, 2026) had 24 supervising assignments in the Block 12 date range from the prior solver run.

**Fix:** Deleted the 24 supervising assignments. Faculty should not appear in Block 12 coverage.

### 4. Memorial Day Not Flagged

May 25, 2026 (Monday) is Memorial Day but was not flagged as `is_holiday=true` in the blocks table. This could affect leave/off calculations during the handjam.

**Status:** Fixed during pre-handjam session.

### 5. Seven Name Discrepancies

The Excel uses legal/formal names while the DB uses preferred names — 7 discrepancies found (first name variants, spelling differences). All handled by the NAME_MAP dictionary (27 entries pre-filled).

### 6. Six Split-Block Residents

Six residents have split-block assignments (rotation + night float). Four have combined templates (whole-block handling). Two use primary/secondary split at day 15.

---

## What Was Fixed

1. **Deleted** 16 stale block_assignments, **created** 16 correct ones from Excel Block Schedule
2. **Deleted** 776 stale assignments (712 wrong-rotation + 40 graduated R3 + 24 deployed faculty)
3. **Created** 896 correct resident assignments (16 residents × 56 half-day slots)
4. **Pre-filled** NAME_MAP with 27 entries (17 residents + 10 faculty)
5. **Set** EXCEL_PATH in import script
6. **Documented** 5 gotchas in session log

---

## What Still Needs the Interactive Handjam

The dry run derived ~80% of the structural schedule but cannot populate:

| Missing Data | Why | Impact |
|-------------|-----|--------|
| Faculty AM/PM activity codes | Come from handjam, not templates | No faculty HDAs |
| Call schedule | Staff Call row in Excel | No call assignments |
| Day-specific overrides | Clinic cancellations, SIM days, conferences | Some HDAs will be wrong |
| Sports med rotator schedule | Listed as SM rotator in Block Schedule | Unclear rotation pattern |
| TY/Flight Surgeon assignments | Transient personnel not in DB | Missing from schedule |
| Medical student assignments | IPAP/USU students vary by block | Missing from schedule |
| Exact NF split dates | Used day 15 cutoff; actual may differ | 2 residents may have wrong split |
| Half-day assignments (HDAs) | Need template-to-code mapping from handjam | 0 HDAs generated |

---

## Bug Found During Dry Run

**Column-order mismatch in rotation template lookup:**

```python
# BUG: SELECT returns (id, abbreviation, name) but unpack was (rid, name, abbr)
cur.execute("SELECT id, abbreviation, name FROM rotation_templates")
rot_templates = {abbr: (rid, name) for rid, name, abbr in cur.fetchall()}
#                                      ^^^ name gets abbreviation, abbr gets name

# FIX:
rot_templates = {abbr: (rid, rname) for rid, abbr, rname in cur.fetchall()}
```

This caused all 16 rotation template lookups to fail silently (returned "NOT FOUND"), which would have resulted in 0 block_assignments created. Caught on first run, fixed, DB restored, and re-run succeeded.

**Lesson:** Always name unpack variables to match SELECT column order. Consider using `dict(cur)` or named tuples to avoid positional bugs.

---

## Artifacts

| File | Purpose | Committed? |
|------|---------|-----------|
| `scripts/data/block12_import/dry_run.py` | Dry run script | No (gitignored) |
| `scripts/data/block12_import/dry_run_report.md` | Comparison report | No (gitignored) |
| `scripts/data/block12_import/import_block12.py` | Import script with NAME_MAP | No (gitignored) |
| `scripts/data/block12_import/fix_block12_assignments.py` | Assignment rebuild | No (gitignored) |
| `scripts/data/block12_import/checkpoint.sh` | DB backup utility | No (gitignored) |
| `scripts/block_import_preflight.py` | Reusable pre-flight validator | Yes |
| `docs/scheduling/BLOCK12_SCHEDULE_LOAD.md` | Session log (updated) | Yes |

---

## Post-Dry-Run DB State

| Table | Count | Notes |
|-------|-------|-------|
| `block_assignments` (B12) | 16 | All correct per Excel Block Schedule |
| `assignments` (primary, B12) | 896 | 16 residents × 56 slots |
| `assignments` (supervising, B12) | 216 | Faculty minus deployed member |
| `half_day_assignments` (B12) | 2 | Preloads only |
| `absences` (overlapping B12) | 8 | Unchanged |

All 16 residents have exactly 56 assignment slots. 9 faculty members have 24 supervising slots each (deployed member excluded).

---

## Recommendations for Interactive Handjam Session

1. **Start from post-dry-run checkpoint** — block_assignments are already correct, no need to redo
2. **Create Block 12 tab in Excel** matching the "Import" layout (Layout A: rotation in col 1, name in col 5)
3. **Verify NF split dates** for the 2 split-block residents — day 15 may not be the actual cutoff
4. **Memorial Day already flagged** — no action needed
5. **Watch for graduated R3** — may appear in the handjam Excel despite not being assigned
6. **Watch for deployed faculty** — should have no entries
7. **Use the NAME_MAP** pre-filled in `import_block12.py` — 7 name variants already documented
8. **Take checkpoints** after each step using `checkpoint.sh`
