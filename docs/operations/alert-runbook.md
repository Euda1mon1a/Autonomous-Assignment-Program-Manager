
# Alert Runbook

Comprehensive guide for responding to alerts and incidents.

## Overview

This runbook provides step-by-step procedures for responding to all automated alerts from the Residency Scheduler monitoring system.

## Alert Severity Levels

| Severity | Response Time | Escalation | Examples |
|----------|--------------|------------|----------|
| **Critical** | Immediate (24/7) | PagerDuty + Email | System down, ACGME violations, security breach |
| **Warning** | Within 1 hour (business hours) | Slack + Email | High latency, low cache hit rate |
| **Info** | Best effort | Slack | Deployment notifications, config changes |

## System Alerts

### HighErrorRate

**Alert**: Error rate exceeds 5% of requests

**Severity**: Critical

**Investigation**:
1. Check error logs: `python scripts/logs/log_parser.py app.log --level ERROR --search "last 1 hour"`
2. Review error types: `python scripts/logs/error_aggregator.py app.log`
3. Check Grafana dashboard for affected endpoints
4. Review recent deployments

**Resolution**:
1. Identify error pattern (authentication, database, validation)
2. Roll back recent deployment if correlation found
3. Apply hotfix if specific bug identified
4. Monitor error rate for 15 minutes after fix

**Escalation**: If error rate doesn't decrease within 30 minutes, escalate to on-call engineer

---

### SlowResponseTime

**Alert**: 95th percentile response time exceeds 2 seconds

**Severity**: Warning

**Investigation**:
1. Check slow query log: Review database performance metrics
2. Identify slow endpoints in Grafana
3. Check cache hit rate
4. Review system resources (CPU, memory)

**Resolution**:
1. Optimize slow database queries
2. Add/fix caching for frequently accessed data
3. Scale horizontally if resource-bound
4. Review and optimize slow code paths

---

### DatabaseConnectionPoolExhaustion

**Alert**: Database connection pool usage exceeds 90%

**Severity**: Critical

**Investigation**:
1. Check active connections: `SELECT count(*) FROM pg_stat_activity;`
2. Identify long-running queries
3. Review connection pool settings
4. Check for connection leaks

**Resolution**:
1. Kill long-running queries if safe
2. Increase connection pool size (short-term)
3. Fix connection leaks in code (long-term)
4. Implement connection timeout policies

---

### HighCPUUsage / LowMemory

**Alert**: CPU usage > 80% or Available memory < 10%

**Severity**: Warning → Critical

**Investigation**:
1. Check process list: `top` or `htop`
2. Review memory usage by process
3. Check for memory leaks
4. Analyze recent traffic patterns

**Resolution**:
1. Restart application if memory leak suspected
2. Scale horizontally (add instances)
3. Optimize resource-intensive operations
4. Review and fix memory leaks

## Compliance Alerts

### ACGMEViolationDetected

**Alert**: ACGME violation detected

**Severity**: Critical

**Response Time**: Immediate

**Investigation**:
1. Identify violation type (80-hour, 1-in-7, supervision)
2. Check affected resident/faculty
3. Review schedule that caused violation
4. Determine if violation is historical or future

**Resolution**:
1. **Immediate**: Notify Program Director
2. **If future violation**: Modify schedule to prevent violation
3. **If historical violation**: Document and prepare justification
4. Log override with justification if unavoidable

**Documentation Required**:
- Violation details
- Affected person
- Justification (if override)
- Corrective action taken
- Program Director notification

**Notification Template**:
```
Subject: URGENT: ACGME Violation Detected

Dear Dr. [Program Director],

An ACGME violation has been detected:

- Rule: [80-hour / 1-in-7 / supervision]
- Affected: [Resident Name / ID]
- Details: [Violation details]
- Status: [Historical / Future]
- Action Taken: [Description]

Requires immediate review.

[Your Name]
[Timestamp]
```

---

### RepeatedACGMEViolations

**Alert**: Multiple ACGME violations for same person

**Severity**: Critical

**Investigation**:
1. Pull full compliance history for person
2. Identify pattern in violations
3. Review scheduling practices
4. Check for system bugs causing violations

**Resolution**:
1. Meet with affected resident/faculty
2. Review workload distribution
3. Implement stricter scheduling constraints
4. Report to Program Director and ACGME liaison

---

### WorkHourThresholdApproaching

**Alert**: Resident approaching 80-hour threshold

**Severity**: Warning

**Investigation**:
1. Calculate exact hours for current week
2. Check scheduled future shifts
3. Review upcoming rotation

**Resolution**:
1. Remove non-essential shifts if possible
2. Find coverage for upcoming shifts
3. Alert resident and supervisor
4. Document proactive measure

## Security Alerts

### FailedAuthenticationSpike

**Alert**: Spike in failed authentication attempts

**Severity**: Critical

**Investigation**:
1. Check source IPs: `grep "auth_failure" app.log | grep -oP 'ip=\K[^"]+' | sort | uniq -c`
2. Identify targeted accounts
3. Review time pattern
4. Check for credential stuffing pattern

**Resolution**:
1. **Immediate**: Block suspicious IPs
2. Enable rate limiting on auth endpoints
3. Force password reset for targeted accounts
4. Enable MFA for affected users
5. Notify security team

**Indicators of Attack**:
- Same IP trying multiple accounts
- Distributed IPs trying same account
- Timing pattern (automated attempts)

---

### SuspiciousActivityDetected

**Alert**: Suspicious activity event logged

**Severity**: Critical

**Investigation**:
1. Review suspicious activity details
2. Check user's recent activity history
3. Verify user identity (contact if needed)
4. Review data access patterns

**Resolution**:
1. **If confirmed malicious**: Lock account immediately
2. **If uncertain**: Monitor and flag for review
3. Document incident details
4. Escalate to security team
5. Initiate incident response if data breach suspected

---

### LargeDataExport

**Alert**: Large data export detected (>1000 records)

**Severity**: Warning

**Investigation**:
1. Identify user and export details
2. Verify user has legitimate need
3. Check for sensitive data in export
4. Review export frequency

**Resolution**:
1. Contact user to verify legitimacy
2. If unauthorized: Block export and investigate
3. If authorized: Document justification
4. Review and tighten export permissions if needed

## Performance Alerts

### SlowDatabaseQueries

**Alert**: Database queries exceeding 1 second

**Severity**: Warning

**Investigation**:
1. Identify slow queries: Check PostgreSQL slow query log
2. Review query execution plans
3. Check index usage
4. Analyze query patterns

**Resolution**:
1. Add missing indexes
2. Optimize query structure
3. Implement query caching
4. Consider query result pagination

---

### LowCacheHitRate

**Alert**: Cache hit rate below 70%

**Severity**: Warning

**Investigation**:
1. Check cache configuration
2. Review cached data TTLs
3. Analyze cache key patterns
4. Check Redis memory usage

**Resolution**:
1. Adjust cache TTLs
2. Add caching for frequently accessed data
3. Review cache invalidation strategy
4. Increase Redis memory if needed

## General Incident Response

### 1. Acknowledge Alert

- Acknowledge in PagerDuty/Slack
- Note start time

### 2. Assess Severity

- Determine user impact
- Check if degraded or down
- Estimate affected users

### 3. Communicate

**For Critical Issues**:
- Post in #incidents Slack channel
- Update status page
- Notify stakeholders

### 4. Investigate

- Follow alert-specific runbook
- Check logs, metrics, traces
- Identify root cause

### 5. Resolve

- Apply fix
- Verify resolution
- Monitor for recurrence

### 6. Document

- Update incident log
- Create post-mortem (for critical)
- File bug/improvement tickets

### 7. Follow Up

- Implement permanent fix
- Update runbook if needed
- Review monitoring coverage

## Escalation Paths

| Issue Type | Primary Contact | Secondary | After Hours |
|------------|----------------|-----------|-------------|
| Application | On-call Engineer | Tech Lead | PagerDuty |
| Database | DBA | Infrastructure Team | PagerDuty |
| Security | Security Team | CISO | PagerDuty |
| Compliance | Program Director | ACGME Liaison | PagerDuty |

## Tools and Resources

### Investigation Tools

```bash
# Log analysis
python scripts/logs/log_parser.py app.log --level ERROR
python scripts/logs/error_aggregator.py app.log

# Metrics
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana

# Tracing
open http://localhost:16686  # Jaeger

# Database
psql -U scheduler -d residency_scheduler
```

### Quick Commands

```bash
# Check application status
curl http://localhost:8000/health

# Check metrics endpoint
curl http://localhost:8000/metrics

# View recent errors
tail -f app.log | grep ERROR

# Check database connections
docker-compose exec db psql -U scheduler -c "SELECT count(*) FROM pg_stat_activity;"
```

## See Also

- [Logging Guide](logging-guide.md)
- [Observability Setup](observability-setup.md)
- [Security Policy](../security/DATA_SECURITY_POLICY.md)
