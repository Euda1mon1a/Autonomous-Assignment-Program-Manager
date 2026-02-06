# Playwright Workflow Skill

> **Purpose:** Guide agents through Playwright test creation and CI integration
> **Phase:** Stabilization (Phase 2 of Hybrid QA Workflow)
> **Workflow:** `.claude/workflows/hybrid-frontend-qa.md`

---

## When to Use This Skill

Use Playwright when:
- ASTRONAUT has validated a feature works
- You need to encode a stable happy path
- You want regression protection in CI
- You need deterministic, fast tests

**Do NOT use Playwright for:**
- Exploring new features (use ASTRONAUT)
- Bug investigation (use ASTRONAUT)
- One-off validation (use ASTRONAUT)

---

## Quick Start

### 1. Bootstrap with Codegen

```bash
# Start recording user actions
npx playwright codegen http://localhost:3000/[route]

# Example: Record admin template creation
npx playwright codegen http://localhost:3000/admin/templates
```

This opens a browser and generates code as you interact.

### 2. Create Test File

```bash
# Create new test file
touch frontend/e2e/tests/[feature]/[feature].spec.ts
```

### 3. Refine Generated Code

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup: login, navigate, etc.
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
  });

  test('should perform primary action successfully', async ({ page }) => {
    // Arrange
    await page.goto('/admin/feature');

    // Act
    await page.fill('#input-field', 'Test Value');
    await page.click('button:has-text("Save")');

    // Assert
    await expect(page.locator('.toast-success')).toBeVisible();
    await expect(page.locator('.saved-item')).toContainText('Test Value');
  });
});
```

### 4. Run Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run specific test file
npx playwright test e2e/tests/feature/feature.spec.ts

# Run with UI for debugging
npm run test:e2e:ui

# Run in headed mode (see browser)
npx playwright test --headed
```

---

## Test Organization

```
frontend/e2e/
├── tests/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── logout.spec.ts
│   ├── schedule/
│   │   ├── view-schedule.spec.ts
│   │   └── edit-schedule.spec.ts
│   ├── admin/
│   │   ├── users.spec.ts
│   │   ├── templates.spec.ts
│   │   └── scheduling.spec.ts
│   └── [feature]/
│       └── [feature].spec.ts
├── pages/                    # Page Object Models
│   ├── LoginPage.ts
│   ├── SchedulePage.ts
│   └── AdminPage.ts
├── fixtures/                 # Test fixtures
│   ├── auth.fixture.ts       # Authenticated user setup
│   └── test-data.ts          # Shared test data
└── global-setup.ts           # One-time setup
```

---

## Page Object Model Pattern

### Define Page Object

```typescript
// e2e/pages/SchedulePage.ts
import { Page, Locator, expect } from '@playwright/test';

export class SchedulePage {
  readonly page: Page;
  readonly grid: Locator;
  readonly saveButton: Locator;
  readonly toast: Locator;

  constructor(page: Page) {
    this.page = page;
    this.grid = page.locator('.schedule-grid');
    this.saveButton = page.locator('button:has-text("Save")');
    this.toast = page.locator('.toast');
  }

  async goto() {
    await this.page.goto('/schedule');
  }

  async selectBlock(blockNumber: number) {
    await this.page.selectOption('#block-select', String(blockNumber));
  }

  async save() {
    await this.saveButton.click();
    await expect(this.toast).toBeVisible();
  }
}
```

### Use in Tests

```typescript
// e2e/tests/schedule/schedule.spec.ts
import { test, expect } from '@playwright/test';
import { SchedulePage } from '../../pages/SchedulePage';

test.describe('Schedule', () => {
  test('can view and edit schedule', async ({ page }) => {
    const schedulePage = new SchedulePage(page);

    await schedulePage.goto();
    await schedulePage.selectBlock(10);
    await expect(schedulePage.grid).toBeVisible();

    // ... make changes ...

    await schedulePage.save();
  });
});
```

---

## Authentication Fixture

```typescript
// e2e/fixtures/auth.fixture.ts
import { test as base } from '@playwright/test';

type AuthFixture = {
  adminPage: Page;
  userPage: Page;
};

export const test = base.extend<AuthFixture>({
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    await use(page);
    await context.close();
  },

  userPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Login as regular user
    await page.goto('/login');
    await page.fill('input[name="username"]', 'resident1');
    await page.fill('input[name="password"]', 'resident123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/my-schedule');

    await use(page);
    await context.close();
  },
});
```

---

## Common Patterns

### Wait for API Response

```typescript
// Wait for specific API call before asserting
const responsePromise = page.waitForResponse('**/api/schedule/**');
await page.click('button:has-text("Load")');
const response = await responsePromise;
expect(response.status()).toBe(200);
```

### Handle Loading States

```typescript
// Wait for loading to complete
await page.waitForSelector('.loading', { state: 'hidden' });
await expect(page.locator('.content')).toBeVisible();
```

### Screenshot on Failure

```typescript
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== testInfo.expectedStatus) {
    await page.screenshot({
      path: `screenshots/${testInfo.title}.png`,
      fullPage: true
    });
  }
});
```

### Accessibility Testing

```typescript
import AxeBuilder from '@axe-core/playwright';

test('should be accessible', async ({ page }) => {
  await page.goto('/schedule');

  const accessibilityResults = await new AxeBuilder({ page }).analyze();
  expect(accessibilityResults.violations).toEqual([]);
});
```

---

## CI Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/frontend-tests.yml
name: Frontend E2E Tests

on:
  push:
    paths:
      - 'frontend/**'

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps chromium

      - name: Run E2E tests
        run: cd frontend && npx playwright test --project=chromium

      - name: Upload test results
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

---

## Debugging

### Visual Debugging

```bash
# Open Playwright UI mode
npx playwright test --ui

# Run in headed mode (see browser)
npx playwright test --headed

# Slow down execution
npx playwright test --headed --slowmo=500
```

### Trace Viewer

```bash
# Run with tracing
npx playwright test --trace on

# View trace
npx playwright show-trace trace.zip
```

### Debug Mode

```bash
# Step through test with debugger
npx playwright test --debug
```

---

## Test Data

### Use Test Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Resident | resident1 | resident123 |
| Faculty | faculty1 | faculty123 |

### Test Data Available

- **People:** 45 (30 residents, 15 faculty)
- **Blocks:** 14 (0-13)
- **Activities:** 730 half-day slots
- **Academic Year:** 2025-07-01 to 2026-06-30

---

## Best Practices

1. **One assertion per test** (ideally)
2. **Use Page Objects** for reusable components
3. **Avoid flaky selectors** - prefer data-testid, roles, text
4. **Wait for stability** before asserting
5. **Keep tests independent** - no test should depend on another
6. **Use fixtures** for setup/teardown
7. **Name tests descriptively** - what should happen, not how

---

## Related Resources

| Resource | Location |
|----------|----------|
| Playwright Config | `frontend/playwright.config.ts` |
| E2E Tests | `frontend/e2e/` |
| Hybrid QA Workflow | `.claude/workflows/hybrid-frontend-qa.md` |
| ASTRONAUT Skill | `.claude/skills/astronaut/SKILL.md` |
| GUI Development | `.claude/workflows/gui-development.md` |

---

*Playwright: Fast, deterministic, regression-proof.*
