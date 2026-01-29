# CP-SAT Pipeline Refinement — Phase 3

Date: 2026-01-28
Scope: Post‑Phase‑2 enhancements (procedure/counseling workflows and allocator steps)

## Purpose
Phase 3 captures procedural clinic refinements that are valuable but not required
for Phase‑2 compliance. These items introduce new activity codes and a targeted
post‑solver allocator for VAS/VASC.

## Phase 3 Tech Debt Notes
- Block quality report ACGME compliance is **stubbed** (hardcoded 100%).
- ACGME hour calculations still use **assignments** as the primary source; time‑off
  exclusions are applied via `half_day_assignments` only.

## Phase 3 Scope

### P3‑1 — Add VASC Activity Code
**Goal:** Introduce **VASC (Vasectomy Counseling)** as a distinct clinical activity.

**Rules**
- VASC uses **normal AT supervision** rules (no extra PROC/VAS demand).
- Counts toward physical capacity like clinic.

**Acceptance Criteria**
- `activities` contains `VASC` (display `VASC`), category `clinical`.
- `activity_requires_fmc_supervision()` treats VASC like clinic.
- VASC appears in export tables/legends.

### P3‑2 — Post‑Solver VAS/VASC Allocator
**Goal:** Add a post‑solver step to target **~3 VAS per block** with some **VASC**.

**Rules**
- Allowed slots: **Thu AM/PM, Fri AM** only.
- Faculty priority: **Kinkennon / LaBounty** first, then **Tagawa**.
- Resident eligibility priority (soft): **PROC > FMC > US/POCUS**.
- **Pairing required**: VAS/VASC requires both faculty + resident in same slot.
- Must not violate capacity or AT coverage.

**Acceptance Criteria**
- Allocator logs: target vs achieved (VAS + VASC), with shortfall reasons.
- Allocator never creates capacity violations or AT shortfalls.
- Block‑10 validation shows VAS/VASC alignment with zero pairing gaps.

**Implementation Checklist**
1. Create `scripts/ops/vas_allocator.py` (post‑solver utility).
2. Input: block number + academic year; load half‑day assignments.
3. Find candidate slots (Thu AM/PM, Fri AM) with:
   - eligible resident (PROC > FMC > US/POCUS) and
   - eligible faculty (Kinkennon/LaBounty preferred, Tagawa fallback)
4. Convert **C → VAS** or **C → VASC** per target mix.
5. Enforce pairing and re‑check:
   - physical capacity
   - AT coverage (no new shortfalls)
6. Write changes + log summary.

**Suggested Mix (Initial)**
- VAS total: 3 per block
- VASC subset: 1–2 of the 3 (if eligible)
