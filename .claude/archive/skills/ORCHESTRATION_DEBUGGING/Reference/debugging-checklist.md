# Debugging Checklist

Step-by-step systematic troubleshooting guide for the scheduling orchestration system.

## Purpose

Provide a methodical approach to diagnosing issues when:
- No clear error message is available
- Issue is intermittent or hard to reproduce
- Multiple components may be involved
- Starting investigation with no direction

## Quick Start

Choose the appropriate checklist based on symptoms:

- [Complete System Health Check](#complete-system-health-check) - Start here if unsure
- [Backend API Issues](#backend-api-issues) - 500 errors, slow responses
- [MCP Tool Failures](#mcp-tool-failures) - Tool timeouts, connection errors
- [Database Issues](#database-issues) - Slow queries, deadlocks, connection errors
- [Schedule Generation Issues](#schedule-generation-issues) - INFEASIBLE, validation failures
- [Celery Task Issues](#celery-task-issues) - Task failures, queue backlogs
- [Agent Workflow Issues](#agent-workflow-issues) - Multi-agent coordination failures

---

## Complete System Health Check

Use this comprehensive checklist when starting an investigation.

### 1. Service Availability

Check that all services are running:

```bash
# Check all containers
docker-compose ps

# Expected output: all services "Up"
# backend        Up (healthy)   8000/tcp
# db             Up             5432/tcp
# redis          Up             6379/tcp
# mcp-server     Up (healthy)   8080/tcp
# celery-worker  Up
# celery-beat    Up
```

**Status:** ☐ All services running

**If failed:**
- [ ] Check which service is down: `docker-compose ps`
- [ ] View service logs: `docker-compose logs [service]`
- [ ] Restart service: `docker-compose restart [service]`
- [ ] Check for startup errors in logs

---

### 2. Basic Connectivity

Test that services can communicate:

```bash
# Test backend API
curl -s http://localhost:8000/health | jq
# Expected: {"status": "healthy"}

# Test MCP server
curl -s http://localhost:8080/health | jq
# Expected: {"status": "ok"}

# Test backend → database
docker-compose exec backend python -c "
from app.db.session import get_db
import asyncio
async def test():
    async for db in get_db():
        print('Database connected')
        break
asyncio.run(test())
"
# Expected: "Database connected"

# Test MCP → backend
docker-compose exec mcp-server curl -s http://backend:8000/health
# Expected: {"status": "healthy"}
```

**Status:** ☐ All connectivity tests pass

**If failed:**
- [ ] Check network configuration in docker-compose.yml
- [ ] Check firewall rules
- [ ] Check service logs for connection errors
- [ ] Verify environment variables (especially URLs)

---

### 3. Database Health

Check database status and performance:

```sql
-- Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

-- Check connection count
SELECT count(*) as connections,
       (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max
FROM pg_stat_activity;
-- Expected: connections < max (e.g., 15/100)

-- Check for long-running queries
SELECT pid, now() - query_start as duration, state, left(query, 50)
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - interval '5 seconds'
ORDER BY duration DESC;
-- Expected: No queries > 5 seconds (unless expected)

-- Check for locks
SELECT count(*) FROM pg_locks WHERE NOT granted;
-- Expected: 0

-- Check table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
-- Expected: Reasonable sizes (assignments table largest)
```

**Status:** ☐ Database healthy

**If failed:**
- [ ] High connection count → See [Connection Pool Exhausted](common-failure-patterns.md#pattern-1-connection-pool-exhausted)
- [ ] Long-running queries → See [Slow Queries](common-failure-patterns.md#pattern-12-slow-queries)
- [ ] Locks detected → See [Deadlocks](common-failure-patterns.md#pattern-2-deadlocks)

---

### 4. Redis Health

Check Redis status:

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check connection
PING
# Expected: PONG

# Check memory usage
INFO memory | grep used_memory_human
# Expected: Reasonable usage (< 1GB for typical workload)

# Check Celery queue depth
LLEN celery
# Expected: < 100 (unless heavy load)

# Check for failed tasks
LLEN celery-failed
# Expected: 0 (or low number)
```

**Status:** ☐ Redis healthy

**If failed:**
- [ ] High memory usage → Clear old keys, increase memory limit
- [ ] Large queue depth → Check Celery workers, increase workers
- [ ] Failed tasks → Investigate task failures in Celery logs

---

### 5. Celery Workers

Check background task processing:

```bash
# Check worker status
docker-compose exec celery-worker celery -A app.core.celery_app inspect active
# Expected: List of active tasks (or empty if idle)

# Check registered tasks
docker-compose exec celery-worker celery -A app.core.celery_app inspect registered
# Expected: List of registered tasks

# Check worker stats
docker-compose exec celery-worker celery -A app.core.celery_app inspect stats
# Expected: Worker info, pool stats
```

**Status:** ☐ Celery healthy

**If failed:**
- [ ] No registered tasks → Worker startup issue, check logs
- [ ] Tasks stuck in active → See [Celery Task Issues](#celery-task-issues)
- [ ] Worker not responding → Restart worker

---

### 6. Recent Errors

Check logs for recent errors across all services:

```bash
# Backend errors (last hour)
docker-compose logs backend --since 1h | grep -i "error\|exception" | tail -20

# MCP server errors
docker-compose logs mcp-server --since 1h | grep -i "error\|exception" | tail -20

# Database errors
docker-compose logs db --since 1h | grep -i "error\|fatal" | tail -20

# Celery errors
docker-compose logs celery-worker --since 1h | grep -i "error\|exception" | tail -20
```

**Status:** ☐ No unexpected errors

**If failed:**
- [ ] Analyze error messages
- [ ] Match to patterns in [Common Failure Patterns](common-failure-patterns.md)
- [ ] Follow specific service checklist below

---

## Backend API Issues

Use this when experiencing API-related problems.

### Symptoms
- HTTP 500 errors
- Slow response times
- Timeout errors
- Validation errors

### Checklist

**1. Check API Health**
```bash
curl -s http://localhost:8000/health | jq
# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}
```
☐ Health check passes

**2. Check Recent API Errors**
```bash
docker-compose logs backend --since 30m | grep "500\|ERROR"
```
☐ No errors or errors identified

**3. Check Response Times**
```bash
# Extract response times from logs
docker-compose logs backend | grep "completed in" | tail -20
# Look for patterns: sudden spikes, consistently slow endpoints
```
☐ Response times normal (< 1s for most endpoints)

**4. Check Database Connection Pool**
```python
# Run this in backend container
docker-compose exec backend python -c "
from app.db.session import engine
print(f'Pool size: {engine.pool.size()}')
print(f'Checked out: {engine.pool.checkedout()}')
print(f'Overflow: {engine.pool.overflow()}')
"
```
☐ Pool not exhausted (checkedout < size + overflow)

**5. Test Specific Endpoint**
```bash
# Test the failing endpoint
curl -v -X POST http://localhost:8000/api/[endpoint] \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"test": "data"}'

# Check response code, headers, body
```
☐ Endpoint responds correctly

**6. Check Environment Variables**
```bash
docker-compose exec backend env | grep -E "DATABASE_URL|REDIS_URL|SECRET_KEY"
```
☐ All required env vars present and correct

**If issues persist:**
- [ ] Enable DEBUG logging: Set `LOG_LEVEL=DEBUG` and restart
- [ ] Check specific error in [Common Failure Patterns](common-failure-patterns.md)
- [ ] Review recent code changes: `git log --oneline -10`

---

## MCP Tool Failures

Use this when MCP tools are failing or timing out.

### Symptoms
- Tool timeout errors
- Connection refused
- Tool returns errors
- Agent can't access tools

### Checklist

**1. Check MCP Server Status**
```bash
docker-compose ps mcp-server
# Expected: Up (healthy)

curl -s http://localhost:8080/health
# Expected: {"status": "ok"}
```
☐ MCP server running and healthy

**2. List Available Tools**
```bash
docker-compose exec mcp-server python -c "
from scheduler_mcp.server import mcp
print(f'Tools: {len(mcp.tools)}')
for tool in sorted([t.name for t in mcp.tools]):
    print(f'  - {tool}')
"
# Expected: 29+ tools listed
```
☐ All expected tools available

**3. Test MCP → Backend Connectivity**
```bash
docker-compose exec mcp-server curl -s http://backend:8000/health
# Expected: {"status": "healthy"}
```
☐ MCP can reach backend

**4. Check Recent MCP Errors**
```bash
docker-compose logs mcp-server --since 30m | grep -i "error\|timeout\|failed"
```
☐ No errors or errors identified

**5. Test Specific Tool**
```bash
# From MCP server container, test a tool
docker-compose exec mcp-server python -c "
from scheduler_mcp.server import mcp
import asyncio

async def test():
    # Example: test health check tool
    result = await mcp.call_tool('health_check_tool', {})
    print(f'Result: {result}')

asyncio.run(test())
"
```
☐ Tool executes successfully

**6. Check Tool Timeout Configuration**
```bash
docker-compose exec mcp-server python -c "
from scheduler_mcp.config import DEFAULT_TIMEOUT
print(f'Default timeout: {DEFAULT_TIMEOUT}s')
"
```
☐ Timeout appropriate for workload

**If issues persist:**
- [ ] Check specific timeout pattern in [Common Failure Patterns](common-failure-patterns.md#pattern-3-validate_schedule-timeout)
- [ ] Increase timeout for slow tools
- [ ] Check backend logs for API errors
- [ ] Review MCP server logs in detail

---

## Database Issues

Use this when experiencing database-related problems.

### Symptoms
- Connection timeouts
- Slow queries
- Deadlock errors
- Connection pool exhausted

### Checklist

**1. Check Database Connection**
```bash
docker-compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1;"
# Expected: Returns 1
```
☐ Database accessible

**2. Check Active Connections**
```sql
SELECT
    datname,
    count(*) as connections,
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
FROM pg_stat_activity
GROUP BY datname, max_connections;
```
☐ Connections < max_connections

**3. Check for Long-Running Queries**
```sql
SELECT
    pid,
    now() - query_start as duration,
    state,
    substring(query, 1, 100) as query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
```
☐ No queries running > 5 seconds (unless expected)

**4. Check for Locks**
```sql
SELECT
    locktype,
    relation::regclass,
    mode,
    pid,
    granted
FROM pg_locks
WHERE NOT granted;
```
☐ No locks waiting (count = 0)

**5. Check Query Performance**
```sql
SELECT
    substring(query, 1, 50) as query,
    calls,
    round(mean_exec_time::numeric, 2) as mean_ms,
    round(max_exec_time::numeric, 2) as max_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```
☐ Query performance acceptable (mean < 100ms for common queries)

**6. Check Table Indexes**
```sql
-- For assignments table (most queried)
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'assignments';

-- Expected indexes:
-- - assignments_pkey (primary key)
-- - idx_assignments_person_id
-- - idx_assignments_date
-- - idx_assignments_person_date
```
☐ All expected indexes present

**7. Check Database Size**
```sql
SELECT
    pg_size_pretty(pg_database_size('residency_scheduler')) as db_size;
```
☐ Database size reasonable (< 10GB for typical deployment)

**If issues persist:**
- [ ] Connection pool exhausted → See [Pattern 1](common-failure-patterns.md#pattern-1-connection-pool-exhausted)
- [ ] Slow queries → See [Pattern 12](common-failure-patterns.md#pattern-12-slow-queries)
- [ ] Deadlocks → See [Pattern 2](common-failure-patterns.md#pattern-2-deadlocks)
- [ ] Missing indexes → Add indexes based on query patterns

---

## Schedule Generation Issues

Use this when schedule generation is failing.

### Symptoms
- Solver returns INFEASIBLE
- Solver timeout
- Generated schedule fails validation
- Constraint errors

### Checklist

**1. Check Solver Logs**
```bash
docker-compose logs backend | grep -i "solver\|constraint\|infeasible" | tail -50
```
☐ Solver logs reviewed

**2. Check Problem Size**
```bash
# Look for log entries about problem size
docker-compose logs backend | grep -i "variables\|constraints" | tail -10

# Example output:
# Creating model with 2500 variables, 5000 constraints
```
☐ Problem size within reasonable limits (< 10k variables)

**3. Verify Input Data**
```sql
-- Check persons available for scheduling
SELECT role, year, count(*) as count
FROM persons
WHERE status = 'active'
GROUP BY role, year;

-- Check blocks for scheduling period
SELECT count(*) as total_blocks,
       min(date) as start_date,
       max(date) as end_date
FROM blocks
WHERE date >= CURRENT_DATE;

-- Check rotation templates
SELECT activity_type, count(*) as count
FROM rotation_templates
WHERE is_active = true
GROUP BY activity_type;
```
☐ Input data looks correct

**4. Test with Minimal Constraints**
```python
# Temporarily disable optional constraints
# In backend/app/scheduling/engine.py

# Comment out optional constraints to isolate issue
# solver.Add(optional_constraint_1)  # ← Commented out
# solver.Add(optional_constraint_2)  # ← Commented out

# Keep only hard constraints (ACGME, coverage)
solver.Add(acgme_80_hour_constraint)
solver.Add(acgme_1_in_7_constraint)
solver.Add(min_coverage_constraint)
```
☐ Simplified problem solves successfully

**5. Check for Constraint Conflicts**
```python
# Add constraint diagnostics
# backend/app/scheduling/engine.py

if solver.Solve() == cp_model.INFEASIBLE:
    # Log all constraints for analysis
    logger.error("Constraints added:")
    for name, constraint in all_constraints.items():
        logger.error(f"  - {name}: {constraint}")

    # Check common conflicts
    if max_hours_constraint and min_coverage_constraint:
        logger.error("Potential conflict between max hours and min coverage")
```
☐ Constraint conflict identified (or ruled out)

**6. Verify ACGME Validation**
```bash
# Test validation endpoint
curl -X POST http://localhost:8000/api/schedule/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "schedule_id": "test-schedule-123"
  }' | jq

# Expected: Detailed validation results
```
☐ Validation works independently

**If issues persist:**
- [ ] INFEASIBLE → See [Pattern 5](common-failure-patterns.md#pattern-5-infeasible---no-solution-found)
- [ ] Timeout → See [Pattern 6](common-failure-patterns.md#pattern-6-solver-timeout)
- [ ] Validation fails → See [Pattern 8](common-failure-patterns.md#pattern-8-acgme-validation-fails-after-generation)
- [ ] Analyze constraint interactions in detail

---

## Celery Task Issues

Use this when background tasks are failing.

### Symptoms
- Tasks not executing
- Task timeouts
- Queue backlog
- Task failures

### Checklist

**1. Check Worker Status**
```bash
docker-compose ps celery-worker celery-beat
# Expected: Both Up
```
☐ Workers running

**2. Check Active Tasks**
```bash
docker-compose exec celery-worker celery -A app.core.celery_app inspect active
```
☐ No stuck tasks (or identified stuck tasks)

**3. Check Queue Depth**
```bash
docker-compose exec redis redis-cli LLEN celery
# Expected: < 100 (depends on load)
```
☐ Queue depth reasonable

**4. Check for Failed Tasks**
```bash
# Check failed queue
docker-compose exec redis redis-cli LLEN celery-failed

# If failed tasks exist, inspect them
docker-compose exec redis redis-cli LRANGE celery-failed 0 -1
```
☐ No failed tasks (or failures identified)

**5. Check Worker Logs**
```bash
docker-compose logs celery-worker --since 30m | grep -i "error\|failed"
```
☐ No errors or errors identified

**6. Check Beat Scheduler**
```bash
# Check that periodic tasks are scheduled
docker-compose logs celery-beat --since 30m | grep "Scheduler"
```
☐ Beat scheduler running correctly

**7. Test Task Execution**
```python
# From backend container
docker-compose exec backend python -c "
from app.tasks.resilience import health_check_task

# Send task
result = health_check_task.delay()
print(f'Task ID: {result.id}')
print(f'Status: {result.status}')

# Wait for result (max 30s)
try:
    output = result.get(timeout=30)
    print(f'Result: {output}')
except Exception as e:
    print(f'Error: {e}')
"
```
☐ Task executes successfully

**If issues persist:**
- [ ] Task serialization error → See [Pattern 9](common-failure-patterns.md#pattern-9-task-serialization-error)
- [ ] Increase worker concurrency
- [ ] Check for task code errors in detail
- [ ] Review task arguments for serializability

---

## Agent Workflow Issues

Use this when multi-agent workflows fail.

### Symptoms
- Workflow stuck in intermediate state
- Agent communication timeout
- Task not acknowledged
- Coordination failure

### Checklist

**1. Check Workflow State**
```sql
-- If using workflow state table
SELECT * FROM workflow_state
WHERE status = 'pending'
  AND created_at < now() - interval '10 minutes';
```
☐ No stuck workflows

**2. Check Agent Queues**
```bash
# Check Redis queues for each agent
docker-compose exec redis redis-cli KEYS "agent:*:queue"

# Check queue depths
for queue in $(docker-compose exec redis redis-cli KEYS "agent:*:queue"); do
    echo "$queue: $(docker-compose exec redis redis-cli LLEN $queue)"
done
```
☐ Queues not backing up

**3. Check Message Acknowledgments**
```bash
# Check for unacknowledged messages
docker-compose exec redis redis-cli KEYS "agent:*:ack:*"
```
☐ No stale ack keys (older than 5 minutes)

**4. Review Agent Logs**
```bash
# If agents log to separate files/streams
docker-compose logs [agent-service] --since 30m
```
☐ Agent logs reviewed for errors

**5. Test Agent Communication**
```python
# Test sending a message between agents
# (Implementation depends on your agent framework)
```
☐ Communication test passes

**If issues persist:**
- [ ] See [Pattern 7](common-failure-patterns.md#pattern-7-multi-agent-coordination-failure)
- [ ] Review agent communication protocol
- [ ] Add message acknowledgment if missing
- [ ] Implement timeout and retry logic

---

## Debugging Decision Tree

Use this to quickly identify which checklist to use:

```
Is there an error message?
├─ YES → Match error to Common Failure Patterns
│        └─ If no match → Continue to next question
└─ NO → Continue

Which symptom describes the issue?
├─ API returns errors → Backend API Issues
├─ MCP tools fail → MCP Tool Failures
├─ Database errors → Database Issues
├─ Schedule won't generate → Schedule Generation Issues
├─ Background tasks fail → Celery Task Issues
├─ Workflow stuck → Agent Workflow Issues
└─ Not sure → Complete System Health Check

Still not resolved?
└─ See incident-review.md for full post-mortem workflow
```

---

## Quick Command Reference

### Essential Health Checks

```bash
# All services status
docker-compose ps

# All service logs
docker-compose logs --tail=50 --follow

# Database connection
docker-compose exec db psql -U scheduler -d residency_scheduler -c "SELECT 1;"

# API health
curl -s http://localhost:8000/health | jq

# MCP health
curl -s http://localhost:8080/health | jq

# Redis health
docker-compose exec redis redis-cli PING

# Celery workers
docker-compose exec celery-worker celery -A app.core.celery_app inspect active
```

### Common Diagnostic Queries

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Long queries
SELECT pid, now() - query_start, query FROM pg_stat_activity WHERE state = 'active';

-- Locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename)) FROM pg_tables WHERE schemaname = 'public';
```

### Log Analysis

```bash
# Backend errors (last hour)
docker-compose logs backend --since 1h | grep -i error

# MCP errors
docker-compose logs mcp-server --since 1h | grep -i error

# Count errors by type
docker-compose logs backend | grep ERROR | awk '{print $NF}' | sort | uniq -c

# Timeline of events
docker-compose logs --since 2025-12-26T14:00:00 --until 2025-12-26T15:00:00 | sort
```

---

## Checklist Template

Use this template for custom checklists:

```markdown
## [Component] Issues

### Symptoms
- [Symptom 1]
- [Symptom 2]

### Checklist

**1. [Check Name]**
```bash
# Command to run
```
☐ [Expected result]

**2. [Check Name]**
```bash
# Command to run
```
☐ [Expected result]

**If issues persist:**
- [ ] [Action 1]
- [ ] [Action 2]
```

---

## References

- [Common Failure Patterns](common-failure-patterns.md) - Known issues and fixes
- [../Workflows/incident-review.md](../Workflows/incident-review.md) - Post-mortem template
- [../Workflows/log-analysis.md](../Workflows/log-analysis.md) - Log analysis techniques
- [../Workflows/root-cause-analysis.md](../Workflows/root-cause-analysis.md) - 5-whys methodology
- `/docs/development/DEBUGGING_WORKFLOW.md` - Overall debugging process
