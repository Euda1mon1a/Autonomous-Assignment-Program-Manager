# Audit Feature Test Suite

Comprehensive test suite for the Audit Log feature module.

## Overview

This test suite provides extensive coverage for all components in the audit feature, including:
- Data fetching and state management (hooks)
- UI components (table, filters, timeline, etc.)
- User interactions and workflows
- Edge cases and error handling

## Test Files

### Component Tests

1. **AuditLogTable.test.tsx** (25+ test cases)
   - Table rendering with audit entries
   - Sorting functionality (all sortable columns)
   - Pagination controls (next, previous, page numbers, page size)
   - Expandable rows with change details
   - Row selection and highlighting
   - ACGME override display
   - Loading and empty states
   - Accessibility features

2. **AuditLogFilters.test.tsx** (30+ test cases)
   - Search with debouncing
   - Date range picker (quick selects and custom dates)
   - Multi-select filters (entity type, action, user, severity)
   - ACGME override checkbox filter
   - Active filter tags with removal
   - Clear all filters functionality
   - Filter combinations
   - Accessibility features

3. **AuditLogExport.test.tsx** (20+ test cases)
   - Export modal open/close
   - Format selection (CSV, JSON, PDF)
   - Export options (metadata, change details)
   - Quick export buttons
   - Export with filters
   - Loading and success/error states
   - Accessibility features

4. **AuditTimeline.test.tsx** (25+ test cases)
   - Timeline rendering with events
   - Date grouping and "Today" display
   - Event cards with all details
   - Action icons and colors
   - ACGME override styling
   - Expand/collapse date groups
   - Event selection
   - Scrolling and max height
   - Special event types
   - Accessibility features

5. **ChangeComparison.test.tsx** (25+ test cases)
   - Single entry detail view
   - Side-by-side comparison mode
   - Change display (before/after values)
   - Value formatting (null, boolean, dates, arrays)
   - ACGME override information
   - Metadata display
   - Technical details (IDs, IP address)
   - Close and clear functionality
   - Accessibility features

6. **AuditLogPage.test.tsx** (30+ test cases)
   - Page layout and structure
   - Statistics cards display
   - View mode switching (table, timeline, comparison)
   - Refresh functionality
   - Filter integration
   - Entry selection in different views
   - Comparison mode workflow
   - Detail panel display
   - Pagination integration
   - Loading states
   - Responsive layout
   - Accessibility features

### Hook Tests

7. **hooks.test.ts** (30+ test cases)
   - `useAuditLogs` - fetch with filters, pagination, sorting
   - `useAuditLogEntry` - single entry fetch
   - `useAuditStatistics` - statistics with date range
   - `useAuditTimeline` - timeline events transformation
   - `useEntityAuditHistory` - entity-specific history
   - `useUserAuditActivity` - user activity logs
   - `useAuditUsers` - available users list
   - `useExportAuditLogs` - export mutation
   - `useMarkAuditReviewed` - review marking mutation
   - Query key generation
   - Loading and error states

### Test Data

8. **mockData.ts**
   - Comprehensive mock audit log entries (15+ entries)
   - Mock users (4 users)
   - Mock statistics
   - Mock paginated responses
   - Helper functions for generating test data
   - Various scenarios (ACGME overrides, different actions, severities)

## Test Coverage

### Features Tested

- ✅ Audit log list rendering
- ✅ Filtering functionality (7+ filter types)
- ✅ Date range selection (quick picks + custom)
- ✅ User selection
- ✅ Export functionality (3 formats)
- ✅ Pagination (page navigation + size selection)
- ✅ Detail view (single entry)
- ✅ Comparison view (side-by-side)
- ✅ Timeline visualization
- ✅ Sorting (5 sortable fields)
- ✅ Search with debouncing
- ✅ ACGME override handling
- ✅ Loading states
- ✅ Error handling
- ✅ Accessibility (ARIA labels, keyboard navigation)

### Total Test Cases

**200+ individual test cases** across all test files covering:
- Unit tests for individual components
- Integration tests for component interactions
- Hook tests for data fetching
- Accessibility tests
- Edge case handling

## Running the Tests

```bash
# Run all audit feature tests
npm test -- audit

# Run specific test file
npm test -- AuditLogTable.test.tsx

# Run with coverage
npm test -- --coverage audit

# Watch mode for development
npm test -- --watch audit
```

## Test Patterns

### Component Test Structure
```typescript
describe('ComponentName', () => {
  describe('Rendering', () => {
    // Tests for initial render
  });

  describe('Interactions', () => {
    // Tests for user interactions
  });

  describe('Edge Cases', () => {
    // Tests for edge cases and errors
  });

  describe('Accessibility', () => {
    // Tests for accessibility features
  });
});
```

### Hook Test Structure
```typescript
describe('hookName', () => {
  it('should fetch data successfully', async () => {
    // Setup mock
    // Render hook
    // Assert results
  });

  it('should handle loading state', () => {
    // Test loading state
  });

  it('should handle error state', async () => {
    // Test error handling
  });
});
```

## Test Utilities

### Custom Wrappers
- `createWrapper()` - QueryClient wrapper for hooks and components
- Mock functions for all API calls
- Custom render functions with providers

### Mock Data Helpers
- `getMockLogs(count)` - Get subset of mock logs
- `getMockLogsByEntityType(type)` - Filter by entity type
- `getMockACGMEOverrideLogs()` - Get ACGME override logs
- `getMockLogsBySeverity(severity)` - Filter by severity
- `createMockAuditLog(overrides)` - Create custom mock entry

## Best Practices

1. **Test Isolation**: Each test is independent and doesn't rely on others
2. **Clear Mocking**: All external dependencies are properly mocked
3. **User-Centric**: Tests focus on user interactions and visible behavior
4. **Accessibility**: Every component includes accessibility tests
5. **Error Handling**: Both success and failure paths are tested
6. **Real Scenarios**: Test data reflects actual use cases

## Maintenance

### Adding New Tests
1. Follow the existing test structure
2. Use descriptive test names
3. Include both positive and negative test cases
4. Add accessibility tests for new features
5. Update mock data if needed

### Updating Tests
- Update tests when component behavior changes
- Keep mock data realistic and up-to-date
- Ensure tests remain fast and reliable
- Document any complex test setups

## Coverage Goals

- **Line Coverage**: >80%
- **Branch Coverage**: >75%
- **Function Coverage**: >80%
- **Statement Coverage**: >80%

## Related Documentation

- Component documentation: `/frontend/src/features/audit/`
- API documentation: `/docs/api/audit.md`
- User guide: `/docs/user-guide/audit-logs.md`
