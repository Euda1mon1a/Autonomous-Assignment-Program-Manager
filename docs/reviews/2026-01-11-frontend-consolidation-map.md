# Frontend Consolidation Map (Tiered Access + Risk Bar)

Date: 2026-01-11
Scope: GUI consolidation options only (review document).

## Context

- The UI should support tiered access where PDs and coordinators can perform manual actions.
- The separate admin vs non-admin theme split is no longer desired.
- Instead, use a risk indicator bar to communicate destructive capability on a page.

## Tier Model (Draft)

- Tier 0: Read-only and self-service actions (no changes to shared data).
- Tier 1: Manual operational changes (reversible, scoped changes).
- Tier 2: Destructive or system-wide changes (bulk delete, overrides, rollback).

Suggested roles:
- Resident/Faculty: Tier 0.
- Program Coordinator, PD: Tier 1.
- Admin/Skeleton Key: Tier 2.

## Risk Indicator Bar (UI Contract)

- Position: Fixed bar just under the global header.
- Color:
  - Green: Read-only or safe actions.
  - Amber: Reversible writes or scoped changes.
  - Red: Destructive or system-wide changes.
- Behavior:
  - Color is based on current user permission on the page, not on the page type alone.
  - If the user lacks the permission to perform risky actions, keep the bar green.
- Content:
  - Short label (e.g., "Read-only", "Scoped Changes", "High Impact").
  - Optional tooltip explaining why the page is amber/red.

## Consolidation Candidates

### Personal Schedule Hub

Routes:
- `frontend/src/app/my-schedule/page.tsx`
- `frontend/src/app/schedule/[personId]/page.tsx`
- Optional integration point: `frontend/src/app/schedule/page.tsx`

Proposed consolidation:
- A single "Personal Schedule" hub with a person selector for Tier 1/2 users.
- Tier 0 defaults to the current user with no selector or export of others.

Benefits:
- One data transformation pipeline for personal schedules.
- Consistent export and print behavior.

Risks:
- Permission leakage if selector is visible for Tier 0.
- Heavier component complexity for basic users.

Mitigations:
- Hard gate person selector and export by tier.
- Default to self when permissions are limited.

Risk bar:
- Green for Tier 0.
- Amber for Tier 1/2 (manual edits or export of others).

### People Hub

Routes:
- `frontend/src/app/people/page.tsx`
- `frontend/src/app/admin/people/page.tsx`

Proposed consolidation:
- A single People hub with read-only directory plus an admin tab.

Benefits:
- Removes duplicate CRUD and filtering logic.
- Single UI for search and filtering.

Risks:
- Non-admins could see or access destructive actions.
- Admin table complexity could overwhelm simple view.

Mitigations:
- Role-gate bulk actions and delete controls.
- Use a simple default tab for Tier 0.

Risk bar:
- Green for Tier 0.
- Amber for Tier 1 (role/PGY updates).
- Red for Tier 2 (bulk delete).

### Swaps Hub

Routes:
- `frontend/src/app/swaps/page.tsx`
- `frontend/src/app/admin/swaps/page.tsx`

Proposed consolidation:
- A swap hub with tabs for Marketplace and Admin Actions.

Benefits:
- Unified view of swap lifecycle and status.
- Consistent filters and search.

Risks:
- Admin actions could be exposed in the same page.

Mitigations:
- Tab-level permission gating.
- Strong confirmation for direct assignment edits.

Risk bar:
- Green for Tier 0.
- Amber or Red for Tier 1/2 based on enabled actions.

### Call Hub

Routes:
- `frontend/src/app/call-roster/page.tsx`
- `frontend/src/app/admin/faculty-call/page.tsx`

Proposed consolidation:
- A call management hub with a read-only roster and an admin panel.

Benefits:
- Single source of truth for call data and filters.
- Less duplication of date range logic.

Risks:
- Admin controls could overload a simple roster view.

Mitigations:
- Tabbed layout with separate UI density.
- Keep roster tab minimal for Tier 0.

Risk bar:
- Green for Tier 0.
- Amber/Red for Tier 1/2 when edits are enabled.

### Import Hub

Routes:
- `frontend/src/app/import/page.tsx`
- `frontend/src/app/import-export/page.tsx`
- `frontend/src/app/admin/import/page.tsx`
- `frontend/src/app/admin/block-import/page.tsx`
- `frontend/src/app/admin/fmit/import/page.tsx`

Proposed consolidation:
- A single Import/Export hub with tabs:
  - Staged Import
  - Block Import (TRIPLER)
  - FMIT Import
  - Export

Benefits:
- Shared history and rollback UI.
- Consistent validation and error handling.

Risks:
- Specialized flows could be hidden or cluttered.

Mitigations:
- Use a guided entry page with clear callouts.
- Tier-gate advanced workflows.

Risk bar:
- Green for Tier 0 (export only).
- Amber/Red for Tier 1/2 depending on import actions.

### Compliance Hub

Routes:
- `frontend/src/app/compliance/page.tsx`
- `frontend/src/app/admin/compliance/page.tsx`

Proposed consolidation:
- A Compliance hub with tabs for ACGME and Away-From-Program.

Benefits:
- Clearer information architecture.
- Single compliance landing page.

Risks:
- Two distinct compliance domains could be conflated.

Mitigations:
- Separate copy, iconography, and labels per tab.

Risk bar:
- Likely green for all tiers (read-only).

### Activities Hub (Optional)

Routes:
- `frontend/src/app/activities/page.tsx` (rotation templates)
- `frontend/src/app/admin/faculty-activities/page.tsx` (faculty weekly patterns)

Proposed consolidation:
- A single Activities hub with tabs for Rotation Templates and Faculty Activity Templates.

Benefits:
- Reduces navigation confusion (two "activity" surfaces).

Risks:
- Different mental models could be blurred.

Mitigations:
- Strong tab labels and help copy.

Risk bar:
- Green for view-only; amber/red for template edits.

## Non-Candidates (Keep Separate)

- `frontend/src/app/admin/scheduling/page.tsx`: experimental lab UI is too specialized.
- `frontend/src/app/admin/audit/page.tsx`: audit log is a distinct admin-only surface.
- `frontend/src/app/admin/health/page.tsx`: operational status should remain isolated.

## Suggested Sequencing (Analysis Only)

1. Personal Schedule Hub
2. People Hub
3. Swaps Hub
4. Call Hub
5. Import Hub
6. Compliance Hub
7. Activities Hub (optional)

## Open Questions

- Should PDs have Tier 2 on any pages, or stay Tier 1 with explicit escalation?
- Is the risk bar label standardized in the design system, or should it be introduced?
