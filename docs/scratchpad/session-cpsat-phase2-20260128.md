# Session Scratchpad: CP-SAT Phase 2 (2026-01-28)

## Session Summary
Continued CP-SAT pipeline refinement from Phase 1 completion through Phase 2 implementation.

## Branch
`cpsat-phase2-compliance` (off `main` after PR #773 merged)

## Phase 1 Completion (Start of Session)
- PR #773 merged: CP-SAT semantics alignment (Steps 1-6)
- Includes: activity_id canonical, CV 30% target, post-call soft constraint, capacity_units, docker-compose cleanup

## Phase 2 Progress

### P0/P1: 80-Hour + 1-in-7 Constraints
**Status:** Deferred (external coordination needed)
- Implemented preassigned workload maps from preload/manual assignments
- Fixed-workload exemption tagging (inpatient/NF/offsite rotations)
- Violations correctly detected and tagged as exempt vs non-exempt
- **Decision:** Inpatient/NF time-off determined by external departments; defer resolution
- Current: 10 violations (3 exempt, 7 non-exempt) - policy/data issue, not solver

### P2: Supervision Ratios
**Status:** Complete
- Assignment-level supervision demand (clinic/CV/PROC/VAS)
- AT/PCAT-only coverage
- PROC/VAS add +1 AT demand
- Locked preloads included in baseline
- **Result:** 0 supervision gaps (was 16)

### P3: Template Activity Requirements
**Status:** Complete
- Backfill script: `scripts/ops/backfill_rotation_activity_requirements.py`
- Audit: 0 missing outpatient requirements (37 templates covered)
- Archived non-rotation procedure templates (BTX, COLPO, VAS, POCUS as templates)
- Remapped assignments to PROC rotation

### P4: Faculty Equity
**Status:** Complete
- All faculty MIN clinic = 0 (AT always has room)
- OIC Mon/Fri clinic avoidance (penalty 15-20, skips AT/PCAT/DO)
- Admin equity: GME/DFM/LEC/ADV per role/week (penalty 12)
- AT equity: AT/PCAT per role/week (penalty 12)
- Chu clinic cap: (0, 4)
- Lamoureux: adjunct (already in DB)
- **Result:** Admin range 0-2, AT range 0-2 (good equity)

## VAS/POCUS Implementation (Current)
**Status:** Implemented, pending validation

### POCUS
- Is a **rotation** (not procedure template)
- Primary activities: US (ultrasound) + C (clinic mix)

### VAS
- **Faculty-paired model** (like SM)
- Slots: Thu AM/PM, Fri AM only
- Faculty eligible: Kinkennon, LaBounty, Tagawa
- Faculty priority: (Kinkennon = LaBounty) >> Tagawa (soft penalty)
- Resident eligibility: Only if faculty VAS present
- Resident rotation priority: PROC (0) > FMC (5) > POCUS (10) > other (20)
- Two-way pairing: resident VAS requires faculty VAS AND vice versa

### Pending Verification
- Confirm VAS in activity requirements for PROC/FMC/POCUS templates
- Run Block 10 regen to validate pairing behavior

## Latest Block 10 Results (Pre-VAS)
- Activity solver: OPTIMAL, 0.24s, 455 activities
- AT shortfall: 0
- Activity min shortfall: 1
- Faculty equity: admin range 2, AT range 0
- OIC Mon/Fri: 6 supervision assignments (not blocked)
- No missing requirements warnings

## Key Files Modified This Session
- `backend/app/scheduling/activity_solver.py` (VAS, equity, OIC)
- `backend/app/scheduling/constraints/faculty_clinic.py` (caps, mins=0)
- `backend/app/scheduling/constraints/acgme.py` (fixed-workload exemption)
- `backend/app/scheduling/validator.py` (exemption tagging)
- `backend/app/scheduling/conflicts/analyzer.py` (exemption tagging)
- `backend/app/scheduling/engine.py` (preassigned workload maps)
- `backend/app/utils/supervision.py` (new helper)
- `scripts/ops/backfill_rotation_activity_requirements.py` (new)
- `docs/planning/CP_SAT_PIPELINE_REFINEMENT_PHASE2.md`
- `docs/reports/block10-cpsat-run-20260128.md`
- `docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md`
- `docs/architecture/BLOCK10_CONSOLIDATED_REFERENCE.md`

## Docker State
- Using `docker-compose.local.yml` (dev.yml deleted in Phase 1)
- `MCP_ALLOW_LOCAL_DEV=true` enabled
- Frontend volume fix applied (node_modules not masked)
- All services healthy

## Next Steps
1. Verify VAS activity requirements for PROC/FMC/POCUS
2. Run Block 10 regen to validate VAS pairing
3. Commit Phase 2 changes
4. Create PR for review

## Open Questions
- None blocking

## Penalty Weight Reference
```
Clinic shortfall:        10
Faculty equity:          12
OIC Mon/Fri clinic:      15-20
Clinic overage:          40
AT coverage:             50
```
