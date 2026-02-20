# ML Integration Status — Historical Block Import

**Date:** 2026-02-20
**Author:** Claude Opus 4.6

---

## Summary

Successfully imported ground truth schedule data from 10 academic blocks (Blocks 2-11, AY 25-26) into the half_day_assignments table. This data serves as:
1. **Authoritative schedule records** — coordinator-approved assignments
2. **ML training data** — every `source='manual'` HDA is a labeled example
3. **Diff analysis baseline** — comparing solver output vs coordinator decisions

## Import Statistics

| Block | Total Cells | Inserted | Updated | Skipped (Manual) | Skipped (Code) |
|-------|------------|----------|---------|-------------------|----------------|
| Block 2 | 1,038 | 1,034 | 0 | 0 | 4 |
| Block 3 | 1,967 | 1,891 | 0 | 0 | 76 |
| Block 4 | 1,873 | 1,816 | 0 | 0 | 57 |
| Block 5 | 1,799 | 1,724 | 0 | 25 | 50 |
| Block 6 | 1,795 | 1,742 | 0 | 0 | 53 |
| Block 7 | 1,693 | 1,691 | 0 | 0 | 2 |
| Block 8 | 1,678 | 1,664 | 0 | 0 | 14 |
| Block 9 | 1,804 | 1,784 | 0 | 0 | 20 |
| Block 10 | 1,680 | 169 | 1,504 | 0 | 7 |
| Block 11 | 1,597 | 150 | 0 | 1,447 | 0 |
| **TOTAL** | **16,924** | **13,665** | **1,504** | **1,472** | **283** |

- **Coverage rate:** 98.3% (16,641 imported / 16,924 total cells)
- **Block 10:** 1,504 existing solver/template HDAs upgraded to `source='manual'`
- **Block 11:** 1,447 already imported as manual (previous import), 150 new cells added
- **Unmapped codes:** 283 cells (1.7%) — mostly last-name call assignments and rare one-off codes

## Database State Post-Import

| Source | HDA Count |
|--------|-----------|
| manual | 16,617 |
| preload | 286 |
| solver | 654 |
| **Total** | **17,557** |

## Infrastructure Changes

### New Files Created
- `scripts/data/code_maps.py` — Shared CODE_MAP (120+ entries) extracted from import_block12.py
- `scripts/data/import_historical_blocks.py` — Multi-block importer (~300 lines)

### Modified Files
- `scripts/ops/extract_ground_truth.py` — Auto-detect column layouts (blocks 2-6 use shifted layout)
- `scripts/data/block12_import/import_block12.py` — Now imports CODE_MAP from shared module

### New DB Records
- **41 activities** added (ICU, ER, Pediatrics, subspecialties, etc.)
- **29 people** added (graduated R3s, visiting residents, additional faculty)

## Excel Layout Discovery

The workbook has two column layouts that the extraction script now handles automatically:

| | Layout B (Blocks 2-6) | Layout A (Blocks 7+) |
|---|---|---|
| Names column | C (3) | E (5) |
| Schedule start | Col 4 | Col 6 |
| Template/Role | Cols A-B | Cols C-D |
| Rotation cols | Not present | Cols A-B |
| Date row | Row 2 (Blocks 3-4) or Row 3 | Row 3 |

## Training Data Readiness

### Ready
- **16,617 labeled half-day assignments** across 10 blocks (8 months of scheduling)
- **56 people** (27 original + 29 added) with assignment histories
- **115 activity codes** covering all observed schedule codes
- Data spans July 2025 through May 2026

### Next Steps
1. **Rebase `feat/schedule-vision-research` branch** — Training pipeline can now use 10 blocks
2. **Fit ScheduleScorer** — `ml_score` node (PR #1181) can be trained on this data
3. **Diff analysis** — Run `diff_truth_vs_db.py` to compare solver output vs ground truth
4. **Block 12 solver** — 10 blocks of pattern data available for informing solver parameters

### Unmapped Code Categories (for future cleanup)
- **Last-name call codes** (e.g., "LastnameA", "LastnameB") — coordinator shorthand for call assignments
- **Exam codes** (COMLEX1, COMLEX2, STEP3) — partially mapped
- **Rare rotations** (OPMed, CAFBHS, WICS) — institution-specific

## Backups
- **Pre-import:** `/tmp/block12_pre_historical_import_20260220T115107.dump` (2.9M)
- **Post-import:** `/tmp/block12_post_historical_import_20260220T115414.dump` (4.0M)
