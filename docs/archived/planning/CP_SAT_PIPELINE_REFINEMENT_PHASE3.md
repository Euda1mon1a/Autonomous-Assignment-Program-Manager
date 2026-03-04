# CP-SAT Pipeline Refinement — Phase 3

Date: 2026-01-28
Status: ✅ **COMPLETE** (2026-01-29)
Scope: Post‑Phase‑2 enhancements (procedure/counseling workflows and allocator steps)

**Next:** See [Phase 4](CP_SAT_PIPELINE_REFINEMENT_PHASE4.md) for consolidation and cleanup.

## Purpose
Phase 3 captures procedural clinic refinements that are valuable but not required
for Phase‑2 compliance. These items introduce new activity codes and a targeted
post‑solver allocator for VAS/VASC.

**Scope guardrails**
- Phase 3 ships as a **separate PR** (not bundled with Phase 2).
- Post‑solver allocator must **not override FMIT, absences (time‑off), or PCAT/DO**.
- VAS/VASC remain **assignment‑level** concepts (not rotations).
- Credentialed procedures are linked via **activities.procedure_id** (VAS/VASC/SM).

## Phase 3 Tech Debt Notes
- Block quality report ACGME compliance is **stubbed** (hardcoded 100%).
- ACGME hour calculations still use **assignments** as the primary source; time‑off
  exclusions are applied via `half_day_assignments` only.
- Targeted test failures (pre‑existing):
  - `/api/schedule/validate` tests fail because legacy `/api/*` redirect drops query params.
  - `SchedulingEngine.__init__` signature change requires test fixture updates.

## Phase 3 Scope

### P3‑1 — Add VASC Activity Code
**Goal:** Introduce **VASC (Vasectomy Counseling)** as a distinct clinical activity.

**Status:** ✅ Implemented (2026-01-29)

**Rules**
- VASC uses **normal AT supervision** rules (no extra PROC/VAS demand).
- Counts toward physical capacity like clinic.

**Acceptance Criteria**
- `activities` contains `VASC` (display `VASC`), category `clinical`.
- `activity_requires_fmc_supervision()` treats VASC like clinic.
- VASC appears in export tables/legends.

### P3‑2 — Post‑Solver VAS/VASC Allocator
**Goal:** Add a post‑solver step to target **~3 VAS per block** with some **VASC**.

**Status:** ✅ Script added (2026-01-29). Pending validation run.

**Rules**
- Allowed slots: **Thu AM/PM, Fri AM** only.
- Faculty eligibility + priority uses **procedure_credentials** (Vasectomy).
  - Competency levels drive priority (expert/master preferred over qualified).
- Resident eligibility priority (soft): **PROC > FMC > US/POCUS**.
- **Pairing required**: VAS/VASC requires both faculty + resident in same slot.
- VAS/VASC use **standard clinic supervision** (no extra +1 AT demand).
- Must not violate capacity or AT coverage.
- Must not override **FMIT, absences (time‑off), or PCAT/DO** assignments.

**Acceptance Criteria**
- Allocator logs: target vs achieved (VAS + VASC), with shortfall reasons.
- Allocator never creates capacity violations or AT shortfalls.
- Block‑10 validation shows VAS/VASC alignment with zero pairing gaps.

**Implementation Checklist**
1. Create `scripts/ops/vas_allocator.py` (post‑solver utility).
2. Input: block number + academic year; load half‑day assignments.
3. Find candidate slots (Thu AM/PM, Fri AM) with:
   - eligible resident (PROC > FMC > US/POCUS) and
   - eligible faculty (active vasectomy credential; competency_level priority)
4. Convert **eligible assignments → VAS/VASC** per target mix (excluding FMIT/time‑off/PCAT/DO).
5. Enforce pairing and re‑check:
    - physical capacity
   - AT coverage (no new shortfalls)
6. Write changes + log summary.

**Suggested Mix (Initial)**
- VAS total: 3 per block
- VASC subset: 1–2 of the 3 (if eligible)

### P3‑3 — Call Night Before Leave (Soft)
**Goal:** Discourage assigning overnight call the night before a blocking absence.

**Status:** ✅ Implemented (2026‑01‑29)

**Rules**
- Soft penalty only (default weight **2.0**).
- Uses the availability matrix to detect **next‑day unavailability**.
- Does **not** block call assignments; only biases the solver.

**Acceptance Criteria**
- Constraint added to default manager (`CallNightBeforeLeaveConstraint`).
- Quality report includes D4 “Call Night Before Leave (Soft)” with count + details.
