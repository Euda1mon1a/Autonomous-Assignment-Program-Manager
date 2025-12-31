***REMOVED*** End-to-End (E2E) Testing Guide

***REMOVED******REMOVED*** Overview

End-to-end tests verify complete user workflows from the browser perspective using Playwright. These tests ensure the frontend and backend work together correctly from a user's perspective.

***REMOVED******REMOVED*** Setup

***REMOVED******REMOVED******REMOVED*** Install Playwright

```bash
cd frontend
npm install @playwright/test
npx playwright install
```

***REMOVED******REMOVED******REMOVED*** Configuration

Playwright configuration is in `playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

***REMOVED******REMOVED*** Running E2E Tests

***REMOVED******REMOVED******REMOVED*** Run All Tests

```bash
cd frontend
npm run test:e2e
```

***REMOVED******REMOVED******REMOVED*** Run Specific Test File

```bash
npx playwright test schedule-management.spec.ts
```

***REMOVED******REMOVED******REMOVED*** Run in UI Mode (Interactive)

```bash
npx playwright test --ui
```

***REMOVED******REMOVED******REMOVED*** Run in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

***REMOVED******REMOVED******REMOVED*** Generate Test Report

```bash
npx playwright show-report
```

***REMOVED******REMOVED*** Test Structure

***REMOVED******REMOVED******REMOVED*** Test File Organization

```
frontend/tests/e2e/
├── schedule-management.spec.ts
├── swap-request.spec.ts
├── compliance-dashboard.spec.ts
├── user-authentication.spec.ts
├── reporting.spec.ts
└── settings.spec.ts
```

***REMOVED******REMOVED******REMOVED*** Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpass');
    await page.click('button[type="submit"]');
  });

  test('should perform action', async ({ page }) => {
    // Navigate
    await page.goto('/feature');

    // Interact
    await page.click('[data-testid="action-button"]');

    // Assert
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
  });
});
```

***REMOVED******REMOVED*** Writing E2E Tests

***REMOVED******REMOVED******REMOVED*** 1. Use Data Test IDs

Always use `data-testid` attributes for reliable selectors:

```tsx
// Component
<button data-testid="create-assignment-button">
  Create Assignment
</button>

// Test
await page.click('[data-testid="create-assignment-button"]');
```

***REMOVED******REMOVED******REMOVED*** 2. Wait for Elements

Use Playwright's auto-waiting features:

```typescript
// Good - Auto-waits for element
await page.click('[data-testid="button"]');

// Also good - Explicit wait
await page.waitForSelector('[data-testid="result"]');

// Bad - Hard-coded sleep
await page.waitForTimeout(1000); // Avoid!
```

***REMOVED******REMOVED******REMOVED*** 3. Handle Navigation

```typescript
// Wait for navigation
await Promise.all([
  page.waitForNavigation(),
  page.click('[data-testid="submit"]')
]);

// Check URL
await expect(page).toHaveURL(/\/dashboard/);
```

***REMOVED******REMOVED******REMOVED*** 4. Form Interactions

```typescript
// Fill text input
await page.fill('[name="email"]', 'user@example.com');

// Select dropdown
await page.selectOption('[name="role"]', 'admin');

// Check checkbox
await page.check('[name="remember"]');

// Upload file
await page.setInputFiles('[name="file"]', 'path/to/file.csv');
```

***REMOVED******REMOVED******REMOVED*** 5. Assertions

```typescript
// Element visibility
await expect(page.locator('[data-testid="message"]')).toBeVisible();

// Text content
await expect(page.locator('h1')).toContainText('Dashboard');

// Element count
await expect(page.locator('.item')).toHaveCount(5);

// Attribute value
await expect(page.locator('input')).toHaveValue('text');

// URL
await expect(page).toHaveURL('http://localhost:3000/dashboard');
```

***REMOVED******REMOVED******REMOVED*** 6. Handle Async Operations

```typescript
// Wait for API response
await page.waitForResponse(
  response => response.url().includes('/api/schedule') && response.status() === 200
);

// Wait for network idle
await page.waitForLoadState('networkidle');
```

***REMOVED******REMOVED*** Test Patterns

***REMOVED******REMOVED******REMOVED*** Authentication Flow

```typescript
test.describe('Authenticated Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('should access protected route', async ({ page }) => {
    await page.goto('/schedule');
    await expect(page.locator('[data-testid="schedule-calendar"]')).toBeVisible();
  });
});
```

***REMOVED******REMOVED******REMOVED*** File Downloads

```typescript
test('should download report', async ({ page }) => {
  await page.goto('/reports');

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('[data-testid="export-pdf-button"]')
  ]);

  // Verify download
  expect(download.suggestedFilename()).toContain('.pdf');

  // Save to file
  await download.saveAs('/path/to/save/file.pdf');
});
```

***REMOVED******REMOVED******REMOVED*** Modal Dialogs

```typescript
test('should confirm deletion', async ({ page }) => {
  await page.goto('/schedule');

  // Click delete button
  await page.click('[data-testid="delete-button"]');

  // Handle modal
  await expect(page.locator('[data-testid="confirm-dialog"]')).toBeVisible();
  await page.click('[data-testid="confirm-delete-button"]');

  // Verify deletion
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
});
```

***REMOVED******REMOVED******REMOVED*** Multi-Step Workflows

```typescript
test('should complete schedule creation workflow', async ({ page }) => {
  // Step 1: Navigate
  await page.goto('/schedule/create');

  // Step 2: Fill form
  await page.fill('[name="start_date"]', '2024-01-01');
  await page.fill('[name="end_date"]', '2024-01-31');

  // Step 3: Select options
  await page.click('[data-testid="select-residents"]');
  await page.click('[data-testid="resident-1"]');
  await page.click('[data-testid="resident-2"]');

  // Step 4: Submit
  await page.click('button[type="submit"]');

  // Step 5: Verify
  await expect(page).toHaveURL(/\/schedule\/\d+/);
  await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
});
```

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Use Page Objects

Organize complex pages into page objects:

```typescript
// pages/schedule.page.ts
export class SchedulePage {
  constructor(private page: Page) {}

  async navigateTo() {
    await this.page.goto('/schedule');
  }

  async createAssignment(data: AssignmentData) {
    await this.page.click('[data-testid="add-assignment-button"]');
    await this.page.fill('[name="date"]', data.date);
    await this.page.selectOption('[name="rotation"]', data.rotation);
    await this.page.click('button[type="submit"]');
  }

  async getAssignmentCount() {
    return await this.page.locator('[data-testid="assignment-item"]').count();
  }
}

// Test
test('should create assignment', async ({ page }) => {
  const schedulePage = new SchedulePage(page);
  await schedulePage.navigateTo();
  await schedulePage.createAssignment({
    date: '2024-01-15',
    rotation: 'Clinic',
  });
  expect(await schedulePage.getAssignmentCount()).toBe(1);
});
```

***REMOVED******REMOVED******REMOVED*** 2. Use Fixtures for Setup

```typescript
import { test as base } from '@playwright/test';

type Fixtures = {
  authenticatedPage: Page;
};

const test = base.extend<Fixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');

    // Use authenticated page
    await use(page);
  },
});

test('should view dashboard', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/dashboard');
  // Already authenticated!
});
```

***REMOVED******REMOVED******REMOVED*** 3. Use Soft Assertions

```typescript
test('should validate form fields', async ({ page }) => {
  await page.goto('/form');

  // Continue even if some assertions fail
  await expect.soft(page.locator('[name="name"]')).toBeVisible();
  await expect.soft(page.locator('[name="email"]')).toBeVisible();
  await expect.soft(page.locator('[name="phone"]')).toBeVisible();

  // All failures reported at end
});
```

***REMOVED******REMOVED******REMOVED*** 4. Use Test Tags

```typescript
test('should load quickly', { tag: '@smoke' }, async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('h1')).toBeVisible();
});

test('should handle large dataset', { tag: '@slow' }, async ({ page }) => {
  // Slow test
});
```

Run specific tags:
```bash
npx playwright test --grep @smoke
```

***REMOVED******REMOVED******REMOVED*** 5. Mobile Testing

```typescript
test.use({ ...devices['iPhone 12'] });

test('should work on mobile', async ({ page }) => {
  await page.goto('/schedule');
  // Test mobile-specific interactions
  await page.click('[data-testid="mobile-menu"]');
});
```

***REMOVED******REMOVED*** Debugging Tests

***REMOVED******REMOVED******REMOVED*** Debug Mode

```bash
npx playwright test --debug
```

***REMOVED******REMOVED******REMOVED*** Trace Viewer

```typescript
// Record trace
test('should trace', async ({ page, context }) => {
  await context.tracing.start({ screenshots: true, snapshots: true });

  // Test code

  await context.tracing.stop({ path: 'trace.zip' });
});
```

View trace:
```bash
npx playwright show-trace trace.zip
```

***REMOVED******REMOVED******REMOVED*** Screenshots

```typescript
// Take screenshot on failure
test('should take screenshot', async ({ page }) => {
  await page.goto('/schedule');

  await page.screenshot({ path: 'screenshot.png' });
});
```

***REMOVED******REMOVED******REMOVED*** Video Recording

```typescript
// playwright.config.ts
use: {
  video: 'on-first-retry',
}
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
        run: |
          cd frontend
          npm ci
      - name: Install Playwright
        run: |
          cd frontend
          npx playwright install --with-deps
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

***REMOVED******REMOVED*** Coverage and Metrics

***REMOVED******REMOVED******REMOVED*** Test Coverage Matrix

| Feature | Smoke Tests | Full Tests | Mobile Tests |
|---------|------------|------------|--------------|
| Authentication | ✅ | ✅ | ✅ |
| Schedule Management | ✅ | ✅ | ⚠️ |
| Swap Requests | ✅ | ✅ | ❌ |
| Compliance Dashboard | ⚠️ | ✅ | ❌ |
| Reporting | ⚠️ | ✅ | ❌ |

***REMOVED******REMOVED******REMOVED*** Performance Metrics

Monitor test execution times:

```bash
npx playwright test --reporter=json > report.json
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Tests Fail in CI but Pass Locally

**Problem:** Different environments.

**Solution:**
- Use consistent Node versions
- Check for timezone issues
- Ensure database state is clean
- Add explicit waits

***REMOVED******REMOVED******REMOVED*** Tests Are Flaky

**Problem:** Timing issues.

**Solution:**
- Use auto-waiting features
- Avoid `page.waitForTimeout()`
- Use `waitForLoadState('networkidle')`
- Increase timeout for slow operations

***REMOVED******REMOVED******REMOVED*** Element Not Found

**Problem:** Selector doesn't match.

**Solution:**
- Use data-testid attributes
- Check element is visible
- Wait for element to appear
- Use Playwright Inspector

***REMOVED******REMOVED*** Next Steps

- [Integration Testing Guide](./integration-testing-guide.md)
- [Test Scenarios Catalog](./test-scenarios.md)
- [Component Testing](../development/COMPONENT_TESTING.md)
