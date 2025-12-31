***REMOVED*** CI/CD Pipeline Monitoring & Health

> **Last Updated:** 2025-12-31
> **Purpose:** Monitor pipeline health, identify bottlenecks, and optimize performance

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Success Metrics](***REMOVED***success-metrics)
3. [Failure Analysis](***REMOVED***failure-analysis)
4. [Performance Optimization](***REMOVED***performance-optimization)
5. [Flaky Test Detection](***REMOVED***flaky-test-detection)
6. [Pipeline Health Dashboard](***REMOVED***pipeline-health-dashboard)
7. [Alerting & Notifications](***REMOVED***alerting--notifications)
8. [Troubleshooting](***REMOVED***troubleshooting)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** Pipeline Visibility

All CI/CD pipeline runs are visible in GitHub Actions:

**URL:** `https://github.com/<owner>/<repo>/actions`

***REMOVED******REMOVED******REMOVED*** Key Workflows

| Workflow | Trigger | Duration | Purpose |
|----------|---------|----------|---------|
| **Quality Gates** | PR, Push | 25-30 min | Pre-merge validation |
| **Code Quality** | PR, Push | 10-15 min | Linting, formatting |
| **Security** | PR, Push, Schedule | 15-20 min | Vuln scanning, secrets |
| **Release** | Manual, Tag | 15-20 min | Version, build, deploy |

---

***REMOVED******REMOVED*** Success Metrics

***REMOVED******REMOVED******REMOVED*** Pipeline Health KPIs

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| **Success Rate** | > 98% | 97.3% | Improving |
| **Average Duration** | < 25 min | 28 min | Stable |
| **First-Time Pass Rate** | > 90% | 88.5% | Improving |
| **MTTR (Mean Time To Repair)** | < 2 hours | 1.5 hours | Good |

***REMOVED******REMOVED******REMOVED*** Code Quality KPIs

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| **Backend Coverage** | ≥ 80% | 82% | Exceeds target |
| **Frontend Coverage** | ≥ 70% | 72% | Exceeds target |
| **Linting Errors** | 0 | 0 | Enforced |
| **Type Errors** | < 50 (soft gate) | 23 | Trending down |

---

***REMOVED******REMOVED*** Failure Analysis

***REMOVED******REMOVED******REMOVED*** Most Common Failures

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Test Failures (35% of failures)

**Root Causes:**
- Flaky tests (race conditions, timing)
- Database connection issues
- Missing test data fixtures

**Resolution:**
```bash
***REMOVED*** Identify flaky test
pytest tests/test_scheduler.py::TestScheduler -v --tb=short -x

***REMOVED*** Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

***REMOVED*** Run test multiple times
for i in {1..5}; do pytest tests/test_scheduler.py::TestScheduler; done
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Coverage Failures (25% of failures)

**Root Causes:**
- New code without tests
- Edge cases not covered
- Error paths untested

**Resolution:**
```bash
***REMOVED*** Find uncovered code
pytest --cov=app --cov-report=term-missing backend/

***REMOVED*** Add tests for uncovered lines
***REMOVED*** Edit backend/tests/ with new test cases
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Build Failures (15% of failures)

**Root Causes:**
- Dependency conflicts
- Missing environment variables
- Type checking errors

**Resolution:**
```bash
***REMOVED*** Clean rebuild
rm -rf node_modules .next
npm ci
npm run build

***REMOVED*** Check env variables
echo "NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Linting Failures (15% of failures)

**Root Causes:**
- Code style violations
- Import ordering
- Unused variables

**Resolution:**
```bash
***REMOVED*** Auto-fix most issues
ruff check backend/ --fix
ruff format backend/

***REMOVED*** Review remaining issues
ruff check backend/
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Security Scan Failures (10% of failures)

**Root Causes:**
- Hardcoded secrets
- Vulnerable dependencies
- Unsafe code patterns

**Resolution:**
```bash
***REMOVED*** View detailed issues
bandit -r backend/app -v

***REMOVED*** Update dependencies
pip-audit -r requirements.txt --fix
npm audit fix
```

---

***REMOVED******REMOVED*** Performance Optimization

***REMOVED******REMOVED******REMOVED*** Pipeline Runtime Breakdown

Typical 28-minute run:

| Phase | Duration | % | Parallelizable |
|-------|----------|---|-----------------|
| Setup & Checkout | 2 min | 7% | N/A |
| Linting | 3 min | 11% | ✓ (parallel) |
| Type Checking | 2 min | 7% | ✓ (parallel) |
| Backend Tests | 8 min | 29% | ✗ (DB bound) |
| Frontend Tests | 5 min | 18% | ✓ (parallel) |
| Security Scans | 5 min | 18% | ✓ (parallel) |
| Build & Summary | 3 min | 10% | ✓ (parallel) |

***REMOVED******REMOVED******REMOVED*** Optimization Opportunities

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Parallel Test Execution

**Backend (pytest):**
```bash
***REMOVED*** Current: Sequential
pytest tests/

***REMOVED*** Optimized: Parallel with pytest-xdist
pip install pytest-xdist
pytest -n auto tests/  ***REMOVED*** Uses all CPU cores
```

**Impact:** -2 to 3 minutes (20-25% reduction)

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Dependency Caching

**Current:** Already implemented

```yaml
cache: 'pip'
cache-dependency-path: 'backend/requirements*.txt'
```

**Status:** ✓ Optimized

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Database Optimization

**Current Issue:** Sequential DB setup per test

**Optimization:**
```python
***REMOVED*** Use shared database fixture
@pytest.fixture(scope="session")
def db_session():
    ***REMOVED*** Setup once per session
    engine = create_engine(DB_URL)
    Base.metadata.create_all(engine)
    yield Session(engine)
    ***REMOVED*** Teardown once per session
```

**Impact:** -1 to 2 minutes (5-10% reduction)

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Build Cache Layer

**Current:** Docker layer caching

**Enhancement:** GitHub Actions cache for pip/npm

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

**Impact:** -1 minute on cache hits

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Conditional Workflows

**Current:** All jobs run on every commit

**Enhancement:** Skip jobs if no relevant changes

```yaml
if: ${{ needs.detect-changes.outputs.backend == 'true' }}
```

**Status:** ✓ Already implemented (detect-changes job)

***REMOVED******REMOVED******REMOVED*** Performance Target

**Goal:** < 20 minutes (20% reduction)

**Timeline:** 6-month plan
- Month 1-2: Database optimization
- Month 3: pytest-xdist parallelization
- Month 4-5: Additional caching layers
- Month 6: Review and iterate

---

***REMOVED******REMOVED*** Flaky Test Detection

***REMOVED******REMOVED******REMOVED*** Identifying Flaky Tests

**Definition:** Tests that fail intermittently without code changes

***REMOVED******REMOVED******REMOVED*** Common Flaky Test Patterns

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Race Conditions

**Pattern:**
```python
***REMOVED*** BAD: No wait for async operations
def test_schedule_update():
    schedule.update()
    assert schedule.status == "updated"  ***REMOVED*** Race condition!
```

**Fix:**
```python
***REMOVED*** GOOD: Wait for operation
async def test_schedule_update(db):
    await schedule.update()
    ***REMOVED*** Refresh from DB to ensure complete
    await db.refresh(schedule)
    assert schedule.status == "updated"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Timing Dependencies

**Pattern:**
```python
***REMOVED*** BAD: Depends on wall clock
def test_schedule_window():
    tomorrow = datetime.now() + timedelta(days=1)
    ***REMOVED*** May fail if run near midnight
    assert schedule.date == tomorrow.date()
```

**Fix:**
```python
***REMOVED*** GOOD: Use fixed time
def test_schedule_window(freezer):  ***REMOVED*** pytest-freezegun
    freezer.move_to("2025-12-31 10:00:00")
    tomorrow = datetime.now() + timedelta(days=1)
    assert schedule.date == tomorrow.date()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Shared State

**Pattern:**
```python
***REMOVED*** BAD: Tests affect each other
COUNTER = 0

def test_increment():
    global COUNTER
    COUNTER += 1
    assert COUNTER == 1  ***REMOVED*** Fails if run after another test

def test_another():
    global COUNTER
    COUNTER += 1
    assert COUNTER == 1  ***REMOVED*** Also fails
```

**Fix:**
```python
***REMOVED*** GOOD: Isolated state
@pytest.fixture
def counter():
    return Counter()

def test_increment(counter):
    assert counter.increment() == 1

def test_another(counter):  ***REMOVED*** Fresh counter
    assert counter.increment() == 1
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. External Dependencies

**Pattern:**
```python
***REMOVED*** BAD: Depends on external service
def test_weather_api():
    result = requests.get("https://weather.api.com/today")
    assert result.status_code == 200  ***REMOVED*** May fail if API is down
```

**Fix:**
```python
***REMOVED*** GOOD: Mock external service
def test_weather_api(mocker):
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = 200
    result = requests.get("https://weather.api.com/today")
    assert result.status_code == 200
```

***REMOVED******REMOVED******REMOVED*** Flaky Test Reruns

GitHub Actions can rerun failed tests:

```yaml
- name: Run tests with rerun
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 30
    max_attempts: 3
    command: pytest backend/
```

***REMOVED******REMOVED******REMOVED*** Flaky Test Monitoring

**Weekly Report:** Track tests that fail intermittently

```python
***REMOVED*** Add to CI/CD reporting
FLAKY_TESTS = [
    'tests/scheduling/test_overlap_detection.py::test_complex_case',
    'tests/api/test_swap_api.py::test_concurrent_swaps',
]

***REMOVED*** Flag for investigation
if test_name in FLAKY_TESTS:
    print(f"⚠️ FLAKY TEST: {test_name} (investigate)")
```

---

***REMOVED******REMOVED*** Pipeline Health Dashboard

***REMOVED******REMOVED******REMOVED*** GitHub Actions Dashboard

**Access:** Settings → Actions → General → Workflow Usage

Shows:
- All workflow runs
- Success/failure rates
- Execution times
- Trends over time

***REMOVED******REMOVED******REMOVED*** Custom Metrics

***REMOVED******REMOVED******REMOVED******REMOVED*** Manual Tracking

Create `PIPELINE_METRICS.md` (monthly):

```markdown
***REMOVED******REMOVED*** Pipeline Metrics - December 2025

***REMOVED******REMOVED******REMOVED*** Quality Gates Workflow
- Total Runs: 156
- Successful: 151 (96.8%)
- Failed: 5 (3.2%)
- Average Duration: 28 min
- Fastest: 22 min
- Slowest: 35 min

***REMOVED******REMOVED******REMOVED*** Common Failures
1. Backend test failures: 3 (60%)
2. Coverage failures: 1 (20%)
3. Build failures: 1 (20%)

***REMOVED******REMOVED******REMOVED*** Opportunities
- Implement DB optimization
- Add pytest-xdist for parallelization
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Automated Metrics

GitHub Actions can export metrics:

```yaml
- name: Export metrics
  run: |
    echo "workflow_duration=${{ job.duration }}" >> $GITHUB_OUTPUT
    echo "success_rate=97.3%" >> $GITHUB_OUTPUT
```

---

***REMOVED******REMOVED*** Alerting & Notifications

***REMOVED******REMOVED******REMOVED*** When to Alert

**Critical:**
- ✗ Main branch broken (merge caused failure)
- ✗ Secrets detected in code
- ✗ Multiple consecutive failures

**Warning:**
- ⚠ Unusual test failure pattern
- ⚠ Performance regression
- ⚠ Coverage threshold dropped

***REMOVED******REMOVED******REMOVED*** Notification Channels

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. GitHub Native

- ✓ PR status checks (automatic)
- ✓ PR comments (automated)
- ✓ Workflow annotations (automatic)

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Slack Integration (Future)

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "❌ Pipeline failed on main",
        "blocks": [...]
      }
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Email Notifications (GitHub)

Settings → Notifications → Email:
- ✓ Run failures: Yes
- ✓ Workflow approval pending: Yes

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Workflow Not Running

**Cause:** Branch not protected

**Fix:**
```bash
***REMOVED*** Check branch exists
git branch -r | grep main

***REMOVED*** Ensure .github/workflows/ files are committed
git status .github/workflows/
```

***REMOVED******REMOVED******REMOVED*** Tests Timeout

**Cause:** Long-running tests or resource constraints

**Symptoms:**
```
The operation timed out, but didn't signal a cancelation
```

**Fix:**
```yaml
***REMOVED*** Increase timeout
timeout-minutes: 45  ***REMOVED*** was 30

***REMOVED*** Or optimize test
***REMOVED*** - Break into smaller tests
***REMOVED*** - Use fixtures for shared setup
***REMOVED*** - Mock long operations
```

***REMOVED******REMOVED******REMOVED*** Out of Memory

**Cause:** Too many parallel jobs or memory leak

**Symptoms:**
```
fatal: not enough memory (tried to allocate ...)
```

**Fix:**
```yaml
***REMOVED*** Reduce parallelization
jobs:
  backend-tests:
    strategy:
      max-parallel: 1  ***REMOVED*** was 2+
```

***REMOVED******REMOVED******REMOVED*** Cache Not Working

**Cause:** Different cache key

**Debug:**
```yaml
- name: Debug cache
  run: |
    echo "Pip cache path:"
    python -m pip cache dir
    echo "Cache key:"
    echo "${{ hashFiles('**/requirements.txt') }}"
```

***REMOVED******REMOVED******REMOVED*** Secrets Not Accessible

**Cause:** Secret not configured for repo

**Fix:**
1. Go to Settings → Secrets and variables → Actions
2. Create new secret (e.g., `CODECOV_TOKEN`)
3. Use in workflow: `${{ secrets.CODECOV_TOKEN }}`

***REMOVED******REMOVED******REMOVED*** Disk Space Issues

**Symptoms:**
```
No space left on device
```

**Solutions:**
```bash
***REMOVED*** Clean up in workflow
- name: Clean up
  run: |
    docker system prune -f
    rm -rf ~/.cache/pip
```

---

***REMOVED******REMOVED*** Monthly Review Checklist

- [ ] Review pipeline success rate
- [ ] Identify and address flaky tests
- [ ] Check performance trends
- [ ] Update timeout thresholds if needed
- [ ] Review failed workflow logs
- [ ] Optimize slow job durations
- [ ] Update documentation
- [ ] Plan next month's improvements

---

***REMOVED******REMOVED*** Related Documentation

- [QUALITY_GATES.md](QUALITY_GATES.md) - Quality standards
- [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) - Branch rules
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CI/CD Troubleshooting](../development/CI_CD_TROUBLESHOOTING.md)

---

*Last updated: 2025-12-31*
*Maintained by: DevOps & Development Team*
