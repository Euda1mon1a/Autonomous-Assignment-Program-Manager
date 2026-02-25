# Excel Pipeline GUI E2E Testing — Architecture Brief

> **Purpose:** Self-contained prompt for any AI to advise on GUI-level end-to-end testing of the Excel-to-DB-to-Excel round-trip pipeline.
> **Project:** Military medical residency scheduler (ACGME-compliant, OPSEC-sensitive)
> **Created:** 2026-02-25

---

## Section 1: Mission

### What We Need Tested

Verify that the **Excel ↔ Database round-trip pipeline** works end-to-end through the GUI:

1. **Export:** Generate a schedule in the database → export it as `.xlsx` via the web UI → verify the downloaded file contains correct data with metadata sheets
2. **Import:** Upload a `.xlsx` file via the web UI → stage it → preview diffs → apply to database → verify assignments landed correctly
3. **Round-trip:** Export a schedule → modify cells in the `.xlsx` → re-import → verify only the modified cells appear as diffs → apply → verify the database reflects the changes
4. **Rollback:** After applying an import, roll it back → verify the database returns to its pre-import state

### Why This Matters

The Excel pipeline is the primary interface between program coordinators (who work in Excel) and the scheduling database. A failure here means:
- Schedules silently corrupted (wrong resident on wrong rotation)
- ACGME violations introduced without detection
- Data loss on round-trip (metadata stripped, fuzzy matching wrong person)
- Rollback fails, leaving database in inconsistent state

### Success Criteria

- Export produces valid `.xlsx` with `__SYS_META__` and `__REF__` hidden sheets
- Import stages correctly with accurate fuzzy matching (person names, rotations)
- Preview shows accurate diff counts (added/removed/modified)
- Apply writes correct records to `half_day_assignments` table
- Rollback restores exact pre-import state
- ACGME validation fires during import preview/apply

---

## Section 2: Pipeline Architecture

### Export Pipeline

```
half_day_assignments (DB — DESCRIPTIVE TRUTH)
  │
  ↓
HalfDayJSONExporter.export()
  (DB → JSON dict with residents[].days[].am/pm codes)
  │
  ↓
JSONToXlsxConverter.convert_from_json()
  (JSON → XLSX bytes using BlockTemplate2 format)
  │
  ↓
CanonicalScheduleExportService._inject_metadata()
  (adds veryHidden __SYS_META__ + __REF__ sheets)
  │
  ↓
Downloaded .xlsx file
  (Block Template2 format with colored cells, validation metadata)
```

**Key files:**
| Component | File |
|-----------|------|
| Export route | `backend/app/api/routes/export.py` |
| Canonical service | `backend/app/services/canonical_schedule_export_service.py` |
| JSON exporter | `backend/app/services/half_day_json_exporter.py` |
| XML exporter (parent) | `backend/app/services/half_day_xml_exporter.py` |
| JSON→XLSX converter | `backend/app/services/json_to_xlsx_converter.py` |
| XML→XLSX converter (parent) | `backend/app/services/xml_to_xlsx_converter.py` |
| Metadata injection | `backend/app/services/excel_metadata.py` |
| Template file | `backend/data/BlockTemplate2_Official.xlsx` (**not yet on disk** — code expects it here) |
| Structure mapping | `docs/scheduling/BlockTemplate2_Structure.xml` (code copies to `backend/data/` at runtime) |

**Export API endpoints:**
| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/export/schedule/xlsx` | Export single block as Block Template2 XLSX |
| `GET` | `/api/v1/export/schedule/year/xlsx` | Export all 14 blocks for academic year |
| `GET` | `/api/v1/export/schedule` | Export schedule (CSV/JSON format) |
| `GET` | `/api/v1/export/people` | Export people data |
| `GET` | `/api/v1/export/absences` | Export absences data |

**Query parameters for `/export/schedule/xlsx`:**
- `start_date`, `end_date` — date range
- `block_number` — block number (auto-calculated if omitted)
- `academic_year` — target academic year

**Metadata sheets injected:**
- `__SYS_META__` (veryHidden): Cell A1 contains JSON — `{"academic_year": 2025, "block_number": 10, "export_timestamp": "...", "export_version": 1, "block_map": {...}}`
- `__REF__` (veryHidden): Column A = valid rotation codes, Column B = valid activity codes, with named ranges `ValidRotations` and `ValidActivities`

### Import Pipeline (Generic Staged Import)

```
Upload .xlsx file
  │
  ↓
POST /api/v1/import/stage
  (file + target_block + conflict_resolution)
  │
  ↓
ImportStagingService.stage_import()
  ├─ Parse Excel (openpyxl)
  ├─ Fuzzy match person names (SequenceMatcher, 70% threshold)
  ├─ Fuzzy match rotation names (SequenceMatcher, 70% threshold)
  ├─ Detect conflicts vs existing assignments
  └─ Create ImportBatch + ImportStagedAssignment records
  │
  ↓
GET /api/v1/import/batches/{batch_id}/preview
  (paginated staged vs existing comparison)
  │
  ↓
POST /api/v1/import/batches/{batch_id}/apply
  (commit staged → live assignments, 24h rollback window)
  │
  ↓
POST /api/v1/import/batches/{batch_id}/rollback
  (undo within 24h: delete created assignments, restore staged status)
```

**Key files:**
| Component | File |
|-----------|------|
| Import staging route | `backend/app/api/routes/import_staging.py` |
| Generic parse route | `backend/app/api/routes/imports.py` |
| Staging service | `backend/app/services/import_staging_service.py` |
| ImportBatch model | `backend/app/models/import_staging.py` |
| Import schemas | `backend/app/schemas/import_staging.py` |

### Half-Day Import Pipeline (Block Template2 Format)

```
Upload Block Template2 .xlsx
  │
  ↓
POST /api/v1/import/half-day/stage
  (file + block_number + academic_year)
  │
  ↓
HalfDayImportService.stage_block_template2()
  ├─ Parse fixed layout (rows 9-69, name in col E, dates in row 3, schedule from col F)
  ├─ Normalize activity codes (LV → LV-AM/LV-PM, etc.)
  ├─ Compute diffs vs live schedule (added/removed/modified)
  └─ Create ImportBatch + ImportStagedAssignment records with diff metadata
  │
  ↓
GET /api/v1/import/half-day/batches/{batch_id}/preview
  (filterable by diff_type, activity_code, person_id, has_errors)
  │
  ↓
POST /api/v1/import/half-day/batches/{batch_id}/draft
  (create ScheduleDraft from selected diffs → converts to DraftAssignmentChangeType records)
```

**Key files:**
| Component | File |
|-----------|------|
| Half-day import route | `backend/app/api/routes/half_day_imports.py` |
| Half-day import service | `backend/app/services/half_day_import_service.py` |
| Half-day import schemas | `backend/app/schemas/half_day_import.py` |

**Block Template2 parsing constants:**
```python
DATA_START_ROW = 9      # First resident row
DATA_END_ROW = 69       # Last row scanned
NAME_COL = 5            # Column E = person name
DATE_ROW = 3            # Row with date values
SCHEDULE_START_COL = 6  # Column F = first schedule cell
```

---

## Section 3: Frontend Routes & Components

### Import Pages

| Route | File | Purpose |
|-------|------|---------|
| `/import` | `frontend/src/app/import/page.tsx` | Main import hub — batch list, file upload, import history |
| `/import/[id]` | `frontend/src/app/import/[id]/page.tsx` | Batch detail — review staged assignments, apply or rollback |
| `/import/half-day` | `frontend/src/app/import/half-day/page.tsx` | Half-day Block Template2 import with diff filters (added/removed/modified) |
| `/admin/import` | `frontend/src/app/admin/import/page.tsx` | Admin bulk import using `BulkImportModal` |
| `/admin/block-import` | `frontend/src/app/admin/block-import/page.tsx` | Block schedule import — 4-step wizard (upload → stage → apply/reject → rollback) |
| `/admin/fmit/import` | `frontend/src/app/admin/fmit/import/page.tsx` | FMIT attending schedule import with fuzzy matching confidence display |
| `/import-export` | `frontend/src/app/import-export/page.tsx` | Simple import/export tab switcher |
| `/hub/import-export` | `frontend/src/app/hub/import-export/page.tsx` | Unified coordinator hub (~55KB) — consolidates all import/export workflows with tiered access control |

### Key Hooks

| Hook | File | API |
|------|------|-----|
| `useImport()` | `frontend/src/hooks/useImport.ts` | `listBatches()`, `getBatch()`, `preview()`, `stage()`, `apply()`, `rollback()`, `delete()` — TanStack Query |
| `useImportStaging()` | `frontend/src/hooks/useImportStaging.ts` | `useImportBatches()`, `useImportBatch()`, `useImportPreview()`, `useStageImport()`, `useApplyImport()`, `useRollbackImport()`, `useDeleteImportBatch()` |
| `useHalfDayImport()` | `frontend/src/hooks/useHalfDayImport.ts` | `useStageHalfDayImport()`, `useHalfDayImportPreview()` (with filters), `useCreateHalfDayDraft()` |
| `useBlockAssignmentImport()` | `frontend/src/hooks/useBlockAssignmentImport.ts` | 4-step wizard state machine: upload → preview → importing → complete. Handles file upload, duplicate actions, template creation, import execution, template download. |
| `useFmitImport()` | `frontend/src/hooks/useFmitImport.ts` | `parseBlock()`, `parseBlockAsync()` — FMIT schedule parsing with fuzzy matching confidence |

### Export Functions

| Function | File | Purpose |
|----------|------|---------|
| `exportToLegacyXlsx(startDate, endDate, blockNumber?, federalHolidays?)` | `frontend/src/lib/export.ts` | Calls `GET /api/v1/export/schedule/xlsx`, downloads blob, extracts filename from `Content-Disposition` |
| `exportToCSV(data, filename, columns)` | `frontend/src/lib/export.ts` | Client-side CSV generation and download |
| `exportToJSON(data, filename)` | `frontend/src/lib/export.ts` | Client-side JSON generation and download |
| `downloadFile(content, filename, mimeType)` | `frontend/src/lib/export.ts` | Generic blob download helper |

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `ImportHistoryTable` | `frontend/src/features/import/components/ImportHistoryTable.tsx` | Batch list with status badges, change counts, action buttons |
| `BatchDiffViewer` | `frontend/src/features/import/components/BatchDiffViewer.tsx` | Visual diff display for staged vs existing |
| `BulkImportModal` | `frontend/src/features/import-export/BulkImportModal.tsx` | Drag-and-drop file upload, data type selector, preview, progress |
| `ExportPanel` | `frontend/src/features/import-export/ExportPanel.tsx` | Format selector (CSV/Excel/JSON/PDF), column customization |
| `ImportPreview` | `frontend/src/features/import-export/ImportPreview.tsx` | Staged rows with validation status and error details |
| `ImportProgressIndicator` | `frontend/src/features/import-export/ImportProgressIndicator.tsx` | Progress bar during import execution |

### API Client Layer

| Module | File | Functions |
|--------|------|-----------|
| Import staging | `frontend/src/api/import.ts` | `stageImport()`, `listBatches()`, `getBatch()`, `getBatchPreview()`, `applyBatch()`, `rollbackBatch()`, `deleteBatch()` |
| Block assignment import | `frontend/src/api/block-assignment-import.ts` | `previewBlockAssignmentImport()`, `executeBlockAssignmentImport()`, `quickCreateRotationTemplate()`, `downloadImportTemplate()`, `exportBlockAssignments()` |
| Half-day import | `frontend/src/api/half-day-import.ts` | `stageHalfDayImport()`, `previewHalfDayImport()`, `createHalfDayDraft()` |

### Type Definitions

| File | Key Types |
|------|-----------|
| `frontend/src/types/import.ts` | `ImportBatchResponse`, `ImportPreviewResponse`, `ImportApplyResponse`, `ImportRollbackResponse`, `ConflictResolutionMode` |
| `frontend/src/types/half-day-import.ts` | `HalfDayImportStageResponse`, `HalfDayDiffType` (ADDED/REMOVED/MODIFIED), `HalfDayDiffMetrics`, `HalfDayPreviewFilters` |
| `frontend/src/types/block-assignment-import.ts` | `BlockAssignmentPreviewResponse`, `BlockAssignmentImportResult`, `DuplicateAction` |
| `frontend/src/types/fmit-import.ts` | `BlockParseResponse`, `ResidentRosterItem`, `ParsedFMITWeek` |

---

## Section 4: API Contracts

### Generic Import Staging

**Stage Import**
```
POST /api/v1/import/stage
Content-Type: multipart/form-data

Form fields:
  file: UploadFile (required)
  target_block: int (1-26)
  target_start_date: date
  target_end_date: date
  conflict_resolution: "replace" | "merge" | "upsert"
  notes: string
  sheet_name: string

Response 201:
{
  "success": true,
  "batch_id": "uuid",
  "message": "Staged 45 assignments",
  "row_count": 45,
  "error_count": 0,
  "warning_count": 2
}
```

**List Batches**
```
GET /api/v1/import/batches?page=1&page_size=20&status=staged

Response 200:
{
  "items": [ImportBatchListItem...],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

**Preview Staged Import**
```
GET /api/v1/import/batches/{batch_id}/preview?page=1&page_size=50

Response 200:
{
  "batch_id": "uuid",
  "new_count": 10,
  "update_count": 30,
  "conflict_count": 5,
  "skip_count": 0,
  "staged_assignments": [StagedAssignmentResponse...],
  "conflicts": [...],
  "acgme_violations": [...]
}
```

**Apply Import**
```
POST /api/v1/import/batches/{batch_id}/apply
Content-Type: application/json

{
  "conflict_resolution": "upsert",
  "dry_run": false,
  "validate_acgme": true
}

Response 200:
{
  "batch_id": "uuid",
  "status": "applied",
  "applied_count": 40,
  "skipped_count": 5,
  "error_count": 0,
  "errors": [],
  "acgme_warnings": [],
  "rollback_available": true,
  "rollback_expires_at": "2026-02-26T12:00:00Z"
}
```

**Rollback Import**
```
POST /api/v1/import/batches/{batch_id}/rollback
Content-Type: application/json

{
  "reason": "Wrong block imported"
}

Response 200:
{
  "batch_id": "uuid",
  "status": "rolled_back",
  "rolled_back_count": 40,
  "failed_count": 0,
  "errors": []
}
```

**Delete/Reject Batch**
```
DELETE /api/v1/import/batches/{batch_id}

Response 204 (no content)
```

### Half-Day Import

**Stage Block Template2**
```
POST /api/v1/import/half-day/stage
Content-Type: multipart/form-data

Form fields:
  file: UploadFile (required)
  block_number: int (1-26)
  academic_year: int

Response 200:
{
  "success": true,
  "batch_id": "uuid",
  "created_at": "2026-02-25T10:00:00Z",
  "message": "Staged 840 slots with 23 changes",
  "warnings": ["Row 15: unrecognized code 'XYZ'"],
  "diff_metrics": {
    "total_slots": 840,
    "changed_slots": 23,
    "added": 5,
    "removed": 3,
    "modified": 15,
    "percent_changed": 2.7,
    "manual_half_days": 12,
    "manual_hours": 72,
    "by_activity": {"C": 8, "LV-AM": 3, "NF": 12}
  }
}
```

**Preview Half-Day Import**
```
GET /api/v1/import/half-day/batches/{batch_id}/preview
    ?page=1&page_size=50
    &diff_type=modified
    &activity_code=C
    &has_errors=false
    &person_id=uuid

Response 200:
{
  "batch_id": "uuid",
  "metrics": { HalfDayDiffMetrics },
  "diffs": [
    {
      "staged_id": "uuid",
      "person_id": "uuid",
      "person_name": "Last, First",
      "assignment_date": "2026-03-15",
      "time_of_day": "AM",
      "diff_type": "modified",
      "excel_value": "C",
      "current_value": "NF",
      "warnings": [],
      "errors": []
    }
  ],
  "total_diffs": 23,
  "page": 1,
  "page_size": 50
}
```

**Create Draft from Staged Diffs**
```
POST /api/v1/import/half-day/batches/{batch_id}/draft
Content-Type: application/json

{
  "staged_ids": ["uuid1", "uuid2"],
  "notes": "Block 10 corrections"
}

Response 200:
{
  "success": true,
  "batch_id": "uuid",
  "draft_id": "uuid",
  "message": "Created draft with 15 changes",
  "total_selected": 15,
  "added": 5,
  "modified": 8,
  "removed": 2,
  "skipped": 0,
  "failed": 0,
  "failed_ids": []
}
```

### Export

**Export Single Block XLSX**
```
GET /api/v1/export/schedule/xlsx
    ?block_number=10
    &academic_year=2025
    &start_date=2026-03-12
    &end_date=2026-04-08

Response 200:
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="Block10_2025_schedule.xlsx"

(binary xlsx data)
```

**Export Year XLSX**
```
GET /api/v1/export/schedule/year/xlsx?academic_year=2025

Response 200:
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="AY2025_schedule.xlsx"

(binary xlsx data — 14 block sheets + YTD_SUMMARY)
```

**Parse XLSX (preview only)**
```
POST /api/v1/import/parse-xlsx
Content-Type: multipart/form-data

Form fields:
  file: UploadFile

Response 200:
{
  "success": true,
  "rows": [{"Name": "Last, First", "Rotation1": "FMC", ...}],
  "columns": ["Name", "PGY", "Rotation1", ...],
  "total_rows": 45,
  "sheet_name": "Block 10",
  "warnings": []
}
```

---

## Section 5: Available Testing Tools

### Tool A: Claude-in-Chrome MCP Extension

A live browser automation toolkit running in the user's Chrome session via MCP (Model Context Protocol).

**Available tools (20+):**

| Tool | Purpose |
|------|---------|
| `navigate` | Navigate to URL |
| `find` | Find elements on page (CSS/text selectors) |
| `form_input` | Fill form fields |
| `computer` | Low-level click/type at coordinates |
| `read_page` | Read visible page content |
| `get_page_text` | Get full page text |
| `javascript_tool` | Execute JavaScript in page context |
| `gif_creator` | Record GIF of interactions |
| `tabs_context_mcp` | List open tabs |
| `tabs_create_mcp` | Open new tab |
| `upload_image` | Upload image file |
| `read_console_messages` | Read browser console output |
| `read_network_requests` | Monitor network traffic |

**Strengths:**
- Real browser interaction (not simulated)
- Can inspect network requests and console output
- Can execute arbitrary JavaScript in page context
- GIF recording for visual verification and documentation
- Can interact with file dialogs via `computer` tool (click coordinates)
- Immediate feedback loop — see what the browser sees

**Limitations:**
- Requires active Chrome session (not headless)
- No CI/CD integration
- Single-session (no parallel test execution)
- No built-in assertion library (must script assertions manually)
- File upload requires coordinate-based clicking or JavaScript injection

**Best for:** Exploratory testing, visual verification, one-off validations, debugging specific UI flows, recording demo GIFs.

### Tool B: Playwright

A mature E2E testing framework with existing infrastructure in this project.

**Configuration:** `frontend/playwright.config.ts`
```typescript
{
  testDir: './e2e/tests',
  fullyParallel: true,
  baseURL: 'http://localhost:3000',
  trace: 'on-first-retry',
  screenshot: 'only-on-failure',
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  }
}
```

**NPM scripts:**
```bash
npm run test:e2e        # Run all E2E tests
npm run test:e2e:ui     # Interactive UI mode
```

**Existing infrastructure:**
- 40+ test specs across auth, schedule, swaps, compliance, resilience
- Custom fixtures: auth (4 roles), database (seed/cleanup), schedule helpers
- Page Object Model: `LoginPage`, `SchedulePage`, `SwapPage`, `DashboardPage`, etc.
- Centralized selectors: `frontend/e2e/utils/selectors.ts`
- Test helpers: `waitForLoading()`, `waitForNetworkIdle()`, `fillByLabel()`, `waitForToast()`, etc.
- API mocking utilities: `frontend/e2e/utils/api-mocks.ts`

**Strengths:**
- Headless mode for CI
- Parallel test execution
- Built-in assertions (`expect`)
- File upload via `page.setInputFiles()` (no file dialog needed)
- Network interception and mocking
- Trace viewer for debugging failures
- Existing fixtures and page objects to build on

**Limitations:**
- Requires running backend + database for real import/export to work
- No visual debugging (use trace viewer instead)
- Test data setup requires API calls or database fixtures

**Best for:** Repeatable regression tests, CI integration, file upload simulation, automated validation of import/export flows.

---

## Section 6: Existing Test Patterns

### Pattern 1: Page Navigation + Assertions

```typescript
// frontend/e2e/tests/auth/login.spec.ts
import { test, expect } from '@playwright/test';
import { selectors } from '../../utils/selectors';

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    await expect(page).toHaveTitle(/Login/);
    await expect(page.locator(selectors.login.emailInput)).toBeVisible();
    await expect(page.locator(selectors.login.passwordInput)).toBeVisible();
  });

  test('should login successfully', async ({ page }) => {
    await page.fill(selectors.login.emailInput, 'admin@test.mil');
    await page.fill(selectors.login.passwordInput, 'TestPassword123!');
    await page.click(selectors.login.submitButton);
    await page.waitForURL(/\/(dashboard|schedule)/);
    await expect(page.locator(selectors.nav.userMenu)).toBeVisible();
  });
});
```

### Pattern 2: Fixtures for Auth + Database Seeding

```typescript
// frontend/e2e/tests/schedule/view-schedule.spec.ts
import { test, expect } from '../../fixtures/schedule.fixture';
import { waitForLoading } from '../../utils/test-helpers';

test.describe('View Schedule', () => {
  test('should display schedule calendar', async ({ page, scheduleHelper }) => {
    // SETUP: Seed test data via API
    await scheduleHelper.createPartialSchedule(7, 5);

    // ACT
    await page.goto('/schedule');
    await waitForLoading(page);

    // ASSERT
    await expect(page.locator('[data-testid="schedule-calendar"]')).toBeVisible();
  });

  test('should color-code assignments by rotation', async ({ page, scheduleHelper }) => {
    await scheduleHelper.createFullSchedule(7, 10);
    await page.goto('/schedule');
    await waitForLoading(page);

    const assignments = await page.locator('[data-testid="assignment-card"]').all();
    const colors = new Set();
    for (const assignment of assignments) {
      const bgColor = await assignment.evaluate(el =>
        window.getComputedStyle(el).backgroundColor
      );
      colors.add(bgColor);
    }
    expect(colors.size).toBeGreaterThan(1);
  });
});
```

### Pattern 3: Page Objects for Multi-Step Flows

```typescript
// frontend/e2e/tests/schedule-management.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage, SchedulePage } from '../pages';

test.describe('Schedule Management', () => {
  let loginPage: LoginPage;
  let schedulePage: SchedulePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    schedulePage = new SchedulePage(page);
    await loginPage.clearStorage();
    await loginPage.loginAsAdmin();
  });

  test('should navigate through schedule blocks', async ({ page }) => {
    await schedulePage.navigate();
    await schedulePage.verifySchedulePage();

    const initialDate = await schedulePage.getStartDate();
    await schedulePage.goToNextBlock();
    const nextDate = await schedulePage.getStartDate();
    expect(nextDate).not.toBe(initialDate);

    await schedulePage.goToPreviousBlock();
    const backDate = await schedulePage.getStartDate();
    expect(backDate).toBe(initialDate);
  });
});
```

### Pattern 4: Auth Fixture (Pre-Authenticated Roles)

```typescript
// frontend/e2e/fixtures/auth.fixture.ts (usage)
import { test, expect } from '../../fixtures/auth.fixture';

test('admin can access dashboard', async ({ adminPage }) => {
  await adminPage.goto('/dashboard');
  await expect(adminPage.locator('[data-testid="user-menu"]')).toBeVisible();
});

// Available roles: adminPage, coordinatorPage, facultyPage, residentPage
// Test users: admin@test.mil, coordinator@test.mil, faculty@test.mil, resident@test.mil
// Password: TestPassword123!
```

### Pattern 5: Network Waiting

```typescript
import { waitForNetworkIdle, waitForAPICall } from '../../utils/test-helpers';

test('should load data', async ({ page }) => {
  await page.goto('/schedule');
  await waitForNetworkIdle(page);
  // or wait for specific API call:
  await waitForAPICall(page, '**/api/v1/schedule/**', 'GET');
});
```

### Existing Test Directory Structure

```
frontend/e2e/
├── fixtures/
│   ├── auth.fixture.ts        # Pre-authenticated pages (4 roles)
│   ├── database.fixture.ts    # DB seed/cleanup helpers
│   ├── schedule.fixture.ts    # Schedule scenario builders
│   └── test-data.ts           # Constants
├── utils/
│   ├── selectors.ts           # Centralized CSS/aria selectors
│   ├── test-helpers.ts        # waitForLoading, fillByLabel, etc.
│   └── api-mocks.ts           # Route interception utilities
├── pages/
│   ├── BasePage.ts            # Base class (goto, waitForPageLoad, getButton, etc.)
│   ├── LoginPage.ts
│   ├── DashboardPage.ts
│   ├── SchedulePage.ts
│   ├── SwapPage.ts
│   ├── AnalyticsPage.ts
│   ├── TemplatePage.ts
│   ├── HeatmapPage.ts
│   ├── ResiliencePage.ts
│   └── index.ts               # Barrel export
└── tests/
    ├── auth/                  # 20+ auth specs
    ├── schedule/              # Schedule view specs
    ├── schedule-management.spec.ts
    ├── swap-workflow.spec.ts
    ├── compliance.spec.ts
    ├── resilience-hub.spec.ts
    └── ...                    # 40+ total specs
```

---

## Section 7: Questions for the AI

Answer these in order. Be specific and cite file paths where relevant.

### Strategy Questions

1. **Tool selection:** Given the two tools (Claude-in-Chrome MCP vs Playwright), which should be used for which scenarios? Should we use both? What's the division of labor?

2. **Full E2E test plan:** Design a complete test plan that covers the round-trip: export a known schedule → download the .xlsx → modify specific cells → re-import → verify only modified cells appear as diffs → apply → verify database state. What are all the test cases?

3. **Test data strategy:** How should we seed a known schedule state for deterministic testing? The database needs `half_day_assignments` populated for export to produce anything. Options: (a) Use existing database fixture (`DatabaseHelper.createAssignments()`), (b) Call the scheduling engine via API, (c) Direct SQL inserts, (d) Import a known-good Excel file first. Which approach and why?

### Implementation Questions

4. **File upload in Playwright:** The import pages use `<input type="file">` elements. Playwright supports `page.setInputFiles()` which bypasses the file dialog entirely. But the Chrome extension would need `form_input` or `computer` to interact with the OS file picker. What are the trade-offs? Show the Playwright approach for uploading an Excel file to the `/import/half-day` page.

5. **Import preview verification:** After staging, the preview shows diff counts (added/removed/modified) and individual diffs. How should we assert these are correct? Should we: (a) Compare against a pre-calculated expected diff, (b) Verify counts match what we modified, (c) Spot-check specific person+date+slot combinations? Show the assertion strategy.

6. **ACGME validation during import:** The apply endpoint accepts `validate_acgme: true`. How do we verify ACGME validation actually fires? Should we intentionally create an ACGME-violating import (e.g., exceed 80-hour rule) and verify the warnings appear in the response and UI?

7. **Rollback verification:** After apply → rollback, how do we verify the database returned to its pre-import state? Options: (a) Export again and compare to original export, (b) Query the API for specific assignments, (c) Check the import batch status. What's the most reliable approach?

8. **Multi-step async handling:** The staging → preview → apply flow is multi-step with server-side state. How should tests handle the async nature? Should we use Playwright's `waitForResponse()` to intercept API calls? Should we poll the batch status? Show the recommended pattern.

9. **Excel file manipulation:** Between export and re-import, we need to modify specific cells in the .xlsx. Options: (a) Use `openpyxl` in a Node.js child process, (b) Use `ExcelJS` (already in frontend deps?), (c) Use a pre-prepared modified file, (d) Use the Chrome extension's `javascript_tool` to modify cells via SheetJS. Which approach and why?

### CI & Automation Questions

10. **CI integration:** Can the Playwright import/export tests run headless? What backend fixtures are needed (running PostgreSQL, seeded data, running FastAPI server)? What's the minimal Docker Compose setup?

11. **Write the Playwright specs:** Write the actual Playwright test spec files for the critical paths:
    - `e2e/tests/import-export/export-block.spec.ts` — export a block schedule
    - `e2e/tests/import-export/import-stage-apply.spec.ts` — stage, preview, apply
    - `e2e/tests/import-export/round-trip.spec.ts` — export → modify → re-import → verify
    - `e2e/tests/import-export/rollback.spec.ts` — apply → rollback → verify

12. **Chrome extension automation scripts:** Write Chrome extension automation scripts (using Claude-in-Chrome MCP tools) for visual verification of:
    - Export button click → download happens → file is valid xlsx
    - Import wizard walkthrough (upload → stage → preview → apply)
    - GIF recording of the full round-trip for documentation

---

## Section 8: Key File Paths

### Backend — Export Pipeline

| File | Purpose |
|------|---------|
| `backend/app/api/routes/export.py` | Export API endpoints |
| `backend/app/api/routes/exports.py` | Export job scheduling endpoints |
| `backend/app/services/canonical_schedule_export_service.py` | Main export orchestrator |
| `backend/app/services/half_day_json_exporter.py` | DB → JSON dict |
| `backend/app/services/half_day_xml_exporter.py` | DB → XML (parent class) |
| `backend/app/services/json_to_xlsx_converter.py` | JSON → XLSX |
| `backend/app/services/xml_to_xlsx_converter.py` | XML → XLSX (parent class) |
| `backend/app/services/excel_metadata.py` | `__SYS_META__` + `__REF__` sheet injection |
| `backend/app/services/block_schedule_export_service.py` | Legacy ROSETTA export |
| `backend/data/BlockTemplate2_Official.xlsx` | Production Excel template (**not yet on disk** — code expects it here) |
| `docs/scheduling/BlockTemplate2_Structure.xml` | Row/column mapping definitions (actual location) |

### Backend — Import Pipeline

| File | Purpose |
|------|---------|
| `backend/app/api/routes/import_staging.py` | Import staging API endpoints |
| `backend/app/api/routes/imports.py` | Generic Excel parsing endpoints |
| `backend/app/api/routes/half_day_imports.py` | Half-day import API endpoints |
| `backend/app/services/import_staging_service.py` | Generic import staging service |
| `backend/app/services/half_day_import_service.py` | Half-day Block Template2 import service |
| `backend/app/models/import_staging.py` | `ImportBatch`, `ImportStagedAssignment`, `ImportStagedAbsence` models |
| `backend/app/schemas/import_staging.py` | Import staging Pydantic schemas |
| `backend/app/schemas/half_day_import.py` | Half-day import Pydantic schemas |

### Frontend — Pages

| File | Route |
|------|-------|
| `frontend/src/app/import/page.tsx` | `/import` |
| `frontend/src/app/import/[id]/page.tsx` | `/import/[id]` |
| `frontend/src/app/import/half-day/page.tsx` | `/import/half-day` |
| `frontend/src/app/admin/import/page.tsx` | `/admin/import` |
| `frontend/src/app/admin/block-import/page.tsx` | `/admin/block-import` |
| `frontend/src/app/admin/fmit/import/page.tsx` | `/admin/fmit/import` |
| `frontend/src/app/import-export/page.tsx` | `/import-export` |
| `frontend/src/app/hub/import-export/page.tsx` | `/hub/import-export` |

### Frontend — Hooks

| File | Hook |
|------|------|
| `frontend/src/hooks/useImport.ts` | `useImport()` |
| `frontend/src/hooks/useImportStaging.ts` | `useImportStaging()` |
| `frontend/src/hooks/useHalfDayImport.ts` | `useHalfDayImport()` |
| `frontend/src/hooks/useBlockAssignmentImport.ts` | `useBlockAssignmentImport()` |
| `frontend/src/hooks/useFmitImport.ts` | `useFmitImport()` |

### Frontend — API Clients

| File | Purpose |
|------|---------|
| `frontend/src/api/import.ts` | Generic import staging API |
| `frontend/src/api/half-day-import.ts` | Half-day import API |
| `frontend/src/api/block-assignment-import.ts` | Block assignment import API |

### Frontend — Components

| File | Component |
|------|-----------|
| `frontend/src/features/import/components/ImportHistoryTable.tsx` | Batch history table |
| `frontend/src/features/import/components/BatchDiffViewer.tsx` | Diff visualization |
| `frontend/src/features/import-export/BulkImportModal.tsx` | Upload modal |
| `frontend/src/features/import-export/ExportPanel.tsx` | Export controls |
| `frontend/src/features/import-export/ImportPreview.tsx` | Staged row preview |
| `frontend/src/features/import-export/ImportProgressIndicator.tsx` | Progress bar |
| `frontend/src/features/import-export/index.ts` | Barrel export (types + hooks + utils) |

### Frontend — Types

| File | Purpose |
|------|---------|
| `frontend/src/types/import.ts` | Generic import types |
| `frontend/src/types/half-day-import.ts` | Half-day import types |
| `frontend/src/types/block-assignment-import.ts` | Block assignment import types |
| `frontend/src/types/fmit-import.ts` | FMIT import types |

### Frontend — Export

| File | Purpose |
|------|---------|
| `frontend/src/lib/export.ts` | `exportToLegacyXlsx()`, `exportToCSV()`, `exportToJSON()`, `downloadFile()` |

### E2E Test Infrastructure

| File | Purpose |
|------|---------|
| `frontend/playwright.config.ts` | Playwright configuration |
| `frontend/e2e/fixtures/auth.fixture.ts` | Pre-authenticated page fixtures (4 roles) |
| `frontend/e2e/fixtures/database.fixture.ts` | Database seeding and cleanup |
| `frontend/e2e/fixtures/schedule.fixture.ts` | Schedule scenario builders |
| `frontend/e2e/fixtures/test-data.ts` | Test constants |
| `frontend/e2e/utils/selectors.ts` | Centralized element selectors |
| `frontend/e2e/utils/test-helpers.ts` | Reusable test utilities |
| `frontend/e2e/utils/api-mocks.ts` | API mocking utilities |
| `frontend/e2e/pages/BasePage.ts` | Base page object |
| `frontend/e2e/pages/LoginPage.ts` | Login page object |
| `frontend/e2e/pages/SchedulePage.ts` | Schedule page object |
| `frontend/e2e/pages/index.ts` | Page object barrel export |

### Database Models (Reference)

| File | Tables |
|------|--------|
| `backend/app/models/import_staging.py` | `import_batches`, `import_staged_assignments`, `import_staged_absences` |
| `backend/app/models/half_day_assignment.py` | `half_day_assignments` (descriptive truth) |
| `backend/app/models/block_assignment.py` | `block_assignments` (prescriptive truth) |
| `backend/app/models/person.py` | `people` |
| `backend/app/models/activity.py` | `activities` |
| `backend/app/models/schedule_override.py` | `schedule_overrides` |

---

## Appendix A: Conflict Resolution Modes

| Mode | Behavior | Risk |
|------|----------|------|
| `replace` | Delete all existing assignments in target block, insert only staged | **High** — data loss if wrong block |
| `merge` | Keep existing, add new, skip conflicts | **Low** — no overwrites, but may miss updates |
| `upsert` (default) | Update matching person+date+slot, insert new | **Medium** — intended behavior for corrections |

## Appendix B: Import Batch Status Flow

```
STAGED → APPROVED → APPLIED → ROLLED_BACK
  │                    ↑          (within 24h)
  ├─→ REJECTED         │
  │                    └─→ (24h expires, rollback unavailable)
  └─→ FAILED
```

## Appendix C: Half-Day Diff Types

| Diff Type | Meaning | Example |
|-----------|---------|---------|
| `ADDED` | Slot exists in Excel but not in DB | New assignment for person on date |
| `REMOVED` | Slot exists in DB but not in Excel | Person removed from date |
| `MODIFIED` | Slot exists in both but activity code differs | Changed from `NF` to `C` |

## Appendix D: Fuzzy Matching Details

- **Algorithm:** Python `difflib.SequenceMatcher`
- **Threshold:** 70% similarity
- **Normalization:** `name.lower().strip()`
- **Caching:** All Person/RotationTemplate records loaded into memory on first match
- **Confidence returned:** 0-100 integer (ratio * 100)
- **Example:** "John DOE" → normalized "john doe" → matched "john q doe" at 78% confidence
