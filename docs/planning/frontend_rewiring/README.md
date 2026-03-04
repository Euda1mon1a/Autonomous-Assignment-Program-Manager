# Frontend Rewiring Roadmap: Bridging the Backend Divide

**Date:** March 3, 2026
**Context:** Following a massive 2-week backend refactoring sprint (~95+ commits, 47 active constraints, new export pipelines, new staging tables, ARO introduction), the frontend Next.js application has drifted significantly from the backend truth.

This roadmap outlines the systematic plan to rewire the frontend to consume the new backend capabilities safely without breaking existing routing or component structure.

---

## 1. Executive Summary

The frontend architecture (`docs/architecture/frontend.md`) relies on TanStack Query, React 18, and `openapi-typescript` generated types. The backend has introduced three major paradigm shifts that the frontend must now support:

1.  **Draft vs. Live State:** The backend no longer writes directly to the live `schedule_grid`. It writes to `ScheduleDraft` models, requiring a staging/preview workflow.
2.  **Annual vs. Block Scope:** The backend introduced the Annual Rotation Optimizer (ARO) alongside the daily Block Engine.
3.  **Excel as a Stateful Client:** The `import-export` hub now needs to handle the `__SYS_META__` and `__OVERRIDES__` sheets defined in Phase 1-4 of the stateful roundtrip roadmap.

## 2. Phase 1: Type Safety & Core API Client Updates
*The foundation. Get the TypeScript compiler to pass with the new API contracts.*

- [x] **Regenerate OpenAPI Types:** Execute `npm run generate:types` (already run, resulted in massive camelCase schema updates).
- [ ] **Fix `api-generated.ts` Fallouts:** Update `useAdminScheduling.ts`, `useSchedule.ts`, and `useExport.ts` to reflect any renamed properties (e.g., standardizing `academicYear` vs `academic_year`).
- [ ] **Wire `expand_block_assignments`:** Update the Schedule Generation form UI to include a toggle for the `expand_block_assignments` flag introduced in Session 095.

## 3. Phase 2: The Draft & Publish Lifecycle
*Moving away from destructive "Generate & Pray" to the new "Stage, Preview, Publish" flow.*

- [ ] **Wire `schedule-drafts.ts` API Client:** Ensure the `getScheduleDraft`, `listScheduleDrafts`, and `publishDraft` endpoints are fully mapped.
- [ ] **Refactor `Admin Scheduling Hub` (`/admin/scheduling`):**
    - Change the "Generate" button to trigger a draft creation instead of a direct write.
    - Build a `DraftPreviewPanel` component to visualize the diff between the live schedule and the generated draft.
- [ ] **Implement Break-Glass Approval UI:** For the new Lock Window feature (Master Priority List #9), wire the `approve-break-glass` endpoint into the UI for Tier 1/2 users when a draft modifies a locked timeframe.

## 4. Phase 3: The Annual Rotation Optimizer (ARO)
*Wiring the brand new Track E macro-scheduler.*

- [ ] **New API Client (`annual-planner.ts`):** Create the Axios/Fetch wrappers for `/api/v1/annual-planner/generate` and `/publish`.
- [ ] **New UI Hub (`/hub/annual-planning`):**
    - Build a view to trigger the ARO solver for the upcoming Academic Year.
    - Build a visualization component to display the `AnnualRotationPlan` staging table output (the 14-month block assignment matrix).
    - Add a toggle for `respect_pending_leave=True/False` as defined in the ARO design doc.

## 5. Phase 4: Import/Export "Last Mile" Enhancements
*Bridging the gap for government coordinators.*

- [ ] **Update `ExportPanel.tsx`:**
    - Wire in the new Annual Workbook (14-sheet) export option alongside the single-block export.
    - Expose the `include_qa_sheet` and `include_overrides` parameters to the UI toggles.
- [ ] **Update Import Staging:** Ensure the frontend handles the `BLOCK_MISMATCH` error code gracefully when the backend `import_staging_service` rejects a stale or wrong-block Excel file.

## 6. Phase 5: Cosmetic & UX Debt
*Cleaning up the visual noise from the backend sprint.*

- [ ] **Enums Sync:** The backend explicitly moved user roles, leave types, and absence reasons to `/api/v1/enums/*` (PR #794). Remove hardcoded dropdowns in the frontend and replace with dynamic fetches via TanStack Query.
- [ ] **Color Scheme Parity:** Ensure the frontend `Tailwind` classes or inline styles used for the schedule grid match the newly refined `TAMC_Color_Scheme_Reference.xml` (e.g., `ADV` being black-on-white, `C30`/`C40` distinctions).

---

## Getting Started

**Recommended First PR:**
Tackle Phase 1 and the `expand_block_assignments` UI toggle. This will clear the TypeScript compiler errors and ensure the basic `POST /schedule/generate` payload is healthy before building the new Draft/ARO hubs.
