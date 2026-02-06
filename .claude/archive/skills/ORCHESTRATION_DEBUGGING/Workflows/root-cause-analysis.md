# Root Cause Analysis Workflow

Use the 5-whys methodology to systematically identify the underlying cause of failures in the scheduling system.

## Purpose

Move beyond surface-level symptoms to find the true root cause that, if fixed, will prevent the issue from recurring.

## When to Use

- After identifying a problem's symptoms
- When a quick fix is clear but underlying cause is not
- For post-incident analysis
- When the same issue recurs despite fixes
- Before implementing major changes

## The 5-Whys Methodology

### Core Principle

Ask "Why?" five times (or until you reach the root cause) to peel back layers of symptoms and find the fundamental issue.

**Example:**
```
Problem: Schedule generation failed
Why? → API returned 500 error
Why? → Database query timed out
Why? → Query took 45 seconds to complete
Why? → Table was missing indexes
Why? → Migration wasn't applied during deployment
ROOT CAUSE: Deployment process doesn't verify migrations
```

### Important Rules

1. **Ask why about the problem, not blame**
   - ❌ "Why did the developer forget?"
   - ✅ "Why wasn't the missing migration caught?"

2. **Base answers on facts, not speculation**
   - ❌ "Probably because..."
   - ✅ "Logs show that..."

3. **Stop when you reach a root cause**
   - Sometimes it takes 3 whys, sometimes 7
   - Root cause is actionable and under your control

4. **Verify each answer**
   - Check logs, code, metrics
   - Don't assume

## Workflow Phases

### Phase 1: Problem Statement Definition

Start with a clear, specific problem statement.

#### Problem Statement Template

```markdown
## Problem Statement

**What**: [Specific observable behavior]
**When**: [Timestamp or conditions]
**Where**: [System component]
**Impact**: [Who/what was affected]

**Example**:
- **What**: Schedule generation API endpoint returns 500 errors
- **When**: 2025-12-26 14:30-14:45 UTC
- **Where**: POST /api/schedule/generate
- **Impact**: All users unable to generate schedules (15-minute outage)
```

#### Criteria for Good Problem Statement

- [ ] Observable (can be seen in logs/metrics)
- [ ] Specific (not vague like "system is slow")
- [ ] Measurable (has clear success/failure state)
- [ ] Time-bounded (occurred at specific time)
- [ ] Scoped (specific component identified)

### Phase 2: Iterative "Why" Questioning

Ask why the problem occurred, then why that happened, and so on.

#### Question Framework

For each why, use this framework:

```markdown
### Why #[N]: [Previous answer/problem]

**Question**: Why did [previous answer] happen?

**Evidence**:
- [Log entries]
- [Metrics]
- [Code references]
- [Configuration]

**Answer**: [Fact-based explanation]

**Verification**: [How we confirmed this answer]
```

#### Example: Complete 5-Whys

```markdown
## 5-Whys Analysis: Schedule Generation 500 Errors

### Problem Statement
Schedule generation API returns 500 errors for all requests
on 2025-12-26 from 14:30-14:45 UTC.

---

### Why #1: Why did the API return 500 errors?

**Evidence**:
```bash
$ docker-compose logs backend | grep "500"
2025-12-26 14:30:15 ERROR [uvicorn] "POST /api/schedule/generate HTTP/1.1" 500
2025-12-26 14:30:16 ERROR [uvicorn] "POST /api/schedule/generate HTTP/1.1" 500
```

**Answer**: Database operations failed with timeout errors

**Verification**: Backend error logs show SQLAlchemy timeout exceptions
```python
sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 5 reached
```

---

### Why #2: Why did database operations timeout?

**Evidence**:
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;
-- Result: 15/20 connections active

-- Check long-running queries
SELECT pid, now() - query_start as duration, state, query
FROM pg_stat_activity
WHERE state != 'idle' AND now() - query_start > interval '5 seconds';
-- Result: 8 queries running > 30 seconds
```

**Answer**: Connection pool was exhausted by long-running queries

**Verification**: PostgreSQL showed 15/20 connections in use, with 8 queries
running for >30 seconds, blocking new connections.

---

### Why #3: Why were queries running for >30 seconds?

**Evidence**:
```sql
-- Explain analyze on slow query
EXPLAIN ANALYZE
SELECT * FROM assignments
WHERE person_id = 'resident-001'
  AND date >= '2025-01-01'
  AND date <= '2025-12-31';

-- Result:
Seq Scan on assignments  (cost=0.00..2847.00 rows=500 width=200) (actual time=28345.234..28567.123 rows=365 loops=1)
  Filter: (person_id = 'resident-001' AND date >= '2025-01-01' AND date <= '2025-12-31')
Planning Time: 0.234 ms
Execution Time: 28567.456 ms
```

**Answer**: Queries were doing sequential scans instead of using indexes

**Verification**: EXPLAIN ANALYZE shows "Seq Scan" with ~28 second execution time.
Expected: Index scan with <100ms execution.

---

### Why #4: Why were queries doing sequential scans?

**Evidence**:
```sql
-- Check for indexes on assignments table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'assignments';

-- Result:
indexname          | indexdef
assignments_pkey   | CREATE UNIQUE INDEX assignments_pkey ON assignments USING btree (id)

-- Expected but missing:
-- assignments_person_id_idx
-- assignments_date_idx
```

**Answer**: Required indexes on person_id and date columns were missing

**Verification**: pg_indexes shows only primary key index exists.
Application expects indexes on person_id and date columns for efficient filtering.

---

### Why #5: Why were indexes missing?

**Evidence**:
```bash
# Check Alembic migrations
$ ls backend/alembic/versions/ | grep -i index
20251220_add_assignments_indexes.py  ← Migration exists!

# Check migration status
$ docker-compose exec backend alembic current
INFO  [alembic] Running current
20251215_initial_schema (head)

# Head should be:
# 20251220_add_assignments_indexes
```

**Answer**: The migration to add indexes existed but was not applied

**Verification**: Migration file exists in versions/ but `alembic current`
shows older migration as head.

---

### ROOT CAUSE: Why wasn't the migration applied?

**Evidence**:
```bash
# Check deployment script
$ cat scripts/deploy.sh
#!/bin/bash
git pull origin main
docker-compose build
docker-compose up -d
# ← Missing: alembic upgrade head

# Check CI/CD pipeline
$ cat .github/workflows/deploy.yml
# ← No migration verification step
```

**Answer**: Deployment process doesn't include migration application or verification

**Verification**: Deployment scripts and CI/CD pipeline lack migration steps.
Developer applied migration locally but it wasn't part of automated deployment.

---

## Root Cause Summary

**ROOT CAUSE**: Deployment process doesn't verify or apply database migrations

**Causal Chain**:
1. Deployment process lacks migration verification
2. → Migration to add indexes wasn't applied
3. → Indexes on assignments table were missing
4. → Queries performed sequential scans
5. → Queries took 28+ seconds
6. → Connection pool exhausted
7. → API returned 500 errors
```

### Phase 3: Evidence Gathering

For each "why", gather concrete evidence.

#### Types of Evidence

| Evidence Type | Where to Find | Example |
|---------------|---------------|---------|
| **Logs** | Docker logs, file logs | Error messages, stack traces |
| **Metrics** | Prometheus, database | Query duration, connection count |
| **Code** | Git repository | Function implementation, config |
| **Database** | SQL queries | Table structure, query plans |
| **System** | Docker stats, top | CPU, memory, disk usage |
| **Configuration** | .env, config files | Settings, environment variables |
| **Git history** | git log | Recent changes |

#### Evidence Collection Commands

**Logs**
```bash
# Backend errors in last hour
docker-compose logs backend --since 1h | grep ERROR

# MCP tool calls
docker-compose logs mcp-server | grep "tool_call\|tool_result"

# Database errors
docker-compose logs db | grep -i "error\|fatal"
```

**Metrics**
```bash
# Database connections
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT count(*) as active, max_conn
FROM pg_stat_activity psa
JOIN (SELECT setting::int as max_conn FROM pg_settings WHERE name = 'max_connections') mc ON true
GROUP BY max_conn;"

# Query performance
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;"
```

**Code**
```bash
# Recent changes to relevant files
git log -10 --oneline -- backend/app/api/routes/schedule.py

# Diff of recent change
git diff HEAD~1 backend/app/api/routes/schedule.py
```

**Configuration**
```bash
# Check environment variables
docker-compose exec backend env | grep -i database

# Check migration status
docker-compose exec backend alembic current
docker-compose exec backend alembic heads
```

### Phase 4: Root Cause Identification

Identify when you've reached the root cause.

#### Root Cause Checklist

A true root cause is:

- [ ] **Actionable**: Can be fixed with specific action
- [ ] **Under control**: Within team's ability to change
- [ ] **Preventable**: Fix will prevent recurrence
- [ ] **Specific**: Not vague (e.g., "human error")
- [ ] **Verifiable**: Can confirm it caused the issue

#### Common False Roots

❌ **"Human error"** - Too vague
✅ **"Deployment checklist missing migration verification step"** - Specific and actionable

❌ **"System was overloaded"** - Symptom, not cause
✅ **"Auto-scaling not configured for schedule generation workload"** - Specific

❌ **"Database was slow"** - Symptom
✅ **"Missing index on assignments.person_id causing sequential scans"** - Specific

### Phase 5: Contributing Factors

Identify what made the problem worse or easier to happen.

```markdown
## Contributing Factors

Beyond the root cause, what else contributed?

1. **Lack of Monitoring**
   - No alert on connection pool usage
   - No slow query detection
   - Delay in problem detection

2. **Missing Tests**
   - No performance tests for schedule generation
   - No load testing before deployment
   - Missing index not caught in testing

3. **Documentation Gap**
   - Deployment runbook incomplete
   - Database index strategy not documented
   - New developers not aware of migration process

4. **Process Gap**
   - No code review checklist for migrations
   - No staging environment to catch issues
   - No rollback plan documented
```

## Examples from Scheduling System

### Example 1: MCP Tool Timeout

```markdown
## Problem: MCP validate_schedule tool times out

### Why #1: Why does the tool timeout?
**Evidence**: MCP logs show timeout after 30s
**Answer**: Backend API call takes >30 seconds
**Verification**: `docker-compose logs mcp-server | grep timeout`

### Why #2: Why does the API call take >30 seconds?
**Evidence**: Backend logs show ACGME validation taking 28s
**Answer**: ACGME validator processes all 365 days serially
**Verification**: Code review of `backend/app/scheduling/acgme_validator.py`

### Why #3: Why does validation process days serially?
**Evidence**: Code shows `for day in range(365): validate_day(day)`
**Answer**: Original implementation didn't optimize for bulk validation
**Verification**: Git history shows it was optimized for single-day checks

### Why #4: Why wasn't bulk validation implemented?
**Evidence**: Original PR comments
**Answer**: MVP focused on correctness, not performance
**Verification**: PR #123 comments: "Optimization deferred to v2"

### ROOT CAUSE: ACGME validator not optimized for full-year validation

**Contributing Factors**:
- No performance requirements defined
- No load testing
- Technical debt not prioritized
```

### Example 2: Schedule Generation Infeasible

```markdown
## Problem: Solver returns INFEASIBLE status

### Why #1: Why is the schedule infeasible?
**Evidence**: Solver logs show "No solution found"
**Answer**: Constraints are conflicting
**Verification**: Solver diagnostic output

### Why #2: Why are constraints conflicting?
**Evidence**: Constraint analysis shows:
- Max hours: 80/week
- Min coverage: 24/7
- Available residents: 3
**Answer**: Not enough residents to cover 24/7 with 80-hour limit
**Verification**: Math: 168 hours/week ÷ 3 residents = 56 hours each (feasible)
But constraint also requires 2 residents on call simultaneously = 112 hours/week needed
112 hours × 3 residents = 336 hours available, but need 336 hours for dual coverage

### Why #3: Why is dual coverage required?
**Evidence**: Constraint definition in `constraints/supervision.py`
**Answer**: ACGME supervision rules require 2:1 ratio for PGY-1
**Verification**: `constraints/supervision.py` line 45

### Why #4: Why are all residents PGY-1?
**Evidence**: Database query shows person records
**Answer**: Incorrect seed data for test environment
**Verification**: `SELECT count(*) FROM persons WHERE year = 'PGY-1'` = 3 (all)

### ROOT CAUSE: Test environment seed data has unrealistic resident mix

**Contributing Factors**:
- Seed data not validated against real-world ratios
- No data quality checks
- Test data not representative of production
```

### Example 3: Celery Task Failure

```markdown
## Problem: Scheduled resilience health check fails

### Why #1: Why does the health check task fail?
**Evidence**: Celery logs show exception
**Answer**: Task raises `KeyError: 'defense_level'`
**Verification**: Stack trace in worker logs

### Why #2: Why is 'defense_level' missing?
**Evidence**: Code expects API response: `data['defense_level']`
**Answer**: API endpoint changed response format
**Verification**: API now returns `data['resilience']['defense_level']`

### Why #3: Why did API format change without updating Celery task?
**Evidence**: Git log shows API change in PR #456
**Answer**: PR changed API but didn't update Celery consumer
**Verification**: PR #456 only modified backend/app/api/ not backend/app/tasks/

### Why #4: Why wasn't the Celery task updated in the same PR?
**Evidence**: PR review comments
**Answer**: Developer wasn't aware Celery task consumed this endpoint
**Verification**: No dependency documentation linking API to Celery tasks

### ROOT CAUSE: API and consumer code not co-located; no dependency tracking

**Contributing Factors**:
- No API versioning
- No integration tests for Celery tasks
- No documentation of API consumers
```

## Root Cause Analysis Template

Use this template for systematic analysis:

```markdown
# Root Cause Analysis: [Problem Title]

**Date**: [YYYY-MM-DD]
**Analyst**: [Name/Agent]
**Incident ID**: [if applicable]

## Problem Statement

**What**: [Observable problem]
**When**: [Timestamp/conditions]
**Where**: [Component]
**Impact**: [Who/what affected]

## 5-Whys Analysis

### Why #1: [Problem statement]

**Evidence**:
- [Log/metric/code reference]

**Answer**: [Fact-based explanation]

**Verification**: [How confirmed]

---

### Why #2: [Previous answer]

**Evidence**:
- [Log/metric/code reference]

**Answer**: [Fact-based explanation]

**Verification**: [How confirmed]

---

### Why #3: [Previous answer]

**Evidence**:
- [Log/metric/code reference]

**Answer**: [Fact-based explanation]

**Verification**: [How confirmed]

---

### Why #4: [Previous answer]

**Evidence**:
- [Log/metric/code reference]

**Answer**: [Fact-based explanation]

**Verification**: [How confirmed]

---

### Why #5: [Previous answer]

**Evidence**:
- [Log/metric/code reference]

**Answer**: [Fact-based explanation]

**Verification**: [How confirmed]

---

## Root Cause Summary

**ROOT CAUSE**: [Clear, specific, actionable statement]

**Causal Chain**:
1. [Root cause]
2. → [Next effect]
3. → [Next effect]
4. → [Final symptom]

## Contributing Factors

1. **[Factor category]**: [Description]
2. **[Factor category]**: [Description]

## Verification

- [ ] Root cause is actionable
- [ ] Root cause is under our control
- [ ] Fixing root cause will prevent recurrence
- [ ] Evidence supports each "why"
- [ ] Contributing factors identified

## Recommended Actions

### Immediate Fix
- [What to do right now]

### Root Cause Fix
- [What to change to prevent recurrence]

### Contributing Factor Mitigation
- [Address monitoring gaps]
- [Address testing gaps]
- [Address documentation gaps]

## References

- Logs: [file paths]
- Code: [git commits]
- Related incidents: [IDs]
```

## Common Pitfalls to Avoid

### 1. Stopping Too Soon

❌ **Premature stop**:
```
Problem: Schedule generation failed
Why? → Database was down
Fix: Restart database
```

✅ **Continue to root cause**:
```
Why was database down? → Out of memory
Why out of memory? → Connection leak
Why connection leak? → Connections not closed after errors
Why not closed? → Missing finally block in error handling
ROOT CAUSE: Error handling doesn't ensure connection cleanup
```

### 2. Blaming People

❌ **Blame-focused**:
```
Why? → Developer forgot to add migration
Why? → Developer was careless
```

✅ **Process-focused**:
```
Why? → Migration not in deployment
Why? → No deployment checklist
ROOT CAUSE: Deployment process lacks verification steps
```

### 3. Accepting Vague Answers

❌ **Vague**:
```
Why? → System was overloaded
Why? → Too much traffic
```

✅ **Specific**:
```
Why? → CPU at 100% on scheduler worker
Why? → Constraint solving taking 45 minutes per schedule
Why? → Algorithm complexity O(n!) for n=30 variables
ROOT CAUSE: Brute-force algorithm doesn't scale to problem size
```

## Integration with Other Workflows

### With incident-review.md
Root cause analysis is Phase 4 of incident review.
Use this workflow to complete the "Root Cause Analysis" section.

### With log-analysis.md
Use log analysis to gather evidence for each "why".

### With debugging-checklist.md
Use checklist to systematically gather evidence.

## References

- `incident-review.md` - Complete post-mortem template
- `log-analysis.md` - Evidence gathering from logs
- `../Reference/common-failure-patterns.md` - Known root causes
- [5 Whys Technique (Wikipedia)](https://en.wikipedia.org/wiki/Five_whys)
