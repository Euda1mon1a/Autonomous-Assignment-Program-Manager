# Frontend Rewiring Roadmap: Bridging the Backend Divide

**Date:** March 3, 2026
**Last Updated:** March 4, 2026
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
- [x] **Fix `api-generated.ts` Fallouts:** Types are fresh as of Mar 4, 2026.
- [x] ~~**Wire `expand_block_assignments`:**~~ **REMOVED** — `expand_block_assignments` is deprecated and ignored in the backend (Session 095). No toggle needed.

## 3. Phase 2: The Draft & Publish Lifecycle
*Moving away from destructive "Generate & Pray" to the new "Stage, Preview, Publish" flow.*

**Infrastructure status (all DONE):**
- [x] Draft API client (`frontend/src/api/schedule-drafts.ts`, 112 lines)
- [x] Draft hooks (`frontend/src/hooks/useScheduleDrafts.ts`, 185 lines)
- [x] Draft types (`frontend/src/types/schedule-draft.ts`, 275 lines)
- [x] Draft list page (`frontend/src/app/admin/schedule-drafts/page.tsx`, 382 lines)
- [x] Draft review page (`frontend/src/app/admin/schedule-drafts/[id]/page.tsx`, 642 lines)
- [x] Break-glass approval, flag acknowledgment, publish, rollback, discard

**Wiring (Mar 4):**
- [x] "View Drafts" button added to Scheduling Laboratory header bar (links to `/admin/schedule-drafts`)
- [x] Post-generation success banner with "View in Drafts" link

**Remaining (requires backend changes):**
- [ ] **Generate button creates draft instead of direct write** — Requires solver to write to staging tables instead of live schedule. Backend change needed.
- [ ] **DraftPreviewPanel** — Diff visualization between live schedule and generated draft

## 4. Phase 3: The Annual Rotation Optimizer (ARO)
*Wiring the brand new Track E macro-scheduler.*

**Status: BLOCKED** — No backend `/api/v1/annual-planner` endpoints exist yet.

- [ ] **New API Client (`annual-planner.ts`):** Create the Axios/Fetch wrappers for `/api/v1/annual-planner/generate` and `/publish`.
- [ ] **New UI Hub (`/hub/annual-planning`):**
    - Build a view to trigger the ARO solver for the upcoming Academic Year.
    - Build a visualization component to display the `AnnualRotationPlan` staging table output (the 14-month block assignment matrix).
    - Add a toggle for `respect_pending_leave=True/False` as defined in the ARO design doc.

## 5. Phase 4: Import/Export "Last Mile" Enhancements
*Bridging the gap for government coordinators.*

- [x] **Backend: Wire `include_qa_sheet` and `include_overrides` query params** to `GET /export/schedule/xlsx` and `include_overrides` to `GET /export/schedule/year/xlsx`
- [x] **Frontend: Add export toggle checkboxes** in Import/Export Hub ExportTab for QA sheet and overrides (schedules only)
- [ ] **Update Import Staging:** Ensure the frontend handles the `BLOCK_MISMATCH` error code gracefully when the backend `import_staging_service` rejects a stale or wrong-block Excel file.

## 6. Phase 5: Cosmetic & UX Debt
*Cleaning up the visual noise from the backend sprint.*

- [x] **Enums Sync:** Created `useEnums.ts` hook with TanStack Query wrappers for all 7 `/api/v1/enums/*` endpoints. Algorithm dropdown in Scheduling Laboratory now fetches from API with hardcoded fallback.
- [ ] **Remaining enum dropdowns:** Wire `useActivityCategories()`, `useRotationTypes()`, `usePgyLevels()`, `useConstraintCategories()`, `usePersonTypes()`, `useFreezeScopes()` into their respective UI components.
- [ ] **Color Scheme Parity:** Ensure the frontend `Tailwind` classes or inline styles used for the schedule grid match the newly refined `TAMC_Color_Scheme_Reference.xml` (e.g., `ADV` being black-on-white, `C30`/`C40` distinctions).

---

## Getting Started

**Recommended Next PRs:**
1. **Backend draft-write:** Make solver write to staging tables so "Generate" creates a draft instead of direct write (Phase 2 completion)
2. **ARO backend endpoints:** Implement `/api/v1/annual-planner/*` (Phase 3 unblock)
3. **BLOCK_MISMATCH handling:** Frontend graceful error for stale imports (Phase 4 completion)
