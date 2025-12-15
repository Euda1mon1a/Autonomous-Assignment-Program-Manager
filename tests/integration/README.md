# API Integration Tests

Comprehensive integration tests for the Residency Scheduler API.

## Overview

This test suite provides end-to-end integration testing for all API endpoints, including:

- **Authentication**: Login, logout, registration, user management
- **People**: CRUD operations for residents and faculty
- **Blocks**: Schedule block management
- **Absences**: Vacation, deployment, and absence tracking
- **Assignments**: Rotation assignments with ACGME validation
- **Schedule**: Schedule generation and validation
- **Export**: Data export in CSV, JSON, and Excel formats

## Prerequisites

1. **Backend API Running**: Ensure the FastAPI backend is running and accessible
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Test Database**: The backend should use a separate test database or support database reset between test runs

3. **Node.js**: Version 18 or higher

## Installation

```bash
cd tests/integration
npm install
```

## Configuration

Set the API base URL via environment variable (optional):

```bash
export API_BASE_URL=http://localhost:8000/api
```

Default: `http://localhost:8000/api`

## Running Tests

### Run all tests
```bash
npm test
```

### Run tests in watch mode
```bash
npm run test:watch
```

### Run tests with coverage
```bash
npm run test:coverage
```

### Run tests verbosely
```bash
npm run test:verbose
```

### Run tests for CI/CD
```bash
npm run test:ci
```

## Test Structure

### setup.ts
Contains:
- `ApiClient`: HTTP client wrapper with authentication support
- `TestDatabase`: Database setup and fixture creation helpers
- Test fixtures for people, blocks, absences, and assignments
- Assertion helpers for common response patterns
- Utility functions for dates, retries, and UUID validation

### api.test.ts
Comprehensive test suites organized by endpoint:

1. **Auth Endpoints** (POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout)
   - User registration and authentication
   - Error cases: invalid credentials, duplicate users
   - Token management

2. **People Endpoints** (GET/POST/PUT/DELETE /api/people)
   - CRUD operations for residents and faculty
   - Filtering by type, PGY level, specialty
   - Validation: required fields, PGY level range, person type
   - Error cases: 401 unauthorized, 404 not found

3. **Blocks Endpoints** (GET/POST/DELETE /api/blocks, POST /api/blocks/generate)
   - Block creation and management
   - Bulk block generation
   - Filtering by date range and block number
   - Error cases: duplicate blocks, invalid dates

4. **Absences Endpoints** (GET/POST/PUT/DELETE /api/absences)
   - Absence tracking for residents and faculty
   - Filtering by person, type, date range
   - Validation: absence type, date range
   - Error cases: invalid dates, missing required fields

5. **Assignments Endpoints** (GET/POST/PUT/DELETE /api/assignments)
   - Assignment CRUD with ACGME compliance checking
   - Optimistic locking for concurrent updates
   - Filtering by person, role, date range
   - Error cases: duplicate assignments, invalid roles, 409 conflicts

6. **Schedule Endpoints** (GET /api/schedule/:start/:end, POST /api/schedule/generate, GET /api/schedule/validate)
   - Schedule retrieval and generation
   - ACGME validation
   - Algorithm selection (greedy, cp_sat, pulp, hybrid)
   - Error cases: invalid dates, invalid algorithms

7. **Export Endpoints** (GET /api/export/people, GET /api/export/absences, GET /api/export/schedule, GET /api/export/schedule/xlsx)
   - Data export in multiple formats (CSV, JSON, Excel)
   - Filtering and date range support
   - Error cases: missing required parameters

8. **Error Handling**
   - 404 for non-existent endpoints
   - 400 for validation errors
   - 401 for unauthorized access
   - Malformed JSON handling
   - Invalid UUID handling

## Test Patterns

### Authentication Pattern
```typescript
const client = new ApiClient();
await client.login(username, password);
// Make authenticated requests
await client.logout();
```

### Assertion Helpers
```typescript
assertSuccessResponse(response, 200);
assertUnauthorized(response);
assertNotFound(response, 'Resource not found');
assertValidationError(response);
```

### Creating Test Data
```typescript
const db = new TestDatabase(client);
const { residents, faculty } = await db.setupPeople();
const blocks = await db.setupBlocks(new Date(), 7);
```

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Clean up test data after each test or test suite
3. **Realistic Data**: Use realistic test fixtures that match production data
4. **Error Cases**: Always test both success and failure scenarios
5. **Authentication**: Test both authenticated and unauthenticated access
6. **Edge Cases**: Test boundary conditions (empty lists, max values, etc.)

## Troubleshooting

### Tests failing with connection errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check API_BASE_URL environment variable
- Ensure no firewall blocking localhost connections

### Tests timing out
- Increase timeout in jest.config.js
- Check if backend is responding slowly
- Verify database connection

### Database conflicts
- Tests run serially (maxWorkers=1) to avoid conflicts
- Ensure test database is properly isolated
- Check that database is reset between runs

### Authentication failures
- First test creates admin user; ensure clean database state
- Check that user registration endpoint is working
- Verify token generation and validation

## Coverage

Run coverage report to see test coverage:
```bash
npm run test:coverage
```

Coverage reports are generated in `coverage/` directory.

## Contributing

When adding new endpoints:
1. Add corresponding tests to api.test.ts
2. Add fixtures to setup.ts if needed
3. Test success cases, error cases (401, 404, 400), and edge cases
4. Update this README with new test descriptions

## CI/CD Integration

For continuous integration:
```bash
# In your CI pipeline
cd tests/integration
npm ci
npm run test:ci
```

The `test:ci` script is optimized for CI environments with:
- `--ci` flag for CI-specific behavior
- `--coverage` for code coverage
- `--maxWorkers=2` for controlled parallelism
- Exit code reflects test pass/fail status
