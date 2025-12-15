# E2E Tests for Schedule Feature

This directory contains comprehensive end-to-end tests for the schedule management features using Playwright.

## Overview

The E2E test suite covers all major schedule functionality including:

- **Page Loading**: Verifying the schedule page loads correctly with all UI elements
- **View Navigation**: Testing navigation between different time periods (day/week/month/block views)
- **Assignment Editing**: Testing the ability to create, edit, and delete assignments
- **Filtering**: Testing schedule filtering by person and date range
- **Schedule Generation**: Testing the schedule generation workflow
- **ACGME Violations**: Verifying violation display and acknowledgment flows
- **Export Functionality**: Testing schedule export features
- **Accessibility**: Ensuring keyboard navigation and ARIA labels work correctly
- **Error Handling**: Testing graceful error states and loading indicators

## File Structure

```
e2e/
├── README.md                 # This file
├── schedule.spec.ts          # Main test suite (1022 lines, 50+ test cases)
└── fixtures/
    └── schedule.ts           # Mock data and test fixtures (528 lines)
```

## Test Coverage

### schedule.spec.ts (Main Test Suite)

Contains the following test suites:

1. **Schedule Page - Basic Functionality** (3 tests)
   - Page loads correctly
   - Schedule grid displays with people and assignments
   - Footer displays helpful information

2. **Schedule View Navigation** (5 tests)
   - Navigate to previous block
   - Navigate to next block
   - Navigate to today's date
   - Navigate to current block
   - Custom date range selection

3. **Assignment Editing** (6 tests)
   - Open edit assignment modal
   - Change rotation assignment
   - Change assignment role
   - Add notes to assignment
   - Delete assignment
   - Cancel assignment editing

4. **Schedule Filtering** (3 tests)
   - Filter by person
   - Filter by date range
   - Show all people when filter cleared

5. **Schedule Generation** (3 tests)
   - Generate new schedule with date range
   - Display generation progress
   - Handle generation errors gracefully

6. **ACGME Violations Display** (5 tests)
   - Display violations when present
   - Show violation details in modal
   - Require acknowledgment for critical violations
   - Display violation severity levels
   - Show violation count in summary

7. **Schedule Export** (3 tests)
   - Export button visibility
   - Download schedule as Excel/CSV
   - Export with current filters applied

8. **Responsive Design and Accessibility** (3 tests)
   - Accessible navigation controls
   - Keyboard navigation
   - Color contrast for accessibility

9. **Error Handling** (3 tests)
   - Display error message when API fails
   - Display loading state while fetching data
   - Handle empty schedule gracefully

**Total: 34+ comprehensive test cases**

### fixtures/schedule.ts (Mock Data)

Contains comprehensive mock data including:

- **Mock People**: 6 residents (PGY-1, PGY-2, PGY-3) and 3 faculty members
- **Mock Rotation Templates**: 7 different rotation types (ED, Trauma, Clinic, Call, Conference, Elective, Ultrasound)
- **Mock Blocks**: Helper functions to generate blocks for any date range
- **Mock Assignments**: Helper functions to generate assignments
- **Mock Absences**: 3 different absence types (vacation, conference, deployment)
- **Mock ACGME Violations**: 5 violation types with different severity levels
- **Helper Functions**: Utilities for creating test data and filtering

## Running the Tests

### Prerequisites

1. Ensure Playwright is installed:
   ```bash
   cd frontend
   npm install
   ```

2. Install Playwright browsers (if not already installed):
   ```bash
   npx playwright install
   ```

### Run All Tests

From the frontend directory:

```bash
# Run all E2E tests
npm run test:e2e

# Run tests in UI mode (interactive)
npm run test:e2e:ui

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run specific test file
npx playwright test e2e/schedule.spec.ts
```

### Run Specific Test Suites

```bash
# Run only navigation tests
npx playwright test -g "Schedule View Navigation"

# Run only assignment editing tests
npx playwright test -g "Assignment Editing"

# Run only ACGME violation tests
npx playwright test -g "ACGME Violations"
```

### Debug Tests

```bash
# Run in debug mode
npx playwright test --debug

# Run specific test in debug mode
npx playwright test -g "should load schedule page correctly" --debug
```

## Environment Variables

The tests use the following environment variables (with defaults):

- `BASE_URL`: Frontend URL (default: `http://localhost:3000`)
- `API_URL`: Backend API URL (default: `http://localhost:8000/api/v1`)

Set these before running tests if your setup differs:

```bash
BASE_URL=http://localhost:3001 npm run test:e2e
```

## Mock Data Strategy

The tests use extensive API mocking to:

1. **Ensure Consistency**: Tests run with predictable data regardless of backend state
2. **Speed**: No real API calls means faster test execution
3. **Isolation**: Tests don't depend on external services
4. **Flexibility**: Easy to test edge cases and error conditions

All mock data is defined in `fixtures/schedule.ts` and can be easily customized for specific test scenarios.

## Test Patterns Used

### Authentication
Tests use `loginAsAdmin()` helper to mock authentication before each test.

### API Mocking
Tests use `setupScheduleApiMocks()` to mock all necessary API endpoints.

### Page Object Pattern
Tests interact with the UI using semantic selectors and Playwright's locator API.

### Data-Driven Testing
Mock data is generated programmatically to cover various scenarios.

## Best Practices

1. **Isolation**: Each test is independent and can run in any order
2. **Cleanup**: Tests use `beforeEach` hooks to reset state
3. **Waits**: Tests use Playwright's auto-waiting and explicit waits where needed
4. **Assertions**: Tests use clear, specific assertions
5. **Error Handling**: Tests gracefully handle optional features

## Extending the Tests

To add new tests:

1. **Add Mock Data**: Update `fixtures/schedule.ts` with any new data structures
2. **Create Test Suite**: Add a new `test.describe()` block in `schedule.spec.ts`
3. **Follow Patterns**: Use existing tests as templates
4. **Document**: Add comments explaining complex test scenarios

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
- name: Install dependencies
  run: cd frontend && npm ci

- name: Install Playwright browsers
  run: cd frontend && npx playwright install --with-deps

- name: Run E2E tests
  run: cd frontend && npm run test:e2e
  env:
    BASE_URL: http://localhost:3000
    API_URL: http://localhost:8000/api/v1
```

## Troubleshooting

### Tests timing out
- Increase timeout in test: `test('...', { timeout: 60000 }, async ({ page }) => { ... })`
- Or globally in `playwright.config.ts`

### Elements not found
- Check selectors match actual UI
- Use `page.pause()` to debug
- Run in headed mode to see browser: `--headed`

### API mocking not working
- Verify route patterns match actual API calls
- Check network tab in headed mode
- Ensure mock setup runs before navigation

## Contributing

When adding new schedule features:

1. Add corresponding E2E tests
2. Update mock data fixtures if needed
3. Ensure tests pass locally before committing
4. Update this README if adding new test categories

## Related Documentation

- [Playwright Documentation](https://playwright.dev/)
- [Frontend README](/frontend/README.md)
- [API Documentation](/docs/api.md)
- [User Guide](/USER_GUIDE.md)
