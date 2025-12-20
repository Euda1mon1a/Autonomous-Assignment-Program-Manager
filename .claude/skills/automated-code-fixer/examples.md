# Automated Code Fixer - Examples

## Example 1: Test Failure Due to Missing Await

### Detection
```
$ pytest tests/test_swap_service.py -v
FAILED tests/test_swap_service.py::test_execute_swap
E   RuntimeWarning: coroutine 'execute_swap' was never awaited
```

### Diagnosis
Looking at the test file and service:
- `SwapService.execute_swap()` is async
- Test was calling without `await`

### Fix Applied
```python
# Before
def test_execute_swap(db, swap_request):
    result = swap_service.execute_swap(db, swap_request)
    assert result.status == "completed"

# After
async def test_execute_swap(db, swap_request):
    result = await swap_service.execute_swap(db, swap_request)
    assert result.status == "completed"
```

### Validation
```
$ pytest tests/test_swap_service.py -v
PASSED tests/test_swap_service.py::test_execute_swap
```

---

## Example 2: Type Error in Service Layer

### Detection
```
$ mypy app/ --python-version 3.11
app/services/schedule_service.py:45: error: Missing return type annotation
app/services/schedule_service.py:45: error: Function "get_schedule" has no type annotation for argument "schedule_id"
```

### Diagnosis
Function missing type annotations, violating project standards.

### Fix Applied
```python
# Before
def get_schedule(schedule_id):
    # ... implementation

# After
from typing import Optional
from app.models import Schedule

async def get_schedule(schedule_id: str) -> Optional[Schedule]:
    # ... implementation
```

### Validation
```
$ mypy app/ --python-version 3.11
Success: no issues found in 147 source files
```

---

## Example 3: Security Vulnerability

### Detection
```
$ ruff check app/
app/api/routes/auth.py:23:5: S105 Possible hardcoded password: "default_password"
```

### Diagnosis
Test helper using hardcoded password string, flagged as security issue.

### Fix Applied
```python
# Before
def create_test_user(db):
    password = "default_password"  # S105 violation
    user = User(email="test@test.com", password_hash=hash(password))

# After
import os

def create_test_user(db):
    password = os.environ.get("TEST_USER_PASSWORD", "")
    if not password:
        raise ValueError("TEST_USER_PASSWORD environment variable required")
    user = User(email="test@test.com", password_hash=hash(password))
```

### Validation
```
$ ruff check app/
All checks passed!
```

---

## Example 4: Linting Auto-Fix

### Detection
```
$ ruff check app/services/
app/services/analytics.py:1:1: I001 Import block is un-sorted or un-formatted
app/services/analytics.py:15:80: E501 Line too long (95 > 88 characters)
app/services/analytics.py:42:5: F841 Local variable 'result' is assigned but never used
```

### Fix Applied (Auto)
```bash
$ black app/services/analytics.py
$ ruff check app/services/analytics.py --fix
Found 3 errors (2 fixed, 1 remaining).
```

### Manual Fix Required
```python
# Before - unused variable
result = db.execute(query)
return data

# After - removed unused variable
db.execute(query)
return data
```

### Validation
```
$ ruff check app/services/analytics.py
All checks passed!
```

---

## Example 5: Build Failure Due to Missing Import

### Detection
```
$ python -c "from app.main import app"
ImportError: cannot import name 'ScheduleValidator' from 'app.scheduling'
```

### Diagnosis
Module `ScheduleValidator` was moved but import not updated.

### Fix Applied
```python
# Before
from app.scheduling import ScheduleValidator

# After (check actual location)
from app.scheduling.acgme_validator import ScheduleValidator
```

### Validation
```
$ python -c "from app.main import app"
# No output = success
```

---

## Example 6: CI/CD Pipeline Failure

### Detection
```
GitHub Actions output:
Run pytest --cov=app
FAILED tests/test_resilience.py::TestResilienceService::test_n1_contingency
E   assert 0.75 >= 0.80
```

### Diagnosis
Coverage dropped below 80% threshold due to new untested code.

### Fix Applied
Added tests for new resilience methods:

```python
# tests/test_resilience.py

class TestResilienceService:
    async def test_n1_contingency(self, db, test_schedule):
        """Test N-1 contingency calculation."""
        service = ResilienceService()
        result = await service.calculate_n1_contingency(db, test_schedule.id)

        assert result.vulnerability_score <= 0.2
        assert len(result.critical_persons) >= 0
        assert result.recommendations is not None

    async def test_n2_contingency(self, db, test_schedule):
        """Test N-2 contingency for severe scenarios."""
        service = ResilienceService()
        result = await service.calculate_n2_contingency(db, test_schedule.id)

        assert result is not None
        assert result.cascade_risk_level in ["low", "medium", "high"]
```

### Validation
```
$ pytest --cov=app --cov-fail-under=80
PASSED - Coverage: 82%
```

---

## Example 7: Frontend Type Error

### Detection
```
$ npm run type-check
src/components/ScheduleView.tsx(45,23): error TS2322:
  Type 'undefined' is not assignable to type 'Schedule'.
```

### Diagnosis
Component not handling nullable data from API.

### Fix Applied
```typescript
// Before
const schedule: Schedule = data;

// After
const schedule: Schedule | undefined = data;

// Or with null check
if (!data) {
  return <LoadingSpinner />;
}
const schedule: Schedule = data;
```

### Validation
```
$ npm run type-check
No errors found.
```

---

## Example 8: Escalation Scenario

### Detection
```
$ pytest tests/test_acgme_compliance.py
FAILED tests/test_acgme_compliance.py::test_80_hour_rule
E   AssertionError: ACGME 80-hour rule calculation incorrect
```

### Diagnosis
Issue affects ACGME compliance logic - **MUST ESCALATE**

### Action Taken
```
ESCALATED TO HUMAN

Reason: Fix requires changes to ACGME compliance calculation
File: app/scheduling/acgme_validator.py
Test: tests/test_acgme_compliance.py::test_80_hour_rule

The 80-hour rule calculation is returning 82 hours but test expects 80.
This is regulatory logic and requires human review before any changes.

Current implementation: Lines 45-67 of acgme_validator.py
Related files:
- app/scheduling/engine.py (uses validator)
- docs/compliance.md (documentation)

Suggested approach: Check if averaging period is correctly 4 weeks
```

---

## Automated Fix Summary Template

```markdown
## Fix Report

**Issue:** [Brief description]
**Severity:** [Critical/High/Medium/Low]
**Time to Fix:** [Duration]

### Root Cause
[What was actually wrong]

### Changes Made
- File: `path/to/file.py`
  - [What was changed]

### Tests
- [x] All existing tests pass
- [x] New tests added: [number]
- [x] Coverage: [percentage]

### Validation
- [x] pytest: PASS
- [x] ruff: PASS
- [x] mypy: PASS
- [x] black: PASS

### Notes
[Any additional context or follow-up needed]
```
