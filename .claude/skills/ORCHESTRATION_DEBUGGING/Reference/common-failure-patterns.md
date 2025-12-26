# Common Failure Patterns

Catalog of known issues with symptoms, diagnosis steps, and fixes for the scheduling orchestration system.

## How to Use This Reference

1. **Match symptoms** to patterns below
2. **Follow diagnosis** steps to confirm
3. **Apply documented fix**
4. **Update this document** if you find a new pattern

## Pattern Index

- [Database Connection Failures](#database-connection-failures)
- [MCP Tool Timeouts](#mcp-tool-timeouts)
- [Constraint Engine Errors](#constraint-engine-errors)
- [Agent Communication Failures](#agent-communication-failures)
- [Schedule Generation Failures](#schedule-generation-failures)
- [Celery Task Failures](#celery-task-failures)
- [ACGME Compliance Validation Errors](#acgme-compliance-validation-errors)
- [API Authentication Failures](#api-authentication-failures)
- [Performance Degradation](#performance-degradation)

---

## Database Connection Failures

### Pattern 1: Connection Pool Exhausted

**Symptoms:**
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 5 reached
HTTP 500 errors on all database-dependent endpoints
Requests hanging for 30+ seconds before timeout
```

**Diagnosis:**
```bash
# Check active connections
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT count(*) as active_connections,
       (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
FROM pg_stat_activity;"

# Check for long-running queries
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT pid, now() - query_start as duration, state, query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;"

# Expected: active_connections near max_connections
# Expected: Multiple queries in 'active' state for extended time
```

**Root Cause:**
- Connection leak (connections not properly closed)
- Long-running queries holding connections
- Pool size too small for workload
- Missing connection cleanup in error handlers

**Fix:**

**Immediate:**
```bash
# Restart backend to clear connection pool
docker-compose restart backend

# Terminate long-running queries
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 minutes';"
```

**Permanent:**
```python
# backend/app/db/session.py
# Ensure connections are properly closed

# BAD - no guarantee of cleanup
async def get_db():
    db = AsyncSession()
    return db  # ← Connection may leak on error

# GOOD - always cleanup
async def get_db():
    db = AsyncSession()
    try:
        yield db
    finally:
        await db.close()  # ← Always cleanup

# Increase pool size if needed
# backend/app/core/config.py
SQLALCHEMY_POOL_SIZE = 20  # up from 10
SQLALCHEMY_MAX_OVERFLOW = 10  # up from 5
```

**Prevention:**
- Add monitoring alert: connection pool usage > 80%
- Add query timeout: `statement_timeout = '30s'` in PostgreSQL
- Add connection pool metrics to dashboard
- Review all database access for proper cleanup

**Related Patterns:**
- [Pattern 2: Deadlocks](#pattern-2-deadlocks)
- [Performance Degradation: Slow Queries](#slow-queries)

---

### Pattern 2: Deadlocks

**Symptoms:**
```
psycopg2.errors.DeadlockDetected: deadlock detected
DETAIL: Process 1234 waits for ShareLock on transaction 5678
        Process 5678 waits for ExclusiveLock on transaction 1234
Intermittent 500 errors during concurrent schedule generation
```

**Diagnosis:**
```sql
-- Check for deadlocks (requires log_lock_waits = on)
SELECT * FROM pg_locks WHERE NOT granted;

-- Check lock conflicts
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

**Root Cause:**
- Circular lock dependencies (Transaction A waits for B, B waits for A)
- Updating resources in different order across transactions
- Missing `FOR UPDATE` locks when reading before updating

**Fix:**

**Immediate:**
```python
# Add explicit row-level locking
from sqlalchemy import select

# BAD - race condition
person = await db.execute(select(Person).where(Person.id == id))
person.status = "busy"
await db.commit()

# GOOD - explicit lock prevents deadlock
person = await db.execute(
    select(Person)
    .where(Person.id == id)
    .with_for_update()  # ← Explicit row lock
)
person.status = "busy"
await db.commit()
```

**Permanent:**
```python
# Ensure consistent resource ordering
# backend/app/services/schedule_generator.py

# BAD - variable ordering
for person in people:
    for block in blocks:
        lock_resources(person, block)  # ← Order depends on iteration

# GOOD - consistent ordering
for person in sorted(people, key=lambda p: p.id):  # ← Always same order
    for block in sorted(blocks, key=lambda b: b.id):
        lock_resources(person, block)

# Add retry logic with exponential backoff
async def execute_with_retry(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await operation()
        except DeadlockDetected:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

**Prevention:**
- Use pessimistic locking (`with_for_update()`) for read-then-write
- Ensure consistent ordering of resource access
- Keep transactions short
- Add deadlock retry logic
- Consider optimistic locking for low-contention cases

**Related Patterns:**
- [Pattern 1: Connection Pool Exhausted](#pattern-1-connection-pool-exhausted)

---

## MCP Tool Timeouts

### Pattern 3: validate_schedule Timeout

**Symptoms:**
```
[mcp-server] ERROR: Tool 'validate_schedule' timed out after 30s
Agent receives error: "Tool execution failed"
Schedule validation incomplete
```

**Diagnosis:**
```bash
# Check MCP logs for timeout
docker-compose logs mcp-server | grep -i "timeout\|validate_schedule"

# Check backend API response time
docker-compose logs backend | grep "/api/schedule/validate" | tail -20

# Test API directly
time curl -X POST http://localhost:8000/api/schedule/validate \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": "test-123"}'

# Expected: Response time > 30 seconds
```

**Root Cause:**
- Backend validation endpoint too slow for large schedules
- ACGME validator processes all days serially (O(n) where n = 365)
- No caching of validation results
- MCP timeout too short for workload

**Fix:**

**Immediate:**
```python
# Increase MCP timeout
# mcp-server/src/scheduler_mcp/config.py
DEFAULT_TIMEOUT = 120  # up from 30
```

**Permanent:**
```python
# Optimize ACGME validator
# backend/app/scheduling/acgme_validator.py

# BAD - serial validation
def validate_schedule(schedule):
    for day in range(365):
        validate_day(schedule, day)  # ← Sequential, 365 iterations

# GOOD - batch validation
def validate_schedule(schedule):
    # Validate weekly constraints (52 weeks, not 365 days)
    for week in range(52):
        validate_week(schedule, week)  # ← 85% fewer iterations

    # Parallel validation for independent checks
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(validate_80_hour_rule, schedule),
            executor.submit(validate_1_in_7_rule, schedule),
            executor.submit(validate_supervision, schedule)
        ]
        results = [f.result() for f in futures]

# Add caching
@lru_cache(maxsize=100)
def validate_schedule_cached(schedule_id: str, schedule_hash: str):
    # Cache based on schedule hash
    return validate_schedule(schedule_id)
```

**Prevention:**
- Add performance tests for validation
- Profile slow validation calls
- Set SLA for validation (e.g., < 5 seconds)
- Add monitoring for validation duration
- Consider incremental validation (only changed blocks)

**Related Patterns:**
- [Performance Degradation: Slow API Endpoints](#slow-api-endpoints)

---

### Pattern 4: MCP Server Connection Refused

**Symptoms:**
```
[Agent] Error: Cannot connect to MCP server
[mcp-server] Connection refused (localhost:8080)
MCP tools unavailable
```

**Diagnosis:**
```bash
# Check if MCP server is running
docker-compose ps mcp-server

# Check MCP server logs
docker-compose logs mcp-server --tail=50

# Test connectivity
curl -s http://localhost:8080/health

# From within Docker network
docker-compose exec backend curl -s http://mcp-server:8080/health
```

**Root Cause:**
- MCP server container not started
- MCP server crashed during startup
- Port mapping incorrect
- Firewall blocking connection

**Fix:**

**Immediate:**
```bash
# Restart MCP server
docker-compose restart mcp-server

# Check startup errors
docker-compose logs mcp-server

# Verify port mapping
docker-compose ps mcp-server
# Should show: 0.0.0.0:8080->8080/tcp
```

**Permanent:**
```yaml
# docker-compose.yml - Add health check
mcp-server:
  image: residency-scheduler/mcp-server
  ports:
    - "8080:8080"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  restart: unless-stopped  # Auto-restart on crash
```

**Prevention:**
- Add MCP server health monitoring
- Add auto-restart policy
- Add startup health check
- Monitor MCP server uptime

---

## Constraint Engine Errors

### Pattern 5: INFEASIBLE - No Solution Found

**Symptoms:**
```
[Solver] Status: INFEASIBLE
Schedule generation fails with "No feasible solution"
Logs show conflicting constraints
```

**Diagnosis:**
```bash
# Check solver logs
docker-compose logs backend | grep -i "solver\|infeasible"

# Enable constraint debugging
# In backend/app/scheduling/engine.py
solver.EnableOutput()  # Prints detailed constraint violations

# Test with minimal constraints
# Disable optional constraints one by one to find conflict
```

**Root Cause:**
- Conflicting hard constraints (impossible to satisfy simultaneously)
- Insufficient resources (e.g., not enough residents for required coverage)
- Over-constrained problem (too many rigid requirements)
- Bug in constraint logic

**Fix:**

**Immediate:**
```python
# Add constraint diagnostics
# backend/app/scheduling/engine.py

if solver.Solve() == cp_model.INFEASIBLE:
    # Log all active constraints
    logger.error("INFEASIBLE schedule. Active constraints:")
    for constraint_name, constraint in all_constraints.items():
        logger.error(f"  - {constraint_name}")

    # Try relaxing soft constraints
    logger.info("Attempting solve with soft constraints relaxed...")
    solver_relaxed = SolverWithRelaxedConstraints()
    status = solver_relaxed.Solve()
```

**Permanent:**
```python
# Add constraint validation
# backend/app/scheduling/constraints/validator.py

def validate_constraint_feasibility(persons, blocks, constraints):
    """Pre-validate constraints before solving."""

    # Check resource capacity
    total_blocks = len(blocks)
    total_capacity = sum(p.max_hours * len(blocks) for p in persons)

    if total_blocks > total_capacity:
        raise ValueError(
            f"Insufficient capacity: {total_blocks} blocks needed, "
            f"only {total_capacity} available"
        )

    # Check for known conflicting constraint pairs
    if "max_hours" in constraints and "min_coverage" in constraints:
        required_coverage = constraints["min_coverage"].calculate_required()
        available_hours = constraints["max_hours"].calculate_available()

        if required_coverage > available_hours:
            raise ValueError(
                f"Conflict: min_coverage requires {required_coverage} hours, "
                f"but max_hours allows only {available_hours} hours"
            )

# Add feasibility pre-check to generation
def generate_schedule(persons, blocks, constraints):
    validate_constraint_feasibility(persons, blocks, constraints)
    # ... continue with solving
```

**Prevention:**
- Add feasibility pre-checks before solving
- Log detailed constraint info on INFEASIBLE
- Add tests for known conflicting constraint combinations
- Document constraint compatibility matrix

**Related Patterns:**
- [Schedule Generation Failures](#schedule-generation-failures)

---

### Pattern 6: Solver Timeout

**Symptoms:**
```
[Solver] Status: UNKNOWN (timeout after 300s)
Partial solution returned
Schedule incomplete
```

**Diagnosis:**
```bash
# Check solver logs for timeout
docker-compose logs backend | grep "solver.*timeout\|UNKNOWN"

# Check problem size
docker-compose logs backend | grep "variables\|constraints"
# Look for: "Creating model with 5000 variables, 10000 constraints"
```

**Root Cause:**
- Problem too large (too many variables/constraints)
- Solver time limit too short
- Missing search hints/strategies
- Complex constraint interactions

**Fix:**

**Immediate:**
```python
# Increase solver timeout
# backend/app/scheduling/engine.py
solver.parameters.max_time_in_seconds = 600  # up from 300
```

**Permanent:**
```python
# Add search strategies to guide solver
from ortools.sat.python import cp_model

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 600

# Add search strategy (helps solver make better choices)
solver.parameters.search_branching = cp_model.FIXED_SEARCH
solver.parameters.preferred_variable_order = cp_model.CHOOSE_FIRST

# Add hints from previous solutions
if previous_schedule:
    for person, block, value in previous_schedule:
        solver.AddHint(assignments[(person, block)], value)

# Add solution callback to return best-so-far if timeout
class SolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables):
        super().__init__()
        self.variables = variables
        self.best_solution = None

    def on_solution_callback(self):
        self.best_solution = {v: self.Value(v) for v in self.variables}

collector = SolutionCollector(all_variables)
status = solver.Solve(model, collector)

if status == cp_model.UNKNOWN and collector.best_solution:
    logger.warning("Timeout reached, returning best partial solution")
    return collector.best_solution
```

**Prevention:**
- Profile solver performance on representative problems
- Add problem size limits
- Implement solution caching
- Consider decomposition for large problems

---

## Agent Communication Failures

### Pattern 7: Multi-Agent Coordination Failure

**Symptoms:**
```
[Agent1] Waiting for Agent2 response...
[Agent2] Did not receive task from Agent1
Workflow stuck in intermediate state
```

**Diagnosis:**
```bash
# Check agent logs (if available)
# Look for task handoff messages

# Check for orphaned tasks
docker-compose exec redis redis-cli LRANGE agent:queue:pending 0 -1

# Check for deadlocks in workflow state
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT * FROM workflow_state WHERE status = 'pending' AND created_at < now() - interval '10 minutes';"
```

**Root Cause:**
- Message lost in transit
- Agent crashed before processing message
- Queue misconfiguration
- Task serialization failure

**Fix:**

**Immediate:**
```bash
# Clear stale tasks
docker-compose exec redis redis-cli DEL agent:queue:pending

# Reset workflow state
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
UPDATE workflow_state SET status = 'failed', error = 'Manual reset'
WHERE status = 'pending' AND created_at < now() - interval '10 minutes';"
```

**Permanent:**
```python
# Add task acknowledgment pattern
# backend/app/agents/coordinator.py

async def send_task_with_ack(task, target_agent, timeout=60):
    """Send task and wait for acknowledgment."""
    task_id = str(uuid4())
    task_data = {
        "id": task_id,
        "payload": task,
        "timestamp": datetime.utcnow().isoformat(),
        "sender": "coordinator",
        "target": target_agent
    }

    # Send task
    await redis.lpush(f"agent:{target_agent}:queue", json.dumps(task_data))

    # Wait for ack
    ack_key = f"agent:{target_agent}:ack:{task_id}"
    start_time = time.time()

    while time.time() - start_time < timeout:
        ack = await redis.get(ack_key)
        if ack:
            await redis.delete(ack_key)
            return json.loads(ack)
        await asyncio.sleep(0.5)

    raise TimeoutError(f"No acknowledgment from {target_agent} for task {task_id}")

# Add task retry logic
async def send_task_with_retry(task, target_agent, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await send_task_with_ack(task, target_agent)
        except TimeoutError:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Task retry {attempt + 1}/{max_retries}")
            await asyncio.sleep(2 ** attempt)
```

**Prevention:**
- Implement task acknowledgment
- Add task timeout and retry logic
- Monitor queue depth
- Add workflow state timeouts

---

## Schedule Generation Failures

### Pattern 8: ACGME Validation Fails After Generation

**Symptoms:**
```
[Generator] Schedule generated successfully
[Validator] ACGME validation FAILED
Error: Resident exceeds 80-hour limit in week 12
```

**Diagnosis:**
```bash
# Check validation logs
docker-compose logs backend | grep -i "acgme\|validation\|80.hour\|1.in.7"

# Run validation manually
curl -X POST http://localhost:8000/api/schedule/validate \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": "generated-123"}' | jq
```

**Root Cause:**
- Generator constraints don't match validator logic
- Validator uses different calculation method
- Edge case in constraint implementation
- Timezone handling mismatch

**Fix:**

**Immediate:**
```python
# Add pre-validation to generator
# backend/app/scheduling/engine.py

def generate_schedule(persons, blocks, constraints):
    # Generate schedule
    schedule = solver.Solve()

    # ALWAYS validate before returning
    validation_result = acgme_validator.validate(schedule)

    if not validation_result.is_valid:
        logger.error(f"Generated schedule failed ACGME validation: {validation_result.errors}")
        raise ValueError("Generated schedule violates ACGME rules")

    return schedule
```

**Permanent:**
```python
# Unify constraint logic between generator and validator
# backend/app/scheduling/constraints/acgme.py

class ACGMEConstraints:
    """Shared ACGME logic for both generation and validation."""

    @staticmethod
    def calculate_weekly_hours(assignments, week_start_date):
        """Single source of truth for weekly hour calculation."""
        week_end_date = week_start_date + timedelta(days=7)
        weekly_assignments = [
            a for a in assignments
            if week_start_date <= a.date < week_end_date
        ]
        return sum(a.hours for a in weekly_assignments)

    @staticmethod
    def check_80_hour_rule(assignments, person_id):
        """Check 80-hour rule using canonical calculation."""
        # ... implementation ...

# Use in generator
def add_acgme_constraints_to_solver(solver, persons, blocks):
    for week in range(52):
        week_hours = ACGMEConstraints.calculate_weekly_hours(...)
        solver.Add(week_hours <= 80)

# Use in validator
def validate_acgme_compliance(schedule):
    for person in schedule.persons:
        for week in range(52):
            week_hours = ACGMEConstraints.calculate_weekly_hours(...)
            if week_hours > 80:
                return ValidationError("80-hour violation")
```

**Prevention:**
- Single source of truth for ACGME rules
- Add generator-to-validator integration tests
- Validate every generated schedule before saving
- Add ACGME rule regression tests

---

## Celery Task Failures

### Pattern 9: Task Serialization Error

**Symptoms:**
```
[celery-worker] ERROR: Task failed: Cannot serialize object of type Person
TypeError: Object of type 'Person' is not JSON serializable
```

**Diagnosis:**
```bash
# Check celery logs
docker-compose logs celery-worker | grep -i "serializ"

# Check task arguments
docker-compose exec redis redis-cli LRANGE celery 0 10
```

**Root Cause:**
- Passing SQLAlchemy model objects instead of IDs
- Complex nested objects that can't be pickled
- Circular references in data structures

**Fix:**

**Immediate:**
```python
# Don't pass model objects to tasks
# backend/app/tasks/schedule.py

# BAD - passing model object
person = await db.get(Person, person_id)
generate_schedule_task.delay(person)  # ← Will fail to serialize

# GOOD - pass primitive types only
generate_schedule_task.delay(person_id=person.id)  # ← Serializable

# In task, reload from database
@celery.task
def generate_schedule_task(person_id: str):
    with get_db_session() as db:
        person = db.get(Person, person_id)
        # ... use person
```

**Permanent:**
```python
# Add task argument validation
# backend/app/tasks/base.py

from celery import Task
import json

class ValidatedTask(Task):
    """Base task that validates arguments are serializable."""

    def apply_async(self, args=None, kwargs=None, **options):
        # Validate all arguments are JSON-serializable
        try:
            json.dumps({"args": args, "kwargs": kwargs})
        except (TypeError, ValueError) as e:
            raise ValueError(
                f"Task arguments must be JSON-serializable. "
                f"Pass IDs instead of model objects. Error: {e}"
            )

        return super().apply_async(args, kwargs, **options)

# Use as base class for all tasks
@celery.task(base=ValidatedTask)
def my_task(person_id: str, schedule_id: str):
    # ... implementation
```

**Prevention:**
- Never pass model objects to tasks
- Pass IDs and reload in task
- Add argument validation
- Document task argument requirements

---

## ACGME Compliance Validation Errors

### Pattern 10: False Positive 1-in-7 Violation

**Symptoms:**
```
[Validator] ACGME violation: Resident did not have 24 hours off in 7 days
Database shows resident had day off on day 3
Validation logic incorrect
```

**Diagnosis:**
```sql
-- Check actual assignments
SELECT date, am_assignment, pm_assignment
FROM assignments
WHERE person_id = 'resident-001'
  AND date >= '2025-01-01'
  AND date <= '2025-01-07'
ORDER BY date;

-- Expected: at least one day with both AM and PM = NULL
```

**Root Cause:**
- Validator checking calendar days, not 24-hour periods
- Timezone conversion error (UTC vs local time)
- Off-by-one error in date range calculation

**Fix:**

**Immediate:**
```python
# Fix 1-in-7 validation logic
# backend/app/scheduling/acgme_validator.py

# BAD - checks calendar days
def check_1_in_7(assignments, start_date):
    for day in range(7):
        date = start_date + timedelta(days=day)
        if not has_assignment_on_date(assignments, date):
            return True  # Found a day off
    return False  # No full day off found

# GOOD - checks 24-hour periods
def check_1_in_7(assignments, start_date):
    # Check for ANY 24-hour period without work
    start_time = datetime.combine(start_date, time(0, 0))

    for hour in range(7 * 24):
        period_start = start_time + timedelta(hours=hour)
        period_end = period_start + timedelta(hours=24)

        # Check if this 24-hour period has no assignments
        has_work = any(
            assignment_overlaps(a, period_start, period_end)
            for a in assignments
        )

        if not has_work:
            return True  # Found 24-hour period off

    return False
```

**Permanent:**
```python
# Add comprehensive ACGME tests
# backend/tests/test_acgme_validator.py

class TestACGME1in7Rule:
    """Comprehensive tests for 1-in-7 rule."""

    async def test_1in7_full_day_off(self):
        """Full calendar day off satisfies rule."""
        assignments = create_assignments_with_day_off(day=3)
        assert check_1_in_7(assignments, date(2025, 1, 1))

    async def test_1in7_24_hour_period_off(self):
        """24-hour period (not full day) satisfies rule."""
        # Off from noon Monday to noon Tuesday
        assignments = create_assignments(off_from="Mon 12:00", off_to="Tue 12:00")
        assert check_1_in_7(assignments, date(2025, 1, 1))

    async def test_1in7_violation(self):
        """No 24-hour period off violates rule."""
        # Work every day, alternating AM/PM
        assignments = create_alternating_assignments()
        assert not check_1_in_7(assignments, date(2025, 1, 1))

    async def test_1in7_timezone_handling(self):
        """Handles timezone conversions correctly."""
        # Test with HST timezone
        assignments = create_assignments_hst()
        assert check_1_in_7(assignments, date(2025, 1, 1))
```

**Prevention:**
- Add edge case tests for ACGME rules
- Document exact rule interpretation
- Verify against ACGME official documentation
- Add timezone handling tests

---

## API Authentication Failures

### Pattern 11: JWT Token Expired

**Symptoms:**
```
HTTP 401 Unauthorized
Error: "Token has expired"
MCP tools fail with auth error
```

**Diagnosis:**
```bash
# Check token expiration
curl -X POST http://localhost:8000/api/auth/verify \
  -H "Authorization: Bearer $TOKEN" | jq

# Check token claims
# Decode JWT at jwt.io or:
echo $TOKEN | cut -d. -f2 | base64 -d | jq
```

**Root Cause:**
- Token expired (default TTL too short)
- Clock skew between services
- Token not refreshed

**Fix:**

**Immediate:**
```bash
# Get new token
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' | jq -r '.access_token'
```

**Permanent:**
```python
# Implement token refresh
# backend/app/api/routes/auth.py

@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user_allow_expired)
):
    """Refresh an expired token if still within refresh window."""
    access_token = create_access_token(
        data={"sub": current_user.id},
        expires_delta=timedelta(hours=24)
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Add auto-refresh to MCP client
# mcp-server/src/scheduler_mcp/client.py

class SchedulerAPIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.token_expires_at = None

    async def get_token(self):
        """Get token with auto-refresh."""
        now = datetime.utcnow()

        # Refresh if token expires in < 5 minutes
        if self.token and self.token_expires_at > now + timedelta(minutes=5):
            return self.token

        # Get new token
        response = await self.http_client.post(
            f"{self.base_url}/api/auth/token",
            json={"username": self.username, "password": self.password}
        )
        data = response.json()
        self.token = data["access_token"]
        self.token_expires_at = now + timedelta(hours=24)

        return self.token
```

**Prevention:**
- Increase token TTL for service accounts
- Implement automatic token refresh
- Add token expiration monitoring
- Handle 401 errors with auto-retry after refresh

---

## Performance Degradation

### Pattern 12: Slow Queries

**Symptoms:**
```
API response times increase from 100ms to 5+ seconds
Database CPU usage at 100%
Slow query log shows long-running queries
```

**Diagnosis:**
```sql
-- Find slow queries
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Check for missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND correlation < 0.1  -- Low correlation suggests index would help
ORDER BY tablename, attname;

-- Explain specific slow query
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM assignments
WHERE person_id = 'resident-001'
  AND date >= '2025-01-01';
```

**Root Cause:**
- Missing indexes on frequently queried columns
- Sequential scans on large tables
- N+1 query problem
- Inefficient query structure

**Fix:**

**Immediate:**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_assignments_person_id ON assignments(person_id);
CREATE INDEX CONCURRENTLY idx_assignments_date ON assignments(date);
CREATE INDEX CONCURRENTLY idx_assignments_person_date ON assignments(person_id, date);
```

**Permanent:**
```python
# Add eager loading to prevent N+1
# backend/app/api/routes/assignments.py

# BAD - N+1 query
assignments = await db.execute(select(Assignment))
for assignment in assignments.scalars():
    person = assignment.person  # ← Separate query for each!
    print(f"{person.name}: {assignment.date}")

# GOOD - eager loading
from sqlalchemy.orm import selectinload

assignments = await db.execute(
    select(Assignment)
    .options(selectinload(Assignment.person))  # ← Load all persons in one query
)
for assignment in assignments.scalars():
    person = assignment.person  # ← No additional query
    print(f"{person.name}: {assignment.date}")

# Add query performance monitoring
# backend/app/db/session.py

from sqlalchemy import event
from time import time

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time() - conn.info["query_start_time"].pop(-1)
    if total > 1.0:  # Log queries > 1 second
        logger.warning(f"Slow query ({total:.2f}s): {statement[:100]}...")
```

**Prevention:**
- Add indexes based on query patterns
- Use EXPLAIN ANALYZE for new queries
- Monitor pg_stat_statements
- Add query performance tests
- Use eager loading for relationships

**Related Patterns:**
- [Pattern 1: Connection Pool Exhausted](#pattern-1-connection-pool-exhausted)
- [Pattern 3: validate_schedule Timeout](#pattern-3-validate_schedule-timeout)

---

## Pattern Template

Use this template when adding new patterns:

```markdown
### Pattern [N]: [Name]

**Symptoms:**
```
[Error messages]
[Observable behavior]
```

**Diagnosis:**
```bash
# Commands to confirm this pattern
```

**Root Cause:**
- [What actually causes this]
- [Related factors]

**Fix:**

**Immediate:**
```bash
# Quick fix to restore service
```

**Permanent:**
```python
# Code changes to prevent recurrence
```

**Prevention:**
- [What to add/change]
- [Monitoring recommendations]

**Related Patterns:**
- [Link to related patterns]
```

## Contributing

When you encounter a new failure pattern:

1. **Document it** using the template above
2. **Add to index** at the top of this file
3. **Link related patterns** for cross-reference
4. **Update prevention** measures in relevant code
5. **Add tests** to catch the pattern in CI

## References

- `../Workflows/incident-review.md` - Post-mortem template
- `../Workflows/root-cause-analysis.md` - 5-whys methodology
- `debugging-checklist.md` - Health check procedures
- `/docs/development/DEBUGGING_WORKFLOW.md` - Overall debugging process
