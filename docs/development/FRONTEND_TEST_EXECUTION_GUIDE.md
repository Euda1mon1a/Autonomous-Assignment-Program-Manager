# Frontend Test Execution Guide

**Purpose:** Practical commands and patterns for implementing the 244-hour test suite
**Target:** Test developers, CI/CD engineers

---

## Quick Command Reference

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run specific test file
npm test -- ResilienceDashboard.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="compliance"

# Run with coverage report
npm test -- --coverage

# Run and fail on coverage drop
npm test -- --coverage --coverageThreshold='{"global":{"lines":70}}'

# Run Tier 1 tests only
npm test -- --testPathPattern="resilience|drag|swap"

# Run Tier 2 tests
npm test -- --testPathPattern="compliance|scheduling|schedule"

# Run specific block
npm test -- --testPathPattern="resilience" --coverage
```

### Pre-Commit Hooks

```bash
# Install husky (if not already)
npm install husky --save-dev

# Setup pre-commit hook
cat > .husky/pre-commit << 'EOF'
#!/bin/sh
npm test -- --bail --findRelatedTests
npm run lint
npm run type-check
EOF

chmod +x .husky/pre-commit
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test -- --coverage
      - run: npm run lint
      - run: npm run type-check
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm test -- --testPathPattern="accessibility"
```

---

## Test Fixtures Setup

### Create Fixture Directory Structure

```bash
mkdir -p frontend/__fixtures__/{resilience,compliance,scheduling,swaps,users}
touch frontend/__fixtures__/index.ts
```

### Base Fixtures

#### Resilience Fixtures

```typescript
// __fixtures__/resilience/health-status.ts
export const mockHealthStatus = {
  defenseTier: 'GREEN' as const,
  utilization: 0.72,
  burnoutRt: 1.2,
  lastUpdated: new Date('2025-12-31T10:00:00Z'),
  earlyWarnings: [],
};

export const mockHealthStatusYellow = {
  ...mockHealthStatus,
  defenseTier: 'YELLOW' as const,
  utilization: 0.82,
  burnoutRt: 1.5,
  earlyWarnings: [
    { id: '1', message: 'Utilization trending high', severity: 'warning' },
  ],
};

export const mockHealthStatusRed = {
  ...mockHealthStatus,
  defenseTier: 'RED' as const,
  utilization: 0.95,
  burnoutRt: 2.1,
  earlyWarnings: [
    { id: '1', message: 'Critical utilization', severity: 'critical' },
    { id: '2', message: 'Burnout acceleration', severity: 'critical' },
  ],
};

export const mockN1Contingency = {
  affectedResidents: ['RES-001', 'RES-002'],
  impactLevel: 'high',
  blastRadius: ['INPATIENT', 'CLINIC'],
  mitigation: 'Can absorb 1 faculty loss with schedule adjustment',
};
```

#### Compliance Fixtures

```typescript
// __fixtures__/compliance/work-hours.ts
export const mockWorkHoursCompliant = {
  residentId: 'RES-001',
  currentWeek: 45,
  rolling4Week: 72,
  maxAllowed: 80,
  violations: [],
  status: 'COMPLIANT',
};

export const mockWorkHoursViolation = {
  residentId: 'RES-002',
  currentWeek: 55,
  rolling4Week: 85,
  maxAllowed: 80,
  violations: [
    {
      type: '80_HOUR_RULE',
      week: 2,
      hours: 85,
      remediation: 'Assign lighter schedule next week',
    },
  ],
  status: 'VIOLATION',
};

export const mockSupervisor = {
  pgyLevel: 1,
  requiredRatio: '1:2', // 1 faculty per 2 residents
  currentRatio: '1:3',  // Under-supervised!
  violation: true,
  requiredFacultyCount: 25,
  currentFacultyCount: 16,
};
```

#### Scheduling Fixtures

```typescript
// __fixtures__/scheduling/schedule.ts
export const mockScheduleData = {
  blocks: Array.from({ length: 730 }, (_, i) => ({
    id: `BLOCK-${i}`,
    date: new Date('2025-01-01').toISOString(),
    blockNumber: i,
    assignments: [],
  })),
  residents: [
    { id: 'RES-001', name: 'PGY1-01', pgyLevel: 1 },
    { id: 'RES-002', name: 'PGY2-01', pgyLevel: 2 },
  ],
  faculty: [
    { id: 'FAC-001', name: 'FAC-PD', role: 'ProgramDirector' },
    { id: 'FAC-002', name: 'FAC-APD', role: 'AssociateProgramDirector' },
  ],
};

export const mockAssignment = {
  id: 'ASSIGN-001',
  personId: 'RES-001',
  blockId: 'BLOCK-001',
  rotationType: 'INPATIENT',
  date: '2025-01-01',
  shiftType: 'FULL',
};
```

#### Swap Fixtures

```typescript
// __fixtures__/swaps/swap-requests.ts
export const mockSwapRequest = {
  id: 'SWAP-001',
  requesterId: 'RES-001',
  requestedDate: '2025-02-15',
  wantRotationType: 'CLINIC',
  willing: 'INPATIENT',
  status: 'PENDING',
  createdAt: new Date().toISOString(),
};

export const mockSwapMatch = {
  request1Id: 'SWAP-001',
  request2Id: 'SWAP-002',
  matchQuality: 0.95,
  compliance: true,
  status: 'MATCHED',
};
```

#### User Fixtures

```typescript
// __fixtures__/users/users.ts
export const mockAdminUser = {
  id: 'USER-001',
  email: 'admin@test.com',
  role: 'ADMIN',
  permissions: ['VIEW_ALL', 'EDIT_ALL', 'DELETE_ALL'],
};

export const mockResidentUser = {
  id: 'USER-002',
  email: 'resident@test.com',
  role: 'RESIDENT',
  personId: 'RES-001',
  permissions: ['VIEW_OWN', 'REQUEST_SWAP'],
};
```

### Fixture Index

```typescript
// __fixtures__/index.ts
export * from './resilience/health-status';
export * from './compliance/work-hours';
export * from './scheduling/schedule';
export * from './swaps/swap-requests';
export * from './users/users';
```

---

## Testing Utilities

### Setup File

```typescript
// __tests__/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Next.js router
vi.mock('next/router', () => ({
  useRouter: () => ({
    push: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
}));

// Mock TanStack Query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: null,
    isLoading: false,
    error: null,
  })),
}));

// Mock API client
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} })),
  },
}));

// Suppress console errors in tests
global.console = {
  ...console,
  error: vi.fn(),
  warn: vi.fn(),
};
```

### Custom Render Function

```typescript
// __tests__/test-utils.tsx
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClientProvider, QueryClient } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from '@/store';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const testQueryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={testQueryClient}>
      <Provider store={store}>
        {children}
      </Provider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

### Accessibility Testing Helper

```typescript
// __tests__/accessibility.ts
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

export async function checkAccessibility(container: HTMLElement) {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
}

export function checkKeyboardNavigation(elements: HTMLElement[]) {
  elements.forEach((el) => {
    if (el.tagName !== 'BUTTON' && el.tagName !== 'A') {
      expect(el).toHaveAttribute('tabindex');
    }
  });
}

export function checkAriaLabels(container: HTMLElement) {
  const unlabeledButtons = container.querySelectorAll(
    'button:not([aria-label]):not([aria-labelledby])'
  );
  expect(unlabeledButtons).toHaveLength(0);
}
```

---

## Test Templates

### Component Test Template

```typescript
// __tests__/components/resilience/ResilienceDashboard.test.tsx
import { render, screen, waitFor } from '@/__tests__/test-utils';
import { ResilienceDashboard } from '@/components/resilience';
import { mockHealthStatus } from '@/__fixtures__/resilience';

describe('ResilienceDashboard', () => {
  describe('rendering', () => {
    it('renders dashboard with health data', () => {
      render(<ResilienceDashboard data={mockHealthStatus} />);
      expect(screen.getByText(/Health Status/i)).toBeInTheDocument();
    });

    it('displays all key metrics', () => {
      const { getByTestId } = render(<ResilienceDashboard data={mockHealthStatus} />);
      expect(getByTestId('metric-rt')).toBeInTheDocument();
      expect(getByTestId('metric-utilization')).toBeInTheDocument();
      expect(getByTestId('metric-defense')).toBeInTheDocument();
    });
  });

  describe('data handling', () => {
    it('handles missing data gracefully', () => {
      render(<ResilienceDashboard data={null} />);
      expect(screen.getByText(/No data available/i)).toBeInTheDocument();
    });

    it('updates on data change', () => {
      const { rerender } = render(<ResilienceDashboard data={mockHealthStatus} />);
      expect(screen.getByTestId('metric-rt')).toHaveTextContent('1.2');

      const updatedData = { ...mockHealthStatus, burnoutRt: 2.1 };
      rerender(<ResilienceDashboard data={updatedData} />);
      expect(screen.getByTestId('metric-rt')).toHaveTextContent('2.1');
    });
  });

  describe('accessibility', () => {
    it('has proper ARIA labels', () => {
      const { container } = render(<ResilienceDashboard data={mockHealthStatus} />);
      expect(container.querySelector('[role="status"]')).toBeInTheDocument();
    });

    it('supports keyboard navigation', () => {
      render(<ResilienceDashboard data={mockHealthStatus} />);
      const buttons = screen.getAllByRole('button');
      buttons.forEach((btn) => {
        expect(btn).toHaveFocus() || expect(btn.tabIndex).toBeGreaterThanOrEqual(0);
      });
    });

    it('meets color contrast requirements', () => {
      // Run axe audit
      checkAccessibility(render(<ResilienceDashboard data={mockHealthStatus} />).container);
    });
  });
});
```

### Hook Test Template

```typescript
// __tests__/hooks/useSchedule.test.tsx
import { renderHook, act, waitFor } from '@testing-library/react';
import { useSchedule } from '@/hooks/useSchedule';
import { mockScheduleData } from '@/__fixtures__/scheduling';

describe('useSchedule', () => {
  it('fetches schedule data', async () => {
    const { result } = renderHook(() => useSchedule('RES-001'));

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockScheduleData);
  });

  it('updates schedule data', async () => {
    const { result } = renderHook(() => useSchedule('RES-001'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.updateAssignment({
        ...mockAssignment,
        rotationType: 'CLINIC',
      });
    });

    expect(result.current.data.assignments[0].rotationType).toBe('CLINIC');
  });

  it('handles errors gracefully', async () => {
    // Mock API error
    const { result } = renderHook(() => useSchedule('INVALID'));

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });

    expect(result.current.data).toBeNull();
  });
});
```

### Integration Test Template

```typescript
// __tests__/features/swap-marketplace/swap-workflow.test.tsx
import { render, screen, fireEvent, waitFor } from '@/__tests__/test-utils';
import { SwapMarketplace } from '@/features/swap-marketplace';
import { mockSwapRequest } from '@/__fixtures__/swaps';

describe('Swap Marketplace Workflow', () => {
  it('completes full swap request workflow', async () => {
    render(<SwapMarketplace />);

    // Step 1: Create request
    const createBtn = screen.getByText(/Request Swap/i);
    fireEvent.click(createBtn);

    const dateInput = screen.getByLabelText(/Date/i);
    fireEvent.change(dateInput, { target: { value: '2025-02-15' } });

    const submitBtn = screen.getByText(/Submit/i);
    fireEvent.click(submitBtn);

    // Step 2: Wait for confirmation
    await waitFor(() => {
      expect(screen.getByText(/Request created/i)).toBeInTheDocument();
    });

    // Step 3: Auto-matcher finds match
    await waitFor(() => {
      expect(screen.getByText(/Match found/i)).toBeInTheDocument();
    });

    // Step 4: Approve match
    const approveBtn = screen.getByText(/Approve/i);
    fireEvent.click(approveBtn);

    // Step 5: Confirm completion
    await waitFor(() => {
      expect(screen.getByText(/Swap approved/i)).toBeInTheDocument();
    });
  });
});
```

---

## Performance Testing

### Add Performance Tests

```typescript
// __tests__/performance/schedule-rendering.test.tsx
import { render } from '@/__tests__/test-utils';
import { ScheduleGrid } from '@/components/schedule';

describe('ScheduleGrid Performance', () => {
  it('renders 365 days × 50 residents in <1000ms', () => {
    const start = performance.now();

    render(<ScheduleGrid residents={Array(50).fill()} blocks={Array(730).fill()} />);

    const duration = performance.now() - start;
    expect(duration).toBeLessThan(1000);
  });
});
```

### Run Performance Tests

```bash
# Run performance tests
npm test -- --testPathPattern="performance"

# Generate performance report
npm test -- --coverage --coverageReporters=text-summary
```

---

## Debugging Tests

### VSCode Launch Configuration

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Jest Debug",
      "program": "${workspaceFolder}/node_modules/.bin/jest",
      "args": ["--runInBand", "--no-cache", "${file}"],
      "console": "integratedTerminal",
      "internalConsoleOptions": "neverOpen"
    }
  ]
}
```

### Debug Commands

```bash
# Run single test file with debugger
node --inspect-brk node_modules/.bin/jest --runInBand ResilienceDashboard.test.tsx

# Run with additional logging
DEBUG=* npm test

# Generate HTML coverage report
npm test -- --coverage --coverageReporters=html
# Open coverage/index.html
```

---

## CI/CD Integration

### Coverage Thresholds

```javascript
// jest.config.js
module.exports = {
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
    './src/components/resilience/': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    './src/components/compliance/': {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};
```

### GitHub Actions Workflow

```yaml
name: Test Coverage Report

on: [pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm test -- --coverage
      - uses: codecov/codecov-action@v3
      - name: Comment PR with coverage
        uses: romeovs/lcov-reporter-action@v0.3.1
```

---

## Quick Wins (Easy Tests to Start)

1. **UI Components** (1-2 hours each)
   - Button, Input, Badge, Card
   - Straightforward unit tests

2. **Layout Components** (1 hour each)
   - Container, Grid, Stack, Sidebar
   - Simple rendering tests

3. **Badge Components** (30 mins each)
   - RotationBadge, ShiftIndicator
   - Status display components

4. **Alert Components** (2 hours)
   - ViolationAlert, ComplianceAlert
   - Mock data + rendering

**Recommendation:** Start with UI components to build test confidence, then move to complex components.

---

## Parallel Testing Strategy

### Run Tests in Parallel

```bash
# Default: runs in parallel with workers
npm test

# Explicit worker count
npm test -- --maxWorkers=4

# Disable parallelization (debugging)
npm test -- --runInBand
```

### Distribute Across CI Runners

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    test-suite:
      - resilience
      - compliance
      - scheduling
      - ui-components
      - features

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test -- --testPathPattern="${{ matrix.test-suite }}"
```

---

## Maintenance & Monitoring

### Keep Tests Updated

```bash
# Update snapshots (after intentional changes)
npm test -- --updateSnapshot

# Check for outdated tests
npm test -- --listTests | wc -l

# Find slow tests
npm test -- --detectOpenHandles
```

### Monitor Coverage Over Time

```bash
# Generate coverage baseline
npm test -- --coverage > coverage-baseline.txt

# Compare new coverage
npm test -- --coverage | diff coverage-baseline.txt -
```

---

## Resources

- **Jest Docs:** https://jestjs.io/
- **Testing Library:** https://testing-library.com/
- **Playwright:** https://playwright.dev/
- **Axe Accessibility:** https://www.deque.com/axe/

---

**Guide Version:** 1.0
**Last Updated:** 2025-12-31
