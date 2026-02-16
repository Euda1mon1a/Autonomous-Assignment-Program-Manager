# Block 10 CP-SAT Regen + Activity Solver Report (2026-01-28)

## Run Summary (Phase 2 P4: faculty equity)
**Block window:** **2026-03-12 → 2026-04-08** (Block 10, **AY2025**).

- **CP-SAT generation succeeded** with **589** solver assignments + **20** call nights.
- **144 solver assignments skipped** due to immutable existing assignments → **445 persisted**.
- **Activity solver succeeded** (OPTIMAL, **0.24s**, **455** activities).
- **PCAT/DO integrity check passed** (20 calls verified; **34** PCAT/DO slots synced).
- **Physical capacity constraints applied** (soft 6 / hard 8) across **40/40** slots.
- **Activity min shortfall total:** 1 (soft penalty applied).
- **AT coverage shortfall total:** 0.
- **Faculty admin equity range total:** 2.
- **Faculty AT equity range total:** 0.

### P3 Follow‑up (resolved)
- Archived non‑rotation templates (**BTX/COLPO/VAS/POCUS/PROC‑AM/PR‑PM**) and
  remapped any block/assignment rows to **PROC** rotation.
- **No “missing activity requirements” warnings** after cleanup.

### OIC Availability Check
OIC supervision on Mon/Fri is still permitted; run produced **6** Mon/Fri
AT/PCAT/DO assignments for OIC (no blocking from the new preference).

## Run Summary (Phase 2 P2: supervision ratios)
**Block window:** **2026-03-12 → 2026-04-08** (Block 10, **AY2025**).

- **CP-SAT generation succeeded** with **589** solver assignments + **20** call nights.
- **144 solver assignments skipped** due to immutable existing assignments → **445 persisted**.
- **Activity solver succeeded** (FEASIBLE, **30.24s**, **457** activities).
- **PCAT/DO integrity check passed** (20 calls verified; **32** PCAT/DO slots synced).
- **Physical capacity constraints applied** (soft 6 / hard 8) across **40/40** slots.
- **Activity min shortfall total:** 1 (soft penalty applied).
- **AT coverage shortfall total:** 0.

## Key Change (P2)
- Supervision demand now counts **clinic/CV/PROC/VAS** slots (assignment-level), not just solver slots.
- **PROC/VAS add +1 AT** demand (scaled by 4 in CP-SAT).
- **Supervision coverage restricted to AT/PCAT** activities only.
- Conflict analyzer supervision check now uses **half‑day assignments** + AT/PCAT coverage.

## Validation (backend)
- **ACGME validator:** 10 violations (8 × 1‑in‑7, 2 × 80‑hour).
- **Conflict analysis:** 10 total, **0 supervision gaps**, 8 × 1‑in‑7, 2 × 80‑hour.

## P3 Template Requirements Audit
- Ran: `python3.11 scripts/ops/backfill_rotation_activity_requirements.py --dry-run`
- Result: **0 requirements created** (all **37** outpatient templates already have
  rotation activity requirements).

## Command
```
DB_PASSWORD=local_dev_password \
  python3.11 scripts/ops/block_regen.py --block 10 --academic-year 2025 --timeout 300 --clear
```
