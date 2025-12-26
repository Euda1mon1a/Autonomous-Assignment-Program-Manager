# Tool Error Patterns

Known failure modes, error signatures, and workarounds for MCP tools.

## Overview

This document catalogs observed error patterns, their root causes, and proven recovery strategies. Updated based on production incidents and testing.

---

## Common Error Patterns

### 1. Connection Timeout Errors

**Signature:**
```
ConnectionError: Failed to connect to http://backend:8000
TimeoutError: Request timed out after 30s
```

**Affected Tools:**
- `validate_schedule_tool`
- `detect_conflicts_tool`
- `analyze_swap_candidates_tool`
- All tools requiring API_BASE_URL

**Root Causes:**
1. Backend API not running
2. Network issues between containers
3. Backend under heavy load
4. Database query taking too long

**Workarounds:**

```python
# 1. Check backend health first
docker-compose exec mcp-server curl -s http://backend:8000/health

# 2. Increase timeout for large date ranges
# Backend operations scale with date range size
# Small range (1 week): 5-10s
# Medium range (1 month): 10-30s
# Large range (1 year): 30-120s

# 3. Retry with exponential backoff
result = await retry_with_backoff(
    validate_schedule_tool,
    max_retries=3,
    base_delay=2.0,
    start_date="2025-01-01",
    end_date="2025-01-31"
)

# 4. Use cached data for read-only operations
result = await get_with_cache_fallback(
    "schedule_status_resource",
    cache_key="schedule_status_2025-01",
    start_date="2025-01-01",
    end_date="2025-01-31"
)
```

**Prevention:**
- Use background tasks for operations expected to exceed 30s
- Monitor backend API latency metrics
- Add database indexes for date-range queries

---

### 2. Celery Worker Not Available

**Signature:**
```
ConnectionError: No active Celery workers found
RuntimeError: Failed to queue task. Check Celery/Redis connection
```

**Affected Tools:**
- `start_background_task_tool`
- `get_task_status_tool`
- `list_active_tasks_tool`
- `cancel_task_tool`

**Root Causes:**
1. Celery worker not running
2. Redis connection failed
3. Worker crashed or stuck
4. Task queue full

**Workarounds:**

```bash
# 1. Check worker status
docker-compose ps celery-worker

# 2. Check Redis connectivity
docker-compose exec mcp-server redis-cli ping
# Expected: PONG

# 3. Check active workers
docker-compose exec mcp-server celery -A app.core.celery_app inspect active

# 4. Restart workers if stuck
docker-compose restart celery-worker celery-beat

# 5. Fallback to synchronous execution (if <30s)
try:
    task_result = await start_background_task_tool(
        task_type="metrics_computation",
        params={"start_date": "2025-01-01", "end_date": "2025-01-31"}
    )
except ConnectionError:
    logger.warning("Celery unavailable, running synchronously")
    # Call backend API directly for synchronous execution
    result = await call_api_directly("/api/metrics/compute", {...})
```

**Prevention:**
- Monitor Celery worker health
- Set up worker auto-restart
- Implement task timeouts
- Monitor Redis memory usage

---

### 3. Database Lock/Deadlock

**Signature:**
```
OperationalError: database is locked
DatabaseError: deadlock detected
```

**Affected Tools:**
- Tools performing write operations (generate_schedule via API)
- Tools with long transactions

**Root Causes:**
1. Concurrent write operations
2. Long-running transactions
3. Missing database indexes
4. Transaction isolation level issues

**Workarounds:**

```python
# 1. Retry with exponential backoff (database locks are transient)
result = await retry_with_backoff(
    generate_schedule,
    max_retries=5,
    base_delay=0.5,  # Short delay for lock contention
    start_date="2025-01-01",
    end_date="2025-01-31"
)

# 2. Serialize write operations
# Don't run multiple schedule generations concurrently
write_lock = asyncio.Lock()

async with write_lock:
    result = await generate_schedule(...)

# 3. Check for active long-running queries
# SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';
```

**Prevention:**
- Use database connection pooling
- Keep transactions short
- Add appropriate indexes
- Use row-level locking where appropriate

---

### 4. Validation Schema Errors

**Signature:**
```
ValueError: Invalid constraint_config: invalid_value. Must be one of: ['default', 'minimal', 'strict', 'resilience']
ValueError: schedule_id must be 1-64 characters, no special characters allowed
pydantic.ValidationError: field required
```

**Affected Tools:**
- All tools (input validation)

**Root Causes:**
1. Incorrect parameter types
2. Missing required parameters
3. Invalid enum values
4. Schema violations

**Workarounds:**

```python
# 1. Validate inputs before calling tool
def validate_date_format(date_str: str) -> bool:
    """Validate YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

# 2. Use enums for valid values
from scheduler_mcp.tools.validate_schedule import ConstraintConfig

valid_configs = [c.value for c in ConstraintConfig]
if config not in valid_configs:
    raise ValueError(f"Invalid config. Must be one of: {valid_configs}")

# 3. Check required parameters
required = ["start_date", "end_date"]
missing = [p for p in required if p not in params]
if missing:
    raise ValueError(f"Missing required parameters: {missing}")

# 4. Sanitize schedule_id
import re

def sanitize_schedule_id(schedule_id: str) -> str:
    """Ensure schedule_id is valid."""
    # Remove special characters
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', schedule_id)
    # Truncate to 64 chars
    sanitized = sanitized[:64]
    if not sanitized:
        raise ValueError("schedule_id must contain at least one alphanumeric character")
    return sanitized
```

**Prevention:**
- Validate inputs early
- Use type hints and Pydantic models
- Document parameter constraints
- Provide clear error messages

---

### 5. Rate Limit Exceeded (Future)

**Signature:**
```
HTTPError: 429 Too Many Requests
RateLimitError: Rate limit exceeded. Retry after 60s
```

**Affected Tools (when implemented):**
- GitHub API calls in deployment tools
- External security scanning services

**Root Causes:**
1. Too many requests in short time window
2. Shared rate limit across multiple users
3. API quota exceeded

**Workarounds:**

```python
# 1. Respect Retry-After header
import time

try:
    result = await call_tool(...)
except HTTPError as e:
    if e.status_code == 429:
        retry_after = int(e.headers.get("Retry-After", 60))
        logger.warning(f"Rate limited. Retrying after {retry_after}s")
        await asyncio.sleep(retry_after)
        result = await call_tool(...)

# 2. Implement token bucket rate limiter
from collections import deque
from time import time

class RateLimiter:
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()

    async def acquire(self):
        now = time()

        # Remove old calls outside time window
        while self.calls and self.calls[0] < now - self.time_window:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            # Wait until oldest call expires
            wait_time = self.time_window - (now - self.calls[0])
            logger.info(f"Rate limit reached. Waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

        self.calls.append(now)

# Usage
github_limiter = RateLimiter(max_calls=5000, time_window=3600)

await github_limiter.acquire()
result = await validate_deployment_tool(...)

# 3. Cache API responses to reduce calls
GITHUB_CACHE = TTLCache(maxsize=100, ttl=300)  # 5-minute cache

async def get_github_data_cached(endpoint: str):
    if endpoint in GITHUB_CACHE:
        return GITHUB_CACHE[endpoint]

    result = await fetch_github_api(endpoint)
    GITHUB_CACHE[endpoint] = result
    return result
```

**Prevention:**
- Implement rate limiting at application level
- Cache API responses
- Use webhooks instead of polling
- Monitor rate limit usage

---

### 6. Task Stuck/Timeout

**Signature:**
```
TimeoutError: Task abc123 did not complete within 300s
Task status: started (progress: 50%)
```

**Affected Tools:**
- `start_background_task_tool` (long-running tasks)

**Root Causes:**
1. Task genuinely taking longer than expected
2. Task hanging on I/O operation
3. Deadlock in task code
4. Worker crashed mid-task

**Workarounds:**

```python
# 1. Implement task timeout with cancellation
import asyncio

async def run_task_with_timeout(
    task_type: str,
    params: dict,
    timeout: int = 300
):
    """Run background task with timeout."""

    # Start task
    task_result = await start_background_task_tool(
        task_type=task_type,
        params=params
    )

    task_id = task_result.task_id

    # Poll with timeout
    start_time = time.time()
    while time.time() - start_time < timeout:
        status = await get_task_status_tool(task_id=task_id)

        if status.status == "success":
            return status.result

        elif status.status == "failure":
            raise RuntimeError(f"Task failed: {status.error}")

        elif status.status == "started":
            # Check progress
            if status.progress > 0:
                logger.info(f"Task {task_id} progress: {status.progress}%")

        await asyncio.sleep(5)

    # Timeout - cancel task
    logger.error(f"Task {task_id} timeout after {timeout}s. Canceling.")
    await cancel_task_tool(task_id=task_id)
    raise TimeoutError(f"Task did not complete within {timeout}s")

# 2. Check worker logs for stuck tasks
docker-compose logs celery-worker | grep "Task.*started"

# 3. Restart worker to clear stuck tasks (last resort)
docker-compose restart celery-worker
```

**Prevention:**
- Set task time limits in Celery config
- Implement progress reporting in long tasks
- Monitor worker resource usage
- Add task heartbeats

---

### 7. Deployment Validation Failures

**Signature:**
```
DeploymentError: Validation failed - 3 blockers found
Test failure: test_acgme_compliance FAILED
SecurityError: Critical vulnerabilities detected
```

**Affected Tools:**
- `validate_deployment_tool`
- `run_security_scan_tool`
- `run_smoke_tests_tool`

**Root Causes:**
1. Legitimate test failures
2. Flaky tests
3. Environment configuration mismatch
4. Database migration issues

**Workarounds:**

```python
# 1. Analyze blockers before aborting
validation = await validate_deployment_tool(
    environment="staging",
    git_ref="main"
)

if not validation.valid:
    # Check if blockers are critical
    critical_blockers = [
        b for b in validation.blockers
        if any(kw in b.lower() for kw in ["critical", "security", "migration"])
    ]

    if critical_blockers:
        # Hard stop
        raise DeploymentError(f"Critical blockers: {critical_blockers}")
    else:
        # Warning only
        logger.warning(f"Non-critical blockers: {validation.blockers}")

# 2. Retry flaky tests
smoke_test_result = None
for attempt in range(3):
    smoke_test_result = await run_smoke_tests_tool(
        environment="staging",
        test_suite="full"
    )

    if smoke_test_result.passed:
        break

    # Check which tests failed
    failed_tests = [r.check_name for r in smoke_test_result.results if r.status == "failed"]
    logger.warning(f"Attempt {attempt + 1}/3: Failed tests: {failed_tests}")

    await asyncio.sleep(10)

# 3. Run security scan with thresholds
security_scan = await run_security_scan_tool(git_ref="main")

critical_count = security_scan.severity_summary.get("critical", 0)
high_count = security_scan.severity_summary.get("high", 0)

if critical_count > 0:
    raise SecurityError(f"Critical vulnerabilities: {critical_count}")
elif high_count > 5:
    logger.warning(f"High severity vulnerabilities: {high_count}")
```

**Prevention:**
- Fix flaky tests
- Use test retries appropriately
- Keep dependencies up to date
- Run security scans in CI

---

### 8. Resource Not Found

**Signature:**
```
HTTPError: 404 Not Found
ValueError: schedule_id 'abc123' does not exist
KeyError: 'task_id'
```

**Affected Tools:**
- `validate_schedule_by_id_tool`
- `get_task_status_tool`
- `get_deployment_status_tool`

**Root Causes:**
1. Invalid ID
2. Resource deleted
3. ID from different environment
4. Typo in ID

**Workarounds:**

```python
# 1. Validate ID exists before operations
async def safe_validate_schedule(schedule_id: str):
    """Validate schedule with existence check."""

    # Check if schedule exists first
    try:
        status = await schedule_status_resource(
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        # Verify schedule_id in active schedules
        # (implementation depends on API)

    except HTTPError as e:
        if e.status_code == 404:
            raise ValueError(f"Schedule {schedule_id} not found")

    # Proceed with validation
    return await validate_schedule_by_id_tool(schedule_id=schedule_id)

# 2. Handle 404s gracefully
try:
    result = await get_task_status_tool(task_id="unknown-id")
except HTTPError as e:
    if e.status_code == 404:
        logger.warning(f"Task not found. May have expired or been deleted.")
        return {"status": "not_found"}
    raise

# 3. Provide suggestions for typos (fuzzy matching)
from difflib import get_close_matches

valid_ids = ["schedule-001", "schedule-002", "schedule-003"]
if schedule_id not in valid_ids:
    suggestions = get_close_matches(schedule_id, valid_ids, n=3)
    raise ValueError(f"Schedule ID not found. Did you mean: {suggestions}?")
```

**Prevention:**
- Validate IDs early
- Provide autocomplete for IDs
- Use UUIDs to avoid collisions
- Document ID formats

---

## Tool-Specific Error Patterns

### validate_schedule_tool

**Common Errors:**

1. **Date Range Too Large**
   - Error: `TimeoutError` after 30s
   - Threshold: ~3 months max for single call
   - Workaround: Split into smaller ranges or use background task

2. **No Assignments in Date Range**
   - Error: None (returns `is_valid: true` with 0 issues)
   - Interpretation: Schedule is empty
   - Workaround: Check `total_assignments` in schedule_status first

3. **Database Connection Lost Mid-Query**
   - Error: `OperationalError: connection lost`
   - Workaround: Retry with fresh connection

### detect_conflicts_tool

**Common Errors:**

1. **Conflict Type Typo**
   - Error: `ValueError: Invalid conflict_type`
   - Valid types: See `ConflictType` enum
   - Workaround: Use enum values directly

2. **Auto-Resolution Not Implemented**
   - Error: None (returns empty `resolution_options`)
   - Status: Auto-resolution is placeholder for some conflict types
   - Workaround: Manual resolution required

### start_background_task_tool

**Common Errors:**

1. **Invalid Task Type**
   - Error: `ValueError: Invalid task_type`
   - Workaround: Use `TaskType` enum values

2. **Missing Required Params**
   - Error: `ValueError: severity parameter required for crisis_activation`
   - Workaround: Check task-specific param requirements

3. **Task Queue Full**
   - Error: `ConnectionError: Task queue full`
   - Workaround: Wait and retry, or scale workers

### benchmark_solvers_tool

**Common Errors:**

1. **Solver Timeout**
   - Error: None (solver marked as "timeout" in results)
   - Handling: Results still useful for comparison
   - Workaround: Increase `timeout_per_run`

2. **Insufficient Scenarios**
   - Error: None (results may not be statistically significant)
   - Recommendation: Use `scenario_count >= 20` for production decisions

---

## Error Recovery Strategies by Severity

### Low Severity (Log and Continue)
- Validation warnings
- Non-critical conflicts
- Partial results available
- Cache misses

### Medium Severity (Retry with Backoff)
- Connection timeouts
- Database locks
- Rate limits
- Worker busy

### High Severity (Escalate to Human)
- Security vulnerabilities (critical)
- Deployment validation failures
- Data integrity violations
- All retries exhausted

### Emergency Severity (Alert and Rollback)
- Production deployment failure
- Rollback failure
- Database corruption detected
- System-wide outage

---

## Monitoring Recommendations

### Metrics to Track

1. **Tool Error Rates**
   - Track errors per tool per hour
   - Alert if >5% error rate sustained

2. **Latency Percentiles**
   - p50, p95, p99 latency per tool
   - Alert if p99 exceeds 2× normal

3. **Retry Counts**
   - Number of retries per tool invocation
   - Alert if average retries >1.5

4. **Task Timeout Rate**
   - Percentage of background tasks timing out
   - Alert if >2%

### Logging Best Practices

```python
# Structured logging for errors
logger.error(
    "Tool error",
    extra={
        "tool_name": "validate_schedule_tool",
        "error_type": "TimeoutError",
        "params": {"start_date": "2025-01-01", "end_date": "2025-12-31"},
        "retry_attempt": 3,
        "duration_ms": 30000,
    }
)
```

---

## Known Issues Tracking

| Issue ID | Tool | Description | Status | Workaround |
|----------|------|-------------|--------|------------|
| MCP-001 | validate_schedule_tool | Timeout on date ranges >6 months | Open | Split into smaller ranges |
| MCP-002 | analyze_swap_candidates_tool | Empty candidates when backend API down | Open | Use cached swap history |
| MCP-003 | start_background_task_tool | Task IDs not unique across restarts | Closed | Fixed in v0.1.1 |

---

## Testing Error Paths

### Unit Tests for Error Handling

```python
@pytest.mark.asyncio
async def test_validate_schedule_timeout():
    """Test timeout handling in validate_schedule_tool."""

    with patch('httpx.AsyncClient.post', side_effect=asyncio.TimeoutError):
        with pytest.raises(asyncio.TimeoutError):
            await validate_schedule_tool(
                start_date="2025-01-01",
                end_date="2025-12-31"
            )

@pytest.mark.asyncio
async def test_retry_on_connection_error():
    """Test retry logic for connection errors."""

    call_count = 0

    async def failing_call(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Connection failed")
        return {"status": "success"}

    with patch('scheduler_mcp.tools.call_api', side_effect=failing_call):
        result = await retry_with_backoff(validate_schedule_tool, max_retries=3)
        assert call_count == 3
        assert result["status"] == "success"
```

---

## Version History

- **2025-12-26**: Initial error pattern catalog
- **MCP Server**: v0.1.0
