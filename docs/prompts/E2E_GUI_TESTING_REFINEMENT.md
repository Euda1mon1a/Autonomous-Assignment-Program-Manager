# Full-Stack GUI E2E Testing — Refinement Brief

> **Purpose:** Self-contained prompt for AI-assisted refinement of the end-to-end GUI test suite for a military medical residency scheduler.
> **Target AI:** Gemini Pro 3.1 (Extended Thinking)
> **Project:** Military medical residency scheduler (ACGME-compliant, OPSEC-sensitive)
> **Created:** 2026-02-25

---

## Section 1: Mission

### What We Need

A strategic refinement plan for the existing Playwright E2E test suite. The suite has **580 test cases across 34 spec files**, but coverage is shallow and unevenly distributed. We need guidance on:

1. **Coverage gap analysis** — Which of the 53 frontend pages have zero test coverage? Which high-risk flows are untested?
2. **Test quality** — Many specs test basic visibility (`toBeVisible`) rather than functional behavior. Where should we deepen assertions?
3. **Infrastructure gaps** — What fixtures, page objects, selectors, and helpers are missing?
4. **Data seeding strategy** — 9 tests are `test.skip(!process.env.E2E_HAS_SEEDED_DATA)` and 3 are `test.fixme()`. How do we make these runnable?
5. **Prioritized roadmap** — Given limited time, which 10 spec files would deliver the most confidence?

### Why This Matters

This is a scheduling application for a **military medical residency program**. Failures mean:
- Wrong resident assigned to wrong rotation (patient safety)
- ACGME work-hour violations (program accreditation risk)
- Undetected schedule conflicts (operational gaps)
- Data corruption through import/export pipeline (silent errors)

The app is pre-production. E2E tests are the last safety net before manual QA by program coordinators.

### Constraints

- **No CI/CD yet** — tests run locally only (macOS, Chromium)
- **No test database seeding pipeline** — backend + Postgres must be running with real-ish data
- **OPSEC** — no real names, schedules, or military data in test fixtures
- **Single developer** — prioritize ROI over exhaustive coverage

---

## Section 2: Current Test Inventory

### Spec Files (34 total)

**Auth (13 specs, ~85 tests)**
| File | Tests | Status |
|------|-------|--------|
| `auth/login.spec.ts` | ~8 | Functional |
| `auth/logout.spec.ts` | ~6 | Functional |
| `auth/session.spec.ts` | ~5 | Functional |
| `auth/role-access.spec.ts` | ~8 | Functional |
| `auth/password-reset.spec.ts` | ~6 | Functional |
| `auth/token-refresh.spec.ts` | ~6 | Functional |
| `auth/account-lockout.spec.ts` | ~5 | Functional |
| `auth/brute-force-protection.spec.ts` | ~5 | Functional |
| `auth/csrf-protection.spec.ts` | ~5 | Functional |
| `auth/clickjacking-protection.spec.ts` | ~5 | Functional |
| `auth/security-headers.spec.ts` | ~5 | Functional |
| `auth/session-hijacking.spec.ts` | ~5 | Functional |
| `auth/xss-protection.spec.ts` | ~5 | Functional |
| `auth/multi-factor-auth.spec.ts` | ~5 | Functional |
| `auth/auth-edge-cases.spec.ts` | ~5 | Functional |

**Import/Export (5 specs, ~30 tests)**
| File | Tests | Status |
|------|-------|--------|
| `import-export/import-stage-apply.spec.ts` | 8 | 4 skip (need seeded DB) |
| `import-export/export-block.spec.ts` | 4 | 3 skip (need seeded DB) |
| `import-export/round-trip.spec.ts` | 3 | All skip (need seeded DB) |
| `import-export/acgme-violation-import.spec.ts` | 1 | Skip (need seeded DB) |
| `import-export/rollback.spec.ts` | 7 | **3 fixme** (blocked) |

**Feature Pages (16 specs, ~465 tests)**
| File | Tests | Status |
|------|-------|--------|
| `resilience-hub.spec.ts` | ~40 | Functional |
| `templates.spec.ts` | ~30 | Functional |
| `heatmap.spec.ts` | ~25 | Functional |
| `analytics.spec.ts` | ~25 | Functional |
| `absence-management.spec.ts` | ~25 | Functional |
| `schedule-management.spec.ts` | ~20 | Functional |
| `bulk-operations.spec.ts` | ~20 | Functional |
| `swap-workflow.spec.ts` | ~20 | Functional |
| `mobile-responsive.spec.ts` | ~15 | Functional |
| `schedule/view-schedule.spec.ts` | ~8 | Functional |
| `templates/create-pattern.spec.ts` | ~12 | Functional |
| `templates/edit-pattern.spec.ts` | ~12 | Functional |
| `templates/delete-pattern.spec.ts` | ~12 | Functional |
| `templates/preferences.spec.ts` | ~15 | Functional |

### Blocked/Skipped Tests

| Marker | Count | Reason |
|--------|-------|--------|
| `test.skip(!process.env.E2E_HAS_SEEDED_DATA)` | 9 | Need seeded PostgreSQL with people + assignments |
| `test.fixme()` | 3 | In `rollback.spec.ts` — need backend rollback endpoint operational + seeded data |

### Infrastructure

**Fixtures:**
| File | Purpose |
|------|---------|
| `e2e/fixtures/auth.fixture.ts` | Pre-authenticated pages for 4 roles (admin, coordinator, faculty, resident) |
| `e2e/fixtures/database.fixture.ts` | Database seeding/cleanup helpers |
| `e2e/fixtures/schedule.fixture.ts` | Schedule scenario builders (`createPartialSchedule`, `createFullSchedule`) |
| `e2e/fixtures/test-data.ts` | Constants (test users, URLs, timeouts) |
| `e2e/fixtures/generate-test-xlsx.ts` | Synthetic xlsx generator (Block Template2 format with `__SYS_META__`) |
| `e2e/fixtures/test-block10.xlsx` | Generated test fixture (5 synthetic residents, 28 days) |
| `e2e/fixtures/test-acgme-violation.xlsx` | Generated fixture with 1-in-7 NF violation |

**Page Objects (10):**
| Page Object | File |
|-------------|------|
| `BasePage` | `e2e/pages/BasePage.ts` |
| `LoginPage` | `e2e/pages/LoginPage.ts` |
| `DashboardPage` | `e2e/pages/DashboardPage.ts` |
| `SchedulePage` | `e2e/pages/SchedulePage.ts` |
| `SwapPage` | `e2e/pages/SwapPage.ts` |
| `AnalyticsPage` | `e2e/pages/AnalyticsPage.ts` |
| `TemplatePage` | `e2e/pages/TemplatePage.ts` |
| `HeatmapPage` | `e2e/pages/HeatmapPage.ts` |
| `ResiliencePage` | `e2e/pages/ResiliencePage.ts` |
| `ImportExportPage` | `e2e/pages/ImportExportPage.ts` |

**Utils:**
| File | Key Functions |
|------|---------------|
| `e2e/utils/selectors.ts` | Centralized CSS/aria selectors for all pages (12 selector groups) |
| `e2e/utils/test-helpers.ts` | `waitForNetworkIdle`, `waitForLoading`, `waitForToast`, `fillByLabel`, `uploadFile`, `waitForDownload`, `waitForTableData`, `dragAndDrop`, `mockTime` |
| `e2e/utils/xlsx-helpers.ts` | `streamToBuffer`, `parseExportedXlsx`, `verifySysMeta`, `mutateXlsxCell` |
| `e2e/utils/api-mocks.ts` | Route interception and API mocking utilities |

**Playwright Config:**
```typescript
{
  testDir: './e2e/tests',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  baseURL: 'http://localhost:3000',
  trace: 'on-first-retry',
  screenshot: 'only-on-failure',
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: { command: 'npm run dev', url: 'http://localhost:3000', reuseExistingServer: !process.env.CI }
}
```

---

## Section 3: Coverage Gap Analysis

### All Frontend Pages (53 routes)

**With E2E Coverage (checked):**
| Route | Spec File | Depth |
|-------|-----------|-------|
| `/login` | `auth/login.spec.ts` | Deep (form validation, error states, success) |
| `/schedule` | `schedule/view-schedule.spec.ts` | Medium (calendar render, color-coding) |
| `/schedule` | `schedule-management.spec.ts` | Medium (navigation, block switching) |
| `/swaps` | `swap-workflow.spec.ts` | Medium (create, approve, reject) |
| `/templates` | `templates/*.spec.ts` | Deep (CRUD + preferences) |
| `/heatmap` | `heatmap.spec.ts` | Medium |
| `/absences` | `absence-management.spec.ts` | Medium |
| `/import/half-day` | `import-export/import-stage-apply.spec.ts` | Deep (but 4/8 skipped) |
| `/hub/import-export` | `import-export/export-block.spec.ts` | Medium (3/4 skipped) |
| Resilience dashboard | `resilience-hub.spec.ts` | Deep |
| Responsive | `mobile-responsive.spec.ts` | Shallow |
| Analytics | `analytics.spec.ts` | Medium |

**WITHOUT E2E Coverage (31 routes — 58%):**

*User-facing pages (HIGH priority):*
| Route | Page | Risk |
|-------|------|------|
| `/compliance` | ACGME compliance dashboard | **CRITICAL** — core safety feature |
| `/daily-manifest` | Today's assignments view | **HIGH** — daily operational tool |
| `/call-hub` | Call schedule management | **HIGH** — on-call assignments |
| `/call-roster` | Call roster view | **HIGH** — on-call visibility |
| `/my-schedule` | Personal schedule (resident view) | **HIGH** — most-used page for residents |
| `/conflicts` | Schedule conflict viewer | **HIGH** — safety net |
| `/wellness` | Wellness tracking | MEDIUM |
| `/proxy-coverage` | Proxy/coverage management | MEDIUM |
| `/command-center` | Operations center | MEDIUM |
| `/rotations` | Rotation management | MEDIUM |
| `/activities` | Activity code management | LOW |
| `/solver-viz` | Solver visualization | LOW |
| `/help` | Help page | LOW |
| `/settings` | User settings | LOW |
| `/import` | Import hub/history | MEDIUM |
| `/import/[id]` | Batch detail view | **HIGH** — review + apply flow |
| `/import-export` | Simple import/export tab | LOW (redundant with hub) |

*Admin pages (20 routes — zero coverage):*
| Route | Risk |
|-------|------|
| `/admin/dashboard` | MEDIUM |
| `/admin/scheduling` | **CRITICAL** — schedule generation |
| `/admin/compliance` | **HIGH** — admin compliance view |
| `/admin/block-import` | **HIGH** — 4-step import wizard |
| `/admin/import` | **HIGH** — bulk import |
| `/admin/fmit/import` | **HIGH** — FMIT schedule import |
| `/admin/swaps` | MEDIUM |
| `/admin/people` | MEDIUM |
| `/admin/users` | MEDIUM |
| `/admin/rotations` | MEDIUM |
| `/admin/faculty-call` | MEDIUM |
| `/admin/schedule-drafts` | MEDIUM |
| `/admin/resilience-hub` | MEDIUM |
| `/admin/resilience-overseer` | LOW |
| `/admin/health` | LOW |
| `/admin/status` | LOW |
| `/admin/audit` | LOW |
| `/admin/credentials` | LOW |
| `/admin/procedures` | LOW |
| `/admin/block-explorer` | LOW |
| `/admin/labs` | LOW |
| `/admin/game-theory` | LOW |
| `/admin/pec` | LOW |
| `/admin/legacy` | LOW |
| `/admin/debugger` | LOW |
| `/admin/schema` | LOW |
| `/(hub)/people` | MEDIUM |

### Selector Coverage Gaps

The `selectors.ts` file has 12 groups: `common`, `nav`, `login`, `dashboard`, `schedule`, `assignment`, `swap`, `swapForm`, `compliance`, `resilience`, `settings`, `table`, `validation`, `a11y`, `dragDrop`, `importExport`, `calendar`.

**Missing selector groups for untested pages:**
- No `callHub` / `callRoster` selectors
- No `dailyManifest` selectors
- No `mySchedule` selectors
- No `conflicts` selectors
- No `wellness` selectors
- No `commandCenter` selectors
- No `admin.*` selectors (for any of the 20+ admin pages)
- No `rotations` / `activities` selectors
- No `solverViz` selectors
- `compliance` selectors exist but `/compliance` page has no spec

### Page Object Gaps

Existing: `BasePage`, `LoginPage`, `DashboardPage`, `SchedulePage`, `SwapPage`, `AnalyticsPage`, `TemplatePage`, `HeatmapPage`, `ResiliencePage`, `ImportExportPage`

**Missing:**
- `CompliancePage` (selectors exist, no page object, no spec)
- `CallHubPage`
- `DailyManifestPage`
- `MySchedulePage`
- `ConflictsPage`
- `AdminSchedulingPage`
- `AdminBlockImportPage`
- `AdminFmitImportPage`

---

## Section 4: Existing Selector Reference

```typescript
export const selectors = {
  common: {
    loadingSpinner: '[data-testid="loading-spinner"]',
    toast: '[data-testid="toast"]',
    toastClose: '[data-testid="toast-close"]',
    errorMessage: '[data-testid="error-message"]',
    successMessage: '[data-testid="success-message"]',
    modal: '[role="dialog"]',
    modalClose: '[role="dialog"] button:has-text("Close")',
    confirmButton: 'button:has-text("Confirm")',
    cancelButton: 'button:has-text("Cancel")',
    saveButton: 'button:has-text("Save")',
    deleteButton: 'button:has-text("Delete")',
    editButton: 'button:has-text("Edit")',
    backButton: 'button:has-text("Back")',
  },
  nav: {
    userMenu: '[data-testid="user-menu"]',
    logoutButton: 'button:has-text("Logout")',
    dashboardLink: 'a:has-text("Dashboard")',
    scheduleLink: 'a:has-text("Schedule")',
    swapLink: 'a:has-text("Swaps")',
    complianceLink: 'a:has-text("Compliance")',
    resilienceLink: 'a:has-text("Resilience")',
    settingsLink: 'a:has-text("Settings")',
  },
  login: {
    emailInput: 'input[name="email"]',
    passwordInput: 'input[name="password"]',
    submitButton: 'button[type="submit"]',
    forgotPasswordLink: 'a:has-text("Forgot Password")',
    errorMessage: '[data-testid="login-error"]',
    rememberMeCheckbox: 'input[name="remember"]',
  },
  dashboard: {
    welcomeMessage: '[data-testid="welcome-message"]',
    upcomingShifts: '[data-testid="upcoming-shifts"]',
    recentAlerts: '[data-testid="recent-alerts"]',
    quickStats: '[data-testid="quick-stats"]',
    complianceWidget: '[data-testid="compliance-widget"]',
    resilienceWidget: '[data-testid="resilience-widget"]',
  },
  schedule: {
    calendar: '[data-testid="schedule-calendar"]',
    calendarDay: '[data-testid="calendar-day"]',
    calendarBlock: '[data-testid="calendar-block"]',
    assignment: '[data-testid="assignment"]',
    assignmentCard: '[data-testid="assignment-card"]',
    createAssignmentButton: 'button:has-text("Create Assignment")',
    filterButton: '[data-testid="filter-button"]',
    exportButton: '[data-testid="export-button"]',
    printButton: '[data-testid="print-button"]',
    viewModeToggle: '[data-testid="view-mode-toggle"]',
    dateRangePicker: '[data-testid="date-range-picker"]',
    personFilter: '[data-testid="person-filter"]',
    rotationFilter: '[data-testid="rotation-filter"]',
    conflictIndicator: '[data-testid="conflict-indicator"]',
    emptyState: '[data-testid="schedule-empty-state"]',
  },
  compliance: {
    complianceSummary: '[data-testid="compliance-summary"]',
    violationsList: '[data-testid="violations-list"]',
    violationCard: '[data-testid="violation-card"]',
    workHoursChart: '[data-testid="work-hours-chart"]',
    dayOffIndicator: '[data-testid="day-off-indicator"]',
    supervisionRatio: '[data-testid="supervision-ratio"]',
    filterPerson: '[data-testid="compliance-filter-person"]',
    filterDateRange: '[data-testid="compliance-filter-date"]',
    exportReport: '[data-testid="export-compliance-report"]',
    violationSeverity: '[data-testid="violation-severity"]',
  },
  resilience: {
    dashboard: '[data-testid="resilience-dashboard"]',
    defenseLevel: '[data-testid="defense-level"]',
    defenseLevelBadge: '[data-testid="defense-level-badge"]',
    utilizationChart: '[data-testid="utilization-chart"]',
    utilizationValue: '[data-testid="utilization-value"]',
    n1Contingency: '[data-testid="n1-contingency"]',
    alertsList: '[data-testid="alerts-list"]',
    alertCard: '[data-testid="alert-card"]',
    burnoutRt: '[data-testid="burnout-rt"]',
    criticalIndex: '[data-testid="critical-index"]',
    coverageGaps: '[data-testid="coverage-gaps"]',
    refreshButton: '[data-testid="refresh-dashboard"]',
  },
  importExport: {
    // Hub tabs
    hubTabStaged: '[data-testid="hub-tab-staged"]',
    hubTabBlock: '[data-testid="hub-tab-block"]',
    hubTabFmit: '[data-testid="hub-tab-fmit"]',
    hubTabExport: '[data-testid="hub-tab-export"]',
    // Half-day upload step
    hdFileInput: '[data-testid="hd-file-input"]',
    hdBlockNumber: '[data-testid="hd-block-number"]',
    hdAcademicYear: '[data-testid="hd-academic-year"]',
    hdStageBtn: '[data-testid="hd-stage-btn"]',
    // Half-day preview step
    hdFilterDiffType: '[data-testid="hd-filter-difftype"]',
    hdFilterActivity: '[data-testid="hd-filter-activity"]',
    hdFilterErrors: '[data-testid="hd-filter-errors"]',
    hdFilterPerson: '[data-testid="hd-filter-person"]',
    hdSelectPageBtn: '[data-testid="hd-select-page-btn"]',
    hdDiffTable: '[data-testid="hd-diff-table"]',
    hdMetricTotal: '[data-testid="hd-metric-total"]',
    hdMetricChanged: '[data-testid="hd-metric-changed"]',
    hdMetricAddedRemoved: '[data-testid="hd-metric-added-removed"]',
    hdMetricHours: '[data-testid="hd-metric-hours"]',
    hdPaginationInfo: '[data-testid="hd-pagination-info"]',
    hdDraftNotes: '[data-testid="hd-draft-notes"]',
    hdCreateDraftBtn: '[data-testid="hd-create-draft-btn"]',
    // Half-day draft step
    hdDraftAdded: '[data-testid="hd-draft-added"]',
    hdDraftModified: '[data-testid="hd-draft-modified"]',
    hdDraftRemoved: '[data-testid="hd-draft-removed"]',
    hdViewDraftBtn: '[data-testid="hd-view-draft-btn"]',
    // Batch review
    batchStatusBadge: '[data-testid="batch-status-badge"]',
    batchApplyBtn: '[data-testid="batch-apply-btn"]',
    batchCancelBtn: '[data-testid="batch-cancel-btn"]',
    batchStatNew: '[data-testid="batch-stat-new"]',
    batchStatUpdates: '[data-testid="batch-stat-updates"]',
    batchStatViolations: '[data-testid="batch-stat-violations"]',
    // Export
    exportFormatCsv: '[data-testid="export-format-csv"]',
    exportFormatXlsx: '[data-testid="export-format-xlsx"]',
    exportFormatJson: '[data-testid="export-format-json"]',
    exportSubmitBtn: '[data-testid="export-submit-btn"]',
  },
  // ... also: assignment, swap, swapForm, settings, table, validation, a11y, dragDrop, calendar
};
```

---

## Section 5: Existing Test Patterns

### Pattern 1: Auth Fixture (Pre-Authenticated Roles)

```typescript
import { test, expect } from '../../fixtures/auth.fixture';

// Available fixtures: adminPage, coordinatorPage, facultyPage, residentPage
test('admin can access dashboard', async ({ adminPage }) => {
  await adminPage.goto('/dashboard');
  await expect(adminPage.locator('[data-testid="user-menu"]')).toBeVisible();
});
```

### Pattern 2: Upload → Stage → Assert with waitForResponse

```typescript
test('should stage import and display diff metrics', async ({ adminPage }) => {
  test.skip(!process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

  await adminPage.locator(selectors.importExport.hdFileInput).setInputFiles(TEST_XLSX_PATH);
  await adminPage.locator(selectors.importExport.hdBlockNumber).fill('10');
  await adminPage.locator(selectors.importExport.hdAcademicYear).fill('2025');

  const [stageResponse] = await Promise.all([
    adminPage.waitForResponse(
      (resp) => resp.url().includes('/stage') && resp.status() === 200,
      { timeout: 30_000 },
    ),
    adminPage.locator(selectors.importExport.hdStageBtn).click(),
  ]);
  expect(stageResponse.ok()).toBe(true);

  await expect(adminPage.locator(selectors.importExport.hdMetricTotal)).toBeVisible({ timeout: 10_000 });
});
```

### Pattern 3: Page Object with Multi-Step Flow

```typescript
import { LoginPage, SchedulePage } from '../pages';

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
});
```

### Pattern 4: Download + Parse xlsx

```typescript
import { streamToBuffer, parseExportedXlsx, verifySysMeta } from '../../utils/xlsx-helpers';

test('should export valid xlsx with __SYS_META__', async ({ adminPage }) => {
  const [download] = await Promise.all([
    adminPage.waitForEvent('download'),
    adminPage.locator(selectors.importExport.exportSubmitBtn).click(),
  ]);
  const readStream = await download.createReadStream();
  const buffer = await streamToBuffer(readStream! as unknown as ReadableStream);
  const { meta, sheetName, rows } = await parseExportedXlsx(buffer);
  expect(meta!.academic_year).toBeDefined(); // @enum-ok
  expect(rows.length).toBeGreaterThan(0);
});
```

### Pattern 5: Conditional Skip for Seeded Data

```typescript
// Inside a test (not at describe level)
test.skip(!process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');

// At describe level (must use callback form)
test.skip(() => !process.env.E2E_HAS_SEEDED_DATA, 'Requires seeded database');
```

---

## Section 6: Key Frontend Architecture

### Tech Stack
- **Next.js 14** (App Router) + **React 18** + **TypeScript** (strict)
- **TailwindCSS 3.4** for styling
- **TanStack Query 5** for data fetching (hooks pattern: `useQuery`, `useMutation`)
- **Axios** with interceptors: request keys → snake_case, response keys → camelCase
- Enum values stay snake_case (Gorgon's Gaze convention)
- URL query params stay snake_case

### Hooks Layer (API Integration)

| Hook | File | API Endpoints |
|------|------|---------------|
| `useImport()` | `src/hooks/useImport.ts` | `listBatches`, `getBatch`, `preview`, `stage`, `apply`, `rollback`, `delete` |
| `useImportStaging()` | `src/hooks/useImportStaging.ts` | `useImportBatches`, `useStageImport`, `useApplyImport`, `useRollbackImport` |
| `useHalfDayImport()` | `src/hooks/useHalfDayImport.ts` | `useStageHalfDayImport`, `useHalfDayImportPreview`, `useCreateHalfDayDraft` |
| `useBlockAssignmentImport()` | `src/hooks/useBlockAssignmentImport.ts` | 4-step wizard: upload → preview → import → complete |
| `useFmitImport()` | `src/hooks/useFmitImport.ts` | `parseBlock`, `parseBlockAsync` |
| `useExportData()` | `src/hooks/useExportData.ts` | `GET /export/people`, `/export/schedule`, `/export/absences` |
| `usePeople()` | `src/hooks/usePeople.ts` | `GET /people` with pagination |

### Import/Export Components

| Component | File |
|-----------|------|
| `ImportHistoryTable` | `src/features/import/components/ImportHistoryTable.tsx` |
| `BatchDiffViewer` | `src/features/import/components/BatchDiffViewer.tsx` |
| `BulkImportModal` | `src/features/import-export/BulkImportModal.tsx` |
| `ExportPanel` | `src/features/import-export/ExportPanel.tsx` |
| `ImportPreview` | `src/features/import-export/ImportPreview.tsx` |
| `ImportProgressIndicator` | `src/features/import-export/ImportProgressIndicator.tsx` |

### Key API Contracts

**Import staging:**
- `POST /api/v1/import/stage` — upload xlsx, get `batch_id`
- `GET /api/v1/import/batches/{id}/preview` — paginated staged assignments
- `POST /api/v1/import/batches/{id}/apply` — commit to DB (24h rollback window)
- `POST /api/v1/import/batches/{id}/rollback` — undo within 24h

**Half-day import:**
- `POST /api/v1/import/half-day/stage` — upload Block Template2, get diff metrics
- `GET /api/v1/import/half-day/batches/{id}/preview` — filterable diffs (by type, activity, person)
- `POST /api/v1/import/half-day/batches/{id}/draft` — create draft from selected diffs

**Export:**
- `GET /api/v1/export/schedule/xlsx?block_number=10&academic_year=2025` — Block Template2 xlsx download
- `GET /api/v1/export/people` — people JSON
- `GET /api/v1/export/schedule?start_date=...&end_date=...` — schedule JSON

---

## Section 7: The 3 Blocked Tests (rollback.spec.ts)

```typescript
// rollback.spec.ts — currently blocked by test.fixme()
test.describe('Rollback After Apply', () => {
  test.fixme();  // Blocks the entire describe

  test.describe('Full Rollback Workflow', () => {
    // 4 tests: upload→stage→draft→apply, display rollback controls,
    //          execute rollback, verify via API
  });

  test.describe('Rollback Edge Cases', () => {
    test('should not allow rollback on draft batch', async () => {
      test.fixme();  // Nested fixme
    });
    test('should not allow double rollback', async () => {
      test.fixme();  // Nested fixme
    });
  });
});
```

**Blockers:**
1. Needs seeded database with matching person records
2. Backend rollback endpoint must be operational
3. Batch must reach APPLIED state before rollback can be tested
4. The test shares state (`batchUrl`) across sequential tests within a describe — fragile pattern

---

## Section 8: Questions for the AI

Answer these in order. Be specific, cite file paths, and show code where relevant.

### Strategy

1. **Priority ranking:** Given the coverage gap analysis (31 uncovered pages), rank the top 10 pages/flows that should get E2E specs next, considering: (a) patient safety risk, (b) daily usage frequency, (c) data mutation risk, (d) existing infrastructure to build on. Justify each pick.

2. **Test depth vs breadth:** The suite has 580 tests but most are shallow (`toBeVisible` assertions). For each of the top 10 pages, define what "meaningful coverage" looks like — what should be asserted beyond visibility? What user workflows must complete end-to-end?

3. **Seeded data strategy:** 12 tests are blocked by missing seeded data. Design a data seeding approach that:
   - Uses synthetic data only (OPSEC requirement)
   - Can be run before each test suite (not each test)
   - Seeds people, block assignments, half-day assignments, activities
   - Is deterministic (same seed = same data)
   - Doesn't require Docker (we run natively on macOS with local Postgres)

   Options to evaluate: (a) Playwright `globalSetup` calling backend seed API, (b) SQL script run via `psql`, (c) Backend management command, (d) Fixtures loaded via API calls in `beforeAll`. Which approach and why?

4. **Rollback unblock:** The 3 `test.fixme()` tests in `rollback.spec.ts` are blocked. What specific prerequisites must be satisfied to unblock them? Write the minimal changes needed.

### Architecture

5. **Page Object vs Direct Selectors:** The suite uses both patterns — some specs use page objects (`LoginPage`, `SchedulePage`), others use direct selectors (`selectors.importExport.hdStageBtn`). Which pattern should we standardize on? Should we create page objects for all 10 priority pages, or use selectors directly? Trade-offs?

6. **Test isolation:** Several tests in `rollback.spec.ts` share state via `let batchUrl` across tests in the same describe. This is fragile — if test 1 fails, tests 2-4 fail. Should we:
   (a) Combine into one large test?
   (b) Use Playwright's `test.step()` for sub-steps?
   (c) Use fixtures to create pre-populated state?
   Show the recommended refactoring.

7. **API mocking vs real backend:** The `api-mocks.ts` utility exists but isn't used by import/export tests (they hit real backend). When should we mock vs use real backend? Should we have two test modes (fast/mocked and slow/real)?

### Implementation

8. **Write the compliance spec:** The `/compliance` page has selectors defined but no spec file. Write `e2e/tests/compliance/compliance-dashboard.spec.ts` that tests:
   - Page loads with compliance summary visible
   - Violation cards render (if any exist)
   - Person filter works
   - Export compliance report downloads a file
   - ACGME metrics display (80-hour, 1-in-7, supervision ratio)

9. **Write the daily-manifest spec:** The `/daily-manifest` page has no selectors or spec. Design the selectors and write `e2e/tests/daily-manifest.spec.ts` that tests:
   - Today's assignments render
   - Correct resident count shown
   - Filter by rotation type works
   - No coverage gaps highlighted (or gaps correctly shown)

10. **Write the admin-scheduling spec:** The `/admin/scheduling` page is the most critical untested admin page (schedule generation). Design `e2e/tests/admin/scheduling.spec.ts` that tests:
    - Page renders with block selector
    - Can configure generation parameters
    - Generate button triggers solver
    - Progress indicator shows during generation
    - Results display with assignment counts
    - ACGME validation runs on generated schedule

11. **Fixture enhancement:** Enhance `database.fixture.ts` to support:
    - Seeding a known set of people (17 synthetic residents + 13 synthetic faculty)
    - Seeding block assignments for a specific block
    - Seeding half-day assignments with known activity codes
    - Cleanup that restores database to pre-test state
    - Exporting a "snapshot" and restoring it (for rollback verification)

12. **CI-ready configuration:** Design a `playwright.config.ci.ts` that:
    - Runs against a Docker Compose stack (Postgres + FastAPI + Next.js)
    - Seeds test data via global setup
    - Sets `E2E_HAS_SEEDED_DATA=true`
    - Runs in headless Chromium
    - Generates HTML report + JUnit XML
    - Fails fast on first error in CI

---

## Section 9: Key File Paths

### Frontend Pages (53 routes)
```
src/app/page.tsx                          # Home/landing
src/app/login/page.tsx                    # Login
src/app/schedule/page.tsx                 # Schedule calendar
src/app/schedule/[personId]/page.tsx      # Person schedule
src/app/my-schedule/page.tsx              # Personal schedule (resident)
src/app/swaps/page.tsx                    # Swap management
src/app/compliance/page.tsx               # ACGME compliance
src/app/heatmap/page.tsx                  # Coverage heatmap
src/app/daily-manifest/page.tsx           # Today's assignments
src/app/call-hub/page.tsx                 # Call schedule
src/app/call-roster/page.tsx              # Call roster
src/app/conflicts/page.tsx                # Conflict viewer
src/app/absences/page.tsx                 # Absence management
src/app/wellness/page.tsx                 # Wellness tracking
src/app/proxy-coverage/page.tsx           # Proxy/coverage
src/app/command-center/page.tsx           # Operations
src/app/rotations/page.tsx                # Rotation management
src/app/activities/page.tsx               # Activity codes
src/app/templates/page.tsx                # Templates
src/app/settings/page.tsx                 # Settings
src/app/solver-viz/page.tsx               # Solver visualization
src/app/help/page.tsx                     # Help
src/app/import/page.tsx                   # Import hub
src/app/import/[id]/page.tsx              # Batch detail
src/app/import/half-day/page.tsx          # Half-day import
src/app/import-export/page.tsx            # Simple import/export
src/app/hub/import-export/page.tsx        # Unified import/export hub
src/app/(hub)/people/page.tsx             # People directory

# Admin pages (20+)
src/app/admin/dashboard/page.tsx
src/app/admin/scheduling/page.tsx         # Schedule generation (CRITICAL)
src/app/admin/compliance/page.tsx
src/app/admin/block-import/page.tsx       # 4-step block import wizard
src/app/admin/import/page.tsx             # Bulk import
src/app/admin/fmit/import/page.tsx        # FMIT import
src/app/admin/swaps/page.tsx
src/app/admin/people/page.tsx
src/app/admin/users/page.tsx
src/app/admin/rotations/page.tsx
src/app/admin/faculty-call/page.tsx
src/app/admin/schedule-drafts/page.tsx
src/app/admin/resilience-hub/page.tsx
src/app/admin/resilience-overseer/page.tsx
src/app/admin/health/page.tsx
src/app/admin/status/page.tsx
src/app/admin/audit/page.tsx
src/app/admin/credentials/page.tsx
src/app/admin/procedures/page.tsx
src/app/admin/block-explorer/page.tsx
src/app/admin/labs/page.tsx
src/app/admin/game-theory/page.tsx
src/app/admin/pec/page.tsx
src/app/admin/legacy/page.tsx
src/app/admin/debugger/page.tsx
src/app/admin/schema/page.tsx
```

### E2E Infrastructure
```
frontend/playwright.config.ts
frontend/e2e/fixtures/auth.fixture.ts
frontend/e2e/fixtures/database.fixture.ts
frontend/e2e/fixtures/schedule.fixture.ts
frontend/e2e/fixtures/test-data.ts
frontend/e2e/fixtures/generate-test-xlsx.ts
frontend/e2e/fixtures/test-block10.xlsx
frontend/e2e/fixtures/test-acgme-violation.xlsx
frontend/e2e/utils/selectors.ts
frontend/e2e/utils/test-helpers.ts
frontend/e2e/utils/xlsx-helpers.ts
frontend/e2e/utils/api-mocks.ts
frontend/e2e/pages/*.ts (10 page objects)
frontend/e2e/tests/**/*.spec.ts (34 spec files)
```

### Backend Endpoints (relevant to E2E)
```
backend/app/api/routes/export.py
backend/app/api/routes/import_staging.py
backend/app/api/routes/half_day_imports.py
backend/app/api/routes/imports.py
backend/app/api/routes/people.py
backend/app/api/routes/schedule.py
backend/app/api/routes/auth.py
backend/app/api/routes/swaps.py
backend/app/api/routes/compliance.py
```

---

## Appendix A: Test Skip/Fixme Summary

| File | Marker | Reason |
|------|--------|--------|
| `import-stage-apply.spec.ts` | `test.skip` x4 | Need seeded DB with matching person records |
| `export-block.spec.ts` | `test.skip` x3 | Need seeded DB |
| `round-trip.spec.ts` | `test.skip` x1 (describe-level) | Need seeded DB with block 10 assignments |
| `acgme-violation-import.spec.ts` | `test.skip` x1 | Need seeded DB with matching person records |
| `rollback.spec.ts` | `test.fixme` x3 | Need seeded DB + operational rollback endpoint |

## Appendix B: NPM Scripts

```json
{
  "test:e2e": "npx playwright test",
  "test:e2e:ui": "npx playwright test --ui",
  "generate:test-fixtures": "npx tsx e2e/fixtures/generate-test-xlsx.ts",
  "generate:types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/api-generated.ts",
  "generate:types:check": "openapi-typescript http://localhost:8000/openapi.json -o /dev/stdout | diff - src/types/api-generated.ts"
}
```

## Appendix C: Auth Fixture Roles

```typescript
// e2e/fixtures/auth.fixture.ts
// Provides pre-authenticated Page objects:
//   adminPage       — admin@test.mil / TestPassword123!
//   coordinatorPage — coordinator@test.mil / TestPassword123!
//   facultyPage     — faculty@test.mil / TestPassword123!
//   residentPage    — resident@test.mil / TestPassword123!
```

## Appendix D: Block Template2 Format

```
Row 3:    Date headers (e.g., "2026-03-12", "2026-03-13", ...)
Row 8:    Column headers ("Name", "Date1", "Date2", ...)
Rows 9-69: Data rows
  Col E (5):    Person name ("Last, First")
  Col F+ (6+):  Activity code per day ("C", "NF", "LV", "FMIT", etc.)

Hidden sheets:
  __SYS_META__ (veryHidden): Cell A1 = JSON metadata
  __REF__ (veryHidden): Column A = valid rotation codes, Column B = valid activity codes
```
