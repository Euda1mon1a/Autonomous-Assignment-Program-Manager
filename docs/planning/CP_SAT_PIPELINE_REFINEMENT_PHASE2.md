# CP-SAT Pipeline Refinement — Phase 2 Roadmap

Date: 2026-01-28
Scope: Phase 2 (post-Phase‑1 canonicalization + Step‑6 validation)

## Purpose
Phase 2 focuses on **correctness and clinical constraints** that were intentionally deferred during Phase 1. The pipeline is now stable and reproducible; Phase 2 fixes known compliance gaps and turns template data into enforceable constraints.

## Decision: Include Step‑6 Validation Findings in Phase 2
**Recommendation: INCLUDE** the Step‑6 validation findings in Phase 2. These issues are the natural next steps of pipeline refinement (compliance + supervision) and should not be split into a separate phase unless we want to freeze the schedule quality at a known‑imperfect baseline.

Rationale:
- The items directly impact schedule validity (ACGME compliance and supervision).
- They are already measurable and repeatable via MCP/validation tools.
- Keeping them in Phase 2 preserves a clean “Phase 1 = canonical pipeline, Phase 2 = compliance + constraint completeness” boundary.

If a separate phase is desired later, split Phase 2 into:
- **Phase 2A (Compliance/Core Constraints)**
- **Phase 2B (Optimization/Quality Enhancements)**

## Baseline (Step‑6 Validation Complete ✓)
Issues are consistent across runs and documented; they are Phase‑2 work, not Phase‑1 blockers.

| Issue Category | Count | Phase 2 Work |
| --- | --- | --- |
| 80‑hour violations | 2 | P0: Work‑hour constraint enforcement |
| Consecutive‑days (1‑in‑7) | 8 | P1: Time‑off in solver context |
| Supervision gaps | 16 | P2: AT/PCAT ratio constraints |
| Template warnings | Several | P3: Activity requirement data cleanup |

## Guiding Principles (Phase 2)
- **Rotation level = inpatient/outpatient only.**
- **Non‑rotation workload fairness is assignment‑level, faculty‑only.**
- **Resident rotations rely on template soft constraints; no extra rotation‑level workload logic.**
- **Conferences are absences; sick leave is manual post‑release.**

## Phase 2 Scope
### P0 — Compliance Hardening
- Enforce 80‑hour limits in solver context (time‑off aware).
- Resolve critical work‑hour violations to 0 in validation runs.

**P0 Substeps + Acceptance Criteria**
1. Load time‑off templates into solver context (see P1).
2. Add 80‑hour constraint in solver (soft, high penalty).
3. Validate: **0 non‑exempt 80‑hour violations** in Block‑10 MCP validation.

### P1 — Time‑Off Context
- Ensure time‑off templates/absences are loaded into solver context.
- Restore 1‑in‑7 rest constraints with correct data.

**P1 Substeps + Acceptance Criteria**
1. Ensure time‑off templates are present in solver context.
2. Ensure time‑off half‑days are assigned/locked before CP‑SAT.
3. Validate: **0 non‑exempt 1‑in‑7 violations** (fixed‑workload exempt allowed).

**Status (2026‑01‑28)**
- Implemented **preassigned workload maps** from preload/manual half‑day assignments.
- 1‑in‑7 and 80‑hour constraints now **account for fixed workload** and skip infeasible windows.
- Validation still reports **2× 80‑hour** and **8× 1‑in‑7** violations (fixed‑workload driven).
- Policy: **fixed‑workload violations are exempt but tagged**; non‑exempt remain actionable.
- **Templates sheet integration:** OFF/W weekly patterns now applied as time‑off preloads.
  - Source: `data/inpatient_time_off_overrides.json`
  - Pipeline: `scripts/ops/generate_inpatient_time_off_overrides.py` → `scripts/ops/apply_inpatient_time_off_overrides.py`
  - Current mappings: **PEDSW (week‑4 weekend W)**, **PNF (Fri PM OFF)**
- **Manual rules added (authoritative):**
  - **FMIT PGY‑1/PGY‑2:** Saturday = W (AM/PM, weeks 1–4)
  - **FMIT PGY‑3:** Sunday = W (AM/PM, weeks 1–4)
  - **IMW (IM / IM‑PGY1):** Saturday = W (AM/PM, weeks 1–4)
  - **PEDSW (Peds Ward Day):** Saturday = W (AM/PM, weeks 1–4)
  - **PNF (Peds NF):** Saturday = W (AM/PM, weeks 1–4)
  - Manual file: `data/inpatient_time_off_overrides_manual.json`
- **Status update:** 80‑hour and 1‑in‑7 violations cleared for Block 10.

### P2 — Supervision Constraints
- Align AT/PCAT ratio constraints with current staffing patterns.
- Make supervision constraints feasible but enforced (hard or high‑penalty soft).

**P2 Substeps + Acceptance Criteria**
1. Confirm supervision provider set (AT + PCAT) and required set (C/CV/PROC/VAS).
2. Implement supervision ratio as soft constraint (penalty 50–75).
3. Validate: **supervision gaps = 0** in MCP detect_conflicts (or justified).

**Status (2026‑01‑28)**
- Implemented assignment‑level supervision demand (clinic/CV/PROC/VAS).
- Supervision coverage restricted to **AT/PCAT** only.
- PROC/VAS add +1 AT demand (scaled by 4 units in CP‑SAT).
- Conflict analyzer now evaluates **half‑day assignments** for supervision ratios.
- Block 10 conflict analysis: **0 supervision gaps**.

### P3 — Template/Activity Data Cleanup
- Eliminate missing activity requirement warnings (data completeness).
- Ensure all outpatient templates have rotation_activity_requirements.

**P3 Substeps + Acceptance Criteria**
1. Identify templates missing activity requirements (warnings list).
2. Backfill requirements for outpatient templates.
3. Validate: **0 missing activity requirement warnings** in solver logs.

**Status (2026-01-28)**
- Added `scripts/ops/backfill_rotation_activity_requirements.py` to backfill
  requirements from `weekly_patterns`.
- Audit run (dry-run) reports **0 missing outpatient requirements**
  (37 outpatient templates already have requirements).
- P3 complete; keep backfill script for future templates.

### P4 — Faculty Equity at Assignment Level (Non‑rotation)
- Move admin/academic equity to **assignment‑level** for faculty only
  (AT/GME/DFM/LEC/ADV, etc.).
- Remove rotation‑level academic/admin workload logic.
- Define role‑based targets (core vs PD vs adjunct) and penalties.

**P4 Substeps + Acceptance Criteria**
1. Define role‑based targets (core vs PD vs adjunct) and weights.
2. Implement assignment‑level equity in activity solver objective.
3. Validate: equity metric reported; penalty weight documented.

**Status (2026‑01‑28)**
- Implemented **assignment‑level equity** in activity solver:
  - Admin/academic set: **GME/DFM/LEC/ADV** (per‑week, per‑role range penalty).
  - Supervision set: **AT/PCAT** (per‑week, per‑role range penalty).
- Added solver logging for equity range totals.

**P3 Follow‑up (2026‑01‑28)**
- Archived non‑rotation templates **BTX/COLPO/VAS/POCUS/PROC‑AM/PR‑PM** and
  remapped any block/assignment rows to **PROC** rotation.
- Removed fallback warnings for these templates.

**Deferred Policy (2026‑01‑28)**
- **VAS post‑solver allocation** (not implemented):
  - Target **~3 VAS per block**, include some **VAS+C** pairings.
  - Resident priority (soft): **PROC > FMC > US/POCUS**.
  - May be cleaner as a **post‑solver** step than a core CP‑SAT constraint.
  - **VASC = Vasectomy Counseling**: normal AT supervision rules (clinic‑like),
    group counseling + exams/consents.

## Non‑Goals (Phase 2)
- GUI/UX changes (defer until correctness is stable).
- Production automation or policy enforcement beyond local dev.
- Rewriting legacy schedulers or replacing CP‑SAT.

## Entry Criteria
- Phase‑1 canonical pipeline generates Block 10 without INFEASIBLE.
- MCP validation tools run without 404/500 errors.
- Known gaps documented (Step‑6 complete).

## Exit Criteria
- Zero 80‑hour violations in Block‑10 validation.
- 1‑in‑7 rest violations resolved or explicitly exempted.
- Supervision gaps reduced to 0 or justified by policy.
- No missing activity‑requirement warnings for outpatient templates.
- Faculty assignment equity defined and reported at assignment level.

## Phase 2 Workstreams (Proposed Order)
1. **Time‑off in solver context** (enables 80‑hour + 1‑in‑7 validity)
2. **Work‑hour constraints** (validate P0 success)
3. **Supervision ratios** (AT/PCAT constraints)
4. **Template requirements cleanup**
5. **Faculty assignment‑level equity**

## Deferred to Phase 3
Procedure/counseling refinements (VASC + post‑solver VAS allocator) moved to
Phase 3 to keep Phase 2 focused on compliance. See
`docs/planning/CP_SAT_PIPELINE_REFINEMENT_PHASE3.md`.

## Validation Checklist (Per Iteration)
- Run `block_regen.py` for Block 10 (AY2025).
- Run MCP tools:
  - `validate_schedule_tool`
  - `detect_conflicts_tool`
  - `generate_block_quality_report_tool`
- Update docs:
  - `docs/reports/block10-cpsat-run-*.md`
  - `docs/analysis/block10_mcp_validation_*.md` (local only)

---

## Open Questions (Need Decisions)
1. Should supervision ratios be hard or soft (high‑penalty) in Phase 2?
2. What is the target equity model for faculty admin/academic work?
3. Should conferences be treated as absence only (default) or as educational rotations?
