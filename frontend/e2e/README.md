# E2E Testing Guide

Comprehensive Playwright E2E test suite for the Medical Residency Scheduler application.

## Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Utilities](#utilities)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

This E2E test suite uses Playwright to test the complete user workflow of the Medical Residency Scheduler application, including:

- **Authentication flows** - Login, logout, session management, password reset
- **Schedule management** - CRUD operations, drag-drop, filtering, conflicts
- **Swap workflows** - Creating, approving, rejecting, and rolling back swaps
- **ACGME compliance** - Work hour violations, supervision ratios, day-off rules
- **Resilience dashboard** - Defense levels, utilization, N-1 contingency, alerts

## Setup

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:3000`

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Install Playwright browsers
npx playwright install

# Install system dependencies (Linux only)
npx playwright install-deps
```

### Environment Variables

Create a `.env.test` file in the `frontend` directory:

```bash
PLAYWRIGHT_BASE_URL=http://localhost:3000
PLAYWRIGHT_API_URL=http://localhost:8000
CLEAN_AUTH_STATE=false  # Set to true to clean auth states after tests
```

## Running Tests

### All Tests

```bash
# Run all tests
npm run test:e2e

# Run with UI mode (recommended for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run in debug mode
npm run test:e2e:debug
```

### Specific Test Suites

```bash
# Authentication tests only
npx playwright test tests/auth

# Schedule management tests only
npx playwright test tests/schedule

# Swap flow tests only
npx playwright test tests/swap

# Compliance tests only
npx playwright test tests/compliance

# Resilience tests only
npx playwright test tests/resilience
```

### Specific Browsers

```bash
# Chromium only
npx playwright test --project=chromium

# Firefox only
npx playwright test --project=firefox

# WebKit (Safari) only
npx playwright test --project=webkit

# Mobile Chrome
npx playwright test --project=mobile-chrome

# Mobile Safari
npx playwright test --project=mobile-safari
```

### Other Options

```bash
# Run specific test file
npx playwright test tests/auth/login.spec.ts

# Run tests matching a pattern
npx playwright test --grep "login"

# Run tests in parallel (default)
npx playwright test --workers=4

# Run tests sequentially
npx playwright test --workers=1

# Update snapshots (for visual regression tests)
npx playwright test --update-snapshots
```

## Test Structure

```
frontend/e2e/
├── fixtures/               # Test fixtures
│   ├── auth.fixture.ts    # Authentication contexts
│   ├── database.fixture.ts # Database seeding
│   └── schedule.fixture.ts # Schedule scenarios
├── tests/                 # Test files
│   ├── auth/             # Authentication tests
│   ├── schedule/         # Schedule management tests
│   ├── swap/             # Swap flow tests
│   ├── compliance/       # ACGME compliance tests
│   └── resilience/       # Resilience dashboard tests
├── utils/                # Utility functions
│   ├── test-helpers.ts   # Common test helpers
│   ├── api-mocks.ts      # API mocking utilities
│   └── selectors.ts      # Page object selectors
├── snapshots/            # Visual regression snapshots
├── test-results/         # Test results and artifacts
├── .auth/                # Stored authentication states
├── global-setup.ts       # Global setup (runs before all tests)
├── global-teardown.ts    # Global teardown (runs after all tests)
├── playwright.config.ts  # Playwright configuration
└── README.md            # This file
```

## Writing Tests

### Basic Test Example

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

### Using Fixtures

```typescript
import { test, expect } from '../fixtures/auth.fixture';

test('should access admin panel', async ({ adminPage }) => {
  // adminPage is already authenticated as admin
  await adminPage.goto('/admin');

  await expect(adminPage.locator('h1')).toContainText('Admin Panel');
});
```

### Using Test Helpers

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

### Page Object Pattern

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

## Fixtures

### Authentication Fixture

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

### Database Fixture

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

### Schedule Fixture

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

## Utilities

### Test Helpers

Common utility functions for testing:

- `waitForNetworkIdle(page)` - Wait for all network requests to finish
- `waitForAPICall(page, pattern)` - Wait for specific API call
- `waitForToast(page, message)` - Wait for toast notification
- `waitForLoading(page)` - Wait for loading spinner to disappear
- `fillByLabel(page, label, value)` - Fill input by label text
- `clickButton(page, text)` - Click button by text
- `dragAndDrop(page, source, target)` - Drag and drop element

### API Mocks

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

### Selectors

Centralized selectors for maintainability:

```typescript
import { selectors } from '../utils/selectors';

// Instead of:
await page.click('button:has-text("Save")');

// Use:
await page.click(selectors.common.saveButton);
```

## CI/CD Integration

### GitHub Actions

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

### Docker

Run tests in Docker:

```bash
docker run -it --rm \
  -v $(pwd):/app \
  -w /app/frontend \
  mcr.microsoft.com/playwright:v1.40.0 \
  npm run test:e2e
```

## Troubleshooting

### Tests are flaky

- Increase timeouts in `playwright.config.ts`
- Add explicit waits: `await page.waitForLoadState('networkidle')`
- Use `test.setTimeout(60000)` for slow tests
- Check for race conditions

### Authentication fails

- Verify backend is running on correct port
- Check test users are seeded correctly
- Delete `.auth` directory and re-run setup
- Check environment variables

### Visual regression tests fail

- Update snapshots: `npx playwright test --update-snapshots`
- Check for timing issues (animations, loading states)
- Increase `threshold` in `playwright.config.ts`

### Backend not accessible

- Verify backend is running: `curl http://localhost:8000/health`
- Check Docker containers: `docker-compose ps`
- Check environment variables
- Increase `webServer.timeout` in config

### Slow test execution

- Run tests in parallel: `npx playwright test --workers=4`
- Use authentication fixtures (pre-authenticated)
- Skip unnecessary visual regression tests
- Use `test.skip()` for tests not relevant to current work

### Debug specific test

```bash
# Run with debug mode
npx playwright test tests/auth/login.spec.ts --debug

# Use headed mode
npx playwright test tests/auth/login.spec.ts --headed

# Use UI mode (recommended)
npx playwright test --ui
```

## Best Practices

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

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
- [Project CLAUDE.md](../../CLAUDE.md) - Project guidelines

## Support

For issues or questions:

1. Check this README
2. Check [Playwright documentation](https://playwright.dev)
3. Review existing test examples
4. Ask in team chat or create GitHub issue
