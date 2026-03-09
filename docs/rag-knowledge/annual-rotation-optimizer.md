# Annual Rotation Optimizer (ARO)

> **doc_type:** scheduling_policy
> **Source:** Condensed from `docs/architecture/ANNUAL_ROTATION_OPTIMIZER.md`
> **Last Updated:** 2026-03-09
> **Purpose:** ARO two-tier architecture, solver constraints, leave parsing

---

## Problem

The block-level scheduling engine assigns half-day activities WITHIN a 28-day block. The ARO sits one level above: it decides **which rotation** each resident does in **each block** across all 14 blocks of an academic year.

**Input:** 75 leave requests from 18 residents + PGY-specific rotation requirements
**Output:** 18-resident x 14-block rotation assignment grid maximizing leave satisfaction

---

## Two-Tier Architecture

```
Annual Rotation Optimizer (ARO)     ← assigns rotations to blocks
    |
    v  writes AnnualRotationAssignment (staging)
    |
    v  publish --> BlockAssignment (live)
SchedulingEngine / ActivitySolver   ← assigns half-day activities within block
    |
    v  writes HalfDayAssignment
Live Schedule
```

**Key:** ARO and the daily engine share ZERO constraints. ARO produces `BlockAssignment` records consumed by the existing engine unchanged.

### Model Size

- ~2,200 BoolVars after domain reduction (18 residents x 13 blocks x ~12 eligible rotations)
- Trivial for CP-SAT — solve time <5 seconds

---

## Decision Variable

```python
x[r, b, t] = model.NewBoolVar(f"aro_{r}_{b}_{t}")
```
- `r` = resident index (0-17)
- `b` = block number (1-13 only — Block 0 excluded)
- `t` = rotation template index

Only created where (resident's PGY, rotation, block) is feasible.

**Block 0 exclusion:** 1-day orientation "shock absorber." No rotation variables created. Cross-AY absences mapped to Block 1.

**Combined rotations as single choices:** `[Peds NF + Ward]` = one `t` index. Publish step writes both `rotation_template_id` and `secondary_rotation_template_id`.

---

## Hard Constraints

| ID | Constraint | Implementation |
|----|-----------|----------------|
| H1 | One rotation per block | `AddExactlyOne` per (resident, block) |
| H2 | Fixed assignments | PGY-1 Block 1 = FMO, PGY-3 Block 13 = Military |
| H3 | Rotation completeness | Each required rotation assigned exactly once |
| H4 | Capacity per block | `sum(x[*, b, t]) <= max_residents` |
| H5 | Block eligibility | MBU only blocks 7,9-13; no TAMC L+D blocks 1-2; Psych >= block 4 |
| H6 | Sequencing | Kap L+D must come after TAMC L+D (auxiliary `done_pred` variables) |
| H7 | FMIT cross-PGY | At least 1 resident from each PGY level in FMIT blocks |

### H6 Sequencing (Auxiliary Variables)

```python
done_tamc[r, b] = model.NewBoolVar(...)
model.AddMaxEquality(done_tamc[r, b], [done_tamc[r, b-1], x[r, b, tamc_idx]])
model.Add(x[r, b, kap_idx] == 0).OnlyEnforceIf(done_tamc[r, b-1].Not())
```

---

## Soft Constraints

| ID | Constraint | Weight | Description |
|----|-----------|--------|-------------|
| S1 | Leave satisfaction | 1000 | Each leave request in a leave-eligible block = +1000 |
| S2 | Rotation spread | 10 | Penalty for same rotation in consecutive blocks |

### Cross-Block Leave (S1)

8 of 75 requests span block boundaries. `AddMinEquality` enforces ALL touched blocks must be leave-eligible:

```python
model.AddMinEquality(sat, block_sats)  # sat=1 only if ALL blocks eligible
```

---

## PGY Rotation Requirements

| PGY | Total | Leave-Eligible | Fixed Blocks |
|-----|-------|----------------|-------------|
| 1 | 12 | 6 | Block 1 = FMO |
| 2 | 13 | 6 | None |
| 3 | 12 | 5 | Block 13 = Military |

### Key Capacity Limits

| Rotation | Max per Block |
|----------|--------------|
| FMIT 1/2 | 3 |
| FMC | 6 |
| Electives | 6 |
| SM, MSK | 1 each |
| Others | 1 |

### Key Block Restrictions

- TAMC L+D: NOT blocks 1-2 (PGY-1)
- MBU: ONLY blocks 7, 9-13 (PGY-1)
- [PSYCH + NF]: Starting block 4 (PGY-3)
- Sequencing: Kap L+D after TAMC L+D (PGY-1)

---

## Leave Demand Heatmap

Block 7 (14 requests, holidays) and Block 10 (11 requests, spring break) are the most constrained. Solver must distribute leave-eligible rotations to maximize satisfaction in these hot blocks.

---

## Staging & Lifecycle

```
CREATE (draft) → IMPORT LEAVE → OPTIMIZE (optimized) → REVIEW → APPROVE → PUBLISH
```

**Isolation guarantee:** Staging tables (`annual_rotation_plans`, `annual_rotation_assignments`) never touch `block_assignments` until explicit publish. AY 25-26 continues operating unaffected.

**Publish guard:** Verifies `approved` status, creates MCP backup, deletes only target AY `block_assignments`, writes new rows, marks `published`.

---

## Leave Import

**No separate `leave_requests` table.** Leave requests write directly to `absences` table (status=pending). The solver queries absences by date overlap with the target AY.

**Strict name matching (Unmatched Queue):**
1. Exact last-name match (case-insensitive)
2. Zero or multiple matches → unmatched queue for manual resolution
3. No fuzzy fallback (too risky for annual leave)

**`respect_pending_leave` flag:**
- `True` (Draft): Honors approved + pending requests
- `False` (Strict): Honors approved only

---

## Implementation Status

| Component | Status |
|-----------|--------|
| Solver core (48 tests) | Done |
| DB models + migration | Done (PR #1276) |
| Service layer | Done (PR #1276) |
| API routes (8 endpoints) | Done (PR #1276) |
| Leave import endpoint | Pending |
| Excel export | Pending |
| Frontend UI | Pending |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Monolithic solver | ~250 lines of constraints, all share same `x[r,b,t]` vars |
| PGY config as code | Changes at most once/year |
| Combined rotations as single solver choice | Publish writes both template IDs |
| Block 0 excluded | 1-day orientation, no rotation to assign |
| Cross-block leave via AddMinEquality | ALL touched blocks must be leave-eligible |
| Strict name matching | Fuzzy too risky for annual leave assignment |
| Absence feed-forward | Cross-AY absences propagate automatically via date overlap |

---

## Key Files

- `backend/app/scheduling/annual/solver.py` — CP-SAT solver
- `backend/app/scheduling/annual/pgy_config.py` — PGY rotation requirements
- `backend/app/scheduling/annual/context.py` — AnnualContext, ResidentInfo
- `backend/app/scheduling/annual/leave_parser.py` — Excel date parser
- `backend/tests/scheduling/annual/test_annual_solver.py` — 27 solver tests
- `backend/tests/scheduling/annual/test_leave_parser.py` — 21 parser tests
