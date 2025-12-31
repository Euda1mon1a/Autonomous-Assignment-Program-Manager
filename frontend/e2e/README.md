***REMOVED*** E2E Testing Guide

Comprehensive Playwright E2E test suite for the Medical Residency Scheduler application.

***REMOVED******REMOVED*** Table of Contents

- [Overview](***REMOVED***overview)
- [Setup](***REMOVED***setup)
- [Running Tests](***REMOVED***running-tests)
- [Test Structure](***REMOVED***test-structure)
- [Writing Tests](***REMOVED***writing-tests)
- [Fixtures](***REMOVED***fixtures)
- [Utilities](***REMOVED***utilities)
- [CI/CD Integration](***REMOVED***cicd-integration)
- [Troubleshooting](***REMOVED***troubleshooting)

***REMOVED******REMOVED*** Overview

This E2E test suite uses Playwright to test the complete user workflow of the Medical Residency Scheduler application, including:

- **Authentication flows** - Login, logout, session management, password reset
- **Schedule management** - CRUD operations, drag-drop, filtering, conflicts
- **Swap workflows** - Creating, approving, rejecting, and rolling back swaps
- **ACGME compliance** - Work hour violations, supervision ratios, day-off rules
- **Resilience dashboard** - Defense levels, utilization, N-1 contingency, alerts

***REMOVED******REMOVED*** Setup

***REMOVED******REMOVED******REMOVED*** Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:3000`

***REMOVED******REMOVED******REMOVED*** Installation

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Install Playwright browsers
npx playwright install

***REMOVED*** Install system dependencies (Linux only)
npx playwright install-deps
```

***REMOVED******REMOVED******REMOVED*** Environment Variables

Create a `.env.test` file in the `frontend` directory:

```bash
PLAYWRIGHT_BASE_URL=http://localhost:3000
PLAYWRIGHT_API_URL=http://localhost:8000
CLEAN_AUTH_STATE=false  ***REMOVED*** Set to true to clean auth states after tests
```

***REMOVED******REMOVED*** Running Tests

***REMOVED******REMOVED******REMOVED*** All Tests

```bash
***REMOVED*** Run all tests
npm run test:e2e

***REMOVED*** Run with UI mode (recommended for development)
npm run test:e2e:ui

***REMOVED*** Run in headed mode (see browser)
npm run test:e2e:headed

***REMOVED*** Run in debug mode
npm run test:e2e:debug
```

***REMOVED******REMOVED******REMOVED*** Specific Test Suites

```bash
***REMOVED*** Authentication tests only
npx playwright test tests/auth

***REMOVED*** Schedule management tests only
npx playwright test tests/schedule

***REMOVED*** Swap flow tests only
npx playwright test tests/swap

***REMOVED*** Compliance tests only
npx playwright test tests/compliance

***REMOVED*** Resilience tests only
npx playwright test tests/resilience
```

***REMOVED******REMOVED******REMOVED*** Specific Browsers

```bash
***REMOVED*** Chromium only
npx playwright test --project=chromium

***REMOVED*** Firefox only
npx playwright test --project=firefox

***REMOVED*** WebKit (Safari) only
npx playwright test --project=webkit

***REMOVED*** Mobile Chrome
npx playwright test --project=mobile-chrome

***REMOVED*** Mobile Safari
npx playwright test --project=mobile-safari
```

***REMOVED******REMOVED******REMOVED*** Other Options

```bash
***REMOVED*** Run specific test file
npx playwright test tests/auth/login.spec.ts

***REMOVED*** Run tests matching a pattern
npx playwright test --grep "login"

***REMOVED*** Run tests in parallel (default)
npx playwright test --workers=4

***REMOVED*** Run tests sequentially
npx playwright test --workers=1

***REMOVED*** Update snapshots (for visual regression tests)
npx playwright test --update-snapshots
```

***REMOVED******REMOVED*** Test Structure

```
frontend/e2e/
├── fixtures/               ***REMOVED*** Test fixtures
│   ├── auth.fixture.ts    ***REMOVED*** Authentication contexts
│   ├── database.fixture.ts ***REMOVED*** Database seeding
│   └── schedule.fixture.ts ***REMOVED*** Schedule scenarios
├── tests/                 ***REMOVED*** Test files
│   ├── auth/             ***REMOVED*** Authentication tests
│   ├── schedule/         ***REMOVED*** Schedule management tests
│   ├── swap/             ***REMOVED*** Swap flow tests
│   ├── compliance/       ***REMOVED*** ACGME compliance tests
│   └── resilience/       ***REMOVED*** Resilience dashboard tests
├── utils/                ***REMOVED*** Utility functions
│   ├── test-helpers.ts   ***REMOVED*** Common test helpers
│   ├── api-mocks.ts      ***REMOVED*** API mocking utilities
│   └── selectors.ts      ***REMOVED*** Page object selectors
├── snapshots/            ***REMOVED*** Visual regression snapshots
├── test-results/         ***REMOVED*** Test results and artifacts
├── .auth/                ***REMOVED*** Stored authentication states
├── global-setup.ts       ***REMOVED*** Global setup (runs before all tests)
├── global-teardown.ts    ***REMOVED*** Global teardown (runs after all tests)
├── playwright.config.ts  ***REMOVED*** Playwright configuration
└── README.md            ***REMOVED*** This file
```

***REMOVED******REMOVED*** Writing Tests

***REMOVED******REMOVED******REMOVED*** Basic Test Example

```typescript
import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'admin@test.mil');
    await page.fill('input[name="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');

    // Wait for redirect
    await page.waitForURL('/dashboard');

    // Verify logged in
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });
});
```

***REMOVED******REMOVED******REMOVED*** Using Fixtures

```typescript
import { test, expect } from '../fixtures/auth.fixture';

test('should access admin panel', async ({ adminPage }) => {
  // adminPage is already authenticated as admin
  await adminPage.goto('/admin');

  await expect(adminPage.locator('h1')).toContainText('Admin Panel');
});
```

***REMOVED******REMOVED******REMOVED*** Using Test Helpers

```typescript
import { test, expect } from '@playwright/test';
import { waitForToast, clickButton } from '../utils/test-helpers';

test('should show success toast', async ({ page }) => {
  await page.goto('/schedule');

  await clickButton(page, 'Create Assignment');

  const toast = await waitForToast(page, 'Assignment created successfully');
  await expect(toast).toBeVisible();
});
```

***REMOVED******REMOVED******REMOVED*** Page Object Pattern

```typescript
import { test, expect } from '@playwright/test';
import { selectors } from '../utils/selectors';

test('should filter schedule by person', async ({ page }) => {
  await page.goto('/schedule');

  // Use centralized selectors
  await page.click(selectors.schedule.filterButton);
  await page.selectOption(selectors.schedule.personFilter, 'test-resident-001');
  await page.click(selectors.common.confirmButton);

  await expect(page.locator(selectors.schedule.assignment)).toHaveCount(5);
});
```

***REMOVED******REMOVED*** Fixtures

***REMOVED******REMOVED******REMOVED*** Authentication Fixture

Provides pre-authenticated page contexts for different user roles:

```typescript
import { test, expect } from '../fixtures/auth.fixture';

test('Admin can access settings', async ({ adminPage }) => {
  // Already authenticated as admin
  await adminPage.goto('/settings');
});

test('Faculty can view schedule', async ({ facultyPage }) => {
  // Already authenticated as faculty
  await facultyPage.goto('/schedule');
});

test('Resident can create swap', async ({ residentPage }) => {
  // Already authenticated as resident
  await residentPage.goto('/swaps/new');
});
```

***REMOVED******REMOVED******REMOVED*** Database Fixture

Provides database seeding and cleanup:

```typescript
import { test, expect } from '../fixtures/database.fixture';

test('should display seeded residents', async ({ page, db }) => {
  // Seed 10 residents
  await db.seedResidents(10);

  await page.goto('/residents');

  const rows = page.locator('table tbody tr');
  await expect(rows).toHaveCount(10);

  // Automatic cleanup after test
});
```

***REMOVED******REMOVED******REMOVED*** Schedule Fixture

Provides pre-configured schedule scenarios:

```typescript
import { test, expect } from '../fixtures/schedule.fixture';

test('should show empty schedule', async ({ page, scheduleHelper }) => {
  const scenario = await scheduleHelper.createEmptySchedule(7);

  await page.goto('/schedule');

  await expect(page.locator('[data-testid="schedule-empty-state"]')).toBeVisible();
});

test('should show conflicts', async ({ page, scheduleHelper }) => {
  const scenario = await scheduleHelper.createConflictingSchedule();

  await page.goto('/schedule');

  await expect(page.locator('[data-testid="conflict-indicator"]')).toBeVisible();
});
```

***REMOVED******REMOVED*** Utilities

***REMOVED******REMOVED******REMOVED*** Test Helpers

Common utility functions for testing:

- `waitForNetworkIdle(page)` - Wait for all network requests to finish
- `waitForAPICall(page, pattern)` - Wait for specific API call
- `waitForToast(page, message)` - Wait for toast notification
- `waitForLoading(page)` - Wait for loading spinner to disappear
- `fillByLabel(page, label, value)` - Fill input by label text
- `clickButton(page, text)` - Click button by text
- `dragAndDrop(page, source, target)` - Drag and drop element

***REMOVED******REMOVED******REMOVED*** API Mocks

Mock API responses for testing:

```typescript
import { createMocks } from '../utils/api-mocks';

test('should handle API error', async ({ page }) => {
  const mocks = createMocks(page);

  // Mock 500 error
  await mocks.errors.mock500('**/api/v1/schedule');

  await page.goto('/schedule');

  await expect(page.locator('[data-testid="error-message"]')).toContainText('Server error');
});
```

***REMOVED******REMOVED******REMOVED*** Selectors

Centralized selectors for maintainability:

```typescript
import { selectors } from '../utils/selectors';

// Instead of:
await page.click('button:has-text("Save")');

// Use:
await page.click(selectors.common.saveButton);
```

***REMOVED******REMOVED*** CI/CD Integration

***REMOVED******REMOVED******REMOVED*** GitHub Actions

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Start backend
        run: docker-compose up -d backend db redis

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/e2e/test-results/
```

***REMOVED******REMOVED******REMOVED*** Docker

Run tests in Docker:

```bash
docker run -it --rm \
  -v $(pwd):/app \
  -w /app/frontend \
  mcr.microsoft.com/playwright:v1.40.0 \
  npm run test:e2e
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Tests are flaky

- Increase timeouts in `playwright.config.ts`
- Add explicit waits: `await page.waitForLoadState('networkidle')`
- Use `test.setTimeout(60000)` for slow tests
- Check for race conditions

***REMOVED******REMOVED******REMOVED*** Authentication fails

- Verify backend is running on correct port
- Check test users are seeded correctly
- Delete `.auth` directory and re-run setup
- Check environment variables

***REMOVED******REMOVED******REMOVED*** Visual regression tests fail

- Update snapshots: `npx playwright test --update-snapshots`
- Check for timing issues (animations, loading states)
- Increase `threshold` in `playwright.config.ts`

***REMOVED******REMOVED******REMOVED*** Backend not accessible

- Verify backend is running: `curl http://localhost:8000/health`
- Check Docker containers: `docker-compose ps`
- Check environment variables
- Increase `webServer.timeout` in config

***REMOVED******REMOVED******REMOVED*** Slow test execution

- Run tests in parallel: `npx playwright test --workers=4`
- Use authentication fixtures (pre-authenticated)
- Skip unnecessary visual regression tests
- Use `test.skip()` for tests not relevant to current work

***REMOVED******REMOVED******REMOVED*** Debug specific test

```bash
***REMOVED*** Run with debug mode
npx playwright test tests/auth/login.spec.ts --debug

***REMOVED*** Use headed mode
npx playwright test tests/auth/login.spec.ts --headed

***REMOVED*** Use UI mode (recommended)
npx playwright test --ui
```

***REMOVED******REMOVED*** Best Practices

1. **Use fixtures** - Pre-authenticate users, seed database
2. **Use selectors** - Centralize selectors in `selectors.ts`
3. **Use helpers** - Reuse common functions from `test-helpers.ts`
4. **Test isolation** - Each test should be independent
5. **Avoid hardcoded waits** - Use `waitFor*` helpers instead of `page.waitForTimeout()`
6. **Page Object Model** - Encapsulate page interactions
7. **Meaningful assertions** - Use descriptive error messages
8. **Visual regression** - Use for critical UI components only
9. **Accessibility** - Test keyboard navigation and screen readers
10. **Mobile testing** - Test responsive behavior

***REMOVED******REMOVED*** Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
- [Project CLAUDE.md](../../CLAUDE.md) - Project guidelines

***REMOVED******REMOVED*** Support

For issues or questions:

1. Check this README
2. Check [Playwright documentation](https://playwright.dev)
3. Review existing test examples
4. Ask in team chat or create GitHub issue
