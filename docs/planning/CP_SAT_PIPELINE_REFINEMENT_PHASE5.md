# CP-SAT Pipeline Refinement — Phase 5

Date: 2026-01-29
Scope: Post-release change management (short-notice coverage + optional Excel round-trip)

## Purpose
Phase 5 addresses the operational gap between a **generated schedule** and
**real-world disruptions** (deployments, illness, emergent coverage). The goal is to
adjust a live schedule **without nuking existing assignments** already released to
patients or clinics.

## Decision Summary
**Primary path:** Add a **Coverage Override Layer** (admin-only) that overlays the
base schedule rather than regenerating it.

**Optional path:** Excel round-trip import/export only if external workflows require it.

## Guiding Principles
- **Do not regenerate** the base schedule for short-notice coverage changes.
- Preserve the **original assignment history** for audit and rollback.
- Changes must be **minimal, explicit, and reversible**.
- Admin workflow only (not a resident swap marketplace).

---

## Phase 5 Scope

### P5-1 — Coverage Override Layer (Admin-Only)
**Goal:** Allow admins to reassign coverage for a released clinic slot without
changing the underlying base schedule.

**Concept**
- Base schedule stays immutable after release.
- Overrides are stored as a **delta** and applied at view/export time.

**Data Model (minimal)**
- `schedule_overrides` table:
  - `id`
  - `half_day_assignment_id`
  - `replacement_person_id`
  - `reason` (deployment/sick/urgent)
  - `effective_date` + `time_of_day`
  - `created_by`, `created_at`
  - `is_active` (for rollback)

**Behavior**
- UI/export shows **replacement** when override is active.
- Original assignment remains for audit and rollback.
- Overrides never touch FMIT/absences/PCAT/DO unless explicitly allowed.

**Acceptance Criteria**
- Admin can create an override without regenerating a block.
- Exports reflect overrides while keeping base schedule intact.
- Audit trail captures who changed what and why.

---

### P5-2 — Targeted Swap (Optional Name)
**Goal:** Provide a minimal “swap” workflow for the **single-slot replacement** case.

**Notes**
- This is not a marketplace swap; it is a **short-notice coverage reassignment**.
- Implementation can be a UI wrapper on top of `schedule_overrides`.

**Acceptance Criteria**
- One-click replace for a released clinic slot.
- Auto-validation (no conflicts, credentialed activity checks).

---

### P5-3 — Excel Round-Trip Export/Import (Optional)
**Goal:** Enable external teams to modify a schedule in Excel and re-import **only
the differences**.

**Notes**
- Use **stable IDs** in export (assignment_id) to avoid destructive re-creates.
- Import should generate **overrides** by default (not rewrite base schedule).

**Acceptance Criteria**
- Export includes assignment IDs + clinic slot metadata.
- Import generates overrides instead of deleting/recreating assignments.
- Rejects changes that violate constraints (credentials, overlaps).

---

## Recommendation
Start with **P5-1 (Coverage Override Layer)**. It solves the real-world problem
most cleanly and creates a stable foundation for any future “swap” or Excel
workflow. Excel import can be layered later if necessary.

## Out of Scope
- Resident-driven swap marketplace
- Full block regeneration for short-notice coverage
- Automated optimization of overrides
