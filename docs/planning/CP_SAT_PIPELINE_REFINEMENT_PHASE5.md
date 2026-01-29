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
- `schedule_overrides` table (half-day):
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
- FMIT/AT/PCAT/DO cannot be cancelled; coverage-only allowed.
- Time-off assignments cannot be overridden.

**Acceptance Criteria**
- Admin can create an override without regenerating a block.
- Exports reflect overrides while keeping base schedule intact.
- Audit trail captures who changed what and why.

**API Draft (Admin)**
- `POST /admin/schedule-overrides`
  - Create coverage (replacement) or cancellation (empty slot).
- `GET /admin/schedule-overrides?block_number&academic_year&active_only`
  - List overrides for a block or date range.
- `DELETE /admin/schedule-overrides/{id}`
  - Soft-delete (deactivate) override.

**Call Coverage (Admin)**
- `call_overrides` table (call assignments):
  - Mirrors `schedule_overrides` for call coverage.
  - Call must **always be staffed** (coverage-only).
- `POST /admin/call-overrides`
- `GET /admin/call-overrides`
- `DELETE /admin/call-overrides/{id}`

**Policy Notes**
- Reject overrides if replacement already has a slot at the same date/time
  (unless the replacement’s slot is already cancelled).
- One active override per assignment (partial unique index).
- Protected slots: FMIT/AT/PCAT/DO cannot be cancelled.
- GAP override: marks required slot unfilled (visible shortage, does not count as coverage).

**Future Read Layer**
- Schedule reads/export should apply overrides by default
  (`include_overrides=true`), with optional base-only view for audit.
  - Implemented in half-day schedule API + canonical export (Phase 5 draft).

**Manual Cascade Workflow (Now)**
When the best replacement is already assigned:
1. Identify a low-impact backfill (often GME/DFM) for the replacement’s slot.
2. Create override for the backfill first (freeing the replacement).
3. Create override for the original slot (replacement covers target).

**Future: Cascade Helper (P5.1)**
Automate multi-step replacements using resilience tooling:
- Use `backend/app/resilience/` modules to propose low-impact backfills.
- Use MCP tools (when wired) to estimate blast radius and contingency options.
- Create overrides atomically after admin confirmation.

**Cascade Helper (P5.1 — Updated)**
Handle deployment-style cascades across both **half-day** and **call**:

Inputs:
- Deployed person + date range

Outputs:
- Ordered override steps (cancel/backfill first, then coverage)
- Warnings + N-1 penalty score

Sacrifice Hierarchy:
1. GME/DFM (admin)
2. Faculty solo clinic
3. Procedure supervision (VAS/SM/BTX/COLPO)

Protected (never auto-sacrifice):
- FMIT
- AT/PCAT/DO (resident supervision)

Rules:
- Call must always be staffed (coverage-only).
- Call replacements must match person type (faculty now; resident later).
- Adjunct faculty excluded from auto-cascade.
- Same-day clinic + call is allowed **with warning**.
- N-1 hard-block for protected coverage loss.
- If replacement has next-day protected work (AT/PCAT/DO/FMIT/time-off), warn and do
  not auto-reassign PCAT/DO. Manual follow-up required.
- GAP overrides are auto-created only for post-call PCAT/DO after call changes.

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
