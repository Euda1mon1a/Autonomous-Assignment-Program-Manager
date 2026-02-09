# AAPM Agent Task Queue

Work on the first unchecked task (`- [ ]`). After completing it, change it to `- [x]`, commit your changes, then stop.

## Phase 1: Fix & Clean
- [x] Fix import error in tests/services/test_faculty_pipeline.py — the module `app.services.faculty_assignment_expansion_service` does not exist. Either create a stub or fix the import to point to the correct module. Run tests after.
- [x] Run `ruff check backend/ --fix` to auto-fix safe lint issues. Then manually fix any remaining errors. Commit fixes.
- [x] Run `cd frontend && npx tsc --noEmit` and fix any TypeScript type errors found. Commit fixes.
- [x] Run `cd frontend && npm run lint` and fix any ESLint errors found. Commit fixes.
- [x] Search for `# TODO` and `# FIXME` comments in backend/app/ — pick the easiest one and implement it. Commit.
- [x] Search for `// TODO` and `// FIXME` comments in frontend/src/ — pick the easiest one and implement it. Commit.

## Phase 2: Test Coverage
- [x] List files in backend/app/services/ that have NO corresponding test file in tests/services/. Pick the first one and write basic tests (happy path + error case). Commit.
- [ ] Continue writing tests for the next untested service file. Commit.
- [ ] Continue writing tests for the next untested service file. Commit.
- [ ] List files in backend/app/api/routes/ that have NO corresponding test file in tests/api/. Pick the first one and write basic route tests. Commit.
- [ ] Continue writing tests for the next untested route file. Commit.
- [ ] Continue writing tests for the next untested route file. Commit.
- [ ] Review tests/scheduling/ — if sparse, add edge case tests for the schedule engine. Commit.
- [ ] Review tests/ for any test files that are empty or only have placeholder tests. Fill them in. Commit.

## Phase 3: Code Quality
- [ ] Scan backend/app/services/ for functions missing return type hints. Add them. Commit.
- [ ] Scan backend/app/services/ for functions missing parameter type hints. Add them. Commit.
- [ ] Scan backend/app/api/routes/ for endpoints with poor error messages (generic "Error" or "Something went wrong"). Improve them. Commit.
- [ ] Look for hardcoded magic numbers or strings in backend/app/ that should be constants. Extract to config or constants. Commit.
- [ ] Review backend/app/models/ for models missing __repr__ or __str__ methods. Add them. Commit.
- [ ] Review Pydantic schemas in backend/app/schemas/ for fields missing descriptions or examples. Add them. Commit.

## Phase 4: Frontend Quality
- [ ] Review frontend/src/components/ for components missing TypeScript prop interfaces. Add proper typing. Commit.
- [ ] Review frontend/src/hooks/ for hooks with missing error handling. Add try/catch and error states. Commit.
- [ ] Look for `any` type usage in frontend/src/ and replace with proper types. Commit.
- [ ] Review frontend/src/app/ pages for missing loading states or error boundaries. Add them. Commit.
- [ ] Check frontend/src/components/ for accessibility issues (missing aria-labels, non-semantic elements). Fix them. Commit.

## Phase 5: Dead Code & Cleanup
- [ ] Run `ruff check backend/ --select F401` to find unused imports. Remove them. Commit.
- [ ] Search for functions in backend/app/ that are defined but never called from anywhere. Remove dead code. Commit.
- [ ] Search for commented-out code blocks in backend/app/. Remove them (git has history). Commit.
- [ ] Search for commented-out code blocks in frontend/src/. Remove them. Commit.
- [ ] Look for duplicate utility functions across backend/app/. Consolidate. Commit.
