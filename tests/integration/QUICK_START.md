# Quick Start Guide - API Integration Tests

## 🚀 Installation & Setup

### 1. Start the Backend API
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify it's running:
```bash
curl http://localhost:8000/health
```

### 2. Install Test Dependencies
```bash
cd tests/integration
npm install
```

### 3. Run Tests
```bash
# Easy way - using the helper script
./run-tests.sh

# Or directly with npm
npm test
```

## 📊 Test Commands

```bash
npm test              # Run all tests
npm run test:watch    # Watch mode (re-run on changes)
npm run test:coverage # Generate coverage report
npm run test:verbose  # Detailed output
npm run test:ci       # CI/CD mode
```

## 🎯 What Gets Tested

### ✅ Authentication (18 tests)
- User registration, login, logout
- Token management
- Authorization checks

### ✅ People Management (24 tests)
- Residents and faculty CRUD
- PGY level validation
- Type filtering

### ✅ Schedule Blocks (16 tests)
- Block creation and management
- Date range filtering
- Bulk generation

### ✅ Absences (20 tests)
- Vacation, deployment, medical leave
- Date range validation
- Person-specific queries

### ✅ Assignments (26 tests)
- Rotation assignments
- ACGME compliance warnings
- Optimistic locking

### ✅ Schedule Generation (12 tests)
- Algorithm selection
- ACGME validation
- Date range queries

### ✅ Data Export (16 tests)
- CSV, JSON, Excel formats
- People, absences, schedules
- Date filtering

### ✅ Error Handling (6 tests)
- 401 Unauthorized
- 404 Not Found
- 400 Validation Errors
- 409 Conflicts

## 📁 File Structure

```
tests/integration/
├── setup.ts              # Test utilities and fixtures
├── api.test.ts           # Main test suite (100+ tests)
├── package.json          # Dependencies
├── tsconfig.json         # TypeScript config
├── jest.config.js        # Jest config
├── run-tests.sh          # Helper script
├── README.md             # Full documentation
├── TESTS_SUMMARY.md      # Detailed test coverage
├── QUICK_START.md        # This file
├── .env.example          # Environment template
└── .gitignore            # Git ignore patterns
```

## 🔧 Configuration

### Environment Variables (Optional)
```bash
export API_BASE_URL=http://localhost:8000/api
export TEST_TIMEOUT=30000
```

Or create `.env` file:
```bash
cp .env.example .env
# Edit .env as needed
```

## ✨ Key Features

- **100+ Test Cases**: Comprehensive coverage
- **Error Testing**: All error codes (401, 404, 400, 409)
- **Authentication**: Token-based auth testing
- **Validation**: Schema and business rule validation
- **CRUD Operations**: Full create, read, update, delete
- **Export Testing**: CSV, JSON, Excel formats
- **ACGME Compliance**: Validation rule testing

## 📈 Example Output

```bash
$ npm test

API Integration Tests
  Auth Endpoints
    POST /auth/register
      ✓ should register the first user as admin (234ms)
      ✓ should not register duplicate username (45ms)
      ...
  People Endpoints
    POST /api/people
      ✓ should create a resident with valid data (67ms)
      ✓ should create a faculty member with valid data (54ms)
      ...

Test Suites: 8 passed, 8 total
Tests:       100+ passed, 100+ total
Time:        45.234s
```

## 🐛 Troubleshooting

### Backend not running
```bash
Error: connect ECONNREFUSED 127.0.0.1:8000

Solution:
cd backend
uvicorn app.main:app --reload --port 8000
```

### Dependencies missing
```bash
Error: Cannot find module 'axios'

Solution:
npm install
```

### Port already in use
```bash
Solution:
export API_BASE_URL=http://localhost:DIFFERENT_PORT/api
```

### Test timeout
```bash
Solution:
export TEST_TIMEOUT=60000  # Increase to 60 seconds
```

## 📖 Next Steps

1. ✅ Run tests to verify setup
2. ✅ Check coverage report (`npm run test:coverage`)
3. ✅ Review README.md for detailed docs
4. ✅ Review TESTS_SUMMARY.md for test breakdown
5. ✅ Integrate into CI/CD pipeline

## 🎓 Learning the Tests

### Read Tests as Documentation
The tests serve as living API documentation:
- See `api.test.ts` for endpoint examples
- See `setup.ts` for request/response formats
- Tests show both success and error cases

### Add Your Own Tests
1. Add test case to appropriate suite in `api.test.ts`
2. Add fixtures to `setup.ts` if needed
3. Run `npm test` to verify
4. Update documentation

## 📞 Support

- Full docs: `README.md`
- Test details: `TESTS_SUMMARY.md`
- Backend API docs: http://localhost:8000/docs
- Backend source: `backend/app/api/routes/`

---

**Ready to test?** Just run: `./run-tests.sh`
