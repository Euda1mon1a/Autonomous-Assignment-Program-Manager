***REMOVED*** Automated Code Fixer - Examples

***REMOVED******REMOVED*** Example 1: Test Failure Due to Missing Await

***REMOVED******REMOVED******REMOVED*** Detection
```
$ pytest tests/test_swap_service.py -v
FAILED tests/test_swap_service.py::test_execute_swap
E   RuntimeWarning: coroutine 'execute_swap' was never awaited
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Looking at the test file and service:
- `SwapService.execute_swap()` is async
- Test was calling without `await`

***REMOVED******REMOVED******REMOVED*** Fix Applied
```python
***REMOVED*** Before
def test_execute_swap(db, swap_request):
    result = swap_service.execute_swap(db, swap_request)
    assert result.status == "completed"

***REMOVED*** After
async def test_execute_swap(db, swap_request):
    result = await swap_service.execute_swap(db, swap_request)
    assert result.status == "completed"
```

***REMOVED******REMOVED******REMOVED*** Validation
```
$ pytest tests/test_swap_service.py -v
PASSED tests/test_swap_service.py::test_execute_swap
```

---

***REMOVED******REMOVED*** Example 2: Type Error in Service Layer

***REMOVED******REMOVED******REMOVED*** Detection
```
$ mypy app/ --python-version 3.11
app/services/schedule_service.py:45: error: Missing return type annotation
app/services/schedule_service.py:45: error: Function "get_schedule" has no type annotation for argument "schedule_id"
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Function missing type annotations, violating project standards.

***REMOVED******REMOVED******REMOVED*** Fix Applied
```python
***REMOVED*** Before
def get_schedule(schedule_id):
    ***REMOVED*** ... implementation

***REMOVED*** After
from typing import Optional
from app.models import Schedule

async def get_schedule(schedule_id: str) -> Optional[Schedule]:
    ***REMOVED*** ... implementation
```

***REMOVED******REMOVED******REMOVED*** Validation
```
$ mypy app/ --python-version 3.11
Success: no issues found in 147 source files
```

---

***REMOVED******REMOVED*** Example 3: Security Vulnerability

***REMOVED******REMOVED******REMOVED*** Detection
```
$ ruff check app/
app/api/routes/auth.py:23:5: S105 Possible hardcoded password: "default_password"
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Test helper using hardcoded password string, flagged as security issue.

***REMOVED******REMOVED******REMOVED*** Fix Applied
```python
***REMOVED*** Before
def create_test_user(db):
    password = "default_password"  ***REMOVED*** S105 violation
    user = User(email="test@test.com", password_hash=hash(password))

***REMOVED*** After
import os

def create_test_user(db):
    password = os.environ.get("TEST_USER_PASSWORD", "")
    if not password:
        raise ValueError("TEST_USER_PASSWORD environment variable required")
    user = User(email="test@test.com", password_hash=hash(password))
```

***REMOVED******REMOVED******REMOVED*** Validation
```
$ ruff check app/
All checks passed!
```

---

***REMOVED******REMOVED*** Example 4: Linting Auto-Fix

***REMOVED******REMOVED******REMOVED*** Detection
```
$ ruff check app/services/
app/services/analytics.py:1:1: I001 Import block is un-sorted or un-formatted
app/services/analytics.py:15:80: E501 Line too long (95 > 88 characters)
app/services/analytics.py:42:5: F841 Local variable 'result' is assigned but never used
```

***REMOVED******REMOVED******REMOVED*** Fix Applied (Auto)
```bash
$ black app/services/analytics.py
$ ruff check app/services/analytics.py --fix
Found 3 errors (2 fixed, 1 remaining).
```

***REMOVED******REMOVED******REMOVED*** Manual Fix Required
```python
***REMOVED*** Before - unused variable
result = db.execute(query)
return data

***REMOVED*** After - removed unused variable
db.execute(query)
return data
```

***REMOVED******REMOVED******REMOVED*** Validation
```
$ ruff check app/services/analytics.py
All checks passed!
```

---

***REMOVED******REMOVED*** Example 5: Build Failure Due to Missing Import

***REMOVED******REMOVED******REMOVED*** Detection
```
$ python -c "from app.main import app"
ImportError: cannot import name 'ScheduleValidator' from 'app.scheduling'
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Module `ScheduleValidator` was moved but import not updated.

***REMOVED******REMOVED******REMOVED*** Fix Applied
```python
***REMOVED*** Before
from app.scheduling import ScheduleValidator

***REMOVED*** After (check actual location)
from app.scheduling.acgme_validator import ScheduleValidator
```

***REMOVED******REMOVED******REMOVED*** Validation
```
$ python -c "from app.main import app"
***REMOVED*** No output = success
```

---

***REMOVED******REMOVED*** Example 6: CI/CD Pipeline Failure

***REMOVED******REMOVED******REMOVED*** Detection
```
GitHub Actions output:
Run pytest --cov=app
FAILED tests/test_resilience.py::TestResilienceService::test_n1_contingency
E   assert 0.75 >= 0.80
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Coverage dropped below 80% threshold due to new untested code.

***REMOVED******REMOVED******REMOVED*** Fix Applied
Added tests for new resilience methods:

```python
***REMOVED*** tests/test_resilience.py

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

***REMOVED******REMOVED******REMOVED*** Validation
```
$ pytest --cov=app --cov-fail-under=80
PASSED - Coverage: 82%
```

---

***REMOVED******REMOVED*** Example 7: Frontend Type Error

***REMOVED******REMOVED******REMOVED*** Detection
```
$ npm run type-check
src/components/ScheduleView.tsx(45,23): error TS2322:
  Type 'undefined' is not assignable to type 'Schedule'.
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Component not handling nullable data from API.

***REMOVED******REMOVED******REMOVED*** Fix Applied
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

***REMOVED******REMOVED******REMOVED*** Validation
```
$ npm run type-check
No errors found.
```

---

***REMOVED******REMOVED*** Example 8: Escalation Scenario

***REMOVED******REMOVED******REMOVED*** Detection
```
$ pytest tests/test_acgme_compliance.py
FAILED tests/test_acgme_compliance.py::test_80_hour_rule
E   AssertionError: ACGME 80-hour rule calculation incorrect
```

***REMOVED******REMOVED******REMOVED*** Diagnosis
Issue affects ACGME compliance logic - **MUST ESCALATE**

***REMOVED******REMOVED******REMOVED*** Action Taken
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

***REMOVED******REMOVED*** Automated Fix Summary Template

```markdown
***REMOVED******REMOVED*** Fix Report

**Issue:** [Brief description]
**Severity:** [Critical/High/Medium/Low]
**Time to Fix:** [Duration]

***REMOVED******REMOVED******REMOVED*** Root Cause
[What was actually wrong]

***REMOVED******REMOVED******REMOVED*** Changes Made
- File: `path/to/file.py`
  - [What was changed]

***REMOVED******REMOVED******REMOVED*** Tests
- [x] All existing tests pass
- [x] New tests added: [number]
- [x] Coverage: [percentage]

***REMOVED******REMOVED******REMOVED*** Validation
- [x] pytest: PASS
- [x] ruff: PASS
- [x] mypy: PASS
- [x] black: PASS

***REMOVED******REMOVED******REMOVED*** Notes
[Any additional context or follow-up needed]
```
