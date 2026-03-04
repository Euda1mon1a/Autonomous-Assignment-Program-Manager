# Lock Window + Break-Glass Scheduling Spec

**Status:** Draft (implementation-ready)
**Last Updated:** 2026-02-04
**Owner:** Scheduling / Resilience
**Scope:** System-initiated schedule changes and publish gating

## TL;DR
- A lock date lives in the DB and is editable from the GUI.
- Any system-initiated change that touches dates on or before the lock date can be **staged**, but **cannot be published** without break-glass approval.
- Manual changes are always allowed by approved Coordinator/Admin with audit.
- Break-glass requires approval + reason + full re-validation (ACGME, coverage, conflicts).
- Swaps inside the lock window also require break-glass (even if user-initiated).

---

## Goals
1. Prevent unintended churn in near-term schedules while still allowing emergency changes.
2. Keep CP-SAT authoritative by default; allow exceptions only through explicit break-glass.
3. Preserve auditability with reasons, role approvals, and validation snapshots.
4. Keep operations simple: drafts allowed, publish blocked, with clear warnings.

## Non-Goals
- Bypassing ACGME/coverage/conflict validation (break-glass does **not** skip validation).
- Auto-publishing partial drafts (future enhancement).
- Replacing manual edits (manual edits remain allowed with audit).

---

## Definitions
- **Lock Date:** A date stored in DB settings (editable from GUI). Dates on or before this are considered locked.
- **Locked Window:** Dates **on or before lock_date** (inclusive): `date <= lock_date`.
- **Null Lock Date:** If `schedule_lock_date` is NULL, **no lock window** is applied (everything is publishable).
- **System-Initiated Change:** Any schedule change created by solver, resilience, import, or auto-swap.
- **Manual Change:** A human (Coordinator/Admin) edits assignments directly in the GUI.
- **Break-Glass:** An explicit approval step (Coordinator/Admin) that allows publish within the lock window, with reason and audit.

---

## Policy Rules
### 1) System-Initiated Changes
- Allowed to **stage** inside lock window.
- **Blocked from publish** inside lock window unless break-glass approval is granted.
- Must show a critical warning before publish attempt.

### 2) Manual Changes
- Always allowed for approved Coordinator/Admin.
- Must be audited with reason and user context.
- **Note:** This is a deliberate decision (see Open Questions for risk assessment).

### 3) Swaps
- Swaps touching locked dates require break-glass approval, even if user-initiated.
- Reason: swaps modify published schedule and can destabilize near-term coverage.

### 4) Validation
- All publish attempts (including break-glass) must pass full validation:
  - ACGME rules
  - Coverage constraints
  - Conflict checks

---

## Assignment-Level Guardrails
Most governance should happen at the **assignment level**. This spec adds:
- **Lock-window checks** at draft publish time.
- **Break-glass approvals** recorded per draft/assignment set.
- **Audit records** tied to assignment changes.

---

## Workflow (Stage -> Draft -> Publish)
1. **Stage**: System creates staged changes (allowed even in lock window).
2. **Draft**: Draft created; lock-window violations generate blocking flags.
3. **Publish**:
   - If draft touches locked dates, publish is blocked unless break-glass is approved.
   - Break-glass approval requires reason + role + re-validation.

---

## Break-Glass Requirements
- **Who can approve:** Coordinator or Admin (no SPOF).
- **Required fields:**
  - `approved_by_id`
  - `approved_at`
  - `approval_reason`
  - Snapshot of `lock_date` at approval
- **Re-validation:** Must re-run validation at approval time and before publish.

---

## Data Model Additions
### Settings
- `schedule_lock_date` (DATE, nullable)

### Schedule Drafts
Add approval fields:
- `approved_by_id` (FK users)
- `approved_at` (timestamp)
- `approval_reason` (text)
- `lock_date_at_approval` (date snapshot)

### Draft Flags
- New flag type: `LOCK_WINDOW_VIOLATION`
- Severity: `ERROR` (documented as blocking)

---

## RBAC
- **View:** All authenticated users can view lock date and draft flags.
- **Edit lock date:** Admin-only (for now; Coordinator later).
- **Create drafts:** Coordinator/Admin.
- **Approve break-glass:** Coordinator/Admin.

---

## Observability
- Activity log entry for each break-glass approval and publish.
- Dashboard indicator: "Break-glass used X times in last 7 days" (recommended).

---

## Edge Cases & Clarifications
1. **Draft Staleness**
   - If draft age > 24h, require re-validation before publish.

2. **Lock Date Changes After Drafts Exist**
   - When lock date changes, re-flag all unpublished drafts asynchronously.

3. **Partial Publish**
   - Initial behavior: block entire draft.
   - Future enhancement: publish non-locked portion, keep locked portion staged.

4. **Manual Edits in Lock Window**
   - Currently allowed (decision). Risk: could bypass lock controls.
   - Future enhancement: require break-glass for manual edits inside lock window.

---

## Open Questions (Future Decisions)
- Should manual edits inside the lock window require break-glass?
- Should ERROR be renamed to BLOCKING for clarity?
- Should break-glass notifications send Slack/email or just dashboard + audit?
- Should partial publish be enabled later?

---

## References
- Roadmap: `docs/planning/LOCK_WINDOW_BREAK_GLASS_ROADMAP.md`
- Supplemental policy: `docs/architecture/LOCK_WINDOW_BREAK_GLASS_POLICY.md`
