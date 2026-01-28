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

### P1 — Time‑Off Context
- Ensure time‑off templates/absences are loaded into solver context.
- Restore 1‑in‑7 rest constraints with correct data.

### P2 — Supervision Constraints
- Align AT/PCAT ratio constraints with current staffing patterns.
- Make supervision constraints feasible but enforced (hard or high‑penalty soft).

### P3 — Template/Activity Data Cleanup
- Eliminate missing activity requirement warnings (data completeness).
- Ensure all outpatient templates have rotation_activity_requirements.

### P4 — Faculty Equity at Assignment Level (Non‑rotation)
- Move admin/academic equity to **assignment‑level** for faculty only
  (AT/GME/DFM/LEC/ADV, etc.).
- Remove rotation‑level academic/admin workload logic.
- Define role‑based targets (core vs PD vs adjunct) and penalties.

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
