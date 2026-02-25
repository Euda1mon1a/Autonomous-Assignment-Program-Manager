# E2E Test Unblock + Export Tab Wiring — Implementation Roadmap

> **Purpose:** Mac Mini execution roadmap for unblocking 10 `test.fixme()` Playwright tests and wiring the Export tab to real backend data.
> **Predecessor:** `EXCEL_PIPELINE_GUI_TESTING.md` (architecture brief) + `CHROME_MCP_VISUAL_QA.md` (visual QA scripts)
> **Created:** 2026-02-25
> **Status:** Ready for autonomous execution

---

## Problem Statement

The E2E testing infrastructure (Phases 0–4) is fully built:
- 42 `data-testid` attributes across 7 UI files
- `ImportExportPage` page object with full method coverage
- 5 Playwright spec files (export, import, round-trip, rollback, ACGME violation)
- `xlsx-helpers.ts` utility using `xlsx-populate`
- Database/schedule fixtures with half-day seeding methods

**But 10 tests are `test.fixme()` because:**
1. Two `.xlsx` fixture files don't exist (`test-block10.xlsx`, `test-acgme-violation.xlsx`)
2. The backend seed endpoint is a stub
3. The Export tab is wired to an empty array — no data to export

---

## Phase A: Synthetic Excel Fixture Generator

### A1. Create generator script

**File:** `frontend/e2e/fixtures/generate-test-xlsx.ts` (NEW)

Uses `xlsx-populate` (already installed) to programmatically create two fixture files.

**`test-block10.xlsx`** — Valid Block Template2 format:
- Row 3: date headers (28 consecutive dates, deterministic start: 2025-03-10)
- Row 8: column headers ("Name", "PGY", then dates)
- Rows 9–13: 5 synthetic residents with rotating activity codes
- Col E: `Test Resident 1` through `Test Resident 5`
- Col F+: `C`, `NF`, `FMIT-PG`, `LV-AM`, `ADMIN` (rotating per resident)
- `__SYS_META__` veryHidden sheet: `{"block_number": 10, "academic_year": 2025, "exported_at": "2025-03-01T00:00:00Z", "format_version": "1.0"}`
- `__REF__` sheet: activity code lookup table

**`test-acgme-violation.xlsx`** — Same format, one resident violates 1-in-7:
- Resident 1: `NF` for days 1–7 (violation), `C` for days 8–28
- Residents 2–5: normal rotation pattern

### A2. Add npm script

**File:** `frontend/package.json`

```json
"generate:test-fixtures": "tsx e2e/fixtures/generate-test-xlsx.ts"
```

### A3. Generate and commit fixtures

```bash
cd frontend && npm run generate:test-fixtures
```

Commit the generated `.xlsx` files so they're available without running the generator.

---

## Phase B: Remove `test.fixme()` Markers

### Files to modify (10 fixme calls across 4 files):

| File | fixme count | Action |
|------|-------------|--------|
| `e2e/tests/import-export/import-stage-apply.spec.ts` | 6 | Remove fixme, verify `test-block10.xlsx` path |
| `e2e/tests/import-export/export-block.spec.ts` | 3 | Remove fixme, add conditional skip if no DB data |
| `e2e/tests/import-export/round-trip.spec.ts` | 1 | Remove fixme, use synthetic fixture for upload |
| `e2e/tests/import-export/acgme-violation-import.spec.ts` | 1 | Remove fixme, use `test-acgme-violation.xlsx` |

**Pattern for export tests (no seeded DB):** Replace `test.fixme()` with:
```typescript
test.skip(!process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');
```

This lets CI skip gracefully while local runs with seeded data pass.

---

## Phase C: Wire Export Tab to Backend API

### C1. Create `useExportData` hook

**File:** `frontend/src/hooks/useExportData.ts` (NEW)

```typescript
import { useQuery } from '@tanstack/react-query';
import { get } from '@/lib/api';

type ExportType = 'schedules' | 'people' | 'assignments';

interface ExportFilters {
  startDate?: string;
  endDate?: string;
}

const exportEndpoints: Record<ExportType, string> = {
  people: '/export/people',
  schedules: '/export/schedule',
  assignments: '/export/absences',
};

export function useExportData(type: ExportType, filters?: ExportFilters) {
  return useQuery({
    queryKey: ['export', type, filters],
    queryFn: async () => {
      const params: Record<string, string> = { format: 'json' };
      if (filters?.startDate) params.start_date = filters.startDate;
      if (filters?.endDate) params.end_date = filters.endDate;
      return get(exportEndpoints[type], { params });
    },
    enabled: false, // Only fetch on explicit trigger
  });
}
```

### C2. Wire into ExportTab

**File:** `frontend/src/app/hub/import-export/page.tsx`

Replace line ~1141:
```typescript
// BEFORE
const exportData: Record<string, unknown>[] = [];

// AFTER
const { data: exportData = [], refetch, isLoading } = useExportData(selectedExportType);
```

### C3. Update ExportPanel sections

Each expandable section (schedules, people, assignments) should trigger its own `useExportData` query via `refetch()` when expanded.

---

## Phase D: Track Human-Only Step

**File:** `HUMAN_TODO.md` (append)

Script 4 (Native Excel Formatting Check):
- Requires non-empty export (unblocked by Phase C)
- Requires opening .xlsx in macOS Excel/Numbers + visual verification
- Not automatable via browser agents

---

## Execution Order

```
Phase A (fixtures)  ─── no deps, do first
Phase B (unfixme)   ─── depends on A
Phase C (export)    ─── independent, parallel with A+B
Phase D (tracking)  ─── trivial, at commit time
```

---

## Verification

1. `cd frontend && npm run generate:test-fixtures` → two .xlsx files created
2. `npx playwright test e2e/tests/import-export/ --list` → 0 fixme tests
3. Navigate to `/hub/import-export` → Export tab → data loads → buttons enabled
4. `npx playwright test e2e/tests/import-export/` → import tests pass against dev server

---

## Backend Endpoints (already exist, no changes needed)

| Endpoint | Method | Auth | Returns |
|----------|--------|------|---------|
| `/api/v1/export/people` | GET | Admin | People JSON/CSV |
| `/api/v1/export/schedule` | GET | Admin | Schedule JSON/CSV |
| `/api/v1/export/absences` | GET | Admin | Absences JSON/CSV |
| `/api/v1/export/schedule/xlsx` | GET | Admin | Excel file |

---

## Key Files Reference

| File | Role |
|------|------|
| `frontend/e2e/utils/xlsx-helpers.ts` | Parse/mutate xlsx (existing) |
| `frontend/e2e/pages/ImportExportPage.ts` | Page object (existing) |
| `frontend/e2e/fixtures/database.fixture.ts` | DB seeding (existing) |
| `frontend/e2e/fixtures/schedule.fixture.ts` | Schedule scenarios (existing) |
| `frontend/src/features/import-export/useExport.ts` | Client-side format/download (existing) |
| `frontend/src/features/import-export/ExportPanel.tsx` | Export UI (existing) |
| `frontend/src/hooks/usePeople.ts` | React Query pattern to follow |
| `backend/app/api/routes/export.py` | Backend export endpoints |
