---
name: automated-code-fixer
description: Automated IT helper for detecting and fixing code issues. Use when code fails tests, linting, type-checking, or has security vulnerabilities. Enforces strict quality gates before accepting fixes.
---

***REMOVED*** Automated Code Fixer

An intelligent "IT guy" skill that automatically detects and fixes code issues with strict quality controls.

***REMOVED******REMOVED*** When This Skill Activates

- Test failures detected
- Linting errors reported
- Type-checking errors found
- Security vulnerabilities identified
- Build failures encountered
- CI/CD pipeline failures

***REMOVED******REMOVED*** Strict Quality Gates

**CRITICAL: All fixes must pass these gates before being accepted:**

***REMOVED******REMOVED******REMOVED*** Gate 1: Test Validation
- All existing tests must pass after fix
- New code must have corresponding tests
- Coverage cannot decrease below 70%

***REMOVED******REMOVED******REMOVED*** Gate 2: Linting Compliance
- Black formatting must pass
- Ruff linting with zero errors
- No new security warnings

***REMOVED******REMOVED******REMOVED*** Gate 3: Type Safety
- mypy type-checking must pass
- No untyped function signatures
- No `Any` type escapes

***REMOVED******REMOVED******REMOVED*** Gate 4: Security Check
- No hardcoded secrets
- No SQL injection vulnerabilities
- No path traversal issues
- Input validation on all user data

***REMOVED******REMOVED******REMOVED*** Gate 5: Architectural Compliance
- Follow layered architecture (Route -> Controller -> Service -> Model)
- Database changes require migrations
- Async/await for all DB operations

***REMOVED******REMOVED*** Fix Process

***REMOVED******REMOVED******REMOVED*** Step 1: Diagnose
```bash
***REMOVED*** Run diagnostics
cd /home/user/Autonomous-Assignment-Program-Manager/backend
pytest --tb=short 2>&1 | head -50
ruff check app/ tests/
mypy app/ --python-version 3.11
```

***REMOVED******REMOVED******REMOVED*** Step 2: Analyze
- Identify root cause (not just symptoms)
- Check related files for context
- Review test expectations

***REMOVED******REMOVED******REMOVED*** Step 3: Fix
- Make minimal, focused changes
- Follow existing code patterns
- Add comments only where logic isn't self-evident

***REMOVED******REMOVED******REMOVED*** Step 4: Validate
```bash
***REMOVED*** Must all pass before accepting fix
pytest --tb=short
ruff check app/ tests/
black --check app/ tests/
mypy app/ --python-version 3.11
```

***REMOVED******REMOVED******REMOVED*** Step 5: Report
Provide concise summary:
- What was broken
- Root cause
- What was fixed
- Tests added/modified

***REMOVED******REMOVED*** Escalation Rules

**Escalate to human when:**
1. Fix requires changing models/migrations
2. Fix affects ACGME compliance logic
3. Fix touches authentication/security code
4. Multiple interdependent failures
5. Unclear requirements or business logic
6. Fix would take >30 minutes

***REMOVED******REMOVED*** Rollback Protocol

If fix causes additional failures:
1. Immediately revert changes
2. Document what went wrong
3. Escalate to human with full context

***REMOVED******REMOVED*** Integration with Existing Commands

This skill works with the project's slash commands:
- `/run-tests` - Execute test suite
- `/lint-fix` - Auto-format and fix linting
- `/health-check` - System health validation
- `/check-compliance` - ACGME compliance verification

***REMOVED******REMOVED*** Example Fixes

***REMOVED******REMOVED******REMOVED*** Test Failure
```
pytest output: FAILED tests/test_swap_executor.py::test_execute_swap - AssertionError

Diagnosis: SwapExecutor.execute_swap() not awaiting async call
Fix: Added 'await' to database query on line 47
Validation: All tests pass, coverage maintained at 78%
```

***REMOVED******REMOVED******REMOVED*** Type Error
```
mypy output: app/services/schedule.py:23: error: Missing return type annotation

Diagnosis: Function missing type hints
Fix: Added -> Optional[Schedule] return type
Validation: mypy passes, no runtime changes
```

***REMOVED******REMOVED******REMOVED*** Security Issue
```
ruff output: S105 Possible hardcoded password in variable assignment

Diagnosis: Test file using hardcoded password
Fix: Replaced with environment variable via conftest fixture
Validation: No security warnings, tests pass
```

***REMOVED******REMOVED*** References

- See `reference.md` for detailed fix patterns
- See `examples.md` for common fix scenarios
