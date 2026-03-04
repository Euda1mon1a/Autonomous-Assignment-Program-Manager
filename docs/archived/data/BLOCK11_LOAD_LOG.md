# Block 11 Schedule Load — 2026-02-12

## Summary

Loaded the complete Block 11 schedule (2026-04-09 to 2026-05-06) into the database from the authoritative Excel source of truth, verified cell-by-cell.

## Source

- **Excel:** `Block 11 for claude code.xlsx` (archived repo)
- **Sheet:** "Block 11 Import" — 144 rows × 75 columns
- **Layout:** Row 4 = Staff Call, Rows 10-25 = Residents (56 half-day slots each), Rows 31-40 = C19 Faculty

## What Was Loaded

| Component | Count | Verification |
|-----------|-------|-------------|
| Resident HDAs | 896 slots (16 residents × 56) | 896/896 match Excel |
| Faculty HDAs | 401 slots (10 faculty) | All match Excel |
| Call assignments | 28 overnight (1 per night) | 28/28 match Excel Row 4 |

## Activities Created

11 new activities added to support Block 11 codes:

| Code | Category | Name |
|------|----------|------|
| DERM | clinical | Dermatology |
| C30 | clinical | Clinic 30-Min |
| ORIENT | educational | Orientation |
| CODING | educational | Coding |
| HV | clinical | Home Visit |
| V2 | clinical | Virtual Visit |
| RETREAT | educational | Retreat |
| CCC | administrative | Clinical Competency Committee |
| SLV | administrative | Supervisory Leave |
| LV | administrative | Leave |
| HR-SUP | administrative | HR Supervisor Training |

## Personnel Notes

- One off-cycle graduate removed from block 11+ assignments
- One faculty member deployed entire block (DEP × 56 slots)
- Asterisk on Excel names = DO degree (OMT); no scheduling impact, can add to DB later
- Adjunct faculty, PSY, fellows, and MS3s — out of scope for initial load

## Call Schedule Distribution

9 faculty share 28 overnight call assignments (1 per night, no gaps). One faculty has 4 nights; the other 8 each have 3 nights. Balanced distribution across the block.

## FMIT Attending Coverage

4 faculty rotate FMIT attending coverage across the block in weekly segments, with one covering the tail end of the prior block on Day 1.

## Artifacts

- `/tmp/block11_schedule_grid.md` — Markdown grid visualization
- `/tmp/block11_schedule_output.xlsx` — Plain Excel for copy/paste
- `/tmp/block11_checkpoint_20260212.sql` — Full DB backup (77K lines)
- `/tmp/verify_fixes.py` — Cell-by-cell verification script

## Process

1. Resident schedules loaded from handjam, verified against Excel — 14/16 matched immediately
2. Two residents reloaded from Excel due to handjam offset errors — fixed to 56/56
3. Faculty loaded from handjam, then 4 reloaded from Excel (offset errors in original handjam)
4. Call schedule rebuilt entirely from Excel Row 4 (original derivation method was incorrect)
5. Final verification: **1,260/1,260 slots match Excel source of truth**
