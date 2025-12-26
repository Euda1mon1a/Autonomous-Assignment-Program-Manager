***REMOVED*** Incident Review Workflow

Post-mortem template for systematic incident analysis. Use after resolving any significant failure or when conducting a retrospective.

***REMOVED******REMOVED*** Purpose

Convert failures into learning opportunities by:
1. Documenting what happened
2. Understanding why it happened
3. Preventing it from happening again
4. Improving system resilience

***REMOVED******REMOVED*** When to Use

- After resolving a production incident
- When debugging reveals systemic issues
- For scheduled system health reviews
- When multiple related failures occur

***REMOVED******REMOVED*** Workflow Phases

***REMOVED******REMOVED******REMOVED*** Phase 1: Incident Identification

***REMOVED******REMOVED******REMOVED******REMOVED*** Basic Information
```markdown
***REMOVED******REMOVED*** Incident ID: INC-[YYYYMMDD]-[NNN]

**Date/Time**: [UTC timestamp]
**Duration**: [time from detection to resolution]
**Severity**: [CRITICAL|HIGH|MEDIUM|LOW]
**Affected Systems**: [list components]
**Reported By**: [agent/user/monitoring]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Severity Classification

| Level | Definition | Example |
|-------|------------|---------|
| **CRITICAL** | System down, data loss risk, compliance violation | Database corruption, all schedules deleted |
| **HIGH** | Major functionality impaired, workaround exists | Schedule generation fails, manual fixes possible |
| **MEDIUM** | Degraded performance, user impact manageable | Slow queries, some MCP tools timeout |
| **LOW** | Minor issues, limited impact | Logging errors, cosmetic UI bugs |

***REMOVED******REMOVED******REMOVED*** Phase 2: Timeline Reconstruction

Document events in chronological order. Be precise with timestamps.

***REMOVED******REMOVED******REMOVED******REMOVED*** Timeline Template
```markdown
***REMOVED******REMOVED******REMOVED*** Timeline

| Time (UTC) | Event | Component | Evidence |
|------------|-------|-----------|----------|
| 14:30:15 | First error logged | Backend API | `logs/backend.log:1234` |
| 14:30:42 | MCP tool timeout | MCP Server | `docker-compose logs mcp-server` |
| 14:31:05 | Database deadlock | PostgreSQL | `pg_stat_activity` query |
| 14:32:00 | Detection by monitoring | Prometheus | Alert fired |
| 14:33:30 | Investigation started | Human/Agent | - |
| 14:38:15 | Root cause identified | - | Database lock contention |
| 14:42:00 | Fix implemented | Backend | Commit `abc123` |
| 14:45:30 | Service restored | All | Health checks green |
| 15:00:00 | Monitoring confirmed stable | Prometheus | No new errors |
```

***REMOVED******REMOVED******REMOVED******REMOVED*** How to Gather Timeline Data

**1. Check Git History**
```bash
git log --since="2025-12-26 14:00" --until="2025-12-26 15:00" --oneline
```

**2. Extract Log Timestamps**
```bash
***REMOVED*** Backend logs
docker-compose logs backend --since 2025-12-26T14:00:00 --until 2025-12-26T15:00:00

***REMOVED*** Database logs
docker-compose logs db | grep "2025-12-26 14:"

***REMOVED*** MCP server logs
docker-compose logs mcp-server | grep "ERROR\|WARN" | tail -50
```

**3. Check Database Activity**
```sql
-- Recent queries (if logging enabled)
SELECT query_start, usename, state, query
FROM pg_stat_activity
WHERE query_start >= '2025-12-26 14:00:00'
ORDER BY query_start;
```

**4. Review Monitoring/Alerts**
```bash
***REMOVED*** Check Prometheus alerts (if configured)
curl http://localhost:9090/api/v1/alerts

***REMOVED*** Check application metrics
curl http://localhost:8000/metrics
```

***REMOVED******REMOVED******REMOVED*** Phase 3: Impact Assessment

***REMOVED******REMOVED******REMOVED******REMOVED*** User Impact
```markdown
***REMOVED******REMOVED******REMOVED*** User Impact

**Users Affected**: [number or "all" or "none"]
- Faculty: [number affected / total]
- Residents: [number affected / total]
- Coordinators: [number affected / total]

**Operations Affected**:
- [ ] Schedule viewing
- [ ] Schedule generation
- [ ] Swap requests
- [ ] Leave requests
- [ ] ACGME compliance checking
- [ ] Reporting

**Workaround Available**: [YES/NO]
- If yes: [describe workaround]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Data Integrity
```markdown
***REMOVED******REMOVED******REMOVED*** Data Integrity Assessment

**Database State**: [INTACT|INCONSISTENT|CORRUPTED]

**Checks Performed**:
```sql
-- Example: Check for orphaned assignments
SELECT COUNT(*) FROM assignments a
LEFT JOIN persons p ON a.person_id = p.id
WHERE p.id IS NULL;

-- Check for overlapping assignments
SELECT person_id, date, COUNT(*) as overlap_count
FROM assignments
GROUP BY person_id, date
HAVING COUNT(*) > 1;

-- Verify ACGME compliance
-- (run validation queries from app/scheduling/acgme_validator.py)
```

**Findings**:
- [ ] No data corruption detected
- [ ] Inconsistencies found: [describe]
- [ ] Corruption detected: [describe]

**Remediation Required**: [YES/NO]
- If yes: [describe recovery plan]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Compliance Impact
```markdown
***REMOVED******REMOVED******REMOVED*** ACGME Compliance Impact

**Compliance Status**: [MAINTAINED|AT RISK|VIOLATED]

**Checks**:
- [ ] 80-hour work week limit maintained
- [ ] 1-in-7 days off maintained
- [ ] Supervision ratios maintained
- [ ] All residents have valid assignments

**Violations Detected**: [list or "none"]

**Corrective Actions**: [if violations occurred]
```

***REMOVED******REMOVED******REMOVED*** Phase 4: Root Cause Analysis

Use the 5-whys methodology (see `root-cause-analysis.md` for details).

***REMOVED******REMOVED******REMOVED******REMOVED*** Problem Statement
```markdown
***REMOVED******REMOVED******REMOVED*** Problem Statement

**Observed Symptom**: [what users/system experienced]

**Example**:
Schedule generation API endpoint returned 500 error for all requests
from 14:30-14:45 UTC on 2025-12-26.
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 5-Whys Investigation
```markdown
***REMOVED******REMOVED******REMOVED*** Root Cause Analysis (5-Whys)

**1. Why did the API return 500 errors?**
→ Because the database connection pool was exhausted

**2. Why was the connection pool exhausted?**
→ Because multiple long-running queries held connections open

**3. Why were queries long-running?**
→ Because they were missing indexes on the assignments table

**4. Why were indexes missing?**
→ Because the migration to add them was created but not applied

**5. Why wasn't the migration applied?**
→ Because deployment process doesn't verify migration status

**ROOT CAUSE**: Missing deployment verification step to ensure
all migrations are applied before starting the application.
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Contributing Factors
```markdown
***REMOVED******REMOVED******REMOVED*** Contributing Factors

Beyond the root cause, what made this worse or easier to happen?

- **Lack of monitoring**: No alerts on connection pool usage
- **Missing documentation**: Index creation not in deployment checklist
- **Test coverage gap**: Performance tests don't catch missing indexes
- **Human error**: Developer forgot to run migrations locally
```

***REMOVED******REMOVED******REMOVED*** Phase 5: Resolution Documentation

***REMOVED******REMOVED******REMOVED******REMOVED*** Fix Applied
```markdown
***REMOVED******REMOVED******REMOVED*** Fix Applied

**Type**: [CODE|CONFIG|DATABASE|INFRASTRUCTURE]

**Changes Made**:
1. Applied missing migration: `alembic upgrade head`
2. Added indexes to assignments table (person_id, date)
3. Restarted backend services to clear connection pool

**Git Commits**:
- `abc123f` - fix: add missing indexes to assignments table
- `def456a` - chore: update deployment checklist

**Deployment Steps**:
```bash
***REMOVED*** Steps taken to apply fix
cd backend
alembic upgrade head
docker-compose restart backend
```

**Verification**:
- [ ] All tests pass: `pytest`
- [ ] Query performance improved (measure with EXPLAIN ANALYZE)
- [ ] Connection pool no longer exhausting
- [ ] No new errors in logs
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Immediate Actions
```markdown
***REMOVED******REMOVED******REMOVED*** Immediate Actions Taken

| Action | Owner | Status | Completion Time |
|--------|-------|--------|-----------------|
| Apply migration | Agent | ✓ Complete | 14:42 UTC |
| Restart services | Agent | ✓ Complete | 14:43 UTC |
| Verify fix | Agent | ✓ Complete | 14:45 UTC |
| Monitor for 30 min | Agent | ✓ Complete | 15:15 UTC |
| Notify users | Human | ✓ Complete | 15:00 UTC |
```

***REMOVED******REMOVED******REMOVED*** Phase 6: Prevention Measures

***REMOVED******REMOVED******REMOVED******REMOVED*** Short-term (< 1 week)
```markdown
***REMOVED******REMOVED******REMOVED*** Short-term Prevention (Tactical)

- [ ] Add deployment verification step
  - Script to check migration status
  - Fail fast if migrations pending
  - Owner: [assign]
  - Due: [date]

- [ ] Add monitoring alert
  - Alert when connection pool > 80% used
  - Alert when query duration > 5 seconds
  - Owner: [assign]
  - Due: [date]

- [ ] Update documentation
  - Add to deployment runbook
  - Document index strategy
  - Owner: [assign]
  - Due: [date]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Long-term (> 1 week)
```markdown
***REMOVED******REMOVED******REMOVED*** Long-term Prevention (Strategic)

- [ ] Implement automated migration checking in CI/CD
  - Verify all migrations applied in staging
  - Block deployment if migrations pending
  - Owner: [assign]
  - Due: [date]

- [ ] Add performance testing
  - Load tests for schedule generation
  - Database query performance benchmarks
  - Owner: [assign]
  - Due: [date]

- [ ] Review and optimize database schema
  - Audit all tables for missing indexes
  - Add EXPLAIN ANALYZE to slow query log
  - Owner: [assign]
  - Due: [date]

- [ ] Improve observability
  - Add distributed tracing
  - Add connection pool metrics to dashboard
  - Owner: [assign]
  - Due: [date]
```

***REMOVED******REMOVED******REMOVED*** Phase 7: Lessons Learned

***REMOVED******REMOVED******REMOVED******REMOVED*** What Went Well
```markdown
***REMOVED******REMOVED******REMOVED*** What Went Well

- Detection was quick (< 2 minutes from first error)
- Root cause identified in 8 minutes
- Fix was straightforward once identified
- No data corruption occurred
- ACGME compliance maintained
```

***REMOVED******REMOVED******REMOVED******REMOVED*** What Could Be Improved
```markdown
***REMOVED******REMOVED******REMOVED*** What Could Be Improved

- Should have caught missing migration in code review
- Performance testing would have detected this before production
- Monitoring should have alerted earlier (before pool exhausted)
- Documentation of index strategy was lacking
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Knowledge Gained
```markdown
***REMOVED******REMOVED******REMOVED*** Knowledge Gained

- Connection pool exhaustion causes 500 errors (not timeouts)
- Missing indexes on assignments table severely impact performance
- Need better visibility into database performance metrics
- Deployment process has gaps in verification
```

***REMOVED******REMOVED******REMOVED*** Phase 8: Action Items

***REMOVED******REMOVED******REMOVED******REMOVED*** Action Item Template
```markdown
***REMOVED******REMOVED******REMOVED*** Action Items

| ID | Action | Type | Priority | Owner | Due Date | Status |
|----|--------|------|----------|-------|----------|--------|
| AI-001 | Add migration check to CI | Automation | HIGH | Agent | 2025-12-30 | Open |
| AI-002 | Create connection pool alert | Monitoring | HIGH | Agent | 2025-12-28 | Open |
| AI-003 | Update deployment docs | Documentation | MEDIUM | Agent | 2025-12-29 | Open |
| AI-004 | Audit schema for indexes | Database | MEDIUM | Human | 2026-01-05 | Open |
| AI-005 | Add performance tests | Testing | LOW | Agent | 2026-01-10 | Open |
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Tracking
```bash
***REMOVED*** Create GitHub issues for action items
gh issue create \
  --title "[Post-Incident] Add migration check to CI" \
  --body "From incident INC-20251226-001. See incident report for details." \
  --label "incident-response,high-priority"
```

***REMOVED******REMOVED*** Example Complete Incident Review

See the example below for a real incident from the scheduling system:

```markdown
***REMOVED******REMOVED*** Incident ID: INC-20251226-001

**Date/Time**: 2025-12-26 14:30 UTC
**Duration**: 15 minutes (detection to resolution)
**Severity**: HIGH
**Affected Systems**: Backend API, Schedule Generation
**Reported By**: Automated monitoring

***REMOVED******REMOVED******REMOVED*** Summary
Schedule generation API endpoint returned 500 errors due to database
connection pool exhaustion caused by missing indexes on assignments table.

***REMOVED******REMOVED******REMOVED*** Timeline

| Time (UTC) | Event | Component | Evidence |
|------------|-------|-----------|----------|
| 14:30:15 | First 500 error | Backend API | `logs/backend.log:1234` |
| 14:30:42 | Connection pool exhausted | PostgreSQL | Max connections reached |
| 14:32:00 | Alert fired | Prometheus | HTTP 500 rate > threshold |
| 14:33:30 | Investigation started | Agent | Skill activated |
| 14:38:15 | Root cause identified | - | Missing indexes + pending migration |
| 14:42:00 | Migration applied | Backend | `alembic upgrade head` |
| 14:43:00 | Services restarted | Docker | `docker-compose restart backend` |
| 14:45:30 | Service restored | All | Health checks green |

***REMOVED******REMOVED******REMOVED*** Impact Assessment

**Users Affected**: All (complete service outage for schedule generation)
**Data Integrity**: INTACT - no corruption detected
**ACGME Compliance**: MAINTAINED - existing schedules unaffected

***REMOVED******REMOVED******REMOVED*** Root Cause

Missing indexes on assignments table caused slow queries, which exhausted
the database connection pool. The migration to add indexes existed but
was not applied due to missing deployment verification.

***REMOVED******REMOVED******REMOVED*** Resolution

1. Applied pending migration: `20251220_add_assignments_indexes.py`
2. Restarted backend to clear connection pool
3. Verified query performance improved (300ms → 15ms)

***REMOVED******REMOVED******REMOVED*** Prevention Measures

**Short-term**:
- Add migration verification to deployment script
- Add connection pool monitoring alert

**Long-term**:
- Implement automated migration checks in CI/CD
- Add database performance testing to test suite

***REMOVED******REMOVED******REMOVED*** Lessons Learned

- Need better deployment verification
- Missing indexes have severe performance impact
- Connection pool exhaustion manifests as 500 errors
```

***REMOVED******REMOVED*** Templates and Checklists

***REMOVED******REMOVED******REMOVED*** Quick Incident Report (for minor issues)
```markdown
***REMOVED******REMOVED*** Quick Incident Report

**Issue**: [one-sentence description]
**Time**: [timestamp]
**Root Cause**: [brief explanation]
**Fix**: [what was done]
**Prevention**: [one action item]
```

***REMOVED******REMOVED******REMOVED*** Investigation Checklist
- [ ] Timeline reconstructed with evidence
- [ ] Impact assessed (users, data, compliance)
- [ ] Root cause identified using 5-whys
- [ ] Fix verified and tested
- [ ] Prevention measures defined
- [ ] Action items created and assigned
- [ ] Documentation updated
- [ ] Team notified

***REMOVED******REMOVED*** References

- `root-cause-analysis.md` - Detailed 5-whys methodology
- `log-analysis.md` - Log parsing and correlation techniques
- `../Reference/debugging-checklist.md` - System health check steps
- `/docs/development/DEBUGGING_WORKFLOW.md` - Overall debugging process
