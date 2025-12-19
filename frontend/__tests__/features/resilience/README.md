# Resilience Hub Frontend Tests

This directory contains comprehensive test suites for the Resilience Hub frontend components.

## Test Files

### 1. `resilience-hub.test.tsx`
Main dashboard component tests covering:
- **Initial Rendering** (5 tests): Title, description, buttons, view toggles, and data fetching
- **Loading State** (2 tests): Skeleton loading and loading text
- **Error State** (3 tests): Error messages, retry functionality, and error recovery
- **Green Status** (6 tests): Healthy system indicators, optimal utilization, defense levels
- **Yellow Status** (6 tests): Warning indicators, high utilization, N-2 failures
- **Red Status** (7 tests): Critical status, containment mode, crisis indicators
- **Redundancy Status** (5 tests): N+1/N+2 indicators, service redundancy display
- **User Interactions** (3 tests): Tab switching, refresh functionality, modal triggers
- **Utilization Metrics** (4 tests): Progress bars, buffer display, wait time multipliers
- **Quick Actions** (4 tests): Fallback buttons, analysis triggers, modal interactions
- **Auto-Refresh** (2 tests): Automatic polling, cleanup on unmount
- **Accessibility** (3 tests): ARIA labels, keyboard navigation, screen reader support
- **Custom ClassName** (1 test): CSS class application

**Total: 51 test cases**

### 2. `health-status.test.tsx`
Health status indicator component tests covering:
- **Green Status Rendering** (8 tests): Green badges, healthy icons, optimal levels
- **Yellow Status Rendering** (8 tests): Yellow badges, warning icons, degraded status
- **Orange Status Rendering** (5 tests): Orange badges, elevated risk indicators
- **Red Status Rendering** (7 tests): Red badges, critical status, crisis mode, pulsing animations
- **Black Status Rendering** (6 tests): Black badges, emergency mode, catastrophic indicators
- **Utilization Display** (6 tests): Progress bars, color coding, buffer display
- **N-1/N-2 Status Display** (5 tests): Pass/fail indicators, checkmarks and X icons
- **Phase Transition Risk** (3 tests): Risk levels with color-coded badges
- **Active Fallbacks** (3 tests): Fallback count display and highlighting
- **Interactive Features** (3 tests): Expandable details, tooltips, onChange callbacks
- **Timestamp Display** (2 tests): Last updated time, relative formatting
- **Accessibility** (3 tests): ARIA labels, progress bar attributes, screen reader announcements
- **Compact Mode** (2 tests): Reduced information display, essential-only view
- **Custom ClassName** (1 test): CSS class application

**Total: 62 test cases**

### 3. `contingency-analysis.test.tsx`
Contingency analysis component tests covering:
- **Initial Rendering** (5 tests): Title, description, buttons, date range selector, data fetching
- **Loading State** (3 tests): Loading skeleton, loading text, disabled buttons
- **Error State** (3 tests): Error messages, retry button, error recovery
- **N-1/N-2 Summary** (5 tests): Pass/fail status, risk percentages, timestamps
- **N-1 Vulnerabilities Display** (6 tests): Faculty lists, severity badges, affected blocks, empty states
- **N-2 Fatal Pairs Display** (5 tests): Pair identification, warnings, empty states
- **Critical Faculty Display** (8 tests): Centrality scores, services covered, replacement difficulty, risk levels
- **Recommended Actions** (5 tests): Action lists, checkboxes, completion tracking
- **User Interactions** (4 tests): Analysis triggers, date filtering, faculty expansion, export
- **Filtering and Sorting** (3 tests): Severity filters, sort options, faculty search
- **Visual Indicators** (3 tests): Heatmaps, score visualizations, network graphs
- **Accessibility** (3 tests): Heading hierarchy, accessible tables, screen reader announcements
- **Custom ClassName** (1 test): CSS class application

**Total: 54 test cases**

## Mock Data

### `resilience-mocks.ts`
Comprehensive mock data factories and responses including:
- **Health Check States**: Green (healthy), Yellow (warning), Red (critical), Black (emergency)
- **Contingency Reports**: N-1/N-2 analysis, vulnerabilities, fatal pairs
- **Fallback Schedules**: Pre-computed scenarios, activation status
- **Load Shedding**: Activity suspension levels
- **Event History**: System events and state changes

## Test Coverage Summary

| Component | Test Cases | Coverage Areas |
|-----------|-----------|----------------|
| Resilience Hub | 51 | Dashboard rendering, status displays, user interactions |
| Health Status | 62 | Status indicators (5 levels), metrics, accessibility |
| Contingency Analysis | 54 | Vulnerability analysis, critical faculty, recommendations |
| **Total** | **167** | **Comprehensive coverage** |

## Running the Tests

```bash
# Run all resilience tests
npm test -- resilience

# Run specific test file
npm test -- resilience-hub.test.tsx
npm test -- health-status.test.tsx
npm test -- contingency-analysis.test.tsx

# Run with coverage
npm test -- --coverage resilience

# Run in watch mode
npm test -- --watch resilience
```

## Test Patterns Used

1. **React Testing Library**: All tests use RTL for component rendering and queries
2. **User Event**: Simulates real user interactions (clicks, typing, hovering)
3. **API Mocking**: Jest mocks for `@/lib/api` module
4. **Async Patterns**: `waitFor` for asynchronous assertions
5. **Accessibility**: ARIA labels, roles, and screen reader support testing
6. **Error Boundaries**: Proper error state handling and retry mechanisms

## Component Props Expected

### ResilienceHub
```typescript
interface ResilienceHubProps {
  className?: string;
}
```

### HealthStatusIndicator
```typescript
interface HealthStatusIndicatorProps {
  status: HealthCheckResponse;
  className?: string;
  compact?: boolean;
  expandable?: boolean;
  onChange?: (newStatus: string, oldStatus: string) => void;
}
```

### ContingencyAnalysis
```typescript
interface ContingencyAnalysisProps {
  className?: string;
}
```

## Backend API Endpoints

Tests mock the following API endpoints:
- `GET /resilience/health` - System health check
- `GET /resilience/vulnerability` - N-1/N-2 analysis
- `GET /resilience/fallbacks` - Fallback schedules
- `GET /resilience/history/events` - Event history
- `POST /resilience/vulnerability/export` - Export analysis

## Defense Levels

The tests cover all five defense levels from nuclear safety paradigm:
1. **PREVENTION** (Green) - Normal operations, proactive measures
2. **CONTROL** (Yellow) - Early warning, monitoring activated
3. **SAFETY_SYSTEMS** (Orange) - Automated responses engaged
4. **CONTAINMENT** (Red) - Service reduction, crisis mode
5. **EMERGENCY** (Black) - Emergency protocols, external escalation

## Status Levels

Tests validate proper rendering of all status levels:
- **Green**: System healthy, 75-80% utilization
- **Yellow**: Warning, 80-85% utilization, N-2 may fail
- **Orange**: Degraded, 85-90% utilization, safety systems active
- **Red**: Critical, 90-95% utilization, crisis mode
- **Black**: Emergency, 95%+ utilization, catastrophic failure imminent

## Notes

- All components support custom CSS classes via `className` prop
- Tests follow the existing pattern from analytics and audit features
- Mock data matches backend API response schemas
- Accessibility is a first-class concern in all components
- Tests validate both happy path and error scenarios
- Loading states and transitions are thoroughly tested

## Future Enhancements

Potential areas for additional testing:
- Integration tests with actual API calls
- E2E tests with Playwright
- Performance testing for large datasets
- Visual regression testing for status transitions
- Mobile responsive layout tests
