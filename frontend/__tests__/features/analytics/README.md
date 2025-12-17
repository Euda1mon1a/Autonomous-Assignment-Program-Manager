# Analytics Feature Tests

Comprehensive test suite for the Analytics feature module, covering all components and hooks with 169 test cases.

## Test Files

### Component Tests

#### 1. MetricsCard.test.tsx (34 test cases)
Tests for the `MetricsCard` component that displays individual metric information.

**Coverage:**
- ✅ Rendering metric name, value, and description
- ✅ Value formatting (percentages, scores, integers)
- ✅ Status indicators (excellent, good, warning, critical)
- ✅ Status-based background colors
- ✅ Trend indicators (up, down, stable)
- ✅ Trend value display with proper signs
- ✅ Threshold display with warning/critical values
- ✅ Progress bar visualization
- ✅ Compact mode rendering
- ✅ Click interaction handling
- ✅ Hover styles for clickable cards
- ✅ Loading skeleton states
- ✅ Custom className application

#### 2. FairnessTrend.test.tsx (20 test cases)
Tests for the `FairnessTrend` component that displays fairness metrics over time.

**Coverage:**
- ✅ Loading state with skeleton
- ✅ Error state handling
- ✅ Chart title and subtitle rendering
- ✅ Statistics summary display (avg Gini, variance, PGY equity)
- ✅ Improvement rate display
- ✅ Metric selector functionality
- ✅ PGY equity comparison chart
- ✅ Toggle PGY comparison visibility
- ✅ API integration with correct time periods (3, 6, 12 months)
- ✅ Custom className support

#### 3. VersionComparison.test.tsx (24 test cases)
Tests for the `VersionComparison` component for comparing schedule versions.

**Coverage:**
- ✅ Initial state with empty message
- ✅ Version selector rendering
- ✅ Loading available versions
- ✅ Version A and B selection
- ✅ Loading state during comparison
- ✅ Impact assessment display (positive/negative/neutral)
- ✅ Affected residents count
- ✅ Risk level display (low/medium/high)
- ✅ Metric changes section
- ✅ Metric deltas with arrows
- ✅ Impact bars (fairness, coverage, compliance)
- ✅ Expand/collapse impact details
- ✅ Category filtering (all, fairness, coverage, compliance, workload)
- ✅ Recommendation display
- ✅ Error handling
- ✅ API integration with correct parameters

#### 4. WhatIfAnalysis.test.tsx (31 test cases)
Tests for the `WhatIfAnalysis` component for simulating schedule changes.

**Coverage:**
- ✅ Title and description rendering
- ✅ Base version selector
- ✅ Analysis scope selector (immediate, week, month, quarter)
- ✅ Empty state for no changes
- ✅ Add Change button functionality
- ✅ Change type selection (6 types)
- ✅ Change description editing
- ✅ Change removal
- ✅ Change number badges
- ✅ Parameters JSON editing
- ✅ Run button disabled/enabled states
- ✅ Running analysis with correct API call
- ✅ Loading state during analysis
- ✅ Results display
- ✅ Recommendation display (approved/not recommended)
- ✅ Confidence score display
- ✅ Warnings display
- ✅ Constraint impacts display
- ✅ Error handling

#### 5. AnalyticsDashboard.test.tsx (31 test cases)
Tests for the main `AnalyticsDashboard` component.

**Coverage:**
- ✅ Dashboard title and description
- ✅ Refresh and Export buttons
- ✅ View tabs (Overview, Trends, Comparison, What-If)
- ✅ Tab navigation and switching
- ✅ Quick stats (total, excellent, warning, critical counts)
- ✅ Key metrics section
- ✅ All 7 metric cards display
- ✅ Loading skeletons for metrics
- ✅ Error message for failed metrics load
- ✅ Alerts section rendering
- ✅ Alert count display
- ✅ Toggle acknowledged alerts
- ✅ Empty state for no alerts
- ✅ Fairness trends preview
- ✅ Refresh functionality with API call
- ✅ Export functionality with PDF format
- ✅ View content rendering for each tab
- ✅ API integration for metrics and alerts
- ✅ Custom className support

### Hook Tests

#### 6. hooks.test.ts (29 test cases)
Tests for all analytics data fetching and mutation hooks.

**Query Hooks Coverage:**
- ✅ `useCurrentMetrics` - fetch, cache, and error handling
- ✅ `useFairnessTrend` - fetch with different time periods, error handling
- ✅ `usePgyEquity` - fetch and error handling
- ✅ `useVersionComparison` - fetch with version IDs, disabled state, error handling
- ✅ `useScheduleVersions` - fetch and error handling
- ✅ `useMetricAlerts` - fetch all/filtered alerts, error handling

**Mutation Hooks Coverage:**
- ✅ `useWhatIfAnalysis` - submit analysis request, error handling
- ✅ `useAcknowledgeAlert` - acknowledge with/without notes, error handling
- ✅ `useDismissAlert` - dismiss alert, error handling
- ✅ `useExportAnalytics` - export as PDF/CSV, error handling
- ✅ `useRefreshMetrics` - refresh metrics, error handling

## Mock Data

### analytics-mocks.ts
Comprehensive mock data factories for all analytics types:

**Factories:**
- `metric` - Individual metric with all properties
- `scheduleMetrics` - Complete set of schedule metrics
- `fairnessTrendPoint` - Single trend data point
- `fairnessTrendData` - Complete trend data with statistics
- `pgyEquityData` - PGY level equity data
- `scheduleVersion` - Schedule version with metadata
- `metricDelta` - Metric comparison delta
- `impactAssessment` - Impact assessment with recommendations
- `versionComparison` - Complete version comparison
- `proposedChange` - What-if analysis change
- `warning` - Analysis warning
- `constraintImpact` - Constraint impact data
- `predictedImpact` - What-if analysis predicted impact
- `whatIfAnalysisRequest` - What-if analysis request
- `whatIfAnalysisResult` - Complete what-if analysis result
- `metricAlert` - Metric threshold alert

**Mock Responses:**
- Pre-configured responses for all API endpoints
- Ready-to-use test data for common scenarios

## Running Tests

```bash
# Run all analytics tests
npm test -- features/analytics

# Run specific test file
npm test -- MetricsCard.test.tsx

# Run with coverage
npm test -- --coverage features/analytics

# Watch mode for development
npm test -- --watch features/analytics
```

## Test Coverage Summary

| Component | Test Cases | Coverage Areas |
|-----------|-----------|----------------|
| MetricsCard | 34 | Rendering, status, trends, thresholds, interactions |
| FairnessTrend | 20 | Charts, statistics, selectors, API integration |
| VersionComparison | 24 | Comparison, impact, filtering, navigation |
| WhatIfAnalysis | 31 | Changes, analysis, results, validations |
| AnalyticsDashboard | 31 | Navigation, metrics, alerts, actions |
| Hooks | 29 | Queries, mutations, caching, errors |
| **Total** | **169** | **Comprehensive coverage of all analytics features** |

## Testing Best Practices

1. **Use Mock Factories**: Import from `analytics-mocks.ts` for consistent test data
2. **Test User Interactions**: Use `userEvent` for realistic interaction testing
3. **Wait for Async**: Always use `waitFor` for async operations
4. **Test Error States**: Every component has error state coverage
5. **Test Loading States**: Loading skeletons are tested for better UX
6. **Mock API Calls**: All API calls are mocked using Jest
7. **Query Client Wrapper**: Use `createWrapper()` for React Query hooks

## Common Patterns

### Testing a Component with API Data
```typescript
import { analyticsMockResponses } from './analytics-mocks';
import * as api from '@/lib/api';

jest.mock('@/lib/api');
const mockedApi = api as jest.Mocked<typeof api>;

mockedApi.get.mockResolvedValue(analyticsMockResponses.currentMetrics);

render(<YourComponent />, { wrapper: createWrapper() });

await waitFor(() => {
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

### Testing User Interactions
```typescript
const user = userEvent.setup();
const button = screen.getByText('Click Me');
await user.click(button);

await waitFor(() => {
  expect(mockFunction).toHaveBeenCalled();
});
```

### Testing Hooks
```typescript
const { result } = renderHook(() => useYourHook(), {
  wrapper: createWrapper(),
});

await waitFor(() => {
  expect(result.current.isSuccess).toBe(true);
});
```

## Maintenance

When adding new analytics features:

1. Add mock factory to `analytics-mocks.ts`
2. Create corresponding test file
3. Cover all interaction paths
4. Test loading and error states
5. Update this README with test counts
6. Ensure at least 80% code coverage
