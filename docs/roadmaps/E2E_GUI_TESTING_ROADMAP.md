# E2E GUI Testing Roadmap

> **Created:** 2026-02-25
> **Source:** Gemini Pro 3.1 extended-thinking analysis of full test suite + Claude synthesis
> **Prompt:** `docs/prompts/E2E_GUI_TESTING_REFINEMENT.md`
> **Master Priority List:** Item #34
> **Status:** PLANNING

---

## Current State

| Metric | Value |
|--------|-------|
| Spec files | 34 (44 including root-level duplicates) |
| Test cases | ~580-700 |
| Skipped (`test.skip`) | 9 (need seeded DB) |
| Blocked (`test.fixme`) | 3 (rollback.spec.ts) |
| Pages with coverage | 13 of 53 (25%) |
| Pages without coverage | 31 (58%) — including 20+ admin pages |
| Assertion depth | Mostly shallow (`toBeVisible`) |
| Infrastructure | Mature (fixtures, POM, selectors, helpers, xlsx utils) |

**Key Insight:** 580 tests creates a false sense of security when most assert visibility rather than functional correctness. A schedule could silently corrupt and every test passes.

---

## Strategic Principles

1. **Exhaustiveness is the enemy of effectiveness.** Focus on workflows where silent failures cause patient safety or accreditation harm.
2. **Assert DOM against API payload**, not just visibility. If the API says 15 violations, the DOM must show 15 cards.
3. **Native-first execution.** All infrastructure targets Apple Silicon macOS with local Postgres/Redis — no Docker required.
4. **Real backend, not mocks.** Mock only for negative testing (503s, timeouts). The solver, parser, and validator are what we're actually testing.
5. **Hybrid POM:** Page Objects for multi-step mutations (wizards, import flows). Direct selectors for read-only dashboards.

---

## Phase 0: Unblock (1 day)

**Goal:** Make all 12 blocked tests runnable.

### 0a. Backend Dev Seed Endpoint

Create a protected FastAPI endpoint that deterministically seeds the test database.

**File:** `backend/app/api/routes/dev.py`

```python
# Only available when ENV=test or ALLOW_DEV_SEED=true
POST /api/v1/dev/seed?scenario=e2e_baseline
```

**Seeds:**
- 17 synthetic residents (CPT Doe-01 through CPT Doe-17, PGY 1-3)
- 13 synthetic faculty (Dr. Faculty-A through Dr. Faculty-M)
- Block 10 half-day assignments (28 days, rotating codes)
- Activity codes (C, NF, FMIT, LV, etc.)
- Uses `random.seed(42)` for deterministic UUIDs

**Implementation:** Python function using ORM (not raw SQL) — respects Alembic schema.

**Runtime:** Native macOS — `uvicorn` + local Postgres. No Docker.

### 0b. Playwright Global Setup

**File:** `frontend/e2e/global-setup.ts`

```typescript
export default async function globalSetup() {
  const res = await fetch('http://localhost:8000/api/v1/dev/seed?scenario=e2e_baseline', { method: 'POST' });
  if (!res.ok) throw new Error(`DB seed failed: ${res.status}`);
  process.env.E2E_HAS_SEEDED_DATA = 'true';
}
```

**Config update:** Add `globalSetup: require.resolve('./e2e/global-setup.ts')` to `playwright.config.ts`.

### 0c. Unblock rollback.spec.ts

Refactor from shared `let batchUrl` across tests → single test with `test.step()`:

```typescript
test('Full import → apply → rollback workflow', async ({ adminPage }) => {
  let batchId: string;
  await test.step('Upload, stage, and create draft', async () => { /* ... */ });
  await test.step('Apply batch', async () => { /* ... */ });
  await test.step('Rollback and verify status', async () => { /* ... */ });
  await test.step('Verify assignments reverted via API', async () => { /* ... */ });
});
```

Replace `test.fixme()` with `test.skip(() => !process.env.E2E_HAS_SEEDED_DATA)`.

**Outcome:** 9 skips + 3 fixmes → 0 blocked when seeded DB is available.

---

## Phase 1: Critical Safety (3-5 days)

**Goal:** Cover the 4 pages where silent failures cause patient safety or accreditation harm.

### 1a. `/compliance` — ACGME Compliance Dashboard

**Risk:** If an 80-hour violation exists in the DB but doesn't render, the program risks probation.

**File:** `e2e/tests/compliance/compliance-dashboard.spec.ts`

**Tests (deep assertions):**
- [ ] Summary renders with numeric metrics matching API payload
- [ ] Violation cards show correct severity class (`text-red` for 80-hour)
- [ ] Person filter triggers API call, card count matches response `violations.length`
- [ ] Export compliance report downloads file with correct filename
- [ ] 1-in-7 and supervision ratio widgets display actual numbers (not just visible)

**Selectors:** Already exist in `selectors.compliance.*`

### 1b. `/daily-manifest` — Today's Assignments

**Risk:** Resident dropped from view → clinic goes unstaffed.

**File:** `e2e/tests/daily-manifest.spec.ts`

**New selectors needed:** `dailyManifest.container`, `dailyManifest.residentCount`, `dailyManifest.rotationFilter`, `dailyManifest.assignmentRow`, `dailyManifest.coverageGapAlert`

**Tests:**
- [ ] Rendered row count matches header resident count (DOM ↔ DOM consistency)
- [ ] Rotation filter reduces rows mathematically (filteredCount < totalCount > 0)
- [ ] Coverage gap alerts visible when gaps exist in seeded data
- [ ] Date picker changes rendered assignments

### 1c. `/call-hub` — On-Call Schedule

**Risk:** Wrong doctor on call → emergency pager misrouted.

**File:** `e2e/tests/call-hub.spec.ts`

**New selectors needed:** `callHub.todayOnCall`, `callHub.weekView`, `callHub.assignmentCard`, `callHub.pagerContact`

**Tests:**
- [ ] Today's on-call name rendered
- [ ] Week view shows 7 days of call assignments
- [ ] On-call assignment cards show correct time windows

### 1d. `/conflicts` — Schedule Conflict Viewer

**Risk:** Overlapping assignments undetected → two residents think they're off.

**File:** `e2e/tests/conflicts.spec.ts`

**Tests:**
- [ ] Conflict list renders when seeded data has overlaps
- [ ] Conflict detail shows both conflicting assignments
- [ ] Severity indicator matches conflict type

---

## Phase 2: Data Mutation Safety (3-5 days)

**Goal:** Cover the 3 pages with highest database mutation risk.

### 2a. `/admin/scheduling` — Schedule Generation Engine

**Risk:** Frontend passes wrong constraint weights → entire MTF schedule wrong.

**File:** `e2e/tests/admin/scheduling.spec.ts`

**Tests (60s timeout for solver):**
- [ ] Page renders with block selector and ACGME toggle
- [ ] Generate button triggers `POST /schedule/generate`, intercept response
- [ ] Progress indicator visible during solve
- [ ] Result metrics in DOM match response payload (`assignments_created`, solver status)
- [ ] ACGME validation runs on generated output

### 2b. `/admin/block-import` — 4-Step Import Wizard

**Risk:** State bleed between wizard steps → silent DB corruption.

**File:** `e2e/tests/admin/block-import.spec.ts`

**Use Page Object:** `AdminBlockImportPage` (complex wizard state machine)

**Tests (single test with `test.step()`):**
- [ ] Step 1: Upload file, verify preview renders
- [ ] Step 2: Review staged data, verify counts
- [ ] Step 3: Apply or reject, verify status change
- [ ] Step 4: Verify assignments written via API query

### 2c. `/admin/fmit/import` — FMIT Faculty Import

**Risk:** Fuzzy matching assigns wrong attending to Inpatient.

**File:** `e2e/tests/admin/fmit-import.spec.ts`

**Tests:**
- [ ] Upload FMIT schedule file
- [ ] Fuzzy match confidence displayed for each faculty name
- [ ] Low-confidence matches highlighted with warning
- [ ] Apply writes correct faculty-week assignments

---

## Phase 3: High-Traffic Pages (2-3 days)

**Goal:** Cover the pages residents and coordinators use daily.

### 3a. `/my-schedule` — Personal Schedule (Resident)

**File:** `e2e/tests/my-schedule.spec.ts`

**Use `residentPage` fixture** (not admin).

**Tests:**
- [ ] Schedule renders for logged-in resident
- [ ] Correct block assignments shown (match API)
- [ ] Navigation between blocks works
- [ ] No other residents' data visible (access control)

### 3b. `/import/[id]` — Batch Detail / Apply

**File:** `e2e/tests/import/batch-detail.spec.ts`

**Tests:**
- [ ] Batch detail renders with correct status badge
- [ ] Staged assignments table matches API preview response
- [ ] Apply button triggers correct API call
- [ ] Rollback controls visible on applied batch, hidden on draft

### 3c. `/rotations` — Rotation Management

**File:** `e2e/tests/rotations.spec.ts`

**Tests:**
- [ ] Rotation list renders
- [ ] Create rotation (if admin)
- [ ] Edit rotation name
- [ ] Delete shows confirmation (protect against accidental deletion of FMIT)

---

## Phase 4: Deepen Existing Tests (2-3 days)

**Goal:** Upgrade shallow `toBeVisible` assertions in existing specs to meaningful DOM↔API assertions.

### 4a. `resilience-hub.spec.ts` (67 tests)
- [ ] Defense level badge text matches API `defense_level` value
- [ ] Utilization percentage in DOM matches API `utilization_value`
- [ ] Burnout Rt number matches API payload (2 decimal places)

### 4b. `schedule-management.spec.ts` (40 tests)
- [ ] Assignment card count matches API response `assignments.length`
- [ ] Block navigation updates URL params AND re-fetches data
- [ ] Filter by person reduces visible cards to match API filtered count

### 4c. `swap-workflow.spec.ts` (20 tests)
- [ ] Swap creation triggers API call, response matches UI confirmation
- [ ] ACGME pre-check fires before swap approval (intercept validation response)

### 4d. `templates.spec.ts` (36 tests)
- [ ] Create template → verify it appears in list (API + DOM)
- [ ] Delete template → verify removal from list
- [ ] Edit template → verify changes persisted on reload

---

## Phase 5: CI Configuration (1 day)

**Goal:** Make E2E runnable in automated environments (native macOS, no Docker).

**File:** `frontend/playwright.config.ci.ts`

```typescript
export default defineConfig({
  testDir: './e2e/tests',
  fullyParallel: false,     // Sequential for shared DB
  workers: 1,               // Single worker for DB isolation
  retries: 2,
  reporter: [['html', { open: 'never' }], ['junit', { outputFile: 'test-results/e2e-junit.xml' }]],
  globalSetup: require.resolve('./e2e/global-setup.ts'),
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    { command: 'cd ../backend && uvicorn app.main:app --port 8000', url: 'http://localhost:8000/api/v1/health', reuseExistingServer: true, timeout: 30_000 },
    { command: 'npm run dev', url: 'http://localhost:3000', reuseExistingServer: true, timeout: 30_000 },
  ],
});
```

**Native runtime requirements:**
- PostgreSQL 15 (via Homebrew: `brew services start postgresql@15`)
- Redis (via Homebrew: `brew services start redis`)
- Python 3.11+ venv with backend deps
- Node 20+ with frontend deps
- No Docker containers needed

**NPM script:** `"test:e2e:ci": "npx playwright test --config=playwright.config.ci.ts"`

---

## Execution Order

```
Phase 0 (Unblock)           ─── 1 day    ─── Enables all other phases
Phase 1 (Critical Safety)   ─── 3-5 days ─── /compliance, /daily-manifest, /call-hub, /conflicts
Phase 2 (Mutation Safety)   ─── 3-5 days ─── /admin/scheduling, /admin/block-import, /admin/fmit/import
Phase 3 (High-Traffic)      ─── 2-3 days ─── /my-schedule, /import/[id], /rotations
Phase 4 (Deepen Existing)   ─── 2-3 days ─── Upgrade assertions in 4 existing specs
Phase 5 (CI Config)         ─── 1 day    ─── Native macOS CI-ready config
```

**Total estimated:** 12-17 days

---

## New Infrastructure Needed

| Item | File | Phase |
|------|------|-------|
| Dev seed endpoint | `backend/app/api/routes/dev.py` | 0 |
| Global setup | `frontend/e2e/global-setup.ts` | 0 |
| `AdminBlockImportPage` POM | `frontend/e2e/pages/AdminBlockImportPage.ts` | 2 |
| `dailyManifest` selectors | `frontend/e2e/utils/selectors.ts` | 1 |
| `callHub` selectors | `frontend/e2e/utils/selectors.ts` | 1 |
| `conflicts` selectors | `frontend/e2e/utils/selectors.ts` | 1 |
| CI playwright config | `frontend/playwright.config.ci.ts` | 5 |
| DB snapshot/restore endpoints | `backend/app/api/routes/dev.py` | 0 (optional) |

---

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Native-first, no Docker** | Apple Silicon performance, developer preference, reduced complexity |
| **Real backend over mocks** | Testing the actual solver/parser/validator is the point of E2E |
| **Hybrid POM** | Page Objects for wizards, direct selectors for dashboards — minimize maintenance tax |
| **`test.step()` over shared state** | Prevents cascading failures from shared `let` variables across tests |
| **Dev seed endpoint via ORM** | Respects Alembic schema, deterministic via `random.seed(42)`, < 2s execution |
| **Sequential workers for CI** | Shared DB prevents parallel mutation races |

---

## Pages Explicitly Deferred

These 20+ pages are LOW priority and should not receive E2E coverage before Phases 0-5 are complete:

| Page | Reason |
|------|--------|
| `/admin/debugger` | Developer tool, not user-facing |
| `/admin/schema` | Developer tool |
| `/admin/labs` | Experimental |
| `/admin/game-theory` | Research |
| `/admin/legacy` | Deprecated |
| `/admin/pec` | Low usage |
| `/solver-viz` | Developer visualization |
| `/help` | Static content |
| `/admin/block-explorer` | Read-only explorer |
| `/admin/credentials` | Low mutation risk |
| `/admin/resilience-overseer` | Covered by resilience-hub tests |
| `/wellness` | Future feature |
| `/proxy-coverage` | Future feature |
| `/command-center` | Future feature |
| `/settings` | Low risk (profile/password) |
| `/activities` | Admin CRUD, low risk |
| `/import-export` | Redundant with `/hub/import-export` |
