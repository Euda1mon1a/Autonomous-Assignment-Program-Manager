# Log Analysis Workflow

Systematic log parsing and correlation across multiple services to diagnose issues in the scheduling orchestration system.

## Purpose

Extract meaningful insights from logs across:
- Backend API (FastAPI/Uvicorn)
- MCP Server (Model Context Protocol tools)
- Database (PostgreSQL)
- Background Workers (Celery)
- Message Queue (Redis)
- Frontend (Next.js - if applicable)

## When to Use

- Error message is unclear or generic
- Issue spans multiple services
- Need to reconstruct request flow
- Intermittent issues requiring pattern analysis
- Performance degradation investigation
- Post-incident analysis

## Log Locations

### Backend API Logs

**Docker Environment**
```bash
# Real-time logs
docker-compose logs backend --tail=200 --follow

# Specific time range
docker-compose logs backend --since 2025-12-26T14:00:00 --until 2025-12-26T15:00:00

# Save to file for analysis
docker-compose logs backend --no-color > backend_logs.txt
```

**Direct File Access** (if not using Docker)
```bash
# Application logs
tail -f backend/logs/app.log

# Uvicorn access logs
tail -f backend/logs/access.log

# Error logs only
tail -f backend/logs/error.log
```

### MCP Server Logs

**Docker Environment**
```bash
# Real-time MCP logs
docker-compose logs mcp-server --tail=100 --follow

# Tool invocations
docker-compose logs mcp-server | grep "tool_call\|tool_result"

# Errors only
docker-compose logs mcp-server | grep -i "error\|exception\|failed"
```

**Direct Access**
```bash
# If running MCP server directly
tail -f mcp-server/logs/mcp.log
```

### Database Logs

**PostgreSQL Query Logs**
```bash
# Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

# Enable query logging (for current session)
SET log_statement = 'all';
SET log_duration = on;

# View PostgreSQL logs
docker-compose logs db --tail=100
```

**Slow Query Analysis**
```sql
-- Check for slow queries (requires pg_stat_statements extension)
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Check for lock contention
SELECT
    locktype,
    relation::regclass,
    mode,
    transactionid AS tid,
    pid,
    granted
FROM pg_locks
WHERE NOT granted;
```

### Celery Worker Logs

**Docker Environment**
```bash
# Worker logs
docker-compose logs celery-worker --tail=100 --follow

# Beat scheduler logs
docker-compose logs celery-beat --tail=50 --follow

# Filter for specific task
docker-compose logs celery-worker | grep "task_name"
```

**Task Status**
```bash
# Check Redis for task queues
docker-compose exec redis redis-cli

# Inside Redis CLI:
LLEN celery              # Queue length
LRANGE celery 0 10       # First 10 tasks
KEYS celery-task-*       # All task results
```

### Redis Logs

```bash
# Redis server logs
docker-compose logs redis --tail=50

# Monitor Redis commands in real-time
docker-compose exec redis redis-cli MONITOR
```

## Log Analysis Phases

### Phase 1: Log Location Discovery

**Quick Reference Table**

| Component | Log Location | Key Patterns |
|-----------|--------------|--------------|
| **Backend API** | `docker-compose logs backend` | `INFO`, `ERROR`, `WARNING` |
| **MCP Server** | `docker-compose logs mcp-server` | `tool_call`, `tool_result`, `error` |
| **Database** | `docker-compose logs db` | `ERROR`, `FATAL`, `DETAIL` |
| **Celery Worker** | `docker-compose logs celery-worker` | `Task`, `succeeded`, `failed` |
| **Redis** | `docker-compose logs redis` | `WARNING`, `error` |

### Phase 2: Error Pattern Extraction

#### Common Error Patterns

**1. HTTP 500 Errors**
```bash
# Find all 500 errors with context
docker-compose logs backend | grep -B 5 -A 5 "500"

# Count 500 errors by endpoint
docker-compose logs backend | grep "500" | awk '{print $NF}' | sort | uniq -c
```

**Example Output Analysis**
```
2025-12-26 14:30:15 INFO     [assign_shifts] Starting assignment
2025-12-26 14:30:16 ERROR    [database] Connection pool exhausted
2025-12-26 14:30:16 ERROR    [assign_shifts] Failed to assign shifts
2025-12-26 14:30:16 INFO     [uvicorn] "POST /api/assignments HTTP/1.1" 500

→ Pattern: Database connection issue causing 500 error
→ Root: Connection pool exhaustion
```

**2. MCP Tool Timeouts**
```bash
# Find timeout errors
docker-compose logs mcp-server | grep -i "timeout\|timed out"

# Identify which tools are timing out
docker-compose logs mcp-server | grep "timeout" | awk '{print $5}' | sort | uniq -c
```

**Example Output Analysis**
```
2025-12-26 14:32:10 [mcp] tool_call: validate_schedule
2025-12-26 14:32:40 [mcp] ERROR: Tool timeout after 30s
2025-12-26 14:32:40 [mcp] tool_result: error

→ Pattern: validate_schedule tool consistently times out
→ Root: Likely large dataset or inefficient query
```

**3. Database Deadlocks**
```bash
# Find deadlock errors
docker-compose logs db | grep -i "deadlock"

# Context around deadlock
docker-compose logs db | grep -B 10 -A 10 "deadlock"
```

**Example Output Analysis**
```
ERROR: deadlock detected
DETAIL: Process 1234 waits for ShareLock on transaction 5678
        Process 5678 waits for ExclusiveLock on transaction 1234
HINT: See server log for query details

→ Pattern: Circular lock dependency
→ Root: Multiple concurrent updates to same resources
```

**4. Constraint Solver Failures**
```bash
# Find solver errors
docker-compose logs backend | grep -i "solver\|constraint\|infeasible"

# Identify specific constraint failures
docker-compose logs backend | grep "constraint" | awk -F'constraint:' '{print $2}' | sort | uniq -c
```

**Example Output Analysis**
```
2025-12-26 14:35:00 [solver] Adding constraint: max_hours_per_week
2025-12-26 14:35:02 [solver] Adding constraint: min_coverage
2025-12-26 14:35:05 [solver] Solving...
2025-12-26 14:35:30 [solver] INFEASIBLE: No solution found
2025-12-26 14:35:30 [solver] Conflicting constraints: max_hours vs min_coverage

→ Pattern: Constraint conflict
→ Root: Impossible to satisfy both max hours and min coverage
```

### Phase 3: Cross-Service Correlation

Trace a single request across multiple services using request IDs or timestamps.

#### Using Request IDs (Recommended)

**Backend: Add Request ID Logging**
```python
# backend/app/api/deps.py
from uuid import uuid4

async def get_request_id():
    return str(uuid4())

# In routes, use:
logger.info(f"[{request_id}] Processing schedule generation")
```

**Correlation Example**
```bash
# Find request ID in backend
REQUEST_ID="abc-123-def"

# Trace across services
echo "=== Backend Logs ==="
docker-compose logs backend | grep $REQUEST_ID

echo "=== MCP Server Logs ==="
docker-compose logs mcp-server | grep $REQUEST_ID

echo "=== Celery Logs ==="
docker-compose logs celery-worker | grep $REQUEST_ID
```

#### Using Timestamps (When Request IDs Not Available)

**1. Identify failure timestamp from user report or monitoring**
```
Issue reported at: 2025-12-26 14:30 UTC
```

**2. Extract logs around that time (+/- 5 minutes)**
```bash
# Backend
docker-compose logs backend --since 2025-12-26T14:25:00 --until 2025-12-26T14:35:00 > backend_window.log

# MCP Server
docker-compose logs mcp-server --since 2025-12-26T14:25:00 --until 2025-12-26T14:35:00 > mcp_window.log

# Database
docker-compose logs db --since 2025-12-26T14:25:00 --until 2025-12-26T14:35:00 > db_window.log

# Celery
docker-compose logs celery-worker --since 2025-12-26T14:25:00 --until 2025-12-26T14:35:00 > celery_window.log
```

**3. Build timeline from all sources**
```bash
# Merge and sort all logs by timestamp
cat backend_window.log mcp_window.log db_window.log celery_window.log \
  | sort > combined_timeline.log

# Analyze timeline
less combined_timeline.log
```

### Phase 4: Timeline Reconstruction

Build a chronological sequence of events leading to the failure.

#### Timeline Template

```markdown
## Timeline: [Incident Description]

| Time | Service | Event | Evidence |
|------|---------|-------|----------|
| 14:30:00 | Backend | Request received | `POST /api/schedule/generate` |
| 14:30:01 | MCP | Tool call: validate_constraints | `tool_call: validate_constraints` |
| 14:30:02 | Database | Query: SELECT assignments | `SELECT * FROM assignments WHERE...` |
| 14:30:15 | Database | Long query detected | `query duration: 13.5s` |
| 14:30:20 | MCP | Tool timeout | `ERROR: timeout after 30s` |
| 14:30:20 | Backend | Return 500 error | `HTTP 500` |
```

#### Automated Timeline Generation

**Using grep and awk**
```bash
#!/bin/bash
# Extract timeline from logs

echo "| Time | Service | Event |"
echo "|------|---------|-------|"

# Backend events
docker-compose logs backend --since 2025-12-26T14:00:00 --no-color \
  | grep -E "ERROR|WARNING|INFO" \
  | awk '{print "| " $1 " " $2 " | Backend | " substr($0, index($0,$4)) " |"}'

# MCP events
docker-compose logs mcp-server --since 2025-12-26T14:00:00 --no-color \
  | grep -E "error|tool_call|tool_result" \
  | awk '{print "| " $1 " " $2 " | MCP | " substr($0, index($0,$4)) " |"}'

# Sort by timestamp (requires further processing)
```

### Phase 5: Anomaly Detection

Identify patterns that deviate from normal behavior.

#### Frequency Analysis

**1. Error Rate Over Time**
```bash
# Count errors per minute
docker-compose logs backend --since 2025-12-26T14:00:00 \
  | grep ERROR \
  | awk '{print $1 " " $2}' \
  | cut -d: -f1,2 \
  | uniq -c

# Output example:
#   5 2025-12-26 14:30  ← Normal
#  45 2025-12-26 14:31  ← Spike!
#   3 2025-12-26 14:32  ← Recovered
```

**2. Response Time Distribution**
```bash
# Extract response times from uvicorn logs
docker-compose logs backend \
  | grep "completed" \
  | awk '{print $NF}' \
  | sed 's/ms//' \
  | sort -n \
  | awk '
    {
      times[NR] = $1
      sum += $1
    }
    END {
      print "Count: " NR
      print "Mean: " sum/NR " ms"
      print "Median: " times[int(NR/2)] " ms"
      print "P95: " times[int(NR*0.95)] " ms"
      print "P99: " times[int(NR*0.99)] " ms"
      print "Max: " times[NR] " ms"
    }'
```

#### Pattern Recognition

**Recurring Errors**
```bash
# Find most common error messages
docker-compose logs backend \
  | grep ERROR \
  | awk -F'ERROR' '{print $2}' \
  | sort \
  | uniq -c \
  | sort -rn \
  | head -10

# Output shows top 10 most frequent errors
```

**Cascading Failures**
```bash
# Look for error propagation
docker-compose logs backend --since 2025-12-26T14:30:00 \
  | grep -E "ERROR|CRITICAL" \
  | awk '{print $1 " " $2 " - " $0}'

# Visual inspection will show if errors cluster together (cascade)
```

## Diagnostic Queries

### Backend Health Check

```bash
# Check if backend is responding
curl -s http://localhost:8000/health | jq

# Expected output:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected"
# }
```

### Database Connection Status

```sql
-- Active connections
SELECT
    datname,
    count(*) as connections,
    max_conn
FROM pg_stat_activity psa
JOIN (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') mc ON true
GROUP BY datname, max_conn;

-- Long-running queries
SELECT
    pid,
    now() - query_start as duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND now() - query_start > interval '5 seconds'
ORDER BY duration DESC;
```

### MCP Server Connectivity

```bash
# Test from host
curl -s http://localhost:8080/health

# Test from within Docker network
docker-compose exec mcp-server curl -s http://backend:8000/health

# Check tool availability
docker-compose exec mcp-server python -c "
from scheduler_mcp.server import mcp
print(f'Tools available: {len(mcp.tools)}')
for tool in mcp.tools[:5]:
    print(f'  - {tool.name}')
"
```

### Celery Queue Status

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Inside Redis CLI:
# Queue depth
LLEN celery

# Pending tasks
LRANGE celery 0 -1

# Task results (successful)
KEYS celery-task-meta-*

# Failed tasks
LRANGE celery-failed 0 -1
```

## Log Analysis Checklist

Use this checklist when analyzing logs for an incident:

- [ ] **Identify time window** of the incident
- [ ] **Collect logs** from all relevant services
- [ ] **Extract error patterns** using grep/awk
- [ ] **Find first occurrence** of the error
- [ ] **Trace request flow** across services (using request ID or timestamp)
- [ ] **Build timeline** of events
- [ ] **Check for cascading failures** (one error triggering others)
- [ ] **Analyze frequency** (one-time vs recurring)
- [ ] **Correlate with code changes** (git log)
- [ ] **Check resource utilization** (CPU, memory, connections)
- [ ] **Document findings** in incident review

## Advanced Techniques

### Log Aggregation with jq

If logs are in JSON format:

```bash
# Pretty-print JSON logs
docker-compose logs backend --no-color | grep -E '^\{' | jq

# Filter by log level
docker-compose logs backend --no-color | grep -E '^\{' | jq 'select(.level == "ERROR")'

# Extract specific fields
docker-compose logs backend --no-color | grep -E '^\{' | jq '{time, level, message}'

# Count errors by type
docker-compose logs backend --no-color | grep -E '^\{' | jq -r '.error_type' | sort | uniq -c
```

### Regular Expression Patterns

**Common Backend Error Patterns**
```bash
# Database errors
grep -E "psycopg2\.|sqlalchemy\.|database" backend_logs.txt

# Authentication errors
grep -E "401|403|Unauthorized|Forbidden" backend_logs.txt

# Validation errors
grep -E "ValidationError|422|Invalid" backend_logs.txt

# Timeout errors
grep -E "timeout|timed out|TimeoutError" backend_logs.txt

# Memory errors
grep -E "MemoryError|OutOfMemory|cannot allocate" backend_logs.txt
```

**MCP Tool Patterns**
```bash
# Tool execution
grep -E "tool_call:|tool_result:" mcp_logs.txt

# Tool failures
grep -E "tool_result:.*error|tool failed" mcp_logs.txt

# Slow tools
grep -E "tool.*duration|took.*seconds" mcp_logs.txt
```

### Performance Analysis

**Identify slow endpoints**
```bash
# Extract all request durations
docker-compose logs backend \
  | grep "completed in" \
  | awk '{
      endpoint = $(NF-3)
      duration = $(NF-1)
      print endpoint, duration
    }' \
  | sort -k2 -rn \
  | head -20

# Group by endpoint
docker-compose logs backend \
  | grep "completed in" \
  | awk '{print $(NF-3)}' \
  | sort \
  | uniq -c \
  | sort -rn
```

## Example: Complete Log Analysis Session

```bash
#!/bin/bash
# Log analysis for incident INC-20251226-001

echo "=== Incident Log Analysis ==="
echo "Incident: Schedule generation 500 errors"
echo "Time window: 2025-12-26 14:30-14:45 UTC"
echo ""

# 1. Collect logs
echo "Step 1: Collecting logs..."
docker-compose logs backend --since 2025-12-26T14:30:00 --until 2025-12-26T14:45:00 --no-color > backend.log
docker-compose logs mcp-server --since 2025-12-26T14:30:00 --until 2025-12-26T14:45:00 --no-color > mcp.log
docker-compose logs db --since 2025-12-26T14:30:00 --until 2025-12-26T14:45:00 --no-color > db.log

# 2. Find first error
echo "Step 2: Finding first error..."
grep -m 1 "500\|ERROR" backend.log

# 3. Extract error patterns
echo "Step 3: Error patterns..."
grep ERROR backend.log | awk '{print $NF}' | sort | uniq -c

# 4. Build timeline
echo "Step 4: Building timeline..."
cat backend.log mcp.log db.log | sort > timeline.log
echo "Timeline saved to timeline.log"

# 5. Identify root cause indicators
echo "Step 5: Root cause indicators..."
grep -i "connection\|pool\|timeout\|deadlock" timeline.log

echo ""
echo "Analysis complete. Review timeline.log for full details."
```

## References

- `incident-review.md` - Post-mortem template
- `root-cause-analysis.md` - 5-whys methodology
- `../Reference/debugging-checklist.md` - Health check procedures
- `/docs/development/DEBUGGING_WORKFLOW.md` - Overall debugging process
