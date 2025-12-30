# Frontend Test Coverage Analysis Report
## Session 026 - Marathon Plan

**Generated:** 2025-12-30
**Analysis Scope:** `/home/user/Autonomous-Assignment-Program-Manager/frontend`
**Target:** Improve coverage from 60% → 90%

---

## Executive Summary

### Current State
- **Test Suite Size:** 107 test files, 2199 total tests
- **Test Results:** 2001 passing, 198 failing (90.1% pass rate)
- **Source Files:** 235+ TypeScript/TSX files
- **Coverage Status:** ⚠️ **CRITICAL CONFIGURATION ISSUE DETECTED**

### Critical Issues

#### 1. Coverage Collection Misconfiguration ⚠️
**PRIORITY: CRITICAL**

The `jest.config.js` file only collects coverage from `src/lib/**/*`:

```javascript
collectCoverageFrom: [
  'src/lib/**/*.{ts,tsx}',
  '!src/lib/**/*.d.ts',
],
```

**Impact:** Coverage is NOT being collected for:
- ❌ `src/components/**` (80 components)
- ❌ `src/features/**` (14 feature modules)
- ❌ `src/hooks/**` (15 custom hooks)
- ❌ `src/app/**` (24 Next.js pages)

**Current coverage data is meaningless** - it only covers a tiny fraction of the codebase.

#### 2. Missing Source Files (Test Orphans)
**PRIORITY: HIGH**

Tests exist but source files are missing:

| Test File | Missing Source | Impact |
|-----------|----------------|--------|
| `__tests__/features/procedures/Credentialing.test.tsx` | `src/hooks/useProcedures.ts` | Test cannot run |
| `__tests__/features/resilience/*.test.tsx` (4 files) | `src/features/resilience/*` | Entire feature missing |
| `__tests__/features/fmit/FMITDetection.test.tsx` | `src/features/fmit-timeline/FMITDetection.tsx` | Partial implementation |

**Total failing tests due to missing sources:** 89 test suites

#### 3. Test Configuration Issues
- Import path mapping errors in Jest
- Module resolution failing for `@/` aliases
- MSW (Mock Service Worker) compatibility issues with Jest

---

## Detailed Analysis

### 1. Test Infrastructure Status

✅ **Configured:**
- Jest test runner with jsdom environment
- React Testing Library + User Event
- MSW for API mocking
- TypeScript support via ts-jest
- Path aliases configured

⚠️ **Issues:**
- Coverage collection scope too narrow
- Test timeout set to 15s (may cause flaky tests)
- Some module resolution failures

### 2. Source File Inventory

#### By Category

| Category | Total Files | Test Files | Coverage Gap |
|----------|-------------|------------|--------------|
| **Pages** (`src/app`) | 24 | 0 | 100% gap |
| **Components** (`src/components`) | 80 | 32 | 60% gap |
| **Features** (`src/features`) | 81 | 56 | 31% gap |
| **Hooks** (`src/hooks`) | 15 | 7 | 53% gap |
| **Lib/Utils** (`src/lib`) | 6 | 3 | 50% gap |
| **Types** (`src/types`) | 10 | 0 | 100% gap |
| **Contexts** (`src/contexts`) | 3 | 1 | 67% gap |
| **TOTAL** | **235** | **107** | **54% gap** |

### 3. Components Without Tests

#### High Priority (Core User Flows)

**Pages (24 files, 0 tests):**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/app/login/page.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/app/schedule/page.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/app/my-schedule/page.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/app/swaps/page.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/app/absences/page.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/app/people/page.tsx`
- All other pages...

**Critical Components (No Tests):**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/Navigation.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/UserMenu.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/MobileNav.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/EmptyState.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/LoadingSpinner.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/LoadingStates.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/Modal.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/Toast.tsx`

**Schedule Components (Partially Covered):**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/MonthView.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/WeekView.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/ScheduleGrid.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/ScheduleHeader.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/ScheduleLegend.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/MyScheduleWidget.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/PersonalScheduleCard.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/QuickSwapButton.tsx` - No test
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/WorkHoursCalculator.tsx` - No test

**Drag-and-Drop Components (0% coverage):**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/drag/DraggableBlockCell.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/drag/FacultyInpatientWeeksView.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/drag/ResidentAcademicYearView.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/schedule/drag/ScheduleDragProvider.tsx`

#### Medium Priority (Supporting Features)

**Dashboard Components:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/dashboard/QuickActions.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/dashboard/ScheduleSummary.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/dashboard/UpcomingAbsences.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/dashboard/UpcomingAssignmentsPreview.tsx`

**Form Components:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/forms/Input.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/forms/Select.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/forms/TextArea.tsx`

**Common Components:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/common/Breadcrumbs.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/common/CopyToClipboard.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/common/KeyboardShortcutHelp.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/common/ProgressIndicator.tsx`

**Admin Components:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/admin/AlgorithmComparisonChart.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/admin/ClaudeCodeChat.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/admin/ConfigurationPresets.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/admin/CoverageTrendChart.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/admin/MCPCapabilitiesPanel.tsx`

**Game Theory Components:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/game-theory/EvolutionChart.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/game-theory/PayoffMatrix.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/game-theory/StrategyCard.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/game-theory/TournamentCard.tsx`

#### Low Priority (Edge Features)

**3D Visualization:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/features/voxel-schedule/VoxelScheduleView.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/features/holographic-hub/HolographicManifold.tsx`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/features/holographic-hub/LayerControlPanel.tsx`

**RAG Search:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/rag/RAGSearch.tsx`

**Skeleton Loaders (6 files):**
- All files in `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/components/skeletons/`

### 4. Hooks Without Tests

**Missing Tests (8 hooks):**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useBlocks.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useClaudeChat.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useGameTheory.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useHealth.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useRAG.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useResilience.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useAdminScheduling.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/src/hooks/useWebSocket.ts`

### 5. Feature Modules Status

| Feature Module | Source Files | Test Files | Status |
|----------------|--------------|------------|--------|
| **analytics** | 8 | 10 | ✅ Over-tested (good!) |
| **audit** | 8 | 7 | ✅ Well covered |
| **call-roster** | 7 | 3 | ⚠️ Needs more tests |
| **conflicts** | 10 | 2 | ⚠️ 80% gap |
| **daily-manifest** | 6 | 4 | ✅ Good coverage |
| **fmit-timeline** | 6 | 1 | ⚠️ 83% gap |
| **heatmap** | 6 | 4 | ✅ Good coverage |
| **holographic-hub** | 7 | 0 | ❌ 100% gap |
| **import-export** | 9 | 1 | ⚠️ 89% gap |
| **my-dashboard** | 7 | 6 | ✅ Excellent |
| **swap-marketplace** | 8 | 10 | ✅ Over-tested (good!) |
| **templates** | 12 | 10 | ✅ Good coverage |
| **voxel-schedule** | 3 | 0 | ❌ 100% gap |
| **resilience** | 0 | 4 | ❌ Tests orphaned |

### 6. Contexts Status

| Context | Has Test | Priority |
|---------|----------|----------|
| `AuthContext.tsx` | ✅ Yes | Critical |
| `ToastContext.tsx` | ❌ No | High |
| `ClaudeChatContext.tsx` | ❌ No | Medium |

---

## Recommendations

### Phase 1: Fix Critical Infrastructure (Week 1)

#### 1.1 Update Jest Coverage Configuration

**File:** `/home/user/Autonomous-Assignment-Program-Manager/frontend/jest.config.js`

```javascript
collectCoverageFrom: [
  'src/**/*.{ts,tsx}',
  '!src/**/*.d.ts',
  '!src/**/*.stories.tsx',
  '!src/**/*.test.{ts,tsx}',
  '!src/app/layout.tsx',           // Next.js boilerplate
  '!src/app/providers.tsx',        // Provider wrapper only
  '!src/mocks/**',                 // Test mocks
  '!src/types/**',                 // Type definitions only
],
```

#### 1.2 Resolve Missing Source Files

**Action Items:**
1. **Create Resilience Feature Module** (4 orphaned tests)
   - Implement components referenced in tests:
     - `HealthStatusIndicator`
     - `ContingencyAnalysis`
     - `HubVisualization`
     - Resilience hub main component

2. **Create useProcedures Hook**
   - Based on test expectations in `Credentialing.test.tsx`
   - Implement: `useProcedures`, `useProcedure`, `useCredentials`

3. **Review FMIT Feature**
   - Check if `FMITDetection.tsx` should exist or test should be removed

#### 1.3 Fix Module Resolution Errors

**Issue:** `@/` path aliases not resolving correctly in Jest

**Solution:** Verify `tsconfig.jest.json` matches `tsconfig.json` paths:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Phase 2: High-Priority Test Coverage (Weeks 2-3)

Target components by user impact and criticality:

#### 2.1 Core User Flow Tests (Target: 90% coverage)

**Priority Order:**

1. **Navigation & Auth (Week 2, Days 1-2)**
   - `Navigation.tsx`
   - `UserMenu.tsx`
   - `MobileNav.tsx`
   - `ToastContext.tsx`
   - `ProtectedRoute.tsx` (add more scenarios)

2. **Schedule View Components (Week 2, Days 3-5)**
   - `ScheduleGrid.tsx`
   - `MonthView.tsx`
   - `WeekView.tsx`
   - `ScheduleHeader.tsx`
   - `ScheduleLegend.tsx`

3. **Modal/Dialog Components (Week 3, Days 1-2)**
   - `Modal.tsx`
   - `ConfirmDialog.tsx` (add edge cases)
   - `GenerateScheduleDialog.tsx`

4. **Loading & Error States (Week 3, Day 3)**
   - `LoadingSpinner.tsx`
   - `LoadingStates.tsx`
   - `EmptyState.tsx`
   - `ErrorAlert.tsx`

#### 2.2 Form Component Tests (Week 3, Days 4-5)

- `Input.tsx`
- `Select.tsx`
- `TextArea.tsx`
- `DatePicker.tsx` (add more edge cases)

### Phase 3: Feature Module Completion (Weeks 4-5)

#### 3.1 Conflicts Feature (Week 4, Days 1-2)

Missing tests for:
- `ConflictCard.tsx`
- `ConflictHistory.tsx`
- `ConflictResolutionSuggestions.tsx`
- `BatchResolution.tsx`
- `ManualOverrideModal.tsx`

#### 3.2 Import/Export Feature (Week 4, Days 3-4)

Missing tests for:
- `BulkImportModal.tsx`
- `ImportPreview.tsx`
- `ImportProgressIndicator.tsx`
- `useExport.ts`
- `useImport.ts`
- `validation.ts`

#### 3.3 Call Roster Feature (Week 4, Day 5)

Missing tests for:
- `CallCalendarDay.tsx`
- `CallRoster.tsx` (main component)
- Enhanced coverage for `hooks.ts`

#### 3.4 FMIT Timeline (Week 5, Days 1-2)

Missing tests for:
- `FMITTimeline.tsx`
- `TimelineControls.tsx`
- `TimelineRow.tsx`

### Phase 4: Hook Testing (Week 5, Days 3-4)

Test all untested hooks:
- `useBlocks.ts`
- `useClaudeChat.ts`
- `useGameTheory.ts`
- `useHealth.ts`
- `useRAG.ts`
- `useResilience.ts`
- `useAdminScheduling.ts`
- `useWebSocket.ts`

### Phase 5: Admin & Advanced Features (Week 5, Day 5)

**Low priority but should hit 60% coverage:**
- Admin components (5 files)
- Game theory components (4 files)
- Dashboard components (4 files)
- Common utilities (4 files)

### Phase 6: Edge Cases & Polish (Week 6)

- Skeleton loaders (nice-to-have)
- 3D visualization features (low priority)
- RAG search component
- Increase coverage on existing tests to 90%

---

## Test Writing Guidelines

### Component Test Template

```typescript
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ComponentName } from '@/components/ComponentName';

describe('ComponentName', () => {
  it('renders correctly with required props', () => {
    render(<ComponentName prop="value" />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const mockCallback = jest.fn();

    render(<ComponentName onAction={mockCallback} />);

    await user.click(screen.getByRole('button', { name: /action/i }));

    expect(mockCallback).toHaveBeenCalledTimes(1);
  });

  it('shows error state', () => {
    render(<ComponentName error="Error message" />);
    expect(screen.getByText('Error message')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ComponentName isLoading />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
```

### Hook Test Template

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCustomHook } from '@/hooks/useCustomHook';
import * as api from '@/lib/api';

jest.mock('@/lib/api');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useCustomHook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('fetches data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    jest.spyOn(api, 'get').mockResolvedValue(mockData);

    const { result } = renderHook(() => useCustomHook(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockData);
  });

  it('handles errors', async () => {
    jest.spyOn(api, 'get').mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useCustomHook(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });
});
```

---

## Success Metrics

### Coverage Targets

| Phase | Target Coverage | ETA |
|-------|----------------|-----|
| **Phase 1** (Infrastructure) | Fix config, 0% → actual baseline | Week 1 |
| **Phase 2** (Core) | 40% → 70% | Week 3 |
| **Phase 3** (Features) | 70% → 80% | Week 5 |
| **Phase 4** (Hooks) | 80% → 85% | Week 5 |
| **Phase 5** (Admin) | 85% → 90% | Week 6 |
| **Phase 6** (Polish) | 90%+ | Week 6 |

### Test Quality Metrics

- **Flaky test rate:** < 1%
- **Test execution time:** < 60 seconds for full suite
- **Coverage by type:**
  - **Statements:** 90%+
  - **Branches:** 85%+ (conditional logic)
  - **Functions:** 90%+
  - **Lines:** 90%+

---

## Action Items Summary

### Immediate (This Week)

1. ✅ **Fix `jest.config.js`** to collect coverage from all source files
2. ✅ **Create missing source files** (resilience feature, useProcedures hook)
3. ✅ **Fix module resolution** errors in Jest/TypeScript config
4. ✅ **Establish baseline coverage** with corrected configuration

### High Priority (Next 2 Weeks)

5. ✅ Write tests for core navigation components (Navigation, UserMenu, MobileNav)
6. ✅ Write tests for schedule view components (Grid, Month, Week, Header)
7. ✅ Write tests for modal/dialog components
8. ✅ Write tests for form components
9. ✅ Complete conflicts feature tests
10. ✅ Complete import/export feature tests

### Medium Priority (Weeks 4-5)

11. ✅ Test all untested hooks (8 hooks)
12. ✅ Complete call roster feature tests
13. ✅ Complete FMIT timeline tests
14. ✅ Test admin components
15. ✅ Test dashboard components

### Low Priority (Week 6)

16. ✅ Test skeleton loaders
17. ✅ Test 3D visualization features
18. ✅ Increase coverage on existing tests to 90%

---

## Appendix

### Test Command Reference

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- __tests__/components/Navigation.test.tsx

# Run tests in watch mode
npm run test:watch

# Run tests matching pattern
npm test -- --testNamePattern="Navigation"

# Run tests for changed files only
npm test -- --onlyChanged

# Update snapshots
npm test -- -u

# Run with verbose output
npm test -- --verbose

# CI mode (no watch, coverage required)
npm run test:ci
```

### Useful Testing Utilities

**Location:** `/home/user/Autonomous-Assignment-Program-Manager/frontend/__tests__/utils/test-utils.ts`

```typescript
// Create wrapper with providers
import { createWrapper } from '../utils/test-utils';

const { result } = renderHook(() => useCustomHook(), {
  wrapper: createWrapper(),
});
```

**Mock Factories:**
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/__tests__/features/resilience/resilience-mocks.ts`
- `/home/user/Autonomous-Assignment-Program-Manager/frontend/__tests__/utils/test-utils.ts`

---

## Conclusion

**Current Status:** The frontend test infrastructure is in place but has critical configuration issues preventing accurate coverage measurement. 89 test suites are failing due to missing source files (orphaned tests).

**Key Blocker:** Coverage is only being collected from `src/lib/**`, which represents less than 5% of the codebase.

**Recommended Path:**
1. **Week 1:** Fix configuration, implement missing features, establish true baseline
2. **Weeks 2-3:** Focus on core user flows (navigation, schedule views, forms)
3. **Weeks 4-5:** Complete feature modules and hook tests
4. **Week 6:** Polish and achieve 90% coverage target

**Estimated Effort:** 6 weeks with dedicated focus, achievable within Marathon Plan timeline.

**Next Steps:** Begin Phase 1 (Infrastructure fixes) immediately to unblock accurate coverage measurement.
