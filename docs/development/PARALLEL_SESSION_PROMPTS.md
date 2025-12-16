# Parallel Session Prompts - Round 10

**Date**: December 16, 2024
**Terminals**: 5 Opus 4.5 instances
**Coordinator**: Comet Assistant

---

## Pre-Session Checklist

Before launching terminals:
1. Ensure all terminals use unique branch names
2. Verify no file overlap between assignments
3. Set merge order expectations

---

## Terminal 1: Opus-APIFix

**Branch**: `claude/opus-api-fix-r10`
**Priority**: CRITICAL
**Duration**: ~30 min

### Prompt

```
You are Opus-APIFix. Your mission is to fix a critical API endpoint bug in the frontend.

## Context

The API client in `frontend/src/lib/api.ts` sets baseURL to include `/api`:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
```

This means all endpoint paths should NOT include `/api` prefix. However, some hooks incorrectly use `/api/...` causing double prefixing (e.g., `/api/api/assignments`).

## Your Exclusive Files

ONLY modify these files:
- `frontend/src/lib/hooks.ts`
- `frontend/src/lib/api.ts` (if needed)

DO NOT touch any other files.

## Task

1. Read `frontend/src/lib/api.ts` to confirm baseURL configuration
2. Read `frontend/src/lib/hooks.ts` carefully
3. Find ALL instances where endpoints start with `/api/`
4. Remove the `/api` prefix from those endpoints:
   - Change `/api/assignments` to `/assignments`
   - Change `/api/people` to `/people`
   - Change `/api/absences` to `/absences`
   - Change `/api/rotation-templates` to `/rotation-templates`
5. Ensure consistency: ALL paths should NOT start with `/api`
6. Run TypeScript check: `cd frontend && npx tsc --noEmit`
7. Commit with message: "fix(frontend): remove duplicate /api prefix from hook endpoints"
8. Push to branch: `claude/opus-api-fix-r10`

## Expected Changes

| Line | Before | After |
|------|--------|-------|
| ~111 | `/api/assignments?...` | `/assignments?...` |
| ~171 | `/api/people${queryString}` | `/people${queryString}` |
| ~295 | `/api/absences${params}` | `/absences${params}` |
| ~378 | `/api/rotation-templates` | `/rotation-templates` |

## Verification

After changes, all endpoint paths in hooks.ts should look like:
- `/assignments`
- `/people`
- `/people/${id}`
- `/absences`
- `/rotation-templates`

None should start with `/api/`.
```

---

## Terminal 2: Opus-DependabotProtect

**Branch**: `claude/opus-dependabot-protect-r10`
**Priority**: HIGH
**Duration**: ~15 min

### Prompt

```
You are Opus-DependabotProtect. Your mission is to protect the frontend from breaking dependency updates.

## Context

From LAUNCH_LESSONS_LEARNED.md: Tailwind CSS v4 auto-update broke the build because it's a complete rewrite with breaking CSS syntax. We need to prevent this from happening again.

## Your Exclusive Files

ONLY modify these files:
- `.github/dependabot.yml`
- `frontend/package.json` (version pinning only)

DO NOT touch any other files.

## Task 1: Update Dependabot Configuration

Read `.github/dependabot.yml` and add ignore rules for the npm ecosystem:

```yaml
  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    ignore:
      # Tailwind v4 is a breaking rewrite - manual updates only
      - dependency-name: "tailwindcss"
        update-types: ["version-update:semver-major", "version-update:semver-minor"]
      # PostCSS ecosystem - often has breaking changes
      - dependency-name: "postcss"
        update-types: ["version-update:semver-major"]
      - dependency-name: "autoprefixer"
        update-types: ["version-update:semver-major"]
      # Next.js major versions need careful migration
      - dependency-name: "next"
        update-types: ["version-update:semver-major"]
```

## Task 2: Pin Critical Frontend Dependencies

In `frontend/package.json`, change these from caret (^) to exact versions:

```json
{
  "dependencies": {
    "tailwindcss": "3.4.1"  // Remove ^ prefix
  },
  "devDependencies": {
    "postcss": "8.4.32",    // Remove ^ prefix
    "autoprefixer": "10.4.16"  // Remove ^ prefix
  }
}
```

Note: Check the actual current versions in the file and pin those exact versions.

## Task 3: Commit and Push

1. Run: `cd frontend && npm install` to update package-lock.json
2. Commit with message: "chore: protect frontend deps from breaking updates

- Add Dependabot ignore rules for tailwindcss, postcss, autoprefixer, next
- Pin critical CSS toolchain to exact versions
- Prevents auto-updates that broke build (see LAUNCH_LESSONS_LEARNED.md)"
3. Push to branch: `claude/opus-dependabot-protect-r10`
```

---

## Terminal 3: Opus-FrontendTests

**Branch**: `claude/opus-frontend-tests-r10`
**Priority**: HIGH
**Duration**: ~2 hrs

### Prompt

```
You are Opus-FrontendTests. Your mission is to create the frontend test infrastructure.

## Context

The frontend has 77 TypeScript files but zero tests. Jest and React Testing Library are configured. We need MSW (Mock Service Worker) for API mocking.

## Your Exclusive Files

ONLY create/modify these:
- `frontend/src/__tests__/**/*.test.ts(x)` (CREATE)
- `frontend/src/mocks/handlers.ts` (CREATE)
- `frontend/src/mocks/server.ts` (CREATE)
- `frontend/jest.setup.js` (MODIFY if needed)

DO NOT touch any other files.

## Task 1: Install MSW

```bash
cd frontend
npm install -D msw@latest
```

## Task 2: Create MSW Handlers

Create `frontend/src/mocks/handlers.ts`:

```typescript
import { http, HttpResponse } from 'msw';

const API_BASE = 'http://localhost:8000/api';

// Mock data
const mockPeople = [
  { id: 1, name: 'Dr. Smith', email: 'smith@hospital.org', role: 'faculty', pgy_level: null, is_active: true },
  { id: 2, name: 'Dr. Jones', email: 'jones@hospital.org', role: 'resident', pgy_level: 2, is_active: true },
];

const mockAbsences = [
  { id: 1, person_id: 2, type: 'vacation', start_date: '2024-12-20', end_date: '2024-12-27', notes: 'Holiday' },
];

const mockRotationTemplates = [
  { id: 1, name: 'Inpatient', abbreviation: 'INP', activity_type: 'inpatient', max_residents: 4 },
  { id: 2, name: 'Clinic AM', abbreviation: 'CLN', activity_type: 'clinic', max_residents: 6 },
];

export const handlers = [
  // People endpoints
  http.get(`${API_BASE}/people`, () => {
    return HttpResponse.json({ items: mockPeople, total: mockPeople.length });
  }),

  http.get(`${API_BASE}/people/:id`, ({ params }) => {
    const person = mockPeople.find(p => p.id === Number(params.id));
    if (!person) return new HttpResponse(null, { status: 404 });
    return HttpResponse.json(person);
  }),

  http.post(`${API_BASE}/people`, async ({ request }) => {
    const body = await request.json();
    const newPerson = { id: mockPeople.length + 1, ...body, is_active: true };
    return HttpResponse.json(newPerson, { status: 201 });
  }),

  // Absences endpoints
  http.get(`${API_BASE}/absences`, () => {
    return HttpResponse.json({ items: mockAbsences, total: mockAbsences.length });
  }),

  http.post(`${API_BASE}/absences`, async ({ request }) => {
    const body = await request.json();
    const newAbsence = { id: mockAbsences.length + 1, ...body };
    return HttpResponse.json(newAbsence, { status: 201 });
  }),

  // Rotation templates endpoints
  http.get(`${API_BASE}/rotation-templates`, () => {
    return HttpResponse.json({ items: mockRotationTemplates, total: mockRotationTemplates.length });
  }),

  // Schedule endpoints
  http.post(`${API_BASE}/schedule/generate`, () => {
    return HttpResponse.json({
      id: 1,
      status: 'completed',
      assignments_created: 50,
      violations: []
    });
  }),

  http.get(`${API_BASE}/schedule/validate/:id`, () => {
    return HttpResponse.json({
      is_valid: true,
      violations: [],
      compliance_rate: 100
    });
  }),
];
```

## Task 3: Create MSW Server

Create `frontend/src/mocks/server.ts`:

```typescript
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

## Task 4: Update Jest Setup

Update `frontend/jest.setup.js` to include:

```javascript
import '@testing-library/jest-dom';
import { server } from './src/mocks/server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

## Task 5: Create Hook Tests

Create `frontend/src/__tests__/hooks/usePeople.test.tsx`:

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { usePeople, useCreatePerson } from '@/lib/hooks';
import { ReactNode } from 'react';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('usePeople', () => {
  it('fetches people list', async () => {
    const { result } = renderHook(() => usePeople(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.items[0].name).toBe('Dr. Smith');
  });

  it('handles loading state', () => {
    const { result } = renderHook(() => usePeople(), { wrapper: createWrapper() });
    expect(result.current.isLoading).toBe(true);
  });
});

describe('useCreatePerson', () => {
  it('creates a new person', async () => {
    const { result } = renderHook(() => useCreatePerson(), { wrapper: createWrapper() });

    result.current.mutate({
      name: 'Dr. New',
      email: 'new@hospital.org',
      role: 'resident',
      pgy_level: 1
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
```

Create `frontend/src/__tests__/hooks/useAbsences.test.tsx` with similar pattern.

## Task 6: Create Component Test

Create `frontend/src/__tests__/components/AddPersonModal.test.tsx`:

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AddPersonModal from '@/components/AddPersonModal';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
);

describe('AddPersonModal', () => {
  it('renders form fields', () => {
    render(<AddPersonModal isOpen={true} onClose={() => {}} />, { wrapper: Wrapper });

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/role/i)).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(<AddPersonModal isOpen={true} onClose={() => {}} />, { wrapper: Wrapper });

    const submitButton = screen.getByRole('button', { name: /add|save|submit/i });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/required/i)).toBeInTheDocument();
    });
  });

  it('shows PGY level only for residents', async () => {
    render(<AddPersonModal isOpen={true} onClose={() => {}} />, { wrapper: Wrapper });

    // Select faculty role
    const roleSelect = screen.getByLabelText(/role/i);
    await userEvent.selectOptions(roleSelect, 'faculty');

    expect(screen.queryByLabelText(/pgy/i)).not.toBeInTheDocument();
  });
});
```

## Task 7: Run Tests and Commit

```bash
cd frontend
npm test -- --passWithNoTests
```

Commit with message: "test(frontend): add test infrastructure with MSW and initial tests

- Set up MSW handlers for API mocking
- Add usePeople and useAbsences hook tests
- Add AddPersonModal component test
- Configure jest.setup.js for MSW integration"

Push to branch: `claude/opus-frontend-tests-r10`
```

---

## Terminal 4: Opus-E2ETests

**Branch**: `claude/opus-e2e-tests-r10`
**Priority**: MEDIUM
**Duration**: ~2 hrs

### Prompt

```
You are Opus-E2ETests. Your mission is to create Playwright E2E tests for critical user journeys.

## Context

Playwright is installed but no E2E tests exist. We need tests for main user flows to prevent regressions.

## Your Exclusive Files

ONLY create/modify these:
- `frontend/e2e/**/*.spec.ts` (CREATE)
- `frontend/playwright.config.ts` (MODIFY if needed)

DO NOT touch any other files.

## Task 1: Review Playwright Config

Read `frontend/playwright.config.ts` and ensure it's configured for:
- Base URL: http://localhost:3000
- Webserver command to start the dev server
- Reasonable timeouts

## Task 2: Create Auth Tests

Create `frontend/e2e/auth.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('shows login page for unauthenticated users', async ({ page }) => {
    await page.goto('/');
    // Should redirect to login or show login form
    await expect(page.getByRole('button', { name: /sign in|log in/i })).toBeVisible();
  });

  test('logs in with valid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email|username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByText(/dashboard|schedule/i)).toBeVisible();
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel(/email|username/i).fill('wrong@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    await expect(page.getByText(/invalid|incorrect|error/i)).toBeVisible();
  });

  test('logs out successfully', async ({ page }) => {
    // First log in
    await page.goto('/login');
    await page.getByLabel(/email|username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in|log in/i }).click();

    // Then log out
    await page.getByRole('button', { name: /logout|sign out/i }).click();

    // Should be back at login
    await expect(page.getByRole('button', { name: /sign in|log in/i })).toBeVisible();
  });
});
```

## Task 3: Create Schedule Tests

Create `frontend/e2e/schedule.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Schedule Page', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/email|username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await page.waitForURL('/');
  });

  test('displays schedule grid', async ({ page }) => {
    await page.goto('/schedule');

    // Should show schedule grid or calendar
    await expect(page.locator('[data-testid="schedule-grid"]').or(
      page.getByText(/schedule|calendar/i)
    )).toBeVisible();
  });

  test('navigates between blocks/weeks', async ({ page }) => {
    await page.goto('/schedule');

    // Find and click next button
    const nextButton = page.getByRole('button', { name: /next|→|>/i });
    await nextButton.click();

    // Should update the view (URL or displayed dates change)
    await page.waitForTimeout(500);
  });

  test('opens generate schedule dialog', async ({ page }) => {
    await page.goto('/');

    const generateButton = page.getByRole('button', { name: /generate/i });
    if (await generateButton.isVisible()) {
      await generateButton.click();
      await expect(page.getByText(/start date|date range/i)).toBeVisible();
    }
  });
});
```

## Task 4: Create People Tests

Create `frontend/e2e/people.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('People Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email|username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await page.waitForURL('/');
  });

  test('displays people list', async ({ page }) => {
    await page.goto('/people');

    // Should show people cards or table
    await expect(page.getByText(/resident|faculty/i).first()).toBeVisible();
  });

  test('filters by role', async ({ page }) => {
    await page.goto('/people');

    // Click residents filter
    const residentsTab = page.getByRole('tab', { name: /resident/i }).or(
      page.getByRole('button', { name: /resident/i })
    );

    if (await residentsTab.isVisible()) {
      await residentsTab.click();
      await page.waitForTimeout(500);
    }
  });

  test('opens add person modal', async ({ page }) => {
    await page.goto('/people');

    await page.getByRole('button', { name: /add.*person|new.*person/i }).click();

    // Modal should appear with form
    await expect(page.getByLabel(/name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test('adds a new person', async ({ page }) => {
    await page.goto('/people');

    await page.getByRole('button', { name: /add.*person|new.*person/i }).click();

    await page.getByLabel(/name/i).fill('Test Resident');
    await page.getByLabel(/email/i).fill('test@hospital.org');

    const roleSelect = page.getByLabel(/role|type/i);
    await roleSelect.selectOption('resident');

    const pgySelect = page.getByLabel(/pgy/i);
    if (await pgySelect.isVisible()) {
      await pgySelect.selectOption('1');
    }

    await page.getByRole('button', { name: /save|add|submit/i }).click();

    // Should show success or new person in list
    await page.waitForTimeout(1000);
  });
});
```

## Task 5: Create Absences Tests

Create `frontend/e2e/absences.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Absence Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email|username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('password123');
    await page.getByRole('button', { name: /sign in|log in/i }).click();
    await page.waitForURL('/');
  });

  test('displays absences page', async ({ page }) => {
    await page.goto('/absences');

    await expect(page.getByText(/absence|vacation|leave/i).first()).toBeVisible();
  });

  test('toggles between calendar and list view', async ({ page }) => {
    await page.goto('/absences');

    const listViewButton = page.getByRole('button', { name: /list/i });
    const calendarViewButton = page.getByRole('button', { name: /calendar/i });

    if (await listViewButton.isVisible()) {
      await listViewButton.click();
      await page.waitForTimeout(300);
    }

    if (await calendarViewButton.isVisible()) {
      await calendarViewButton.click();
      await page.waitForTimeout(300);
    }
  });

  test('opens add absence modal', async ({ page }) => {
    await page.goto('/absences');

    await page.getByRole('button', { name: /add.*absence|new.*absence/i }).click();

    await expect(page.getByLabel(/person/i).or(page.getByLabel(/resident|employee/i))).toBeVisible();
    await expect(page.getByLabel(/type/i)).toBeVisible();
    await expect(page.getByLabel(/start/i)).toBeVisible();
  });
});
```

## Task 6: Add Test Script and Run

Ensure `frontend/package.json` has:
```json
{
  "scripts": {
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

Run tests (they may fail if backend isn't running, that's OK):
```bash
cd frontend
npx playwright test --reporter=list
```

Commit with message: "test(e2e): add Playwright tests for critical user journeys

- Auth flow tests (login, logout, invalid credentials)
- Schedule page navigation tests
- People CRUD operation tests
- Absence management tests"

Push to branch: `claude/opus-e2e-tests-r10`
```

---

## Terminal 5: Opus-ConsoleCleanup

**Branch**: `claude/opus-console-cleanup-r10`
**Priority**: LOW
**Duration**: ~30 min

### Prompt

```
You are Opus-ConsoleCleanup. Your mission is to replace console.log/error statements with proper error handling.

## Context

The codebase has console.log/error statements that should be replaced with user-facing toast notifications or proper error handling.

## Your Exclusive Files

ONLY modify these files:
- `frontend/src/components/ErrorBoundary.tsx`
- `frontend/src/lib/export.ts`
- `frontend/src/components/ExcelExportButton.tsx`
- `frontend/src/app/absences/page.tsx`
- `frontend/src/components/schedule/QuickAssignMenu.tsx`
- `frontend/src/components/QuickActions.tsx`

DO NOT touch any other files.

## Task 1: Review Each File

For each file, find console.log and console.error statements.

## Task 2: Apply Fixes

### ErrorBoundary.tsx
KEEP console.error here - this is appropriate for error boundaries.
Just add a comment explaining why:
```typescript
// ErrorBoundary should log to console for debugging purposes
console.error('ErrorBoundary caught an error:', error, errorInfo);
```

### export.ts
Replace console.error with throwing an error or returning error state:
```typescript
// Before
console.error('Export failed:', error);

// After
throw new Error(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
```

### ExcelExportButton.tsx
Replace console.error with toast notification. Check if there's a toast/notification system. If not, create a simple alert or add TODO:
```typescript
// Before
console.error('Excel export failed:', error);

// After
// If toast exists:
toast.error('Failed to export Excel file. Please try again.');

// If no toast, use alert temporarily:
alert('Failed to export Excel file. Please try again.');
// TODO: Replace with proper toast notification
```

### absences/page.tsx
Same pattern - replace with toast or user-facing error:
```typescript
// Before
console.error('Failed to load absences:', error);

// After
// Set error state that displays in UI
setError('Failed to load absences. Please refresh the page.');
```

### QuickAssignMenu.tsx
Replace with toast notification:
```typescript
// Before
console.error('Assignment failed:', error);

// After
toast.error('Failed to create assignment. Please try again.');
// Or if no toast:
alert('Failed to create assignment. Please try again.');
```

### QuickActions.tsx
Replace with toast notification:
```typescript
// Before
console.error('Action failed:', error);

// After
toast.error('Action failed. Please try again.');
```

## Task 3: Check for Toast System

Look for existing toast/notification imports in the codebase:
- `react-hot-toast`
- `react-toastify`
- `sonner`
- Custom toast context

If found, use it. If not, use alerts with TODO comments.

## Task 4: Run TypeScript Check

```bash
cd frontend
npx tsc --noEmit
```

Fix any type errors introduced.

## Task 5: Commit and Push

Commit with message: "refactor(frontend): replace console statements with proper error handling

- Keep console.error in ErrorBoundary (appropriate for debugging)
- Replace console.error in export functions with thrown errors
- Replace console.error in UI components with user-facing notifications
- Add TODO comments where toast system needs implementation"

Push to branch: `claude/opus-console-cleanup-r10`
```

---

## Merge Order

After all terminals complete:

```
1. claude/opus-api-fix-r10           # Critical bug fix
2. claude/opus-dependabot-protect-r10 # Config only, no conflicts
3. claude/opus-console-cleanup-r10    # Isolated component fixes
4. claude/opus-frontend-tests-r10     # New test files
5. claude/opus-e2e-tests-r10          # New E2E test files
```

## Conflict Risk Assessment

| Terminal | Conflict Risk | Notes |
|----------|--------------|-------|
| Opus-APIFix | LOW | Only touches lib/hooks.ts |
| Opus-DependabotProtect | NONE | Config files only |
| Opus-FrontendTests | NONE | Creates new test files |
| Opus-E2ETests | NONE | Creates new E2E files |
| Opus-ConsoleCleanup | LOW | Touches 6 specific components |

No file overlap between any terminals.

---

*Generated: December 16, 2024*
