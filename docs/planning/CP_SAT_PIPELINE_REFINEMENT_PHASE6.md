# CP-SAT Pipeline Refinement — Phase 6

Date: 2026-01-30  
Scope: Compliance accuracy, equity, and data‑source hardening (post‑merge)

## Purpose
Phase 6 tightens CP‑SAT into a **deployment‑ready pipeline** by aligning
compliance reporting with reality, formalizing time‑off sources, and
making equity/preferences **data‑driven and measurable**.

**Note:** Residents do **not** deploy. Cascade logic remains faculty‑only.

**Previous:** See [Phase 5](CP_SAT_PIPELINE_REFINEMENT_PHASE5.md) for override + cascade layer.

---

## Phase 6 Scope

### P6-0 — Post‑Merge Stabilization (Gate)
**Goal:** Confirm Phase 5 merge is stable before new work.

**Actions**
- Run validator tools (MCP) for block 10.
- Confirm override + cascade endpoints still operate.
- Run targeted tests in Docker.

**Acceptance Criteria**
- No new 500/404 errors.
- `validate_schedule_tool`, `detect_conflicts_tool`, and block quality report run clean.
- Override and cascade flows still functional.

---

### P6-1 — ACGME Compliance Truth Alignment
**Goal:** Remove stubbed “100% ACGME” and report real validator output.

**Actions**
- Wire block quality report to validator results.
- Ensure time‑off activities (W/OFF/LV/PC) are excluded from duty hours and streaks.

**Acceptance Criteria**
- Block quality report matches validator output exactly.
- No false positives on 80‑hour or 1‑in‑7 due to time‑off miscounting.

---

### P6-2 — External Rotation Time‑Off Intake
**Goal:** Encode external day‑off patterns as explicit data.

**Status:** In progress (PR #784 merged — GUI time‑off patterns now applied to inpatient preloads)

**Examples**
- FMIT: PGY‑1/2 Saturdays off; PGY‑3 Sundays off
- IMW: Saturdays off
- Peds Ward/NF: Saturdays off
- **Temporary default:** Saturday off for all external/inpatient rotations until refined

**Completed**
- Apply GUI time‑off patterns to inpatient preloads (PR #784)

**Remaining**
- Confirm ICU/NICU/L&D authoritative day‑off rules and encode in DB patterns

**Acceptance Criteria**
- External rotation time‑off is represented in DB.
- ACGME violations reflect reality (not missing data).

---

### P6-3 — Excel Import + Diff (Staged)
**Goal:** Import Excel into a staging layer and **measure manual vs automated** changes.

**Endpoints (new)**
- `POST /api/v1/import/half-day/stage` — Upload Block Template2 xlsx, stage diffs
- `GET /api/v1/import/half-day/batches/{id}/preview` — View diff metrics + samples

**Pipeline**
1. Import Excel → staging tables (no direct overwrite).
2. Compute diff vs base schedule (slot‑level).
3. Produce metrics on hand‑jammed changes before apply.

**Required Metrics**
- % of assignments modified by hand
- Count of changes by activity type
- Manual hours per block (total)

**Acceptance Criteria**
- Diff report generated without applying changes.
- Admin can review and apply selectively.

---

### P6-4 — Institutional Events Table
**Goal:** Encode USAFP, holidays, retreats, conferences as structured data.

**Actions**
- New `institutional_events` table.
- Events injected as blocking time or special activities.
- Admin endpoints:
  - `POST /admin/institutional-events`
  - `GET /admin/institutional-events`
  - `GET /admin/institutional-events/{id}`
  - `PUT /admin/institutional-events/{id}`
  - `DELETE /admin/institutional-events/{id}` (soft deactivate)

**Acceptance Criteria**
- Events appear in schedule views and exports.
- Solver respects events as hard constraints.

---

### P6-5 — Equity + Preferences (Core Deliverable)

#### Faculty Equity (by role)
**Requirements**
- GME / DFM / AT equity **by role**
- Clinic (C) equity **by role** (verify existing logic)
- LEC / ADV / Sunday call / Weekday call equity **across the board**
- Holiday equity for **FMIT + call**

#### Resident Equity (full stack)
**Scope**
- All resident assignments: call, clinic (C/CV), inpatient rotations, AT/PCAT/DO, and other activities.
**Granularity**
- Block‑level equity
- Weekly equity
- Assignment‑level guardrails

#### Preferences (Soft)
**Requirement**
- Each faculty has **2 soft preferences**, applied to **clinic or call**.

**Implementation (current)**
- Activity solver: resident clinic equity (weekly + block) + faculty admin/academic/supervision equity
- Call solver: Sunday/weekday/holiday equity across call-eligible faculty
- Preferences table (`faculty_schedule_preferences`) + admin endpoints
- Admin API: `GET/POST/PUT/DELETE /admin/faculty-schedule-preferences`
- Call preferences: day-of-week penalties/bonuses (prefer/avoid)
- Clinic preferences: applied to clinical non-supervision activities (C/CV/PROC/VAS/etc.)
- FMIT holiday equity: tracked via call holiday flags; FMIT-specific holiday equity still manual (preloaded)
- Temporary smoke-test preferences (notes "P6-5 preference smoke check*") were deactivated after validation

**Acceptance Criteria**
- Equity metrics visible in solver output and reports.
- Preferences respected without infeasibility.
- Clinic equity by role confirmed or corrected.

---

### P6-6 — Faculty‑Only Cascade Intelligence (Refinement)
**Goal:** Improve cascade planning with safety + N‑1 scoring.

**Sacrifice Order**
1. GME/DFM (admin)
2. Faculty solo clinic
3. Procedure supervision (VAS/SM/BTX/COLPO)

**Protected (never auto‑sacrifice)**
- FMIT
- AT / PCAT / DO

**Acceptance Criteria**
- Cascade always returns a plan or explicit failure reason.
- Supervision is never auto‑sacrificed.

---

## Out of Scope
- Resident deployments (not applicable)
- Procedure logs (handled in another system)
- Resident swap marketplace

---

## Recommendation
Start with **P6‑1 (ACGME alignment)** and **P6‑2 (time‑off intake)** to ensure
validation accuracy, then proceed to equity + preferences (P6‑5) and Excel
staging (P6‑3).
