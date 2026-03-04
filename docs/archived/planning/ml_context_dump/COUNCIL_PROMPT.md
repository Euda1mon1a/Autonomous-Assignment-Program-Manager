# Council Prompt — Phase 6 E2E Results: Constraint Granularity Problem

## Instructions for Perplexity

Use **Reasoning mode** with the council (GPT-5.2 Thinking, Claude Opus 4.6 Thinking, Gemini 3.1 Pro Thinking). The council previously recommended Phase 6 (E2E solver validation) as the unanimous highest-ROI next step. **Phase 6 is now complete.** The results revealed a structural problem the council didn't anticipate. I need guidance on how to fix it.

---

## Prompt

I'm building a medical residency scheduling system that uses Google OR-Tools CP-SAT to generate schedules. The council previously guided Phases 1-5 (ML constraint mining and calibration) and recommended Phase 6 (E2E solver validation). **Phase 6 is done. The results are surprising and reveal a structural constraint granularity mismatch.**

### Quick Recap (Phases 1-5)

- Mined 17,464 half-day assignments into 276 rotation profiles
- Learned constraints from historical data with split-block awareness, confidence tiers, anomaly detection
- Cross-validation: 88.9% containment (93.5% high-confidence)
- Applied calibration: 13 new constraints, 28 widened, lec min->0 (75 templates), ADV min->0 (27 templates)
- Total: 195 rotation_activity_requirements across 80 templates

### Phase 6 E2E Results (The Surprise)

**Method:** Temporarily unlock all manual slots (change source from "manual" to "template" so the solver picks them up), run the CP-SAT activity solver, compare solver output to coordinator's original assignments, then rollback. DB never modified.

**Critical architectural discovery:** The activity solver **only fills outpatient rotation slots**. It filters by `rotation_type == "outpatient"` via `_filter_outpatient_slots()`. Inpatient, night float, off-service, and education rotations are NOT handled by this solver. The coordinator manually assigns 97% of all slots.

| Block | Total Slots | Outpatient Slots (solver-filled) | Solver Status | Runtime | Constraint Sat. | Jaccard (filled) | Slot Match (filled) |
|-------|------------|----------------------------------|---------------|---------|-----------------|------------------|---------------------|
| 6 | 1,742 | 623 (36%) | FEASIBLE | 180.7s | 24.4% | 0.186 | 9.6% |
| 8 | 1,664 | 636 (38%) | OPTIMAL | 1.6s | 17.8% | 0.153 | 14.0% |
| 10 | 1,681 | 961 (57%) | FEASIBLE | 180.4s | 24.6% | 0.137 | 12.7% |

**Rotation type distribution per block:**

| Block | Outpatient | Inpatient | Off | Education |
|-------|-----------|-----------|-----|-----------|
| 6 | 5 residents | 10 residents | 1 | 1 |
| 8 | 8 residents | 6 residents | 3 | 0 |
| 10 | 7 residents | 8 residents | 2 | 0 |

### The Five Problems Revealed

**Problem 1: Block-level calibration vs weekly-level application (GRANULARITY MISMATCH)**

The ML pipeline (Phase 3+5) learned constraints at **block-level granularity** (e.g., "Family Medicine Clinic rotation needs 8-12 fm_clinic halfdays per 28-day block"). But the solver applies constraints at **weekly granularity** using `applicable_weeks`. The solver partitions each person's slots into weekly buckets, and many person-week combinations only have 1-2 available outpatient slots. Result: massive clamping warnings like "min=3 available=1" (dozens per block).

This is the root cause of the low constraint satisfaction (17-25%). The solver can't satisfy block-level minimums when split across 4 weeks with limited slots per week.

**Problem 2: Solver only handles outpatient rotations (36-57% of slots)**

The activity solver is designed ONLY for outpatient scheduling. All inpatient, night float, off-service, and education rotation slots must be manually assigned by the coordinator. This means the solver's utility is limited to ~40% of the scheduling workload.

**Problem 3: Low slot match is structural, not a quality issue**

The 10-14% slot-level match rate between solver and coordinator is expected because:
- Many valid permutations exist for the same constraints
- The solver optimizes a different objective than the coordinator's implicit preferences
- Faculty administrative patterns differ between solver and coordinator
- The solver assigns fm_clinic heavily (e.g., one person got 30 fm_clinic vs max 6)

**Problem 4: Constraint satisfaction is low even for solver output**

The solver's OWN output only satisfies 17-25% of the DB constraints. Key violations:
- `lec` min=4-5 but solver assigns 0 lec (Phase 5 fixed some templates to min=0, but not all)
- `ADV` min=1 but solver assigns 0 ADV
- `fm_clinic` max=3-6 but solver assigns 14-30 fm_clinic (over-assigns clinic)
- These patterns suggest the solver doesn't have enough activity variety in its candidate pool

**Problem 5: Solver timeout variance**

Block 8 hit OPTIMAL in 1.6s while blocks 6 and 10 ran the full 180s timeout (FEASIBLE only). Block 10 had 961 outpatient slots vs 623-636 for blocks 6/8. The constraint complexity appears to scale nonlinearly with slot count.

### Current Solver Internals (relevant to these problems)

```python
# Activity solver only fills outpatient rotation slots
OUTPATIENT_ACTIVITY_TYPES = {"outpatient"}

# Penalty weights (all soft constraints)
ACTIVITY_MIN_SHORTFALL_PENALTY = 10
CLINIC_MIN_SHORTFALL_PENALTY = 25
ACTIVITY_MAX_OVERAGE_PENALTY = 20
CLINIC_MAX_OVERAGE_PENALTY = 40
AT_COVERAGE_SHORTFALL_PENALTY = 50

# Weekly slot partitioning
# Solver groups slots by person-week, applies requirements per week
# Block-level constraints get distributed across weeks via applicable_weeks
```

The solver's `_load_activity_requirements()` method:
- Queries `rotation_activity_requirements` joined with templates and activities
- Gates on `applicable_weeks`: null = all weeks, non-null = specific weeks only
- Each person-week may have only 1-4 outpatient slots (vs the 8-10 the constraints assume)
- Solver clamps min requirements to available slots when feasibility is impossible

### Questions for the Council

1. **Granularity fix strategy:** The block-level calibration (Phase 3+5) produced constraints that don't work at weekly granularity. Three possible fixes:
   - **Option A:** Re-learn constraints at weekly granularity (mine weekly code_counts per person-rotation, not block totals)
   - **Option B:** Add a weekly-to-block mapping layer that distributes block-level requirements across weeks proportionally
   - **Option C:** Change the solver to apply constraints at block-level instead of weekly
   Which approach has the highest ROI? Are there other options?

2. **Solver scope expansion:** The solver only handles outpatient rotations (36-57% of slots). Should we:
   - **Accept the narrow scope** and focus on making outpatient scheduling excellent?
   - **Expand the solver** to handle inpatient/NF/education rotations?
   - **Build separate solvers** for each rotation type?
   What's the right approach for a 33-person program?

3. **fm_clinic over-assignment:** The solver assigns 14-30 fm_clinic halfdays to some people (vs max 3-6 in constraints). This suggests the solver defaults to fm_clinic when it can't assign other activities. Is this:
   - A constraint issue (not enough activity options defined)?
   - A penalty weight issue (fm_clinic penalty too low)?
   - A structural issue (fm_clinic is the only activity available for most outpatient slots)?

4. **Phase 6b (weight sensitivity) — skip or proceed?** Given that constraints are infeasible at weekly granularity, is weight tuning premature? Or would weight tuning still provide useful signal even with constraint issues?

5. **Revised roadmap:** Given these findings, should we adjust the Phase 7-11 roadmap? The original plan was:
   ```
   Phase 7: Resident weekly FM clinic calibration
   Phase 8: Bayesian penalty weight optimization (Optuna)
   Phase 9: Faculty clinic caps calibration
   Phase 10: Template-family sharing
   Phase 11: ML penalty terms in objective
   ```
   Should Phase 7 now be "Fix granularity mismatch" instead of "FM clinic calibration"? Or are they the same thing?

6. **Metric recalibration:** The original council recommended targets of:
   - Tier 1 (constraint satisfaction) >= 95%
   - Tier 2 (Jaccard) >= 0.70
   - Tier 3 (slot match) >= 50%

   Given that the solver only handles 36-57% of slots, and that many valid permutations exist, should we revise these targets? What are realistic targets for this solver architecture?

7. **Alternative validation approach:** Since slot-level match is structurally low (many valid permutations), should we focus on different metrics? Options:
   - **Distribution match:** Compare activity code frequency distributions (solver vs coordinator)
   - **Constraint-as-objective:** Maximize constraint satisfaction rate as the primary metric
   - **Coordinator preference learning:** Learn the coordinator's implicit preferences as additional soft constraints
   - **Coverage quality:** Measure attending coverage, clinic capacity utilization, equity metrics

### Attached Files (in this directory)

| File | Description |
|------|-------------|
| `ml_mining_results_context.md` | Full context with Phase 1-6 results |
| `e2e_results_summary.json` | Phase 6 E2E results (trimmed, per-block metrics) |
| `validate_e2e.py` | E2E validation script (new) |
| `schema_context.md` | Database schema |
| `learn_constraints.py` | v2 constraint learner |
| `validate_calibration.py` | Cross-validation script |
| `calibrate_constraints.py` | DB writer |
| `mine_rotation_patterns.py` | v2 profile extractor |
| `mine_rules.py` | FP-Growth association rules |
| `cluster_rotations.py` | HDBSCAN clustering |
| `constraint_diff.md` | v1 constraint diff (superseded) |
