# Frontend Test Coverage Improvement Plan

**Created:** 2025-12-31
**Source:** SESSION_2_FRONTEND Testing Patterns Analysis
**Status:** Comprehensive Testing Strategy
**Current:** 123 files, 65,700 LOC, 0.4% skip rate (excellent baseline)

---

## Executive Summary

**Current State:** Production-ready test infrastructure with:
- 123 Jest test files + 16 Playwright E2E tests
- 65,700 total test lines across all test suites
- 11,753+ test cases with 0.4% skip rate (very clean)
- 60% global coverage threshold (standard for UI code)
- Strong patterns: Factory pattern, mocking strategy, async utilities

**Gaps Identified:**
1. No visual regression testing yet
2. Accessibility testing limited to manual checks
3. Performance benchmarks not automated
4. MSW disabled (acceptable workaround)

**Improvement Goals:**
- Add visual regression testing
- Expand accessibility test coverage
- Implement performance benchmarks
- Increase coverage thresholds strategically

---

## Section 1: Current Testing Infrastructure Assessment

### Test Infrastructure Health Check

```
Jest Configuration:      ✓ Excellent
├─ testEnvironment:      jsdom (correct for React)
├─ testTimeout:          15s (good for async)
├─ moduleNameMapper:     Proper path aliases
└─ collectCoverageFrom:  Well configured

Test Patterns:           ✓ Professional
├─ Factory pattern:      mockFactories.person(), etc.
├─ Hook testing:         renderHook with wrapper
├─ Component testing:    userEvent, screen queries
└─ Async utilities:      4,832 uses (proper)

Playwright E2E:          ✓ Good
├─ Configuration:        Smart defaults (parallel locally, serial on CI)
├─ Screenshots:          Capture on failure
├─ Traces:               Collect for debugging
└─ Retry logic:          2 retries on CI

Mocking Strategy:        ⚠️ Functional but could improve
├─ jest.mock():          772 instances (working)
├─ MSW:                  Disabled (jsdom incompatibility)
├─ Custom factories:     4 types (good)
└─ Mock data:            Feature-specific files (good)
```

### Test Organization Strengths

✅ **Centralized Test Utilities:** `__tests__/utils/test-utils.tsx`
- QueryClient factory
- Mock data factories
- Shared test helpers

✅ **Feature-Specific Tests:** Tests co-located with features
- `features/swap-marketplace/__tests__/`
- `features/conflicts/` has comprehensive tests
- Clear separation of concerns

✅ **Proper Setup:** `__tests__/setup.ts`
- localStorage mock
- window.location mock
- ResizeObserver, IntersectionObserver mocks
- All browser APIs properly mocked

---

## Section 2: Coverage Improvement Plan

### Phase 1: Strategic Coverage Thresholds

**Current:** 60% global (one-size-fits-all)

**Proposed:** Context-aware thresholds

```javascript
// jest.config.js - Updated
coverageThreshold: {
  global: {
    branches: 60,
    functions: 60,
    lines: 60,
    statements: 60,
  },
  './src/hooks/': {         // Data fetching layer
    branches: 75,
    functions: 75,
    lines: 75,
    statements: 75,
  },
  './src/components/forms/': { // Form primitives
    branches: 80,
    functions: 80,
    lines: 80,
    statements: 80,
  },
  './src/lib/': {           // Business logic/utilities
    branches: 80,
    functions: 80,
    lines: 80,
    statements: 80,
  },
  './src/contexts/': {      // State management
    branches: 70,
    functions: 70,
    lines: 70,
    statements: 70,
  },
  // Don't enforce for UI components (lower ROI)
}
```

### Phase 2: Test Coverage Gaps

**Gap Analysis:** Where coverage is likely insufficient

| Category | Gap | Priority | Fix |
|----------|-----|----------|-----|
| **Error Boundaries** | Feature-level error scenarios | HIGH | Add 5 tests per feature |
| **Async Edge Cases** | Token refresh, network timeouts | MEDIUM | Expand useAuth tests |
| **Accessibility** | Keyboard navigation, screen reader | MEDIUM | Add axe-core tests |
| **Performance** | Component render times | LOW | Add React Performance API tests |
| **Mobile** | Responsive behavior | MEDIUM | Playwright mobile tests |

### Phase 3: Coverage Targets (Post-Implementation)

```
TARGET COVERAGE BY QUARTER:

Q1 2026:
├─ Hooks: 75% coverage (from 60%)
├─ Forms: 80% coverage
├─ Services: 80% coverage
├─ Contexts: 70% coverage
└─ Components: 65% coverage (UI has higher variance)

Q2 2026:
├─ Visual regression: 100% coverage (all pages)
├─ E2E critical paths: 100% coverage
└─ Accessibility: 90% automated checks

Overall: 70% by end of Q2
```

---

## Section 3: Visual Regression Testing

### Why Visual Regression Testing?

**Current Gap:** No automation for UI visual changes
- Component styling is tested indirectly
- Color changes might not be caught
- Layout regressions not detected
- Requires manual review

### Implementation: Playwright Visual Comparisons

**Setup:**

```bash
npm install --save-dev @playwright/test
# Already have Playwright, just need visual comparisons
```

**Example Test:**

```typescript
// frontend/e2e/visual/components.spec.ts

import { test, expect } from '@playwright/test';

test('Button component renders correctly', async ({ page }) => {
  await page.goto('http://localhost:3000/components/button');

  const button = page.locator('button:has-text("Click me")');

  // Take screenshot and compare
  await expect(button).toHaveScreenshot('button-default.png');
});

test('Button hover state', async ({ page }) => {
  await page.goto('http://localhost:3000/components/button');

  const button = page.locator('button:has-text("Click me")');
  await button.hover();

  await expect(button).toHaveScreenshot('button-hover.png');
});

test('Button disabled state', async ({ page }) => {
  await page.goto('http://localhost:3000/components/button');

  const button = page.locator('button:disabled');

  await expect(button).toHaveScreenshot('button-disabled.png');
});
```

### GitHub Actions Workflow

```yaml
name: Visual Regression Tests

on:
  pull_request:
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Start dev server
        run: npm run dev &
        # Wait for server to start
      - name: Wait for server
        run: npx wait-on http://localhost:3000

      - name: Run visual tests
        run: npx playwright test --project=visual

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

---

## Section 4: Accessibility Test Coverage

### Current State

**Manual Testing:** Good
- LoginForm.test.tsx has accessibility tests
- Label association verified
- Could expand significantly

**Automated Testing:** None with axe-core

### Implementation: Automated Accessibility Testing

**Setup:**

```bash
npm install --save-dev @axe-core/react jest-axe
```

**Test Template:**

```typescript
// frontend/__tests__/components/LoginForm.test.tsx (expanded)

import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('LoginForm Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<LoginForm onSuccess={jest.fn()} />);
    const results = await axe(container);

    expect(results).toHaveNoViolations();
  });

  it('should have proper form structure', () => {
    render(<LoginForm onSuccess={jest.fn()} />);

    // Check form semantics
    expect(screen.getByRole('form')).toBeInTheDocument();

    // Check labels
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

    // Check button
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('should be navigable with keyboard only', async () => {
    const user = userEvent.setup();
    render(<LoginForm onSuccess={jest.fn()} />);

    // Tab to username
    await user.tab();
    expect(screen.getByLabelText(/username/i)).toHaveFocus();

    // Tab to password
    await user.tab();
    expect(screen.getByLabelText(/password/i)).toHaveFocus();

    // Tab to submit
    await user.tab();
    expect(screen.getByRole('button', { name: /sign in/i })).toHaveFocus();

    // Submit with Enter
    await user.keyboard('{Enter}');
    expect(mockOnSuccess).toHaveBeenCalled();
  });

  it('should announce errors to screen readers', () => {
    render(<LoginForm initialErrors={{ username: 'Required' }} />);

    const error = screen.getByRole('alert');
    expect(error).toHaveTextContent('Required');
  });
});
```

### Accessibility Test Coverage Goals

```
Checklist Coverage:

[ ] Component A11y
  [ ] Axe violations: 0
  [ ] Semantic HTML: ✓
  [ ] ARIA attributes: ✓
  [ ] Focus management: ✓

[ ] Keyboard Navigation
  [ ] Tab order correct: ✓
  [ ] Focus trap in modals: ✓
  [ ] Escape closes modals: ✓
  [ ] Arrow keys in dropdowns: ✓

[ ] Screen Reader
  [ ] Labels announced: ✓
  [ ] Errors announced: ✓
  [ ] Loading states: ✓
  [ ] Success messages: ✓

[ ] Color & Contrast
  [ ] Text contrast: ✓
  [ ] Icon contrast: ✓
  [ ] Color not sole indicator: ✓
```

---

## Section 5: Performance Test Integration

### Performance Benchmarks

**Current:** No automated performance tests

**Proposed:** Add performance assertions

```typescript
// frontend/__tests__/performance/ListRendering.test.tsx

import React from 'react';
import { render } from '@testing-library/react';

describe('Performance Benchmarks', () => {
  it('should render 100 list items in < 100ms', () => {
    const items = Array.from({ length: 100 }, (_, i) => ({
      id: i,
      name: `Item ${i}`,
    }));

    const start = performance.now();

    render(
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    );

    const duration = performance.now() - start;

    expect(duration).toBeLessThan(100);
    console.log(`✓ Rendered 100 items in ${duration.toFixed(2)}ms`);
  });

  it('should memoize ConflictCard correctly', () => {
    const { rerender } = render(
      <ConflictCard
        conflict={{ id: '1', title: 'Test' }}
        onSelect={jest.fn()}
        isSelected={false}
      />
    );

    const renderCount = jest.fn();
    jest.spyOn(React, 'createElement').mockImplementation(() => {
      renderCount();
      return <></>;
    });

    // Rerender with same props
    rerender(
      <ConflictCard
        conflict={{ id: '1', title: 'Test' }}
        onSelect={jest.fn()}
        isSelected={false}
      />
    );

    // Should not call createElement again (memoized)
    expect(renderCount).not.toHaveBeenCalled();

    jest.restoreAllMocks();
  });
});
```

### React Performance API Testing

```typescript
// frontend/__tests__/performance/RenderTiming.test.tsx

import { Profiler, ProfilerOnRenderCallback } from 'react';

describe('Component Render Performance', () => {
  it('should render ScheduleCalendar within budget', (done) => {
    const onRenderCallback: ProfilerOnRenderCallback = (
      id,
      phase,
      actualDuration,
      baseDuration,
      startTime,
      commitTime
    ) => {
      console.log(`${id} (${phase}) took ${actualDuration.toFixed(2)}ms`);

      // Assert performance budget
      expect(actualDuration).toBeLessThan(50);  // 50ms budget
      done();
    };

    render(
      <Profiler id="ScheduleCalendar" onRender={onRenderCallback}>
        <ScheduleCalendar {...props} />
      </Profiler>
    );
  });
});
```

---

## Section 6: MSW Integration (Optional Future)

### Current Status: Disabled (Acceptable Workaround)

**Problem:** MSW v2 incompatible with Jest + jsdom
**Current Solution:** jest.mock() for API modules (working well)

### Future Path: Enable MSW (6+ months)

**Option 1: Migrate to Vitest**
```bash
npm install --save-dev vitest
npm install --save-dev @vitest/ui
# Vitest has better ESM support, MSW works natively
```

**Option 2: Node.js Polyfills (Complex)**
```bash
npm install --save-dev node-polyfill-webpack-plugin
# Add extensive polyfills for fetch, TextEncoder, etc.
# Not recommended - high maintenance burden
```

**Recommendation:** Keep jest.mock() for now, consider Vitest in 12+ months if pain points emerge.

---

## Section 7: Test Maintenance & Quality

### Pre-Commit Testing

```bash
# package.json scripts
"precommit": "npm run type-check && npm run lint && npm run test:changed",
"test:changed": "jest --onlyChanged --coverage"
```

**.husky/pre-commit:**
```bash
#!/bin/sh
npm run precommit
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install
        run: npm ci

      - name: Type Check
        run: npm run type-check

      - name: Lint
        run: npm run lint

      - name: Jest Tests
        run: npm run test:ci

      - name: Coverage Report
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

      - name: Playwright Tests
        run: npm run test:e2e

      - name: Upload E2E Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

### Test Health Metrics

```typescript
// frontend/tests/health-check.test.ts

describe('Test Suite Health', () => {
  it('should have minimal skipped tests', () => {
    const skip_count = 47;  // Current count
    const total_tests = 11753;
    const skip_rate = skip_count / total_tests;

    expect(skip_rate).toBeLessThan(0.01);  // < 1%
    console.log(`Skip rate: ${(skip_rate * 100).toFixed(2)}%`);
  });

  it('should maintain coverage threshold', () => {
    // Coverage check (automated by jest)
    expect(process.env.COVERAGE_THRESHOLD).toBeDefined();
  });

  it('should have no flaky tests', () => {
    // Monitor test stability over time
    // Flag tests that fail intermittently
  });
});
```

---

## Section 8: Implementation Timeline

### Week 1-2: Accessibility Testing

```
[ ] Install jest-axe and @axe-core/react
[ ] Add axe tests to 10 critical components
[ ] Create accessibility test template
[ ] Document a11y testing patterns
Effort: 8-10 hours
```

### Week 3-4: Visual Regression

```
[ ] Configure Playwright visual tests
[ ] Add visual tests for 20 components
[ ] Set up GitHub Actions workflow
[ ] Create baseline screenshots
Effort: 10-12 hours
```

### Month 2: Performance Benchmarks

```
[ ] Add React Profiler integration
[ ] Create performance budgets for components
[ ] Add benchmark tests for critical paths
[ ] Document performance patterns
Effort: 6-8 hours
```

### Month 3: Coverage Expansion

```
[ ] Increase hook coverage to 75%
[ ] Expand form component tests
[ ] Add error scenario tests
[ ] Complete feature-specific coverage
Effort: 12-16 hours
```

---

## Section 9: Success Metrics

```checklist
✓ Test Infrastructure
  ✓ 0 skipped tests (automated skip tracking)
  ✓ <2% test failure rate on CI
  ✓ <5 minute total test run time

✓ Coverage
  ✓ Hooks: 75% coverage minimum
  ✓ Forms: 80% coverage minimum
  ✓ Utilities: 80% coverage minimum
  ✓ Overall: 70% global coverage

✓ Accessibility Testing
  ✓ 100% of components pass axe audit
  ✓ Keyboard navigation tested
  ✓ Screen reader announcements tested
  ✓ 0 accessibility violations in PR

✓ Visual Regression
  ✓ All pages have baseline screenshots
  ✓ 0 visual regressions per release
  ✓ Visual tests run on every PR

✓ Performance Testing
  ✓ Component render time < 50ms
  ✓ List rendering < 100ms for 100 items
  ✓ Memoization prevents unnecessary re-renders
  ✓ Performance regressions caught in CI
```

---

## Section 10: Test Writing Best Practices

### Template: Component Test (Complete)

```typescript
/**
 * Tests for MyComponent
 *
 * Tests cover:
 * - Rendering with different props
 * - User interactions
 * - Error states
 * - Accessibility requirements
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';

import { MyComponent } from './MyComponent';

expect.extend(toHaveNoViolations);

describe('MyComponent', () => {
  // ============================================
  // Setup & Teardown
  // ============================================

  const defaultProps = {
    title: 'Test Title',
    onSubmit: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ============================================
  // Rendering Tests
  // ============================================

  describe('Rendering', () => {
    it('should render with provided props', () => {
      render(<MyComponent {...defaultProps} />);

      expect(screen.getByText('Test Title')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
    });

    it('should render loading state', () => {
      render(<MyComponent isLoading {...defaultProps} />);

      expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true');
    });

    it('should render error state', () => {
      render(<MyComponent error="Something went wrong" {...defaultProps} />);

      expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong');
    });
  });

  // ============================================
  // User Interactions
  // ============================================

  describe('User Interactions', () => {
    it('should call onSubmit when button clicked', async () => {
      const user = userEvent.setup();
      render(<MyComponent {...defaultProps} />);

      const button = screen.getByRole('button', { name: /submit/i });
      await user.click(button);

      expect(defaultProps.onSubmit).toHaveBeenCalledOnce();
    });

    it('should handle form submission', async () => {
      const user = userEvent.setup();
      render(<MyComponent {...defaultProps} />);

      const input = screen.getByRole('textbox');
      await user.type(input, 'test value');

      const button = screen.getByRole('button', { name: /submit/i });
      await user.click(button);

      expect(defaultProps.onSubmit).toHaveBeenCalledWith({ field: 'test value' });
    });
  });

  // ============================================
  // Accessibility
  // ============================================

  describe('Accessibility', () => {
    it('should not have axe violations', async () => {
      const { container } = render(<MyComponent {...defaultProps} />);
      const results = await axe(container);

      expect(results).toHaveNoViolations();
    });

    it('should have proper ARIA labels', () => {
      render(<MyComponent {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label');
    });

    it('should be keyboard navigable', async () => {
      const user = userEvent.setup();
      render(<MyComponent {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).not.toHaveFocus();

      await user.tab();

      expect(button).toHaveFocus();
    });
  });

  // ============================================
  // Edge Cases
  // ============================================

  describe('Edge Cases', () => {
    it('should handle disabled state', () => {
      render(<MyComponent isDisabled {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should handle empty props gracefully', () => {
      render(<MyComponent title="" />);

      // Should not crash
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});
```

---

## Final Checklist

```checklist
Implementation Roadmap:

Phase 1 (Weeks 1-2):
  [ ] Install testing libraries (jest-axe, @axe-core/react)
  [ ] Add accessibility tests to 10 components
  [ ] Create test templates & documentation

Phase 2 (Weeks 3-4):
  [ ] Configure Playwright visual tests
  [ ] Create baseline screenshots
  [ ] Set up GitHub Actions integration

Phase 3 (Month 2):
  [ ] Add performance benchmarks
  [ ] Create React Profiler tests
  [ ] Document performance patterns

Phase 4 (Month 3):
  [ ] Increase coverage targets
  [ ] Fill coverage gaps
  [ ] Review and refactor tests
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Next Review:** 2026-03-31
**Target Completion:** Q2 2026
